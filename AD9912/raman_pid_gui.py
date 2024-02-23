"""A module implementing GUI components for Raman PID control.

Created: 2022/03/25
Author: Jiyong Kang <kangz12345@snu.ac.kr>
"""

import contextlib
import enum
import math
import functools
import itertools
import json

from PyQt5.QtWidgets import (
	QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
	QAbstractSpinBox, QCheckBox, QComboBox, QGroupBox, QToolButton, QTabWidget,
	QFileDialog,
	QHBoxLayout, QVBoxLayout, QGridLayout,
	QSizePolicy,
	QApplication,
)
from PyQt5.QtGui import (QIntValidator, QDoubleValidator)
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, Qt, QTimer, QMutex,
						  QWaitCondition)

from Raman_PID_Controller import Raman_PID_Controller
from Arty_S7_v1_01 import ArtyS7

@contextlib.contextmanager
def mutex_region(mutex):
	"""Lock the mutex and unlock it at the end.

	This is a contextmanager which wraps a mutually exclusive region with the
	  given mutex.

	Usage:
	 	with mutex_region(mutex):
	 		...

	 	is equivalent to:

	 	mutex.lock()
	 	...
	 	mutex.unlock()

	Args:
		mutex: QMutex object which has lock() and unlock() method.

	Yields:
		mutex itself, but if it is used inside the with-block, it must be locked
		  when exiting the block.

	Returns:
		Generator which yields mutex. See python contextlib documentation for
		  details.
	"""
	mutex.lock()
	try:
		yield mutex
	finally:
		mutex.unlock()


def attach_text(widget, prefix=None, suffix=None):
	"""Returns a QWidget with QLabels attached on the left and/or right.
	
	Args:
		widget: Any QWidget object.
		prefix: Text to be attached on the left of the widget.
		suffix: Text to be attached on the right of the widget.

	Returns:
		A QWidget object and attached QLabels, in a 3-tuple. If a text is
		  None, the corresponding QLabel is not attached, and None is returned.
	"""
	prefix_label = QLabel(str(prefix)) if prefix else None
	suffix_label = QLabel(str(suffix)) if suffix else None
	if prefix_label is None and suffix_label is None:
		new_widget = widget
	else:
		new_widget = QWidget()
		layout = QHBoxLayout()
		for component in (prefix_label, widget, suffix_label):
			if component is not None:
				layout.addWidget(component)
		new_widget.setLayout(layout)
	return new_widget, prefix_label, suffix_label


def make_spinbox(value_type, value=None, min_=None, max_=None, range_=None,
				 step=None, decimals=None, expanding=True, readonly=False,
				 buttons=True, special="", prefix="", suffix=""):
	"""Returns a QDoubleSpinBox with the given properties.

	If an argument is None, that property is not applied, hence using default.

	Args:
		value_type: Either int or float. Give int for QSpinBox, and float for
		  QDoubleSpinBox.
		value: Initial value.
		min_, max_: Minimim, maximum value. If one of these is given, range_
		  must be None.
		range_: Range in a 2-tuple; (min, max). If this is given, min_ and max_
		  must be None.
		step: Single step size.
		decimals: Number of decimal digits after the floating point. This will
		  be ignored for value_type=int.
		expanding: If True, the horizontal size policy is set to Expanding.
		  Otherwise, Preferred is used.
		readonly: Whether the field is read-only.
		buttons: Whether to show the buttons or not. If True, use the default
		  button symbol.
		special: Special value text.
		prefix, suffix: Prefix and suffix of the spinbox.
	"""
	if not issubclass(value_type, (int, float)):
		raise ValueError(f"value_type must be either int or float. "
						 f"{value_type} is given.")
	if not (min_ is None and max_ is None) and range_ is not None:
		raise RuntimeError("min/max and range can't be given at the same time.")
	spinbox = QSpinBox() if issubclass(value_type, int) else QDoubleSpinBox()
	if decimals is not None and issubclass(value_type, float):
		spinbox.setDecimals(decimals)
	if min_ is not None:
		spinbox.setMinimum(min_)
	if max_ is not None:
		spinbox.setMaximum(max_)
	if range_ is not None:
		spinbox.setRange(*range_)
	if step is not None:
		spinbox.setSingleStep(step)
	if value is not None:
		spinbox.setValue(value)
	if expanding is not None:
		hpolicy = QSizePolicy.Expanding if expanding else QSizePolicy.Preferred
		spinbox.setSizePolicy(hpolicy, QSizePolicy.Fixed)
	if readonly is not None:
		spinbox.setReadOnly(readonly)
	if buttons is not None and not buttons:
		spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
	if special:
		spinbox.setSpecialValueText(special)
	if prefix:
		spinbox.setPrefix(prefix)
	if suffix:
		spinbox.setSuffix(suffix)

	return spinbox


def remove_all(layout):
	"""Removes all the children widgets in layout.

	Args:
		layout: The layout to be emptied.
	"""
	while True:
		item = layout.takeAt(0)
		if item:
			item.widget().deleteLater()
		else:
			break


class StepSpinBox(QWidget):
	"""A spinbox with adjustable step size.
	
	It contains a spinbox and another spinbox without buttons that holds the
	  current step size.

	Public attributes:
		spinbox: QSpinBox or QDoubleSpinBox object.
		stepsize: QSpinBox or QDoubleSpinBox object, which holds the current
		  step size.
		name_label: QLabel object at the left of the spinbox.
		unit_label: QLabel object at the right of the spinbox.
		value_type: float for double, int for int.
	"""

	def __init__(self, name, unit, is_double=True):
		"""
		Args:
			name: The text showed in front of the spinbox.
			unit: The text showed right after the spinbox.
			is_double: Whether to use QDoubleSpinBox or QSpinBox.
		"""
		super().__init__()
		if is_double:
			self.value_type = float
			self.spinbox = QDoubleSpinBox()
			self.stepsize = QDoubleSpinBox()
		else:
			self.value_type = int
			self.spinbox = QSpinBox()
			self.stepsize = QSpinBox()
		self.stepsize.setValue(self.spinbox.singleStep())
		self.stepsize.setButtonSymbols(QAbstractSpinBox.NoButtons)
		self.spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.stepsize.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

		titled_spinbox, self.name_label, self.unit_label = \
			attach_text(self.spinbox, f"{name}: ", f"{unit}")
		titled_stepsize, *_ = attach_text(self.stepsize, "Step: ")

		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(titled_spinbox)
		layout.addWidget(titled_stepsize)
		self.setLayout(layout)

		self.stepsize.valueChanged.connect(self._change_single_step)

	@pyqtSlot(int)
	@pyqtSlot(float)
	def _change_single_step(self, single_step):
		"""Slot for changing the single step size of the spinbox.

		Args:
			single_step: Desired new step size.
		"""
		self.spinbox.setSingleStep(single_step)

	def setSingleStep(self, single_step):
		"""Changes the single step size of the spinbox.

		In fact, this method only changes the value of stepsize, then it
		  triggers the slot which actually changes the step size of spinbox.

		Args:
			single_step: Desired new step size.
		"""
		self.stepsize.setValue(single_step)

	def singleStep(self):
		"""Returns the current single step size of the spinbox."""
		return self.stepsize.value()


