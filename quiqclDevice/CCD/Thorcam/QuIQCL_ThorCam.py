# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 22:56:28 2021

@author: CPO
"""
import os
from time import perf_counter as clock
import numpy as np
import ctypes

from ThorCamBase import ThorCamBase

if os.environ.get('THORCAM_DOCS_GEN') != '1':
    import clr
    from System import Array, Int32, UInt16
    from System.Runtime.InteropServices import GCHandle, GCHandleType

__all__ = ('TSICamera')

_MAP_NET_NP = {
    'Single': np.dtype('float32'),
    'Double': np.dtype('float64'),
    'SByte': np.dtype('int8'),
    'Int16': np.dtype('int16'),
    'Int32': np.dtype('int32'),
    'Int64': np.dtype('int64'),
    'Byte': np.dtype('uint8'),
    'UInt16': np.dtype('uint16'),
    'UInt32': np.dtype('uint32'),
    'UInt64': np.dtype('uint64'),
    'Boolean': np.dtype('bool'),
}

def as_numpy_array(netArray):
    '''
    Given a CLR `System.Array` returns a `numpy.ndarray`.
    '''
    dims = np.empty(netArray.Rank, dtype=int)
    for I in range(netArray.Rank):
        dims[I] = netArray.GetLength(I)
    netType = netArray.GetType().GetElementType().Name

    try:
        npArray = np.empty(dims, order='C', dtype=_MAP_NET_NP[netType])
    except KeyError:
        raise NotImplementedError(
            "as_numpy_array does not yet support System type "
            "{}".format(netType))

    try:  # Memmove
        sourceHandle = GCHandle.Alloc(netArray, GCHandleType.Pinned)
        sourcePtr = sourceHandle.AddrOfPinnedObject().ToInt64()
        destPtr = npArray.__array_interface__['data'][0]
        ctypes.memmove(destPtr, sourcePtr, npArray.nbytes)
    finally:
        if sourceHandle.IsAllocated:
            sourceHandle.Free()
    return npArray


def requires_camera_open(func):
    """Decorator that checks if the camera is open.

    Raises:
        RuntimeError - the func is called before the camera is open.
    """

    def wrapper(self, *args):
        if self.is_opened():
            return func(self, *args)
        else:
            raise RuntimeError('{} is called before the camera is opened.'
                               .format(func.__name__))
    return wrapper

def check_running_parameter(func):
    """Decorator that check if the parameter can be set while the camera is running.

    Raises:
        RuntimeError - the parameter cannot be applied while the camera is running.
    """

    def wrapper(self, *args):
        if self.is_running():
            raise RuntimeError('{} cannot be applied while the camera is running.'
                               .format(func.__name__))
        else:
            return func(self, *args)
            
    return wrapper


class QuIQCL_ThorCam(ThorCamBase):
    """
    This class provids a standalone ThorCam control interface.
    To use, you need to specify the dll path if you installed the ThorCam program somewhere not in a default path.
    Please note that I didn't test whether this class works without installing "ThorCam" from PIP. Maybe there's a way to use it.
    
    This class contains parameter.getter, get_parameter and set_parameter methods.
        - parameter.getter: returns the parameter that the class kees. this is for fast parameter return without communicating with the device
        - get_parameter: retunrs the parameter from the device setting. device connection is needed.
        - set_parameter: set the parameter of the devcie. device connection is necessary.
    """
    
    def __init__(self, thor_bin_path = None):
        super(QuIQCL_ThorCam).__init__()
        """ Load dlls"""
        if not thor_bin_path == None:
            self._thor_bin_path = thor_bin_path
        self._load_tsi(self._thor_bin_path)
        
        self._cam_serial = ""
        self._opened     = False
        self._running    = False
        self._color      = False
        self._cam        = None
        

    def _load_tsi(self, thor_bin_path):
        """Loads the Thor .NET binaries and adds them to the PATH.
        """
        os.environ['PATH'] += os.pathsep + thor_bin_path
        clr.AddReference(
            os.path.join(thor_bin_path, 'Thorlabs.TSI.TLCamera.dll'))
        clr.AddReference(
            os.path.join(thor_bin_path, 'Thorlabs.TSI.TLCameraInterfaces.dll'))
        clr.AddReference(
            os.path.join(thor_bin_path, 'Thorlabs.TSI.Demosaicker.dll'))
        clr.AddReference(
            os.path.join(thor_bin_path, 'Thorlabs.TSI.ColorProcessor.dll'))
        from Thorlabs.TSI.TLCamera import TLCameraSDK
        import Thorlabs.TSI.TLCameraInterfaces as tsi_interface
        self._tsi_sdk = TLCameraSDK.OpenTLCameraSDK()
        self._tsi_interface = tsi_interface

        # Initialize the demosaicker
        from Thorlabs.TSI.Demosaicker import Demosaicker as demosaicker
        self._tsi_demosaicker = demosaicker
        from Thorlabs.TSI.ColorProcessor import ColorProcessorSDK
        self._tsi_color_sdk = ColorProcessorSDK()


    def is_opened(self) -> bool: 
        return self._opened
    
    def get_cam_list(self) -> list:
        """Returns the list of serial numbers of the cameras attached."""
        cams = self._tsi_sdk.DiscoverAvailableCameras()
        return list(sorted(cams))
    
    def is_running(self) -> bool:
        return self._running
    
    @property
    def cam_serial(self):
        return self._cam_serial
    
    @cam_serial.setter
    def cam_serial(self, serial_num):
        self._cam_serial = serial_num
    
    def open_cam(self):
        try:
            self._cam = self._tsi_sdk.OpenCamera(self._cam_serial, False)
            self._opened = True
        except:
            raise ValueError ("Could not find the camera '%s'" % self._cam_serial)
            
    @requires_camera_open
    def close_cam(self):
        if self._cam.IsArmed:
            self._cam.Disarm()
        
        self._cam.Dispose()
        self._cam = None
        self._opened = False
        self._running = False
        
        
    #%% Exposure time
    @property
    def exposure_range(self) -> list:
        return self._exposure_range
    
    @requires_camera_open
    def get_exposure_range(self) -> list:
        rang = self._cam.get_ExposureTimeRange_us()
        self._exposure_range = rang.Minimum / 1000., rang.Maximum / 1000.
        return self._exposure_range
    
    @property
    def exposure_ms(self):
        return self._exposure_time
    
    @requires_camera_open
    def get_exposure_ms(self):
        """Camera exposure time in ms"""
        self._exposure_time = self._cam.get_ExposureTime_us() / 1000
        return self._exposure_time
    
    @requires_camera_open
    def set_exposure_ms(self, value):
        value = int(max(min(value, self._exposure_range[1]),
                        self._exposure_range[0]) * 1000)
        self._cam.set_ExposureTime_us(value)
        self._exposure_time = value/1000
    
    #%% Gain        
    @property
    def gain_range(self) -> list:
        return self._gain_range
    
    @requires_camera_open
    def get_gain_range(self):
        rang = self._cam.get_GainRange()
        self._gain_range = rang.Minimum, rang.Maximum
        return self._gain_range
    
    @property
    def gain(self):
        return self._gain
    
    @requires_camera_open
    def get_gain(self):
        """ADC gain of the CCD"""
        self._gain = self._cam.get_Gain()
        return self._gain
        
    @requires_camera_open
    def set_gain(self, value):
        value = int(max(min(value, self._gain_range[1]), self._gain_range[0]))
        self._gain = value
        self._cam.set_Gain(value)
        
    #%% Binning settings
    @property
    def binning_x_range(self) -> list:
        return self._binning_x_range
    
    @requires_camera_open
    def get_binning_x_range(self) -> list:
        rang = self._cam.get_BinXRange()
        self._binning_x_range = rang.Minimum, rang.Maximum
        return self._binning_x_range
    
    @property
    def binning_y_range(self) -> list:
        return self._binning_y_range
    
    @requires_camera_open
    def get_binning_y_range(self) -> list:
        rang = self._cam.get_BinYRange()
        self._binning_y_range = rang.Minimum, rang.Maximum
        return self._binning_y_range
    
    @property
    def binning_x(self):
        return self._binning_x
    
    @property
    def binning_y(self):
        return self._binning_y
    
    @requires_camera_open
    def get_binning(self) -> dict:
        roi_bin = self._cam.get_ROIAndBin()
        self._binning_x = roi_bin.BinX
        self._binning_y = roi_bin.BinY
    
        return {"bin_x": self._binning_x, "bin_y": self._binning_y}
    
    @requires_camera_open
    @check_running_parameter
    def set_binning_x(self, value):
        value = max(min(
            value, self._binning_x_range[1]), self._binning_x_range[0])
        roi_bin = self._cam.get_ROIAndBin()
        roi_bin.BinX = value
        self._binning_x = value
        self._cam.set_ROIAndBin(roi_bin)
        
    @requires_camera_open
    @check_running_parameter
    def set_binning_height(self, value):
        value = max(min(
            value, self._binning_y_range[1]), self._binning_y_range[0])
        roi_bin = self._cam.get_ROIAndBin()
        roi_bin.BinY = value
        self._binning_y = value
        self._cam.set_ROIAndBin(roi_bin)
    
    #%% Sensor_size
    @property
    def sensor_size(self) -> list:
        return self._sensor_size
    
    @requires_camera_open
    def get_sensor_size(self) -> list:
        self._sensor_size = [self._cam.get_SensorWidth_pixels(), 
                             self._cam.get_SensorHeight_pixels()]
        return self._sensor_size
    
    #%% ROI_settings
    @property
    def roi_x(self):
        return self._roi_x
    
    @property
    def roi_y(self):
        return self._roi_y
    
    @property
    def roi_width(self):
        return self._roi_width
    
    @property
    def roi_height(self):
        return self._roi_height
    
    @requires_camera_open
    def get_roi(self) -> dict:
        roi_bin = self._cam.get_ROIAndBin()
        
        self._roi_x      = roi_bin.ROIOriginX_pixels
        self._roi_y      = roi_bin.ROIOriginY_pixels
        self._roi_width  = roi_bin.ROIWidth_pixels
        self._roi_height = roi_bin.ROIHeight_pixels
        
        return {"roi_x": self._roi_x, "roi_y": self._roi_y,
                "roi_width": self._roi_width, "roi_height": self._roi_height}
            
    @requires_camera_open
    @check_running_parameter
    def set_roi_x(self, value):
        roi_bin = self._cam.get_ROIAndBin()
        x = roi_bin.ROIOriginX_pixels
        value = max(1, min(value, self._sensor_size[0] - x))
        roi_bin.ROIWidth_pixels = value
        self._cam.set_ROIAndBin(roi_bin)
        self._roi_x = x
        
    @requires_camera_open
    @check_running_parameter
    def set_roi_y(self, value):
        roi_bin = self._cam.get_ROIAndBin()
        y = roi_bin.ROIOriginY_pixels
        value = max(1, min(value, self._sensor_size[1] - y))
        roi_bin.ROIHeight_pixels = value
        self._cam.set_ROIAndBin(roi_bin)
        self._roi_y = y
    
    @requires_camera_open
    @check_running_parameter
    def set_roi_width(self, value):
        x = value = max(0, min(value, self._sensor_size[0] - 1))
        roi_bin = self._cam.get_ROIAndBin()
        width = min(self._sensor_size[0] - x, roi_bin.ROIWidth_pixels)

        roi_bin.ROIOriginX_pixels = x
        roi_bin.ROIWidth_pixels = width
        self._cam.set_ROIAndBin(roi_bin)
        self._roi_width = width
        
    @requires_camera_open
    @check_running_parameter
    def set_roi_height(self, value):
        y = value = max(0, min(value, self._sensor_size[1] - 1))
        roi_bin = self._cam.get_ROIAndBin()
        height = min(self._sensor_size[1] - y, roi_bin.ROIHeight_pixels)

        roi_bin.ROIOriginY_pixels = y
        roi_bin.ROIHeight_pixels = height
        self._cam.set_ROIAndBin(roi_bin)
        self._roi_height = height
        
    
    #%% Black level
    @property
    def black_level_range(self) -> list:
        return self._black_level_range
    
    @requires_camera_open
    def get_black_level_range(self) -> list:
        rang = self._cam.get_BlackLevelRange()
        self._black_level_range = rang.Minimum, rang.Maximum
        return self._black_level_range
        
    @property
    def black_level(self):
        return self._black_level
    
    @requires_camera_open
    def get_black_level(self):
        self._black_level = self._cam.get_BlackLevel()
        return self._black_level
    
    @requires_camera_open
    def set_black_level(self, value):
        value = int(max(
                min(value, self._black_level_range[1]),
                self._black_level_range[0]))
        self._black_level = value
        self._cam.set_BlackLevel(value)
            
    #%% Frequencies
    @property
    def supported_freqs(self) -> list:
        return self._supported_freqs
    
    @requires_camera_open
    def get_supported_freqs(self) -> list:
        if self._cam.GetIsDataRateSupported(
                self._tsi_interface.DataRate.ReadoutSpeed20MHz):
            if self._cam.GetIsDataRateSupported(
                    self._tsi_interface.DataRate.ReadoutSpeed40MHz):
                self._supported_freqs = ['20 MHz', '40 MHz']
            else:
                self._supported_freqs = ['20 MHz', ]
        else:
            if self._cam.GetIsDataRateSupported(self._tsi_interface.DataRate.FPS50):
                self._supported_freqs = ['30 FPS', '50 FPS']
            else:
                self._supported_freqs = ['30 FPS', ]
        return self._supported_freqs
        
    @property
    def freq(self) -> str:
        return self._freq
    
    @requires_camera_open
    def get_freq(self) -> str:
        freq_rate = self._cam.get_DataRate()
        if freq_rate == self._tsi_interface.DataRate.ReadoutSpeed20MHz:
            self._freq = "20 MHz"
        elif freq_rate == self._tsi_interface.DataRate.ReadoutSpeed40MHz:
            self._freq = "40 MHz"
        elif freq_rate == self._tsi_interface.DataRate.FPS50:
            self._freq = "50 FPS"
        else:
            self._freq = "30 FPS"
        return self._freq
    
    @requires_camera_open
    @check_running_parameter
    def set_freq(self, value):
        assert isinstance(value, str), "Frequency rate must be a string."
        assert value in self._supported_freqs, "Frequency rate must be among '%s'." % ("', '".join(self._supported_freqs))
        self._freq = value
        if value == "20 MHz":
            self._cam.set_DataRate(self._tsi_interface.DataRate.ReadoutSpeed20MHz)
        elif value == "40 MHz":
            self._cam.set_DataRate(self._tsi_interface.DataRate.ReadoutSpeed40MHz)
        elif value == "50 FPS":
            self._cam.set_DataRate(self._tsi_interface.DataRate.FPS50)
        else:
            self._cam.set_DataRate(self._tsi_interface.DataRate.FPS30)
        
    #%% Taps
    @property
    def supported_taps(self) -> list:
        return self._supported_taps
    
    @requires_camera_open
    def get_supported_taps(self) -> list:
        if self._cam.GetIsTapsSupported(self._tsi_interface.Taps.QuadTap):
            self._supported_taps = ['1', '2', '4']
        elif self._cam.GetIsTapsSupported(self._tsi_interface.Taps.DualTap):
            self._supported_taps = ['1', '2']
        elif self._cam.GetIsTapsSupported(self._tsi_interface.Taps.SingleTap):
            self._supported_taps = ['1', ]
        else:
            self._supported_taps = []
        return self._supported_taps
    
    @property
    def taps(self) -> str:
        return self._taps
    
    @requires_camera_open
    def get_taps(self) -> str:
        if self._cam.GetIsTapsSupported(self._tsi_interface.Taps.SingleTap):
            tap = self._cam.get_Taps()
            if tap == self._tsi_interface.Taps.QuadTap:
                self._taps = "4"
            elif tap == self._tsi_interface.Taps.DualTap:
                self._taps = "2"
            elif tap == self._tsi_interface.Taps.SingleTap:
                self._taps = "1"
        else:
            self._taps = ''
        return self._taps
    
    @requires_camera_open
    @check_running_parameter
    def set_taps(self, value):
        assert isinstance(value, str), "Taps must be a string."
        assert value in self._supported_taps, "Taps must be among '%s'." % ("', '".join(self._supported_taps))
        self._taps = value
        if value == "4":
            self._cam.set_Taps(self._tsi_interface.Taps.QuadTap)
        elif value == "2":
            self._cam.set_Taps(self._tsi_interface.Taps.DualTap)
        else:
            self._cam.set_Taps(self._tsi_interface.Taps.SingleTap)
    
    #%% Color
    @requires_camera_open
    def is_color_supported(self) -> bool:
        self._color = self._cam.get_CameraSensorType() == \
            self._tsi_interface.CameraSensorType.Bayer
        return self._color
    
    @property
    def color_gain(self) -> list:
        if not self._color:
            raise ValueError ("Colors are not supported for this device!")
        else:
            return self._color_gain
        
    #%% Frame queue
    @property
    def frame_queue_size(self):
        return self._frame_queue_size
    
    @requires_camera_open
    def get_frame_queue_size(self):
        self._frame_queue_size = self._cam.get_MaximumNumberOfFramesToQueue()
        return self._frame_queue_size
    
    @requires_camera_open
    @check_running_parameter
    def set_frame_queue_size(self, value):
        value = int(value)
        assert value >= 1, "Frame queue size must be larger than 0."
        self._frame_queue_size = value
        self._cam.set_MaximumNumberOfFramesToQueue(value)
            
    #%% Trigger
    @property
    def trigger_count(self):
        return self._trigger_count
    
    @requires_camera_open
    def get_trigger_count(self):
        self._trigger_count = self._cam.get_FramesPerTrigger_zeroForUnlimited()
        return self._trigger_count
    
    @requires_camera_open
    @check_running_parameter
    def set_trigger_count(self, value):
        """
        If you set the trigger count to be 0, the camera will self-trigger indefinitely, allowing a continuous video feed.
        Otherwise it will generate the prescrribed number of frames and then stop.
        """
        assert value >= 0, "Trigger count value must be positive."
        self._trigger_count = value
        self._cam.set_FramesPerTrigger_zeroForUnlimited(value)
    
    @property
    def trigger_type(self) -> str:
        return self._trigger_type
    
    @requires_camera_open
    def get_trigger_type(self) -> str:
        hw_mode = self._cam.get_OperationMode() == \
                  self._tsi_interface.OperationMode.HardwareTriggered
        self._trigger_type = "HW Trigger" if hw_mode else "SW Trigger"
        return self._trigger_type
    
    @requires_camera_open
    @check_running_parameter
    def set_trigger_type(self, mode):
        assert isinstance(mode, str), "Trigger type must be a string."
        assert mode in self._supported_triggers, "Trigger type must be either '%s'" % ("' or '".join(self._supported_triggers))
        hw_mode = 1 if mode == "HW Trigger" else "SW Trigger"
        self._cam.set_OperationMode(
            self._tsi_interface.OperationMode.HardwareTriggered
            if hw_mode else
            self._tsi_interface.OperationMode.SoftwareTriggered)
        
    
    #%% Settings
    @property
    def settings(self) -> list:
        """All available settings."""
        return self._settings
    
    @property
    def play_settings(self) -> list:
        """Settings that can be changed when the camera is running. (when it is armed.)"""
        return self._play_settings


    #%% Image Acquisition
    @requires_camera_open
    def play_camera(self):
        if self._cam.IsArmed:
            pass
        else:
            self._cam.Arm()
        self._running = True
        
        if self._trigger_type == "SW Trigger": 
            self._cam.IssueSoftwareTrigger()
        else: self._camIssueHardwareTrigger()
        
    @requires_camera_open
    def stop_camera(self):
        if self._cam.IsArmed:
            self._cam.Disarm()
        self._running = False
    
    
    @requires_camera_open
    def read_frame(self):
        """Reads a image from the camera, if available, and returns it.
            It returns
            ``(data, fmt, (w, h), count, queued_count, t)``, otherwise, it returns
        None. See :class:`ThorCamServer`.
        """
        queued_count = self._cam.get_NumberOfQueuedFrames()
        if queued_count <= 0:
            return
            
        frame = None
        while frame == None:
            frame = self._cam.GetPendingFrameOrNull()
            
        t = clock()
        
        count = frame.FrameNumber
        h = frame.ImageData.Height_pixels
        w = frame.ImageData.Width_pixels
        if self._color_processor is not None:
            from Thorlabs.TSI import ColorInterfaces
            demosaicked_data = Array.CreateInstance(UInt16, h * w * 3)
            processed_data = Array.CreateInstance(UInt16, h * w * 3)
            fmt = ColorInterfaces.ColorFormat.BGRPixel
            max_pixel_val = int(2 ** self._cam.BitDepth - 1)

            self._demosaic.Demosaic(
                w, h, Int32(0), Int32(0), self._cam.ColorFilterArrayPhase,
                fmt, ColorInterfaces.ColorSensorType.Bayer,
                Int32(self._cam.BitDepth), frame.ImageData.ImageData_monoOrBGR,
                demosaicked_data)

            self._color_processor.Transform48To48(demosaicked_data, fmt,
                0, max_pixel_val, 0, max_pixel_val,
                0, max_pixel_val, 0, 0, 0, processed_data, fmt)

            pixel_fmt = 'bgr48le'
            data = as_numpy_array(processed_data)
        else:
            pixel_fmt = 'gray16le'
            data = as_numpy_array(frame.ImageData.GetType().GetProperty(
                'ImageData_monoOrBGR').GetValue(frame.ImageData))            
        return data, pixel_fmt, (w, h), count, queued_count, t

#%% TSI_SDK
"""
Disarm():
    - When finished issuing software or hardware triggers, call disarm(). This allows setting parameters that
    - are not available in armed mode such as roi or operation_mode. The camera will automatically
    - disarm when disarm() is called. Disarming the camera does not clear the image queue – polling can
    - continue until the queue is empty. When calling disarm() again, the queue will be automatically cleared.
