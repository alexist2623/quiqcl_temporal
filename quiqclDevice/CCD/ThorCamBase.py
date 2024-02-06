"""
@author: JUNHO JEONG
"""

class ThorCamBase(object):
    """Base class with all the config options that the scientific Thor cams
    may support.
    """
    _thor_bin_path = "C:/Program Files/Thorlabs/Scientific Imaging/ThorCam/"
    """Default path"""

    _supported_freqs = ['20 MHz', ]
    """The supported frequencies."""

    _freq = '20 MHz'
    """The frequency to use."""

    _supported_taps = ['1', ]
    """The supported taps."""

    _taps = '1'
    """The tap to use."""

    _supports_color = False
    """Whether the camera supports color."""

    _exposure_range = [0, 2000]
    """The supported exposure range in ms."""

    _exposure_ms = 5
    """The exposure value in ms to use."""

    _binning_x_range = [0, 0]
    """The supported exposure range."""

    _binning_x = 0
    """The x binning value to use."""

    _binning_y_range = [0, 0]
    """The supported exposure range."""

    _binning_y = 0
    """The y binning value to use."""

    _sensor_size = [0, 0]
    """The size of the sensor in pixels."""

    _roi_x = 0
    """The x start position of the ROI in pixels."""

    _roi_y = 0
    """The y start position of the ROI in pixels."""

    _roi_width = 0
    """The width after the x start position of the ROI in pixels, to use."""

    _roi_height = 0
    """The height after the y start position of the ROI in pixels, to use."""

    _gain_range = [0, 100]
    """The supported exposure range."""

    _gain = 0
    """The gain value to use."""

    _black_level_range = [0, 100]
    """The supported exposure range."""

    _black_level = 0
    """The black level value to use."""

    _frame_queue_size = 1
    """The max number of image frames to be allowed on the camera's hardware
    queue. Once exceeded, the frames are dropped."""

    _supported_triggers = ['SW Trigger', 'HW Trigger']
    """The trigger types supported by the camera."""

    _trigger_type = 'SW Trigger'
    """The trigger type of the camera to use."""

    _trigger_count = 1
    """The number of frames to capture in response to the trigger."""

    _num_queued_frames = 0
    """The number of image frames currently on the camera's hardware queue."""

    _color_processor = None
    """Colors are not supported"""

    _color_gain = [1, 1, 1]
    """The color gain for each red, green, and blue channel."""

    _settings = [
        'exposure_ms', 'binning_x', 'binning_y', 'roi_x', 'roi_y', 'roi_width',
        'roi_height', 'trigger_type', 'trigger_count', 'frame_queue_size',
        'gain', 'black_level', 'freq', 'taps', 'color_gain']
    """All the possible settings that the camera may support.
    """

    _play_settings = ['exposure_ms', 'gain', 'black_level', 'color_gain']
    """All the settings that can be set while the camera is playing.
    """