class DDSControlBox(QWidget):
	"""A DDS control box which can control a DDS.
	
	Note that this does not have to have a DDS object. This will only provide
	  a user interface, emitting proper signals.

	This may have multiple frequency profiles.
	"""

	freqApplyRequested = pyqtSignal(int, float, object)
	freqReadRequested = pyqtSignal()
	powerApplyRequested = pyqtSignal(int, object)
	phaseApplyRequested = pyqtSignal(float, object)
	outputRequested = pyqtSignal(bool, object)
	freqChanged = pyqtSignal(int, float)

	def __init__(self, profiles=1, output_lock=False):
		"""
		Args:
			profiles: The number of frequency profiles, or an iterable of
			  frequency profile indices. For the former case, profile index
			  starts from 0, increased by 1.
			output_lock: If True, the output control is disabled during PID.
			  This feature is useful for the tracking DDS.
		"""
		super().__init__()
		if isinstance(profiles, int):
			self.profiles = range(profiles)
		else:
			self.profiles = tuple(profiles)

		# store the actual device values; -infinity acts as a value unknown
		self._actual_values = {k: -math.inf for k in ("power", "phase")}
		for i in self.profiles:
			self._actual_values["freq", i] = -math.inf

		self.fieldApplyRequested = {"freq": self.freqApplyRequested,
									"power": self.powerApplyRequested,
									"phase": self.phaseApplyRequested}

		# GUI components layout
		self._status_label = QLabel('Unknown')
		self._status_button = QPushButton('Turn OFF')  # will be toggled
		status_widget, *_ = attach_text(self._status_label, "Output status: ")
		status_layout = QHBoxLayout()
		status_layout.addWidget(status_widget)
		status_layout.addWidget(self._status_button)

		self._spinboxes = {}
		self._freqboxes = {i: self._freq_step_spin_box() for i in self.profiles}
		for i, freqbox in zip(self.profiles, self._freqboxes.values()):
			self._spinboxes["freq", i] = freqbox.spinbox

		_power = make_spinbox(int, range_=(0, 1023), step=50)
		self._spinboxes["power"] = _power

		_phase = make_spinbox(float, range_=(0, 360), step=10, decimals=2)
		self._spinboxes["phase"] = _phase

		self._read_button = QPushButton('Read freq.')
		self._apply_button = QPushButton('Apply all')
		buttons_layout = QHBoxLayout()
		buttons_layout.addWidget(self._read_button)
		buttons_layout.addWidget(self._apply_button)

		power_widget, *_ = attach_text(_power, 'Power: ')
		phase_widget, *_ = attach_text(_phase, 'Phase: ', 'deg.')
		power_phase_layout = QHBoxLayout()
		power_phase_layout.addWidget(power_widget)
		power_phase_layout.addWidget(phase_widget)

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addLayout(status_layout)
		for freqbox in self._freqboxes.values():
			layout.addWidget(freqbox)
		layout.addLayout(power_phase_layout)
		layout.addLayout(buttons_layout)
		self.setLayout(layout)

		self._disabled_when_lock = (
			*(self._spinboxes["freq", i] for i in self.profiles),
		)
		if output_lock:
			self._disabled_when_lock += (self._status_button,)

		# signal slot connection
		self._status_button.clicked.connect(self._toggle_status_button)
		for key, spinbox in self._spinboxes.items():
			self._check_spinbox_value(spinbox.value(), key, spinbox)
			spinbox.valueChanged.connect(
				functools.partial(self._check_spinbox_value,
								  key=key, spinbox=spinbox))
		self._read_button.clicked.connect(self.freqReadRequested)
		self._apply_button.clicked.connect(self._apply_clicked)
		for i in self.profiles:
			self._spinboxes["freq", i].valueChanged.connect(
				functools.partial(self.freqChanged.emit, i))

	def _freq_step_spin_box(self):
		freqbox = StepSpinBox('Freq.', 'kHz', is_double=True)
		freqbox.spinbox.setRange(3e3, 400e3)
		freqbox.spinbox.setDecimals(7)
		freqbox.stepsize.setRange(0, math.inf)
		freqbox.stepsize.setDecimals(7)
		return freqbox

	def setOutput(self, enabled):
		"""Changes the output status.

		Args:
			enabled: Desired output status, True for enabled, False for
			  disabled, and None for unknown.
		"""
		if enabled is False:
			self._status_button.setText("Turn ON")
			self._status_label.setText("Disabled")
			self._status_label.setStyleSheet("font-weight: bold; color: red;")
		else:
			self._status_button.setText("Turn OFF")
			if enabled:
				self._status_label.setText("Enabled")
				self._status_label.setStyleSheet("font-weight: bold; "
												 "color: green;")
			elif enabled is None:
				self._status_label.setText("Unknown")
				self._status_label.setStyleSheet("color: black;")

	def setFreq(self, index, freq, actual=False):
		"""Changes the frequency value.

		Args:
			index: The profile index.
			freq: Desired frequency value in kHz.
			actual: See setField().
		"""
		self.setField(("freq", index), freq, actual)

	def setFreqStep(self, index, step):
		"""Changes the frequency step size.

		Args:
			index: The profile index.
			step: Step size in kHz.
		"""
		self._freqboxes[index].setSingleStep(step)

	def setPower(self, power, actual=False):
		"""Changes the power value.

		Args:
			power: Desired power value.
			actual: See setField().
		"""
		self.setField("power", power, actual)

	def setPhase(self, phase, actual=False):
		"""Changes the phase value.

		Args:
			phase: Desired phase value in degree.
			actual: See setField().
		"""
		self.setField("phase", phase, actual)

	def setField(self, field, value, actual=False):
		"""Changes the field value.

		Args:
			field: ("freq", index), "power", or "phase".
			value: Desired value.
			actual: If True, the actual value is also updated. Otherwise, only
			  the value displayed on the spinbox is updated.
		"""
		spinbox = self._spinboxes[field]
		if actual:
			self._actual_values[field] = value
		spinbox.setValue(value)
		if actual:
			spinbox.valueChanged.emit(value)

	def output(self):
		"""Returns the output status.

		True if the output is enabled, False for disabled, and None for unknown.
		"""
		text = self._status_label.text()
		if text == "Enabled":
			return True
		elif text == "Disabled":
			return False
		else:
			return None

	def freq(self, index, actual=True):
		"""Returns the current frequency value of the spinbox.

		Args:
			index: Frequency profile index.
			actual: False for the spinbox value.
		"""
		if actual:
			return self._actual_values["freq", index]
		else:
			return self._spinboxes["freq", index].value()

	def freqStep(self, index):
		"""Returns the current frequency step size in kHz.
		
		Args:
			index: Frequency profile index.
		"""
		return self._freqboxes[index].singleStep()

	def power(self):
		"""Returns the current power value of the spinbox."""
		return self._spinboxes["power"].value()

	def phase(self):
		"""Returns the current phase value of the spinbox."""
		return self._spinboxes["phase"].value()

	def setLockState(self, lock):
		"""Changes the lock state.

		Args:
			lock: See RamanPIDGUI.setLockState().
		"""
		for widget in self._disabled_when_lock:
			widget.setEnabled(not lock)

	def configDict(self):
		"""Returns a dict which contains the config information of this GUI."""
		config = dict()
		config["output"] = self.output()
		config["step"] = self._freqboxes[self.profiles[0]].stepsize.value()
		for field, spinbox in self._spinboxes.items():
			if isinstance(field, tuple):
				field = json.dumps(field)
			config[field] = spinbox.value()
		return config

	def applyConfigDict(self, config):
		"""Applies a config dict to the current GUI state.

		Args:
			config: A dict that contains the config information. The format
			  must be the same as the one returned by configDict().
		"""
		for name, value in config.items():
			try:
				if "freq" in name:
					name = tuple(json.loads(name))
				if name == "output":
					self.setOutput(value)
				elif name == "step":
					for freqbox in self._freqboxes.values():
						freqbox.setSingleStep(value)
				elif name in self._spinboxes:
					self.setField(name, value)
				else:
					print(f"{self}: ignoring config ({name}: {value}).")
			except Exception as e:
				print(f"{self}: failed to apply config ({name}: {value}) "
				 	  f"with error={e!r}.")


	@pyqtSlot()
	def _toggle_status_button(self):
		"""Slot for toggling the status button."""
		enabled = (self._status_button.text() == "Turn ON")
		self.outputRequested.emit(enabled, None)

	def _is_actual(self, value, actual, spinbox):
		"""Returns whether the value and the actual value are equal.

		Args:
			value: Changed value to be compared.
			actual: Actual value to be compared.
			spinbox: QAbstractSpinBox object, e.g., QSpinBox and QDoubleSpinBox.
			  If it is a QDoubleSpinBox, the absolute tolerant for the
			  comparison depends on the decimals of the spinbox.
		"""
		if isinstance(spinbox, QDoubleSpinBox):
			tol = 0.5 / 10**spinbox.decimals()
			return math.isclose(value, actual, abs_tol=tol)
		else:
			return (value == actual)

	def _check_spinbox_value(self, value, key, spinbox):
		"""If they are different, the spinbox will be highlighted.

		Args:
			value: Changed value to be compared.
			key: Corresponding key; "freq", "power", or "phase".
			spinbox: QAbstractSpinBox object, e.g., QSpinBox and QDoubleSpinBox.
		"""
		actual = self._actual_values[key]
		equal = self._is_actual(value, actual, spinbox)
		self._highlight_spinbox(spinbox, not equal)  # highlight if not equal

	def _highlight_spinbox(self, spinbox, highlight):
		"""Highlights or de-highlights the spinbox.

		Args:
			spinbox: Target spinbox object to highlight or de-highlight.
			highlight: If True, the spinbox is highlighted. Otherwise, it is
			  de-highlighted.
		"""
		spinbox.setStyleSheet("QAbstractSpinBox { background-color: yellow; }"
							  if highlight else "")

	def _apply_clicked(self):
		"""Slot for the apply button clicked event.

		It emits apply-requested signals of not actual value fields. If all the
		  fields have actual values, it performs a force update. That is, emits
		  apply-requested signals for all the fields anyways.
		"""
		not_actual_keys = [
			key for key, spinbox
			in self._spinboxes.items()
			if not self._is_actual(spinbox.value(),
								   self._actual_values[key], spinbox)
		]
		if not not_actual_keys:
			# every value seems actual, hence force update
			not_actual_keys = self._spinboxes.keys()
		for key in not_actual_keys:
			spinbox = self._spinboxes[key]
			if spinbox.isEnabled():  # no apply for disabled spinboxes
				if "freq" in key:
					_, index = key
					self.freqApplyRequested.emit(index, spinbox.value(), None)
				else:
					self.fieldApplyRequested[key].emit(spinbox.value(), None)