"""
"""
Dispose():
    - Cleans up the TLCamera instance - make sure to call this when you are done with the camera. If using the
    - with statement, dispose is called automatically upon exit.
"""
"""
Arm(frames_to_buffer: int) →None
    - Before issuing software or hardware triggers to get images from a camera, prepare it for imaging by
    - calling arm(). Depending on the operation_mode, either call issue_software_trigger()
    - or issue a hardware trigger. To start a camera in continuous mode, set the operation_mode
    - to SOFTWARE_TRIGGERED, frames per trigger to zero, Arm the camera, and then call
    - issue_software_trigger() one time. The camera will then self-trigger frames until disarm()
    - or dispose() is called. To start a camera for hardware triggering, set the operation_mode to either
    - HARDWARE_TRIGGERED or BULB, frames per trigger to one, trigger_polarity`
    - to rising-edge or falling-edge triggered, arm the camera, and then issue a triggering signal on the trigger
    - input. If any images are still in the queue when calling arm(), they will be considered stale and cleared
    - from the queue. For more information on the proper procedure for triggering frames and receiving them
    - from the camera, please see the Getting Started section.
"""
"""
Model():
Gets the camera model number such as 1501M or 8051C. This property is Read-Only.
"""
"""
property, frames_per_trigger_zero_for_unlimited:
    - The number of frames generated per software or hardware trigger can be unlimited or finite. If set to zero,
    - the camera will self-trigger indefinitely, allowing a continuous video feed. If set to one or higher, a single
    - software or hardware trigger will generate only the prescribed number of frames and then stop.
    - Type int
"""
"""
property, frames_per_trigger_range:
    - The number of frames generated per software or hardware trigger can be unlimited or finite. If set to
    - zero, the camera will self-trigger indefinitely, allowing a continuous video feed. If set to one or higher, a
    - single software or hardware trigger will generate only the prescribed number of frames and then stop. This
    - property returns the valid range for frames_per_trigger_zero_for_unlimited. This property
    - is Read-Only.
    - Type Range
"""