class CalculatorBox(QWidget):
	"""AOM frequency calculator box."""

	class Direction(enum.Enum):
		POSITIVE = "fixed - var."  # As rep rate grows, var. also grows
		NEGATIVE = "var. - fixed"  # opposite

	class BeamPath(enum.Enum):
		SINGLE_PASS = "Single pass"
		DOUBLE_PASS = "Double pass"

	freqCalculated = pyqtSignal(float)

	def __init__(self, qubit_freq, rep_rate, fixed_freqs, sidebands,
				 ext_offset=None, ext_symmetric=None):
		"""
		Args:
			qubit_freq: Qubit frequency spinbox.
			rep_rate: Function that returns the repetition rate.
			fixed_freqs: See setFixedFreqs().
			sidebands: A dictionary whose keys are the names of sideband groups,
			  and values are the corresponding spinboxes which contain the
			  fundamental frequencies.
			ext_offset, ext_symmetric: External spinbox object which
			  contains a offset, symmetric detuning frequency. If None,
			  linking feature is disabled.
		"""
		super().__init__()

		self._qubit_freq = qubit_freq
		self._rep_rate = rep_rate
		self._fixed_freqs = fixed_freqs
		self._sideband_groups = sidebands
		self._ext_offset = ext_offset
		self._ext_symmetric = ext_symmetric

		self._fixed_freq_combobox = QComboBox()
		self.setFixedFreqs(fixed_freqs)
		fixed_freq_widget = attach_text(self._fixed_freq_combobox,
										"Fixed freq.: ")[0]

		self._comb_spinbox = make_spinbox(int,
										  value=100,
										  range_=(0, 255),
										  special="FIXED",
										  prefix="Comb spacing: ")
		self._dir_button = QPushButton(self.Direction.POSITIVE.value)
		self._beam_path_label = QLabel(self.BeamPath.DOUBLE_PASS.value)
		comb_layout = QHBoxLayout()
		comb_layout.addWidget(self._comb_spinbox)
		comb_layout.addWidget(self._dir_button)
		comb_layout.addWidget(self._beam_path_label)

		# sideband preset - will be initialized later by setSidebands()
		self._sideband_signs = {}
		self._sideband_orders = {}
		self._sideband_blur_targets = {}
		self._sideband_preset_layout = QGridLayout()
		sideband_preset_box = QGroupBox("Preset")
		sideband_preset_box.setLayout(self._sideband_preset_layout)
		# custom sideband
		self._custom_sideband_spinbox = make_spinbox(float,
													 min_=-math.inf,
													 max_=math.inf,
													 decimals=7,
													 buttons=False)
		self._custom_sideband_spinbox.setSuffix(" kHz")
		self._custom_sideband_sign = QToolButton()
		self._custom_sideband_order = make_spinbox(int,
												   range_=(0, 99),
												   expanding=False)
		self._sideband_calc_button = QPushButton("Sideband calculator")
		sub_layout = QHBoxLayout()
		sub_layout.addWidget(self._custom_sideband_spinbox)
		sub_layout.addWidget(self._custom_sideband_sign)
		sub_layout.addWidget(self._custom_sideband_order)
		custom_sideband_box = QGroupBox("Custom")
		custom_sideband_layout = QVBoxLayout()
		custom_sideband_layout.addLayout(sub_layout)
		custom_sideband_layout.addWidget(self._sideband_calc_button)
		custom_sideband_box.setLayout(custom_sideband_layout)
		# total sideband display
		self._total_sideband_spinbox = make_spinbox(float,
													min_=-math.inf,
													max_=math.inf,
													decimals=7,
													readonly=True,
													buttons=False)
		self.setSidebands(sidebands)
		sideband_layout = QGridLayout()
		sideband_layout.addWidget(sideband_preset_box, 0, 0)
		sideband_layout.addWidget(custom_sideband_box, 0, 1)
		sideband_layout.addWidget(
			attach_text(self._total_sideband_spinbox, "Total: ", "kHz")[0],
			1, 0, 1, 2)
		sideband_box = QGroupBox("Sideband")
		sideband_box.setLayout(sideband_layout)

		self._offset_spinbox = make_spinbox(float,
											range_=(-math.inf, math.inf),
											decimals=7,
											buttons=False)
		self._offset_checkbox = QCheckBox("link")
		self._symmetric_spinbox = make_spinbox(float,
											   range_=(-math.inf, math.inf),
											   decimals=7,
											   buttons=False)
		self._symmetric_checkbox = QCheckBox("link")
		detuning_layout = QGridLayout()
		detuning_layout.addWidget(attach_text(self._offset_spinbox,
											  "Offset: ", "kHz")[0], 0, 0)
		detuning_layout.addWidget(self._offset_checkbox, 0, 1)
		detuning_layout.addWidget(attach_text(self._symmetric_spinbox,
											  "Symmetric: ", "kHz")[0], 1, 0)
		detuning_layout.addWidget(self._symmetric_checkbox, 1, 1)
		detuning_box = QGroupBox("Detuning")
		detuning_box.setLayout(detuning_layout)

		self._calculate_button = QPushButton("Calculate")

		layout = QVBoxLayout()
		layout.addWidget(fixed_freq_widget)
		layout.addLayout(comb_layout)
		layout.addWidget(sideband_box)
		layout.addWidget(detuning_box)
		layout.addWidget(self._calculate_button)
		self.setLayout(layout)

		self._disabled_when_lock = (
			self._comb_spinbox,
			self._dir_button,
			self._calculate_button,
		)
		getter_names = (
			"fixedFreqName",
			"combSpacing",
			"direction",
			"beamPath",
			"customSidebandFreq",
			"customSidebandSign",
			"customSidebandOrder",
			"offsetDetuning",
			"offsetDetuningLinked",
			"symmetricDetuning",
			"symmetricDetuningLinked",
		)
		self._config_getters = {s: getattr(self, s) for s in getter_names}
		self._config_setters = {s: getattr(self, f"set{s[0].upper()}{s[1:]}")
								for s in getter_names}

		### signal connection and state initialization
		# linking
		self._link_pairs = {
			self._offset_checkbox: (self._ext_offset, self._offset_spinbox),
			self._symmetric_checkbox: (self._ext_symmetric,
									   self._symmetric_spinbox),
		}
		for checkbox, (ext, spinbox) in self._link_pairs.items():
			if ext is None:
				checkbox.setEnabled(False)
			else:
				checkbox.stateChanged.connect(self._link_changed)
		# direction
		self._dir_button.clicked.connect(self._toggle_direction)
		# sideband sign
		self.setCustomSidebandSign("-")
		self._custom_sideband_sign.clicked.connect(self._sideband_sign_clicked)
		# sideband order
		self._custom_sideband_order.valueChanged.connect(
			self._sideband_order_changed)
		self._custom_sideband_order.valueChanged.connect(
			self._update_total_sideband_value)
		self._custom_sideband_order.valueChanged.emit(0)
		# total sideband calculation
		self._custom_sideband_spinbox.valueChanged.connect(
			self._update_total_sideband_value)
		self._total_sideband_spinbox.valueChanged.connect(
			self._total_sideband_changed)
		# calculate
		self._calculate_button.clicked.connect(self.calculate)

	def fixedFreqName(self):
		"""Returns the currently selected fixed frequency name."""
		return self._fixed_freq_combobox.currentText()

	def combSpacing(self):
		"""Returns the comb spacing number."""
		return self._comb_spinbox.value()

	def direction(self, in_str=True):
		"""Returns the emission direction; POSITIVE or NEGATIVE.

		Args:
			in_str: If True, it returns "POSITIVE" or "NEGATIVE". Otherwise,
			  it returns the Direction enum object.
		"""
		direction = self.Direction(self._dir_button.text())
		if in_str:
			return direction.name
		else:
			return direction

	def beamPath(self, in_str=True):
		"""Returns the beam path; SINGLE_PASS or DOUBLE_PASS.

		Args:
			in_str: If True, it returns "SINGLE_PASS" or "DOUBLE_PASS".
			  Otherwise, it returns the BeamPath enum object.
		"""
		beam_path = self.BeamPath(self._beam_path_label.text())
		if in_str:
			return beam_path.name
		else:
			return beam_path

	def sidebandSign(self, group):
		"""Returns the sideband sign; "+" or "-".

		Args:
			group: Sideband group name.
		"""
		return self._sideband_signs[group].text()

	def customSidebandSign(self):
		"""Returns the custom sieband sign; "+" or "-"."""
		return self._custom_sideband_sign.text()

	def sidebandOrder(self, group):
		"""Returns the sideband order.

		Args:
			group: Sideband group name.
		"""
		return self._sideband_orders[group].value()

	def customSidebandOrder(self):
		"""Returns the custom sideband order."""
		return self._custom_sideband_order.value()

	def customSidebandFreq(self):
		"""Returns the custom sideband frequency in kHz."""
		return self._custom_sideband_spinbox.value()

	def offsetDetuning(self):
		"""Returns the offset detuning in kHz."""
		return self._offset_spinbox.value()

	def offsetDetuningLinked(self):
		"""Returns if the offset detuning is linked."""
		return self._offset_checkbox.checkState() == Qt.Checked

	def symmetricDetuning(self):
		"""Returns the symmetric detuning in kHz."""
		return self._symmetric_spinbox.value()

	def symmetricDetuningLinked(self):
		"""Returns if the symmetric detuning is linked."""
		return self._symmetric_checkbox.checkState() == Qt.Checked

	def setFixedFreqName(self, name):
		"""Changes the fixed frequency name.
		
		Args:
			name: Desired fixed frequency name.
		"""
		self._fixed_freq_combobox.setCurrentText(name)

	def setFixedFreqs(self, fixed_freqs):
		"""Changes the fixed frequencies information.

		If the current text is in the new fixed frequency names, it keeps the
		  current text.

		Args:
			fixed_freqs: Dictionary of {name: (freq, beampath)} where name is
			  the name of each frequency freq, and beampath is a BeamPath object 
			  which indicates freq goes to either SINGLE_PASS or DOUBLE_PASS.
		"""
		self._fixed_freqs = fixed_freqs
		prev_name = self._fixed_freq_combobox.currentText()
		self._fixed_freq_combobox.clear()
		self._fixed_freq_combobox.addItems(fixed_freqs)
		if prev_name in fixed_freqs:
			self._fixed_freq_combobox.setCurrentText(prev_name)

	def setCombSpacing(self, comb):
		"""Changes the comb spacing number.

		Args:
			comb: Desired comb spacing number.
		"""
		self._comb_spinbox.setValue(comb)

	def setDirection(self, direction):
		"""Changes the emission direction.

		Args:
			direction: Desired emission direction; POSITIVE or NEGATIVE.
		"""
		if isinstance(direction, str):
			direction = self.Direction[direction]
		self._dir_button.setText(direction.value)

	def setBeamPath(self, beam_path):
		"""Changes the beam path configuration.

		Args:
			beam_path: Desired beam path configuration; SINGLE_PASS or
			  DOUBLE_PASS.
		"""
		if isinstance(beam_path, str):
			beam_path = self.BeamPath[beam_path]
		self._beam_path_label.setText(beam_path.value)

	def setSidebandSign(self, group, sign):
		"""Changes the sideband sign.

		Args:
			group: Sideband group name.
			sign: Desired sign. It should be one of "+", "-", "red", or "blue".
		"""
		button = self._sideband_signs[group]
		self._set_sideband_sign(button, sign)

	def setCustomSidebandSign(self, sign):
		"""Changes the custom sideband sign.

		Args:
			sign: See setSidebandSign().
		"""
		self._set_sideband_sign(self._custom_sideband_sign, sign)

	def setSidebandOrder(self, group, order):
		"""Changes the sideband order.

		Args:
			group: Sideband group name.
			order: Desired order.
		"""
		self._sideband_orders[group].setValue(order)

	def setCustomSidebandOrder(self, order):
		"""Changes the custom sideband order.

		Args:
			order: Desired order.
		"""
		self._custom_sideband_order.setValue(order)

	def setCustomSidebandFreq(self, freq):
		"""Changes the custom sideband frequency.
		
		Args:
			freq: Desired sideband frequency in kHz.
		"""
		self._custom_sideband_spinbox.setValue(freq)

	def setOffsetDetuning(self, detuning):
		"""Changes the offset detuning and disables the link.

		Args:
			detuning: Desired offset detuning in kHz.
		"""
		self._offset_checkbox.setCheckState(Qt.Unchecked)
		self._offset_spinbox.setValue(detuning)

	def setOffsetDetuningLinked(self, linked):
		"""Changes the linkage of the offset detuning.

		If the external link target is None, this request is ignored.

		Args:
			linked: If True, link the offset detuning. Otherwise, unlink it.
		"""
		if self._offset_checkbox.isEnabled():
			self._offset_checkbox.setCheckState(Qt.Checked if linked
												else Qt.Unchecked)

	def setSymmetricDetuning(self, detuning):
		"""Changes the symmetric detuning and disables the link.

		Args:
			detuning: Desired symmetric detuning in kHz.
		"""
		self._symmetric_checkbox.setCheckState(Qt.Unchecked)
		self._symmetric_spinbox.setValue(detuning)

	def setSymmetricDetuningLinked(self, linked):
		"""Changes the linkage of the symmetric detuning.

		If the external link target is None, this request is ignored.

		Args:
			linked: If True, link the symmetric detuning. Otherwise, unlink it.
		"""
		if self._symmetric_checkbox.isEnabled():
			self._symmetric_checkbox.setCheckState(Qt.Checked if linked
												   else Qt.Unchecked)

	def setLockState(self, lock):
		"""Changes the lock state.

		Args:
			lock: See RamanPIDGUI.setLockState().
		"""
		for widget in self._disabled_when_lock:
			widget.setEnabled(not lock)

	def configDict(self):
		"""Returns a dict which contains the config information of this GUI."""
		return {name: getter() for name, getter in self._config_getters.items()}

	def applyConfigDict(self, config):
		"""Applies a config dict to this GUI.

		Args:
			config: A dict which contains the config information, whose format
			  must be the same as the one returned by configDict().
		"""
		for name, value in config.items():
			try:
				self._config_setters[name](value)
			except Exception as e:
				print(f"{self}: failed to apply config ({name}: {value}) "
					  f"with error={e!r}.")

	def customSidebandMode(self):
		"""Enables the custom sideband and disables the others."""
		for group in self._sideband_groups:
			self.setSidebandOrder(group, 0)
		self.setCustomSidebandOrder(1)

	@pyqtSlot()
	def calculate(self):
		"""Calculates the AOM frequency and emits the signal."""
		qubit_freq = self._qubit_freq.value()
		target_detuning = self._offset_spinbox.value()
		sideband = self._total_sideband_spinbox.value()
		symmetric = self._symmetric_spinbox.value()
		if sideband > 0:
			sideband += symmetric
		else:
			sideband -= symmetric
		target_detuning += sideband

		fixed_freq, fixed_beampath = self._fixed_freqs[self.fixedFreqName()]
		if fixed_beampath == self.BeamPath.DOUBLE_PASS:
			fixed_freq *= 2
		comb = self._comb_spinbox.value()

		if comb == 0:
			if self.direction(False) == self.Direction.NEGATIVE:
				aom_freq = fixed_freq - target_detuning
			else:
				aom_freq = fixed_freq + target_detuning
			if fixed_beampath == self.BeamPath.DOUBLE_PASS:
				aom_freq /= 2
		else:
			target_freq = qubit_freq + target_detuning
			rep_rate = self._rep_rate()
			delta = target_freq - comb * rep_rate
			if self.direction(False) == self.Direction.NEGATIVE:
				# delta = aom_freq - fixed_freq
				aom_freq = fixed_freq + delta
			else:
				# delta = fixed_freq - aom_freq
				aom_freq = fixed_freq - delta
			if self.beamPath(False) == self.BeamPath.DOUBLE_PASS:
				aom_freq /= 2
		self.freqCalculated.emit(aom_freq)
		return aom_freq

	def setSidebands(self, sidebands):
		"""Changes the sideband groups dictionary and GUI.

		Args:
			sidebands: See __init__().
		"""
		self._sideband_groups = sidebands
		self._sideband_signs = {s: QToolButton() for s in sidebands}
		self._sideband_orders = {
			s: make_spinbox(int, range_=(0, 99), expanding=False)
			for s in sidebands
		}
		self._sideband_blur_targets = {self._custom_sideband_order:
									   self._custom_sideband_spinbox}
		layout = self._sideband_preset_layout
		while True:
			item = layout.takeAt(0)
			if item:
				item.widget().deleteLater()
			else:
				break
		for r, s in enumerate(sidebands):
			label = QLabel(f"{s}: ")
			layout.addWidget(label, r, 0)
			layout.addWidget(self._sideband_signs[s], r, 1)
			layout.addWidget(self._sideband_orders[s], r, 2)
			# when harmonic order becomes 0, label is blurred
			self._sideband_blur_targets[self._sideband_orders[s]] = label

		for group, button in self._sideband_signs.items():
			self.setSidebandSign(group, "-")
			button.clicked.connect(self._sideband_sign_clicked)

		for spinbox in self._sideband_orders.values():
			spinbox.valueChanged.connect(self._sideband_order_changed)
			spinbox.valueChanged.connect(self._update_total_sideband_value)
			spinbox.valueChanged.emit(0)

		for spinbox in self._sideband_groups.values():
			spinbox.valueChanged.connect(self._update_total_sideband_value)

	def _set_sideband_sign(self, button, sign):
		"""Changes the sideband sign button style.

		Args:
			button: Target QAbstractButton object (maybe QToolButton).
			sign: See setSidebandSign().
		"""
		if sign == "+" or sign == "blue":
			button.setText("+")
			button.setStyleSheet("font-weight: bold; color: blue")
		elif sign == "-" or sign == "red":
			button.setText("-")
			button.setStyleSheet("font-weight: bold; color: red")
		self._update_total_sideband()

	@pyqtSlot()
	def _sideband_sign_clicked(self):
		"""Toggles the sign of the clicked button."""
		button = self.sender()
		sign = "+" if button.text() == "-" else "-"
		self._set_sideband_sign(button, sign)

	@pyqtSlot(int)
	def _sideband_order_changed(self, order):
		"""Blurs the target widget when order is zero.
		
		Args:
			order: Changed order value.
		"""
		target = self._sideband_blur_targets[self.sender()]
		if order == 0:
			target.setStyleSheet("color: silver;")
		else:
			target.setStyleSheet("color: black;")

	@pyqtSlot()
	def _update_total_sideband(self):
		"""Calculates and updates the total sideband frequency."""
		sideband = (self._custom_sideband_spinbox.value()
					* (1 if self._custom_sideband_sign.text() == "+" else -1)
					* self._custom_sideband_order.value())
		for group, spinbox in self._sideband_groups.items():
			sign = 1 if self._sideband_signs[group].text() == "+" else -1
			order = self._sideband_orders[group].value()
			sideband += spinbox.value() * sign * order
		self._total_sideband_spinbox.setValue(sideband)

	@pyqtSlot(int)
	@pyqtSlot(float)
	def _update_total_sideband_value(self, value):
		"""Accepts a dummy value to fit the slot signature."""
		self._update_total_sideband()

	@pyqtSlot(float)
	def _total_sideband_changed(self, value):
		"""Changes the color depending on the sign of the value."""
		spinbox = self.sender()  # this should be the total sideband spinbox
		prefix = ""
		if value > 0:
			color = "blue"
			prefix = "+"
		elif value < 0:
			color = "red"
		else:
			color = "black"
		spinbox.setPrefix(prefix)
		spinbox.setStyleSheet(f"color: {color}")

	@pyqtSlot()
	def _toggle_direction(self):
		"""Toggles the direction."""
		button = self.sender()  # this should be direction button
		if button.text() == self.Direction.POSITIVE.value:
			direction = self.Direction.NEGATIVE
		else:
			direction = self.Direction.POSITIVE
		button.setText(direction.value)

	@pyqtSlot(int)
	def _link_changed(self, state):
		"""Changes the link connection based on the checkbox state.
		
		Args:
			state: New checkbox state; Qt.CheckState.
		"""
		checkbox = self.sender()
		ext, spinbox = self._link_pairs[checkbox]
		if state == Qt.Checked:
			spinbox.setEnabled(False)
			spinbox.setValue(ext.value())
			ext.valueChanged.connect(spinbox.setValue)
		else:
			ext.valueChanged.disconnect(spinbox.setValue)
			spinbox.setEnabled(True)


class RamanPIDGUI(QWidget):
	"""Main GUI widget for Raman PID control."""

	class DDS(enum.Enum):
		TRACKING = 0
		A = 1
		B = 2
		C = 3

	class PROFILE(enum.Enum):
		TRACKING = 0
		A0 = 1
		B = 2
		C = 3
		A1 = 4

	DDS_OF = {
		PROFILE.TRACKING: DDS.TRACKING,
		PROFILE.A0: DDS.A,
		PROFILE.B: DDS.B,
		PROFILE.C: DDS.C,
		PROFILE.A1: DDS.A,
	}

	PROFILES_OF = {
		DDS.TRACKING: (PROFILE.TRACKING,),
		DDS.A: (PROFILE.A0, PROFILE.A1),
		DDS.B: (PROFILE.B,),
		DDS.C: (PROFILE.C,),
	}

	INDICES_OF = {dds: tuple(profile.value for profile in profiles)
				  for dds, profiles in PROFILES_OF.items()}

	def __init__(self, controller, sidebands=("Trap X",), fixed_freqs=("AOM",)):
		"""
		Args:
			controller: FPGA controller object.
			sidebands: An iterable of sideband group names.
			fixed_freqs: An iterable of fixed frequency names.
		"""
		super().__init__()

		self._controller = controller
		self._controller.adc_start()
		self._sideband_groups = sidebands
		self._fixed_freqs = {name: (0., CalculatorBox.BeamPath.SINGLE_PASS)
							 for name in fixed_freqs}
		self._mutex_fpga = QMutex()  # FPGA access
		self._mutex_lock = QMutex()  # lock control
		self._wait_cond_lock = None

		self._ctl_set_field = {  # controller field setters
			"freq": controller.set_frequency,
			"power": controller.set_current,
			"phase": controller.set_phase,
		}
		self._act_user_sampling_rate = 20.  # 20kHz

		self._load_index = {
			self.PROFILE.TRACKING: (0, 0),
			self.PROFILE.A0: (1, 0),
			self.PROFILE.A1: (1, 1),
			self.PROFILE.B: (2, 0),
			self.PROFILE.C: (2, 1),
		}

		self._ddsboxes = {dds: DDSControlBox(self.INDICES_OF[dds],
											 dds == self.DDS.TRACKING)
						  for dds in self.DDS}

		self._rep_rate = 0.

		### PID group box
		# PID parameters
		PID_PARAM_RANGE = (-1 << 20, 1 << 20)
		self._pid_spinboxes = {
			param: make_spinbox(int, range_=PID_PARAM_RANGE, expanding=False)
			for param in "PID"
		}
		pid_param_layout = QHBoxLayout()
		for param, spinbox in self._pid_spinboxes.items():
			pid_param_layout.addWidget(attach_text(spinbox, f"{param}: ")[0])
		pid_param_box = QGroupBox("PID parameters")
		pid_param_box.setLayout(pid_param_layout)

		# Lock/ADC
		self._lock_button = QPushButton("LOCK")
		self._lock_button.setCheckable(True)
		self._lock_button.setSizePolicy(QSizePolicy.Expanding,
										QSizePolicy.Expanding)
		self._update_checkbox = QCheckBox("Update every")
		self._update_checkbox.setStyleSheet("QCheckBox:checked{color: black;}"
											"QCheckBox:unchecked{color: grey;}")
		self._interval_spinbox = make_spinbox(float,
											  value=1,
											  range_=(0.5, 99.9),
											  decimals=1)
		self._interval_spinbox.setSuffix(" s")
		update_layout = QHBoxLayout()
		update_layout.addWidget(self._update_checkbox)
		update_layout.addWidget(self._interval_spinbox)
		lock_layout = QVBoxLayout()
		lock_layout.addWidget(self._lock_button)
		lock_layout.addLayout(update_layout)
		lock_widget = QWidget()
		lock_widget.setLayout(lock_layout)

		self._adc_spinbox = make_spinbox(float,
										 range_=(-math.inf, math.inf),
										 decimals=4,
										 readonly=True,
										 buttons=False)
		self._adc_spinbox.setSuffix(" V")
		self._adc_read_button = QPushButton("Read")
		self._adc_read_button.setSizePolicy(QSizePolicy.Preferred,
											QSizePolicy.Fixed)
		self._user_sampling_checkbox = QCheckBox("User smpl.")
		self._user_sampling_checkbox.setStyleSheet(
			"QCheckBox:checked{color: black}"
			"QCheckBox:unchecked{color: grey}"
		)
		self._user_sampling_spinbox = make_spinbox(float,
												   value=20,
												   range_=(0.012, 200),
												   decimals=3,
												   buttons=False)
		self._user_sampling_spinbox.setSuffix(" kHz")
		self._adc_plot_button = QPushButton("Plot over time")
		adc_read_layout = QHBoxLayout()
		adc_read_layout.addWidget(self._adc_spinbox)
		adc_read_layout.addWidget(self._adc_read_button)
		user_sampling_layout = QHBoxLayout()
		user_sampling_layout.addWidget(self._user_sampling_checkbox)
		user_sampling_layout.addWidget(self._user_sampling_spinbox)
		adc_layout = QVBoxLayout()
		adc_layout.addLayout(adc_read_layout)
		adc_layout.addLayout(user_sampling_layout)
		adc_layout.addWidget(self._adc_plot_button)
		adc_box = QGroupBox("ADC")
		adc_box.setLayout(adc_layout)
		# horizontal ratio 2 : 1
		policy = adc_box.sizePolicy()
		policy.setHorizontalStretch(2)
		adc_box.setSizePolicy(policy)
		policy = lock_widget.sizePolicy()
		policy.setHorizontalStretch(1)
		lock_widget.setSizePolicy(policy)
		lock_adc_layout = QHBoxLayout()
		lock_adc_layout.addWidget(adc_box)
		lock_adc_layout.addWidget(lock_widget)

		pid_top_layout = QVBoxLayout()
		pid_top_layout.addLayout(lock_adc_layout)
		pid_top_layout.addWidget(pid_param_box)

		# Other parameters
		self._qubit_freq_spinbox = make_spinbox(float,
												range_=(0, math.inf),
											    decimals=7,
											    buttons=False)
		qubit_freq_widget = attach_text(self._qubit_freq_spinbox,
										"Qubit freq.: ", "kHz")[0]

		self._fixed_freq_layout = QGridLayout()
		fixed_freq_box = QGroupBox("Fixed freq.")
		fixed_freq_box.setLayout(self._fixed_freq_layout)
		self._fixed_freq_spinboxes = {}  # will be initialized
		self._init_fixed_freqs()

		self._sideband_layout = QGridLayout()
		sideband_box = QGroupBox("Sideband")
		sideband_box.setLayout(self._sideband_layout)
		self._sideband_spinboxes = {}  # will be initialized
		self._init_sidebands()

		self._offset_detuning_spinbox = make_spinbox(float,
													 min_=-math.inf,
													 max_=math.inf,
													 decimals=7,
													 buttons=False)
		self._sym_detuning_spinbox = make_spinbox(float,
												  range_=(-math.inf, math.inf),
												  decimals=7,
												  buttons=False)
		detuning_layout = QGridLayout()
		for r, name, spinbox in ((0, "Offset", self._offset_detuning_spinbox),
							     (1, "Symmetric", self._sym_detuning_spinbox)):
			detuning_layout.addWidget(QLabel(f"{name}: "), r, 0)
			detuning_layout.addWidget(spinbox, r, 1)
			detuning_layout.addWidget(QLabel("kHz"), r, 2)
		detuning_box = QGroupBox("Detuning")
		detuning_box.setLayout(detuning_layout)

		self._rep_rate_spinbox = make_spinbox(float,
											  range_=(0, math.inf),
											  decimals=6,
											  readonly=True,
											  buttons=False)
		self._harmonics_spinbox = make_spinbox(int,
											   value=100,
											   range_=(1, 127),
											   readonly=True,
											   expanding=False,
											   buttons=False)
		rep_rate_layout = QHBoxLayout()
		rep_rate_layout.addWidget(attach_text(self._rep_rate_spinbox,
											  "Rep. rate: ", "kHz")[0])
		rep_rate_layout.addWidget(attach_text(self._harmonics_spinbox, "* ")[0])

		self._offset_spinbox = make_spinbox(float,
											range_=(0, math.inf),
											decimals=7,
											readonly=True,
											buttons=False)
		offset_widget, *_ = attach_text(self._offset_spinbox,
										"Tracking offset: ", "kHz")

		pid_box = QGroupBox("PID control")
		pid_box_layout = QVBoxLayout()
		pid_box_layout.addLayout(pid_top_layout)
		pid_box_layout.addWidget(qubit_freq_widget)
		pid_box_layout.addWidget(fixed_freq_box)
		pid_box_layout.addWidget(sideband_box)
		pid_box_layout.addWidget(detuning_box)
		pid_box_layout.addLayout(rep_rate_layout)
		pid_box_layout.addWidget(offset_widget)
		pid_box.setLayout(pid_box_layout)

		### config
		self._config_spinboxes = {
			**self._pid_spinboxes,
			"interval": self._interval_spinbox,
			"qubit": self._qubit_freq_spinbox,
			"offset": self._offset_detuning_spinbox,
			"symmetric": self._sym_detuning_spinbox,
			"harmonics": self._harmonics_spinbox,
			"tracking_offset": self._offset_spinbox,
		}
		self._config_file = None
		self._config_lineedit = QLineEdit()
		self._config_lineedit.setReadOnly(True)
		self._config_load_button = QPushButton("Load")
		self._config_save_button = QPushButton("Save")
		self._config_checkboxes = {}
		self._config_checkboxes["pid"] = QCheckBox("PID parameters")
		self._config_checkboxes["dds"] = QCheckBox("DDS status")
		self._config_checkboxes["calc"] = QCheckBox("Calculators")
		config_select_layout = QHBoxLayout()
		config_select_layout.addWidget(QLabel("Selective load/save: "))
		for checkbox in self._config_checkboxes.values():
			checkbox.setCheckState(Qt.Checked)
			config_select_layout.addWidget(checkbox)
		config_left_layout = QVBoxLayout()
		config_left_layout.addWidget(attach_text(self._config_lineedit,
												 "Path: ")[0])
		config_left_layout.addLayout(config_select_layout)
		config_left_widget = QWidget()
		config_left_widget.setLayout(config_left_layout)
		config_layout = QHBoxLayout()
		for stretch, widget in ((6, config_left_widget),
								(1, self._config_load_button),
								(1, self._config_save_button)):
			policy = widget.sizePolicy()
			policy.setHorizontalStretch(stretch)
			policy.setVerticalPolicy(QSizePolicy.Expanding)
			widget.setSizePolicy(policy)
			config_layout.addWidget(widget)
		config_box = QGroupBox("Config")
		config_box.setLayout(config_layout)

		### Tracking DDS group box
		tracking_box = QGroupBox("Tracking DDS")
		tracking_box_layout = QVBoxLayout()
		tracking_box_layout.addWidget(self._ddsboxes[self.DDS.TRACKING])
		tracking_box.setLayout(tracking_box_layout)

		layout = QGridLayout()
		layout.addWidget(pid_box, 0, 0, 2, 1)
		layout.addWidget(tracking_box, 2, 0, 1, 1)
		layout.addWidget(config_box, 0, 1, 1, 3)

		### AOM group box, overall layout
		self._calcboxes = {
			profile: CalculatorBox(qubit_freq=self._qubit_freq_spinbox,
								   rep_rate=self.repetitionRate,
								   fixed_freqs=self._fixed_freqs,
								   sidebands=self._sideband_spinboxes,
								   ext_offset=self._offset_detuning_spinbox,
								   ext_symmetric=self._sym_detuning_spinbox)
			for profile in self.PROFILE if profile != self.PROFILE.TRACKING
		}
		self._calctabs = {}
		for dds in self.DDS:
			if dds != self.DDS.TRACKING:
				tab = QTabWidget()
				for profile in self.PROFILES_OF[dds]:
					tab.addTab(self._calcboxes[profile], profile.name)
				self._calctabs[dds] = tab
		for dds, calctab in self._calctabs.items():
			# Calculator tab widget
			layout.addWidget(calctab, 1, dds.value)
			# DDS group box
			groupbox = QGroupBox(f"DDS {dds.name}")
			box_layout = QVBoxLayout()
			box_layout.addWidget(self._ddsboxes[dds])
			groupbox.setLayout(box_layout)
			layout.addWidget(groupbox, 2, dds.value)
		self.setLayout(layout)

		### signal connection
		# config
		self._config_load_button.clicked.connect(self._config_load_clicked)
		self._config_save_button.clicked.connect(self._config_save_clicked)
		# dds frequency calculation
		for profile, calcbox in self._calcboxes.items():
			dds = self.DDS_OF[profile]
			calcbox.freqCalculated.connect(
				functools.partial(self._ddsboxes[dds].setFreq, profile.value))
		# dds control
		for dds, ddsbox in self._ddsboxes.items():
			ddsbox.outputRequested.connect(self._output_requested(dds))
			ddsbox.freqApplyRequested.connect(self._apply_requested(dds,
																	"freq"))
			ddsbox.powerApplyRequested.connect(self._apply_requested(dds,
																	 "power"))
			ddsbox.phaseApplyRequested.connect(self._apply_requested(dds,
																	 "phase"))
			for profile in self.PROFILES_OF[dds]:
				ddsbox.freqReadRequested.connect(
					self._freq_read_requested(profile))
		# repetition rate
		self._ddsboxes[self.DDS.TRACKING].freqChanged.connect(
			self._update_rep_rate)
		self._harmonics_spinbox.valueChanged.connect(self._update_rep_rate)
		self._offset_spinbox.valueChanged.connect(self._update_rep_rate)
		# lock
		self._lock_button.toggled.connect(self._lock_toggled)
		# adc
		self._adc_read_button.clicked.connect(self._adc_read_clicked)
		self._adc_plot_button.clicked.connect(self._plot_clicked)
		self._user_sampling_spinbox.valueChanged.connect(
			self._user_sampling_rate_changed)
		self._user_sampling_spinbox.editingFinished.connect(
			self._update_user_sampling_rate)
		self._user_sampling_checkbox.stateChanged.connect(
			self._user_sampling_checked)
		self._update_user_sampling_rate()
		self._user_sampling_spinbox.setEnabled(False)
		self._user_sampling_checkbox.setChecked(False)

		# auto update
		self._timer = QTimer()
		self._mutex_update = QMutex()
		self._timer.timeout.connect(self._auto_update)
		self._update_checkbox.stateChanged.connect(self._auto_update_toggled)
		self._interval_spinbox.valueChanged.connect(self._interval_changed)

	def lockState(self):
		"""Returns the current lock state."""
		return self._lock_button.isChecked()

	def setLockState(self, lock, wait_cond=None):
		"""Changes the lock state.

		Note that this does not lock or unlock the mutex, but the button toggled
		  slot does. Therefore, the caller must not lock the mutex before 
		  calling this method.
		
		Args:
			lock: True for starting lock, and False for stopping.
			wait_cond: QWaitCondition object in case of waiting for the lock
			  state change.
		"""
		if wait_cond and self.lockState() == lock:
			wait_cond.wakeAll()
			return
		self._wait_cond_lock = wait_cond
		self._lock_button.setChecked(lock)

	def userSamplingState(self):
		"""Returns whether user sampling is currently on."""
		return self._user_sampling_checkbox.isChecked()

	def lockMutex(self):
		"""Returns the QMutex object for lock control."""
		return self._mutex_lock

	def interval(self):
		"""Returns the current auto update interval in msec."""
		return int(self._interval_spinbox.value() * 1e3)

	def repetitionRate(self):
		"""Returns the current repetition rate."""
		return self._rep_rate

	def calculatorBox(self, profile):
		"""Returns the CalculatorBox object corrensponding to the given profile.

		Args:
			profile: RamanPIDGUI.PROFILE enum object.
		"""
		return self._calcboxes[profile]

	def ddsBox(self, dds):
		"""Returns the DDSBox object corresponding to the given DDS.

		Args:
			dds: RamanPIDGUI.DDS enum object.
		"""
		return self._ddsboxes[dds]

	def configDict(self):
		"""Returns a dict which contains the config information of this GUI."""
		config = {}
		if self._config_checked("pid"):
			config.update({name: spinbox.value()
					  	   for name, spinbox
					  	   in self._config_spinboxes.items()})
			config["fixed_freqs"] = {name: (freq, beampath.name)
						   		 	 for name, (freq, beampath)
						   		 	 in self._fixed_freqs.items()}
			config["sidebands"] = {name: spinbox.value()
						 		   for name, spinbox
						 		   in self._sideband_spinboxes.items()}
		if self._config_checked("dds"):
			config["ddsboxes"] = {dds.name: ddsbox.configDict()
								  for dds, ddsbox
								  in self._ddsboxes.items()}
		if self._config_checked("calc"):
			config["calcboxes"] = {profile.name: calcbox.configDict()
								   for profile, calcbox
								   in self._calcboxes.items()}
		return config

	def applyConfigDict(self, config):
		"""Applies a config dict to this GUI.

		Args:
			config: A dict that contains the config information. The format
			  must be the same as the one returned by configDict().
		"""
		config = config.copy()
		fixed_freqs = config.pop("fixed_freqs", None)
		sidebands = config.pop("sidebands", None)
		if fixed_freqs and self._config_checked("pid"):
			try:
				self._fixed_freqs = {
					name: (freq, CalculatorBox.BeamPath[beampath])
					for name, (freq, beampath) in fixed_freqs.items()
				}
			except Exception as e:
				print(f"{self}: failed to apply config "
					  f"(fixed_freqs: {fixed_freqs}) with error={e!r}.")
			else:
				self._init_fixed_freqs()
				for calcbox in self._calcboxes.values():
					calcbox.setFixedFreqs(self._fixed_freqs)
				for name, (value, _) in fixed_freqs.items():
					try:
						self._fixed_freq_spinboxes[name].setValue(value)
					except Exception as e1:
						print(f"{self}: failed to apply fixed_freq "
							  f"({name}: {value}) with error={e1!r}.")
		if sidebands and self._config_checked("pid"):
			if sidebands.keys() != set(self._sideband_groups):
				self._sideband_groups = tuple(sidebands)
				self._init_sidebands()
				for calcbox in self._calcboxes.values():
					calcbox.setSidebands(self._sideband_spinboxes)
			for name, value in sidebands.items():
				try:
					self._sideband_spinboxes[name].setValue(value)
				except Exception as e:
					print(f"{self}: failed to apply sideband ({name}: {value}) "
						  f"with error={e!r}.")
		ddsboxes = config.pop("ddsboxes", None)
		if ddsboxes and self._config_checked("dds"):
			for name, dds_config in ddsboxes.items():
				try:
					self._ddsboxes[self.DDS[name]].applyConfigDict(dds_config)
				except Exception as e:
					print(f"{self}: failed to apply ddsbox config "
						  f"({name}: {dds_config}) with error={e!r}.")
		calcboxes = config.pop("calcboxes", None)
		if calcboxes and self._config_checked("calc"):
			for name, calc_config in calcboxes.items():
				try:
					self._calcboxes[self.PROFILE[name]].applyConfigDict(calc_config)
				except Exception as e:
					print(f"{self}: failed to apply calcbox config "
						  f"({name}: {calc_config}) with error={e!r}.")
		if self._config_checked("pid"):
			for name, value in config.items():
				try:
					self._config_spinboxes[name].setValue(value)
				except Exception as e:
					print(f"{self}: failed to apply config ({name}: {value}) "
						  f"with error={e!r}.")

	def _output_requested(self, dds):
		"""Constructs a slot for output status change requested signals.

		Args:
			dds: DDS enum object.

		Returns:
			A slot function for output status change requested signals.
		"""
		@pyqtSlot(bool, QWaitCondition)
		def _slot(enabled, wait_cond):
			with mutex_region(self.lockMutex()):
				lock = self.lockState()
				with mutex_region(self._mutex_fpga):
					if lock:
						self._controller.comp_stop()
					if enabled:
						self._controller.power_up(dds.value)
					else:
						self._controller.power_down(dds.value)
					self._ddsboxes[dds].setOutput(enabled)
					if lock:
						self._controller.comp_start()
				if wait_cond:
					wait_cond.wakeAll()
		return _slot

	def _apply_requested(self, dds, field):
		"""Constructs a slot for apply requested signals.

		Args:
			dds: DDS enum object.
			field: One of "freq", "power", or "phase".

		Returns:
			A slot function for apply requested signals.
		"""
		@pyqtSlot(int, QWaitCondition)
		@pyqtSlot(float, QWaitCondition)
		@pyqtSlot(int, float, QWaitCondition)  # freq
		def _slot(*args):
			ctl_setter = self._ctl_set_field[field]
			wait_cond = args[-1]
			if field == "freq":
				index, value = args[:-1]
				applied_value = value / 1e3  # kHz -> MHz
				xfield = ("freq", index)  # extended field
			else:
				index, value = dds.value, args[0]
				applied_value = value
				xfield = field
			with mutex_region(self.lockMutex()):
				lock = self.lockState()
				with mutex_region(self._mutex_fpga):
					if lock:
						self._controller.comp_stop()
					ctl_setter(applied_value, index)
					self._ddsboxes[dds].setField(xfield, value, actual=True)
					if lock:
						self._controller.comp_start()
				if wait_cond:
					wait_cond.wakeAll()
		return _slot

	def _freq_read_requested(self, profile):
		"""Constructs a slot for frequency read requested signals.

		Args:
			profile: PROFILE enum object.

		Returns:
			A slot function for frequency read requested signals.
		"""
		index, subindex = self._load_index[profile]
		dds = self.DDS_OF[profile]
		@pyqtSlot()
		def _slot():
			with mutex_region(self._mutex_fpga):
				adc, *freqs = self._controller.load_data(index)
				freq = freqs[subindex] * 1e3  # MHz -> kHz
				self._ddsboxes[dds].setFreq(profile.value, freq, actual=True)
		return _slot

	@pyqtSlot(int)
	@pyqtSlot(float)
	@pyqtSlot(int, float)
	def _update_rep_rate(self, *args):
		"""Updates the repetition rate.

		This is a slot for the tracking DDS frequency spinbox and the harmonic
		  order spinbox.

		Args:
			args: Dummy argument for the slot signature.
		"""
		offset = self._offset_spinbox.value()
		dds, profile = self.DDS.TRACKING, self.PROFILE.TRACKING
		tracking = self._ddsboxes[dds].freq(profile.value)
		harmonics = offset + tracking
		self._rep_rate = harmonics / self._harmonics_spinbox.value()
		self._rep_rate_spinbox.setValue(self._rep_rate)

	@pyqtSlot(bool)
	def _lock_toggled(self, checked):
		"""Toggles the lock state."""
		with mutex_region(self.lockMutex()):
			success = self._set_lock_state(checked)
			if self._wait_cond_lock:
				self._wait_cond_lock.wakeAll()
		if success:
			if checked:
				self._lock_button.setText("STOP")
			else:
				self._lock_button.setText("LOCK")
		else:
			# restore the button's check state
			self._lock_button.toggle()

	@pyqtSlot()
	def _update_user_sampling_rate(self):
		"""Updates the user sampling rate with the current spinbox value."""
		self._set_user_sampling_rate(self._user_sampling_spinbox.value() * 1e3)

	def _set_user_sampling_rate(self, rate):
		"""Changes the user sampling rate.

		This also changes the spinbox value, to the actual sampling rate.
		Note that the sampling rate must be 50MHz devided by an integer.
		If the given rate does not meet the condition, the closest valid
		  sampling rate is chosen.

		Args:
			rate: Desired sampling rate in Hz.
		"""
		act_rate = self._controller.user_sampling_rate(rate) / 1e3  # in kHz
		decimals = self._user_sampling_spinbox.decimals()
		rounded = round(act_rate,  decimals)
		self._act_user_sampling_rate = act_rate
		self._user_sampling_spinbox.setValue(rounded)
		if rounded == rate / 1e3:
			# valueChanged signal will not be emitted
			self._user_sampling_rate_changed(rounded)

	@pyqtSlot(float)
	def _user_sampling_rate_changed(self, rate):
		"""Slot for tracking the user sampling rate change.

		Args:
			rate: Changed user sampling rate in kHz.
		"""
		decimals = self._user_sampling_spinbox.decimals()
		rounded = round(self._act_user_sampling_rate, decimals)
		if rate == rounded:
			self._user_sampling_spinbox.setStyleSheet("")
		else:
			self._user_sampling_spinbox.setStyleSheet("background-color: yellow")

	def _set_user_sampling(self, on):
		"""Starts or stops user sampling.

		Args:
			on: True for starting user sampling, False for stopping.
		"""
		if on:
			self._controller.user_sampling()
		else:
			self._controller.terminate_condition()

	@pyqtSlot(int)
	def _user_sampling_checked(self, state):
		"""Slot for user sampling checkbox.

		Args:
			state: Qt.CheckState.
		"""
		on = (state == Qt.Checked)
		self._user_sampling_spinbox.setEnabled(on)
		self._set_user_sampling(on)

	@pyqtSlot()
	def _plot_clicked(self):
		"""Plots ADC over time."""
		with mutex_region(self._mutex_fpga):
			if not self.lockState():
				self._controller.adc_start()
			freqdiff = self._controller.adc_load_large_data()  # in Hz
		if not self.lockState() and freqdiff and self.userSamplingState():
			self._ddsboxes[self.DDS.TRACKING].setFreqStep(
				self.PROFILE.TRACKING.value,
				freqdiff / 1e3)

	def _set_lock_state(self, lock):
		"""Changes the lock state.

		Args:
			lock: True for starting lock, and False for stopping.

		Returns:
			True if the state is successfully changed, and False otherwise.
		"""
		if lock and not self._okay_to_lock():
			print("ERROR: cannot start locking.")
			return False
		for spinbox in self._pid_spinboxes.values():
			spinbox.setEnabled(not lock)
		for widget in itertools.chain(self._ddsboxes.values(), 
									  self._calcboxes.values()):
			widget.setLockState(lock)
		if lock:
			self._start_lock()
		else:
			self._stop_lock()
		return True

	def _okay_to_lock(self):
		"""Return True if it is okay to start locking, and False otherwise."""
		if not self._ddsboxes[self.DDS.TRACKING].output():
			return False
		return True

	def _start_lock(self):
		"""Sets up the PID parameters of the FPGA, and starts locking."""
		ctl = self._controller
		with mutex_region(self._mutex_fpga):
			ctl.comp_stop()  # for safety
			ctl.terminate_condition()
			p, i, d = (self._pid_spinboxes[param].value() for param in "PID")
			ctl.comp_set(p, i, d)
			comb_numbers = (self._calcboxes[self.PROFILE[profile]].combSpacing()
					   		for profile in ("A0", "B", "C", "A1"))
			ctl.comp_set_comb_number(*comb_numbers)
			ctl.comp_set_harmonic_order(self._harmonics_spinbox.value())
			for profile, calcbox in self._calcboxes.items():
				if calcbox.direction(False) == CalculatorBox.Direction.POSITIVE:
					ctl.normal_feedback(profile.value)
				else:  # NEGATIVE
					ctl.reverse_feedback(profile.value)
				if calcbox.beamPath(False) == CalculatorBox.BeamPath.DOUBLE_PASS:
					ctl.double_pass(profile.value)
				else:  # SINGLE_PASS
					ctl.single_pass(profile.value)
			ctl.adc_start()
			ctl.comp_start()
		if self._update_checkbox.isChecked():
			self._timer.start(self.interval())

	def _stop_lock(self):
		"""Stops compensation and ADC."""
		self._timer.stop()
		# never share the serial port communication
		with mutex_region(self._mutex_fpga):
			ctl = self._controller
			ctl.comp_stop()
			ctl.dds_stop()
		with mutex_region(self._mutex_update):
			# wait for the last update to finish
			pass
		self._auto_update()

	def _init_fixed_freqs(self):
		"""Initializes the fixed frequency spinboxes and beam path labels.

		Note that self._fixed_freqs and self._fixed_freq_beampaths must be
		  updated before this method is called.
		"""
		self._fixed_freq_spinboxes = {
			name: make_spinbox(float,
							   range_=(0, math.inf),
							   decimals=7,
							   readonly=True,
							   buttons=False)
			for name in self._fixed_freqs
		}
		layout = self._fixed_freq_layout
		remove_all(layout)
		for r, (name, (_, beampath)) in enumerate(self._fixed_freqs.items()):
			layout.addWidget(QLabel(f"{name}: "), r, 0)
			layout.addWidget(self._fixed_freq_spinboxes[name], r, 1)
			layout.addWidget(QLabel("kHz"), r, 2)
			layout.addWidget(QLabel(f"{beampath.name}"), r, 3)

	def _init_sidebands(self):
		"""Initializes the sideband spinboxes.

		Note that self._sideband_groups must be updated before this method is
		  called.
		"""
		self._sideband_spinboxes = {
			group: make_spinbox(float,
								range_=(0, math.inf),
								decimals=7,
								buttons=False)
			for group in self._sideband_groups
		}
		layout = self._sideband_layout
		remove_all(layout)
		for r, (group, spinbox) in enumerate(self._sideband_spinboxes.items()):
			layout.addWidget(QLabel(f"{group}: "), r, 0)
			layout.addWidget(spinbox, r, 1)
			layout.addWidget(QLabel("kHz"), r, 2)

	def _config_checked(self, name):
		"""Returns whether the config checkbox is checked.
		
		Args:
			name: "pid", "dds", or "calc".
		"""
		return self._config_checkboxes[name].checkState() == Qt.Checked

	@pyqtSlot()
	def _config_load_clicked(self):
		"""Opens a file open dialog to open a config file."""
		path = self._config_file if self._config_file else "."
		filename = QFileDialog.getOpenFileName(self,
											   "Open a config file",
											   path,
											   "JSON config files (*.json)")[0]
		if filename:
			self._config_file = filename
			self._config_lineedit.setText(filename)
			with open(filename, "r") as file:
				config = json.load(file)
			self.applyConfigDict(config)

	@pyqtSlot()
	def _config_save_clicked(self):
		"""Saves the current configuration into a file."""
		path = self._config_file if self._config_file else "."
		filename = QFileDialog.getSaveFileName(self,
											   "Save to a config file",
											   path,
											   "JSON config files (*.json)")[0]
		if filename:
			self._config_file = filename
			self._config_lineedit.setText(filename)
			with open(filename, "w") as file:
				json.dump(self.configDict(), file, indent=4)

	@pyqtSlot()
	def _adc_read_clicked(self):
		"""Reads the current ADC input value."""
		with mutex_region(self._mutex_fpga):
			adc_voltage = self._controller.load_data(1)[0]
			self._adc_spinbox.setValue(adc_voltage)

	@pyqtSlot(int)
	def _auto_update_toggled(self, state):
		"""Auto update checkbox is toggled.

		Args:
			state: The new state of the update checkbox.
		"""
		if self.lockState():
			if state == Qt.Checked:
				self._timer.start(self.interval())
			else:
				self._timer.stop()

	@pyqtSlot(float)
	def _interval_changed(self, value):
		"""Auto update interval is changed.

		Args:
			value: The new interval in sec. However, we have self.interval().
		"""
		self._timer.setInterval(self.interval())

	@pyqtSlot()
	def _auto_update(self):
		"""Updates all DDS values and ADC value.

		Note that the DDS frequencies of board 1 and 2 are at difference PID
		  cycles, since they read by two distinct command. Between the two
		  commands, many PID cycles will proceed.

		When it fails to lock, i.e., previous update is still in progress, it
		  skips and ignores this update request.
		"""
		if self._mutex_update.tryLock():
			with mutex_region(self._mutex_fpga):
				freqs = {}
				for i in range(3):
					adc, *_freqs = self._controller.load_data(i)
					freqs[i] = _freqs
				for profile in self.PROFILE:
					dds = self.DDS_OF[profile]
					index, subindex = self._load_index[profile]
					freq = freqs[index][subindex] * 1e3
					self._ddsboxes[dds].setFreq(profile.value, freq, actual=True)
				self._adc_spinbox.setValue(adc)
			self._mutex_update.unlock()


class ScanHelper:
	"""Provides some convenient methods for scanning through RamanPIDGUI."""

	def __init__(self, gui, profiles):
		"""
		Note that even if there is only one target DDS, the arguments should be
		  tuples.

		Args:
			gui: RamanPIDGUI object.
			profiles: Tuple of target RamanPIDGUI.PROFILE enum objects.
		"""
		self.gui = gui
		self.profiles = profiles
		self.ddsboxes = tuple(gui.ddsBox(gui.DDS_OF[p]) for p in profiles)
		self._iter = None  # should be assigned later
		self._gui_enabled = None
		self._wait_cond = QWaitCondition()

	def __iter__(self):
		"""This must return the scan parameter values."""
		raise NotImplementedError

	def _each_step(self, values, mutex):
		"""Actions taken in each step of the scan.

		Note that the lock mutex of RamanPIDGUI is already acquired when this
		  method is called. It must remain locked when it goes back to the
		  caller.

		Args:
			values: The current scan parameter values. It is a tuple whose order
			  is the same as that of DDSes.
			mutex: The lock mutex of RamanPIDGUI, which is currently locked.
		"""
		pass

	def next_step(self):
		"""Take the next step of the scan.

		If the PID lock is running, it pauses the lock and resumes it after
		  changing the scan parameter. Therefore, it needs to acquire the lock.
		The lock mutex of RamanPIDGUI must be unlocked before this method is
		  called.

		Returns:
			Applied value.
		"""
		with mutex_region(self.gui.lockMutex()) as mutex:
			locked = self.gui.lockState()
			if locked:
				# since the repetition rate keeps changing during lock,
				# lock must be paused for a moment for precise calculation. 
				self.gui.setLockState(False, self._wait_cond)
				self._wait_cond.wait(mutex)
			try:
				values = next(self._iter)
			except StopIteration:
				values = None
			else:
				self._each_step(values, mutex)
			finally:
				if locked:
					self.gui.setLockState(True)
		return values

	def ready(self):
		"""Gets ready for scanning."""
		self._gui_enabled = self.gui.isEnabled()
		self.gui.setEnabled(False)

	def wrapup(self):
		"""Wraps up the scanning."""
		self.gui.setEnabled(self._gui_enabled)


class FieldScanHelper(ScanHelper):
	"""Specialized for ordinary field scan."""

	def __init__(self, gui, profiles, fields, values):
		"""
		Note that even if there is only one target profile, the arguments should
		  be tuples.

		Args:
			gui: RamanPIDGUI object.
			profiles: Tuple of target RamanPIDGUI.PROFILE enum objects.
			fields: Scan target field: "freq", "power", "phase".
			values: Iterable of scan value range.
		"""
		super().__init__(gui, profiles)
		self.fields = fields
		self.values = tuple(values)
		self._iter = iter(self.values)

	def __iter__(self):
		return iter(self.values)

	def _each_step(self, values, mutex):
		"""Overriden."""
		pdfv = zip(self.profiles, self.ddsboxes, self.fields, values)
		for profile, ddsbox, field, value in pdfv:
			if field == "power":
				value = round(value)
			if field == "freq":
				index = profile.value
				ddsbox.freqApplyRequested.emit(index, value, self._wait_cond)
			else:
				ddsbox.fieldApplyRequested[field].emit(value, self._wait_cond)
			self._wait_cond.wait(mutex)


class DetuningScanHelper(ScanHelper):
	"""Specialized for frequency detuning scan."""

	def __init__(self, gui, profiles, sign, detuning):
		"""
		Note that even if there is only one target profile, the arguments should
		  be tuples.

		Args:
			gui: RamanPIDGUI object.
			profiles: Tuple of target RamanPIDGUI.PROFILE enum objects.
			sign: Tuple of the sign of the detuning; either "+" or "-".
			detuning: Iterable of tuples of the desired detuning values in kHz.
		"""
		super().__init__(gui, profiles)
		self.calcboxes = tuple(gui.calculatorBox(p) for p in profiles)
		self.signs = sign
		self.detunings = tuple(detuning)
		self._iter = iter(self.detunings)

	def __iter__(self):
		return iter(self.detunings)

	def _each_step(self, detunings, mutex):
		"""Overriden."""
		pcdd = zip(self.profiles, self.calcboxes, self.ddsboxes, detunings)
		for profile, calcbox, ddsbox, detuning in pcdd:
			index = profile.value
			calcbox.setCustomSidebandFreq(detuning)
			freq = calcbox.calculate()
			ddsbox.freqApplyRequested.emit(index, freq, self._wait_cond)
			self._wait_cond.wait(mutex)

	def ready(self):
		"""Extended; sets up the calculator boxes."""
		super().ready()
		for calcbox, sign in zip(self.calcboxes, self.signs):
			calcbox.customSidebandMode()
			calcbox.setCustomSidebandSign(sign)


if __name__ == "__main__":
	app = QApplication([])
	gui = RamanPIDGUI(Raman_PID_Controller(ArtyS7("COM10"), verbose=True))
	gui.show()
	app.exec_()
