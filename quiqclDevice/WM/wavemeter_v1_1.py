import ctypes

byref = ctypes.byref

class wavemeter:
    # Instantiating Constants for 'RFC' parameter
    cInstCheckForWLM = -1;
    cInstResetCalc = 0;
    cInstReturnMode = cInstResetCalc;
    cInstNotification = 1;
    cInstCopyPattern = 2;
    cInstCopyAnalysis = cInstCopyPattern;
    cInstControlWLM = 3;
    cInstControlDelay = 4;
    cInstControlPriority = 5;
    
    # Operation
    cCtrlStopAll = 0
    cCtrlStartAdjustment = 1
    cCtrlStartMeasurement = 2
    
    ##// Amplitude Constants
    cMin1 = 0;
    cMin2 = 1;
    cMax1 = 2;
    cMax2 = 3;
    cAvg1 = 4;
    cAvg2 = 5;
    
    # Notification Constants for 'Mode' parameter
    cNotifyInstallCallback = 0;
    cNotifyRemoveCallback = 1;
    cNotifyInstallWaitEvent = 2;
    cNotifyRemoveWaitEvent = 3;
    cNotifyInstallCallbackEx = 4;
    cNotifyInstallWaitEventEx = 5;

##// Return errorvalues of GetFrequency, GetWavelength and GetWLMVersion
    ErrNoValue = 0;
    ErrNoSignal = -1.0;
    ErrBadSignal = -2.0;
    ErrLowSignal = -3.0;
    ErrBigSignal = -4.0;
    ErrWlmMissing = -5.0;
    ErrNotAvailable = -6.0;
    InfNothingChanged = -7.0;
    ErrNoPulse = -8.0;
    ErrDiv0 = -13.0;
    ErrOutOfRange = -14.0;
    ErrUnitNotAvailable = -15.0;
    ErrMaxErr = ErrUnitNotAvailable;

    # cmi Mode Constants for Callback-Export and WaitForWLMEvent-function
    cmiResultMode = 1;
    cmiRange = 2;
    cmiPulse = 3;
    cmiPulseMode = cmiPulse;
    cmiWideLine = 4;
    cmiWideMode = cmiWideLine;
    cmiFast = 5;
    cmiFastMode = cmiFast;
    cmiExposureMode = 6;
    cmiExposureValue1 = 7;
    cmiExposureValue2 = 8;
    cmiDelay = 9;
    cmiShift = 10;
    cmiShift2 = 11;
    cmiReduce = 12;
    cmiReduced = cmiReduce;
    cmiScale = 13;
    cmiTemperature = 14;
    cmiLink = 15;
    cmiOperation = 16;
    cmiDisplayMode = 17;
    cmiPattern1a = 18;
    cmiPattern1b = 19;
    cmiPattern2a = 20;
    cmiPattern2b = 21;
    cmiMin1 = 22;
    cmiMax1 = 23;
    cmiMin2 = 24;
    cmiMax2 = 25;
    cmiNowTick = 26;
    cmiCallback = 27;
    cmiFrequency1 = 28;
    cmiFrequency2 = 29;
    cmiDLLDetach = 30;
    cmiVersion = 31;
    cmiAnalysisMode = 32;
    cmiDeviationMode = 33;
    cmiDeviationReference = 34;
    cmiDeviationSensitivity = 35;
    cmiAppearance = 36;
    cmiAutoCalMode = 37;
    cmiWavelength1 = 42;
##	const int	cmiWavelength2 = 43;
##	const int	cmiLinewidth = 44;
##	const int	cmiLinewidthMode = 45;
##	const int	cmiLinkDlg = 56;
##	const int	cmiAnalysis = 57;
##	const int	cmiAnalogIn = 66;
##	const int	cmiAnalogOut = 67;
##	const int	cmiDistance = 69;
##	const int	cmiWavelength3 = 90;
##	const int	cmiWavelength4 = 91;
##	const int	cmiWavelength5 = 92;
##	const int	cmiWavelength6 = 93;
##	const int	cmiWavelength7 = 94;
##	const int	cmiWavelength8 = 95;
##	const int	cmiVersion0 = cmiVersion;
##	const int	cmiVersion1 = 96;
##	const int	cmiDLLAttach = 121;
##	const int	cmiSwitcherSignal = 123;
##	const int	cmiSwitcherMode = 124;
##	const int	cmiExposureValue11 = cmiExposureValue1;
##	const int	cmiExposureValue12 = 125;
##	const int	cmiExposureValue13 = 126;
##	const int	cmiExposureValue14 = 127;
##	const int	cmiExposureValue15 = 128;
##	const int	cmiExposureValue16 = 129;
##	const int	cmiExposureValue17 = 130;
##	const int	cmiExposureValue18 = 131;
##	const int	cmiExposureValue21 = cmiExposureValue2;
##	const int	cmiExposureValue22 = 132;
##	const int	cmiExposureValue23 = 133;
##	const int	cmiExposureValue24 = 134;
##	const int	cmiExposureValue25 = 135;
##	const int	cmiExposureValue26 = 136;
##	const int	cmiExposureValue27 = 137;
##	const int	cmiExposureValue28 = 138;
##	const int	cmiPatternAverage = 139;
##	const int	cmiPatternAvg1 = 140;
##	const int	cmiPatternAvg2 = 141;
##	const int	cmiAnalogOut1 = cmiAnalogOut;
##	const int	cmiAnalogOut2 = 142;
##	const int	cmiMin11 = cmiMin1;
##	const int	cmiMin12 = 146;
##	const int	cmiMin13 = 147;
##	const int	cmiMin14 = 148;
##	const int	cmiMin15 = 149;
##	const int	cmiMin16 = 150;
##	const int	cmiMin17 = 151;
##	const int	cmiMin18 = 152;
##	const int	cmiMin21 = cmiMin2;
##	const int	cmiMin22 = 153;
##	const int	cmiMin23 = 154;
##	const int	cmiMin24 = 155;
##	const int	cmiMin25 = 156;
##	const int	cmiMin26 = 157;
##	const int	cmiMin27 = 158;
##	const int	cmiMin28 = 159;
##	const int	cmiMax11 = cmiMax1;
##	const int	cmiMax12 = 160;
##	const int	cmiMax13 = 161;
##	const int	cmiMax14 = 162;
##	const int	cmiMax15 = 163;
##	const int	cmiMax16 = 164;
##	const int	cmiMax17 = 165;
##	const int	cmiMax18 = 166;
##	const int	cmiMax21 = cmiMax2;
##	const int	cmiMax22 = 167;
##	const int	cmiMax23 = 168;
##	const int	cmiMax24 = 169;
##	const int	cmiMax25 = 170;
##	const int	cmiMax26 = 171;
##	const int	cmiMax27 = 172;
##	const int	cmiMax28 = 173;
##	const int	cmiAvg11 = cmiPatternAvg1;
##	const int	cmiAvg12 = 174;
##	const int	cmiAvg13 = 175;
##	const int	cmiAvg14 = 176;
##	const int	cmiAvg15 = 177;
##	const int	cmiAvg16 = 178;
##	const int	cmiAvg17 = 179;
##	const int	cmiAvg18 = 180;
##	const int	cmiAvg21 = cmiPatternAvg2;
##	const int	cmiAvg22 = 181;
##	const int	cmiAvg23 = 182;
##	const int	cmiAvg24 = 183;
##	const int	cmiAvg25 = 184;
##	const int	cmiAvg26 = 185;
##	const int	cmiAvg27 = 186;
##	const int	cmiAvg28 = 187;
##	const int	cmiPatternAnalysisWritten = 202;
##	const int	cmiSwitcherChannel = 203;
##	const int	cmiAnalogOut3 = 237;
##	const int	cmiAnalogOut4 = 238;
##	const int	cmiAnalogOut5 = 239;
##	const int	cmiAnalogOut6 = 240;
##	const int	cmiAnalogOut7 = 241;
##	const int	cmiAnalogOut8 = 242;
##	const int	cmiIntensity = 251;
##	const int	cmiPower = 267;
##	const int	cmiActiveChannel = 300;
##	const int	cmiPIDCourse = 1030;
##	const int	cmiPIDUseTa = 1031;
##	const int	cmiPIDUseT = cmiPIDUseTa;
##	const int	cmiPID_T = 1033;
##	const int	cmiPID_P = 1034;
##	const int	cmiPID_I = 1035;
##	const int	cmiPID_D = 1036;
##	const int	cmiDeviationSensitivityDim = 1040;
##	const int	cmiDeviationSensitivityFactor = 1037;
##	const int	cmiDeviationPolarity = 1038;
##	const int	cmiDeviationSensitivityEx = 1039;
##	const int	cmiDeviationUnit = 1041;
##	const int	cmiPIDConstdt = 1059;
##	const int	cmiPID_dt = 1060;
##	const int	cmiPID_AutoClearHistory = 1061;
##	const int	cmiDeviationChannel = 1063;
##	const int	cmiAutoCalPeriod = 1120;
##	const int	cmiAutoCalUnit = 1121;
##	const int	cmiServerInitialized = 1124;
##	const int	cmiWavelength9 = 1130;
##	const int	cmiExposureValue19 = 1155;
##	const int	cmiExposureValue29 = 1180;
##	const int	cmiMin19 = 1205;
##	const int	cmiMin29 = 1230;
##	const int	cmiMax19 = 1255;
##	const int	cmiMax29 = 1280;
##	const int	cmiAvg19 = 1305;
##	const int	cmiAvg29 = 1330;
##	const int	cmiWavelength10 = 1355;
##	const int	cmiWavelength11 = 1356;
##	const int	cmiWavelength12 = 1357;
##	const int	cmiWavelength13 = 1358;
##	const int	cmiWavelength14 = 1359;
##	const int	cmiWavelength15 = 1360;
##	const int	cmiWavelength16 = 1361;
##	const int	cmiWavelength17 = 1362;
##	const int	cmiExternalInput = 1400;
##	const int	cmiPressure = 1465;
##	const int	cmiBackground = 1475;
##	const int	cmiDistanceMode = 1476;
##	const int	cmiInterval = 1477;
##	const int	cmiIntervalMode = 1478;


##// Pattern- and Analysis Constants
    cPatternDisable = 0;
    cPatternEnable = 1;
    cAnalysisDisable = cPatternDisable;
    cAnalysisEnable = cPatternEnable;
    cSignal1Interferometers = 0;
    cSignal1WideInterferometer = 1;
    cSignal1Grating = 1;
    cSignal2Interferometers = 2;
    cSignal2WideInterferometer = 3;
    cSignalAnalysis = 4;
    cSignalAnalysisX = cSignalAnalysis;
    cSignalAnalysisY = cSignalAnalysis + 1;
    
    
    cExposureMax = 2000
    cExposureMin = 1
    def __init__(self):
        self.wlmData = ctypes.cdll.LoadLibrary('C:\Windows\System32\wlmData.dll')
        
        self.Instantiate = self.wlmData.Instantiate
        self.Instantiate.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.Instantiate.restypes = ctypes.c_long
        
        self.ControlWLM = self.wlmData.ControlWLM
        self.ControlWLM.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.ControlWLM.restype = ctypes.c_long
        
        self.Operation=self.wlmData.Operation
        self.Operation.argtypes=[ctypes.c_ushort]
        self.Operation.restype = ctypes.c_long

##          Need to reformat the following
##        opState=wlmData.GetOperationState(0)
##        if (opState==0): # cStop
##            print "Starting measurement"
##            Operation(0x02) # cCtrlStartMeasurement
##        elif (opState==1): # cAdjustment
##            print "WS-U is in the middle of adjustment"
##            os.exit(1)

        self.SetExposure = self.wlmData.SetExposure
        self.SetExposure.argtype = ctypes.c_ushort
        self.SetExposure.restype = ctypes.c_long
        
        self.SetExposureNum = self.wlmData.SetExposureNum
        self.SetExposureNum.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.SetExposureNum.restype = ctypes.c_long
        
        self.SetExposure2 = self.wlmData.SetExposure2
        self.SetExposure2.argtypes = [ctypes.c_ushort]
        self.SetExposure2.restype = ctypes.c_long

        self.GetExposure = self.wlmData.GetExposure
        self.GetExposure.argtypes = [ctypes.c_ushort]
        self.GetExposure.restype = ctypes.c_ushort

        self.GetInterval = self.wlmData.GetInterval
        self.GetInterval.argtypes = [ctypes.c_long]
        self.GetInterval.restype = ctypes.c_long

        self.WaitForWLMEvent=self.wlmData.WaitForWLMEvent
        self.WaitForWLMEvent.argtypes=[ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_double)]
        self.WaitForWLMEvent.restype=ctypes.c_long
        self.mode=ctypes.c_long()
        self.i=ctypes.c_long()
        self.d=ctypes.c_double()
        
        self.GetWavelengthNum = self.wlmData.GetWavelengthNum
        self.GetWavelengthNum.argtypes = [ctypes.c_long, ctypes.c_double]
        self.GetWavelengthNum.restype = ctypes.c_double

        self.GetFrequencyNum = self.wlmData.GetFrequencyNum
        self.GetFrequencyNum.argtypes = [ctypes.c_long, ctypes.c_double]
        self.GetFrequencyNum.restype = ctypes.c_double


        self.SetSwitcherChannel = self.wlmData.SetSwitcherChannel
        self.SetSwitcherChannel.argtypes = [ctypes.c_long]
        self.SetSwitcherChannel.restype = ctypes.c_long

        self.GetActiveChannel = self.wlmData.GetActiveChannel
        self.GetActiveChannel.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.GetActiveChannel.restype = ctypes.c_long

        self.SetSwitcherSignalStates = self.wlmData.SetSwitcherSignalStates
        self.SetSwitcherSignalStates.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.SetSwitcherSignalStates.restype = ctypes.c_long

        self.SetSwitcherMode = self.wlmData.SetSwitcherMode
        self.SetSwitcherMode.argtypes = [ctypes.c_long]
        self.SetSwitcherMode.restype = ctypes.c_long

        self.SetActiveChannel = self.wlmData.SetActiveChannel
        self.SetActiveChannel.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.SetActiveChannel.restype = ctypes.c_long

        self.GetPatternItemCount=self.wlmData.GetPatternItemCount
        self.GetPatternItemCount.argtypes=[ctypes.c_long]
        self.GetPatternItemCount.restype=ctypes.c_long
        
        self.l1=self.GetPatternItemCount(wavemeter.cSignal1Interferometers)
        self.l2=self.GetPatternItemCount(wavemeter.cSignal1WideInterferometer)

        if self.l1 != 2048 or self.l2 != 2048:
            print ('Error: Pattern Item Count %d, %d. We expect 2048 for both numbers.', self.l1, self.l2)


        self.GetPatternItemSize=self.wlmData.GetPatternItemSize
        self.GetPatternItemSize.argtypes=[ctypes.c_long]
        self.GetPatternItemSize.restype=ctypes.c_long
                    
        self.is1=self.GetPatternItemSize(wavemeter.cSignal1Interferometers)
        self.is2=self.GetPatternItemSize(wavemeter.cSignal1WideInterferometer)

        if self.is1 != 2 or self.is2 != 2:
            print ('Error: Pattern Item Size %d, %d. We expect 2 for both numbers.', self.is1, self.is2)

        self.buf1=ctypes.create_string_buffer(self.l1 * self.is1)
        self.buf2=ctypes.create_string_buffer(self.l2 * self.is2)

        self.SetPattern=self.wlmData.SetPattern
        self.SetPattern.argtypes=[ctypes.c_long, ctypes.c_long]
        self.SetPattern.restype=ctypes.c_long

        self.GetPatternDataNum=self.wlmData.GetPatternDataNum
        self.GetPatternDataNum.argtypes=[ctypes.c_long, ctypes.c_long, ctypes.c_void_p]
        self.GetPatternDataNum.restype=ctypes.c_long

        self.GetPatternData=self.wlmData.GetPatternData
        self.GetPatternData.argtypes=[ctypes.c_long, ctypes.c_void_p]
        self.GetPatternData.restype=ctypes.c_long

        self.SetPattern(wavemeter.cSignal1Interferometers, wavemeter.cPatternEnable)
        self.SetPattern(wavemeter.cSignal1WideInterferometer, wavemeter.cPatternEnable)

        self.GetSwitcherChannel = self.wlmData.GetSwitcherChannel
        self.GetSwitcherChannel.argtypes = [ctypes.c_long]
        self.GetSwitcherChannel.restype = ctypes.c_long
        
        self.GetAmplitudeNum = self.wlmData.GetAmplitudeNum
        self.GetAmplitudeNum.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
        self.GetAmplitudeNum.restype = ctypes.c_long
        
        self.GetCalWavelength = self.wlmData.GetCalWavelength
        self.GetCalWavelength.argtypes = [ctypes.c_long, ctypes.c_double]
        self.GetCalWavelength.restype = ctypes.c_double
        
        self.Calibration = self.wlmData.Calibration
        self.Calibration.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_double, ctypes.c_long]
        self.Calibration.restype = ctypes.c_long
        
        
        self.switchDelay = 100
    
    def updatePatternNum1(self, num):
        self.GetPatternData(wavemeter.cSignal1Interferometers, self.buf1)

    def updatePatternNum2(self, num):
        self.GetPatternData(wavemeter.cSignal1WideInterferometer, self.buf2)
    
    def updatePattern1(self):
        self.GetPatternData(wavemeter.cSignal1Interferometers, self.buf1)

    def updatePattern2(self):
        self.GetPatternData(wavemeter.cSignal1WideInterferometer, self.buf2)

    def WEvent(self):
#        print 'I am  here'
        WEventResult = self.WaitForWLMEvent(byref(self.mode), byref(self.i), byref(self.d))
#        print WEventResult
        return self.mode.value
        
########################################################################################################
# If I need to switch between port 1 and calibration port...
# The assignment of port/channel is a little different from manual
########################################################################################################

    def frontPort(self):
        self.SetActiveChannel(3, 1, 1, 0)

    def backPort(self):
        self.SetActiveChannel(3, 1, 3, 0)


########################################################################################################
# Dummy methods for testing
########################################################################################################

##    def Instantiate(self, a, b, c, d):
##        return 1
##
##    def SetExposure(self, a):
##        return 1
##
##    def SetExposure2(self, a):
##        return 1
##
##    def GetExposure(self, a):
##        return 1
##
##    def GetInterval(self, a):
##        return 1
##
##    def WEvent(self, a, b, c):
##        return 1
##
##    def GetWavelength(self, a):
##        return 469.333333
##
##    def GetFrequency(self, a):
##        return 469.333333






##// ***********  Constants  **********************************************
##
##// Instantiating Constants for 'RFC' parameter
##	const int	cInstCheckForWLM = -1;
##	const int	cInstResetCalc = 0;
##	const int	cInstReturnMode = cInstResetCalc;
##	const int	cInstNotification = 1;
##	const int	cInstCopyPattern = 2;
##	const int	cInstCopyAnalysis = cInstCopyPattern;
##	const int	cInstControlWLM = 3;
##	const int	cInstControlDelay = 4;
##	const int	cInstControlPriority = 5;
##
##// Notification Constants for 'Mode' parameter
##	const int	cNotifyInstallCallback = 0;
##	const int	cNotifyRemoveCallback = 1;
##	const int	cNotifyInstallWaitEvent = 2;
##	const int	cNotifyRemoveWaitEvent = 3;
##	const int	cNotifyInstallCallbackEx = 4;
##	const int	cNotifyInstallWaitEventEx = 5;
##
##// ResultError Constants of Set...-functions
##	const int	ResERR_NoErr = 0;
##	const int	ResERR_WlmMissing = -1;
##	const int	ResERR_CouldNotSet = -2;
##	const int	ResERR_ParmOutOfRange = -3;
##	const int	ResERR_WlmOutOfResources = -4;
##	const int	ResERR_WlmInternalError = -5;
##	const int	ResERR_NotAvailable = -6;
##	const int	ResERR_WlmBusy = -7;
##	const int	ResERR_NotInMeasurementMode = -8;
##	const int	ResERR_OnlyInMeasurementMode = -9;
##	const int	ResERR_ChannelNotAvailable = -10;
##	const int	ResERR_ChannelTemporarilyNotAvailable = -11;
##	const int	ResERR_CalOptionNotAvailable = -12;
##	const int	ResERR_CalWavelengthOutOfRange = -13;
##	const int	ResERR_BadCalibrationSignal = -14;
##	const int	ResERR_UnitNotAvailable = -15;
##
##// cmi Mode Constants for Callback-Export and WaitForWLMEvent-function
##	const int	cmiResultMode = 1;
##	const int	cmiRange = 2;
##	const int	cmiPulse = 3;
##	const int	cmiPulseMode = cmiPulse;
##	const int	cmiWideLine = 4;
##	const int	cmiWideMode = cmiWideLine;
##	const int	cmiFast = 5;
##	const int	cmiFastMode = cmiFast;
##	const int	cmiExposureMode = 6;
##	const int	cmiExposureValue1 = 7;
##	const int	cmiExposureValue2 = 8;
##	const int	cmiDelay = 9;
##	const int	cmiShift = 10;
##	const int	cmiShift2 = 11;
##	const int	cmiReduce = 12;
##	const int	cmiReduced = cmiReduce;
##	const int	cmiScale = 13;
##	const int	cmiTemperature = 14;
##	const int	cmiLink = 15;
##	const int	cmiOperation = 16;
##	const int	cmiDisplayMode = 17;
##	const int	cmiPattern1a = 18;
##	const int	cmiPattern1b = 19;
##	const int	cmiPattern2a = 20;
##	const int	cmiPattern2b = 21;
##	const int	cmiMin1 = 22;
##	const int	cmiMax1 = 23;
##	const int	cmiMin2 = 24;
##	const int	cmiMax2 = 25;
##	const int	cmiNowTick = 26;
##	const int	cmiCallback = 27;
##	const int	cmiFrequency1 = 28;
##	const int	cmiFrequency2 = 29;
##	const int	cmiDLLDetach = 30;
##	const int	cmiVersion = 31;
##	const int	cmiAnalysisMode = 32;
##	const int	cmiDeviationMode = 33;
##	const int	cmiDeviationReference = 34;
##	const int	cmiDeviationSensitivity = 35;
##	const int	cmiAppearance = 36;
##	const int	cmiAutoCalMode = 37;
##	const int	cmiWavelength1 = 42;
##	const int	cmiWavelength2 = 43;
##	const int	cmiLinewidth = 44;
##	const int	cmiLinewidthMode = 45;
##	const int	cmiLinkDlg = 56;
##	const int	cmiAnalysis = 57;
##	const int	cmiAnalogIn = 66;
##	const int	cmiAnalogOut = 67;
##	const int	cmiDistance = 69;
##	const int	cmiWavelength3 = 90;
##	const int	cmiWavelength4 = 91;
##	const int	cmiWavelength5 = 92;
##	const int	cmiWavelength6 = 93;
##	const int	cmiWavelength7 = 94;
##	const int	cmiWavelength8 = 95;
##	const int	cmiVersion0 = cmiVersion;
##	const int	cmiVersion1 = 96;
##	const int	cmiDLLAttach = 121;
##	const int	cmiSwitcherSignal = 123;
##	const int	cmiSwitcherMode = 124;
##	const int	cmiExposureValue11 = cmiExposureValue1;
##	const int	cmiExposureValue12 = 125;
##	const int	cmiExposureValue13 = 126;
##	const int	cmiExposureValue14 = 127;
##	const int	cmiExposureValue15 = 128;
##	const int	cmiExposureValue16 = 129;
##	const int	cmiExposureValue17 = 130;
##	const int	cmiExposureValue18 = 131;
##	const int	cmiExposureValue21 = cmiExposureValue2;
##	const int	cmiExposureValue22 = 132;
##	const int	cmiExposureValue23 = 133;
##	const int	cmiExposureValue24 = 134;
##	const int	cmiExposureValue25 = 135;
##	const int	cmiExposureValue26 = 136;
##	const int	cmiExposureValue27 = 137;
##	const int	cmiExposureValue28 = 138;
##	const int	cmiPatternAverage = 139;
##	const int	cmiPatternAvg1 = 140;
##	const int	cmiPatternAvg2 = 141;
##	const int	cmiAnalogOut1 = cmiAnalogOut;
##	const int	cmiAnalogOut2 = 142;
##	const int	cmiMin11 = cmiMin1;
##	const int	cmiMin12 = 146;
##	const int	cmiMin13 = 147;
##	const int	cmiMin14 = 148;
##	const int	cmiMin15 = 149;
##	const int	cmiMin16 = 150;
##	const int	cmiMin17 = 151;
##	const int	cmiMin18 = 152;
##	const int	cmiMin21 = cmiMin2;
##	const int	cmiMin22 = 153;
##	const int	cmiMin23 = 154;
##	const int	cmiMin24 = 155;
##	const int	cmiMin25 = 156;
##	const int	cmiMin26 = 157;
##	const int	cmiMin27 = 158;
##	const int	cmiMin28 = 159;
##	const int	cmiMax11 = cmiMax1;
##	const int	cmiMax12 = 160;
##	const int	cmiMax13 = 161;
##	const int	cmiMax14 = 162;
##	const int	cmiMax15 = 163;
##	const int	cmiMax16 = 164;
##	const int	cmiMax17 = 165;
##	const int	cmiMax18 = 166;
##	const int	cmiMax21 = cmiMax2;
##	const int	cmiMax22 = 167;
##	const int	cmiMax23 = 168;
##	const int	cmiMax24 = 169;
##	const int	cmiMax25 = 170;
##	const int	cmiMax26 = 171;
##	const int	cmiMax27 = 172;
##	const int	cmiMax28 = 173;
##	const int	cmiAvg11 = cmiPatternAvg1;
##	const int	cmiAvg12 = 174;
##	const int	cmiAvg13 = 175;
##	const int	cmiAvg14 = 176;
##	const int	cmiAvg15 = 177;
##	const int	cmiAvg16 = 178;
##	const int	cmiAvg17 = 179;
##	const int	cmiAvg18 = 180;
##	const int	cmiAvg21 = cmiPatternAvg2;
##	const int	cmiAvg22 = 181;
##	const int	cmiAvg23 = 182;
##	const int	cmiAvg24 = 183;
##	const int	cmiAvg25 = 184;
##	const int	cmiAvg26 = 185;
##	const int	cmiAvg27 = 186;
##	const int	cmiAvg28 = 187;
##	const int	cmiPatternAnalysisWritten = 202;
##	const int	cmiSwitcherChannel = 203;
##	const int	cmiAnalogOut3 = 237;
##	const int	cmiAnalogOut4 = 238;
##	const int	cmiAnalogOut5 = 239;
##	const int	cmiAnalogOut6 = 240;
##	const int	cmiAnalogOut7 = 241;
##	const int	cmiAnalogOut8 = 242;
##	const int	cmiIntensity = 251;
##	const int	cmiPower = 267;
##	const int	cmiActiveChannel = 300;
##	const int	cmiPIDCourse = 1030;
##	const int	cmiPIDUseTa = 1031;
##	const int	cmiPIDUseT = cmiPIDUseTa;
##	const int	cmiPID_T = 1033;
##	const int	cmiPID_P = 1034;
##	const int	cmiPID_I = 1035;
##	const int	cmiPID_D = 1036;
##	const int	cmiDeviationSensitivityDim = 1040;
##	const int	cmiDeviationSensitivityFactor = 1037;
##	const int	cmiDeviationPolarity = 1038;
##	const int	cmiDeviationSensitivityEx = 1039;
##	const int	cmiDeviationUnit = 1041;
##	const int	cmiPIDConstdt = 1059;
##	const int	cmiPID_dt = 1060;
##	const int	cmiPID_AutoClearHistory = 1061;
##	const int	cmiDeviationChannel = 1063;
##	const int	cmiAutoCalPeriod = 1120;
##	const int	cmiAutoCalUnit = 1121;
##	const int	cmiServerInitialized = 1124;
##	const int	cmiWavelength9 = 1130;
##	const int	cmiExposureValue19 = 1155;
##	const int	cmiExposureValue29 = 1180;
##	const int	cmiMin19 = 1205;
##	const int	cmiMin29 = 1230;
##	const int	cmiMax19 = 1255;
##	const int	cmiMax29 = 1280;
##	const int	cmiAvg19 = 1305;
##	const int	cmiAvg29 = 1330;
##	const int	cmiWavelength10 = 1355;
##	const int	cmiWavelength11 = 1356;
##	const int	cmiWavelength12 = 1357;
##	const int	cmiWavelength13 = 1358;
##	const int	cmiWavelength14 = 1359;
##	const int	cmiWavelength15 = 1360;
##	const int	cmiWavelength16 = 1361;
##	const int	cmiWavelength17 = 1362;
##	const int	cmiExternalInput = 1400;
##	const int	cmiPressure = 1465;
##	const int	cmiBackground = 1475;
##	const int	cmiDistanceMode = 1476;
##	const int	cmiInterval = 1477;
##	const int	cmiIntervalMode = 1478;
##
##// WLM Control Mode Constants
##	const int	cCtrlWLMShow = 1;
##	const int	cCtrlWLMHide = 2;
##	const int	cCtrlWLMExit = 3;
##	const int	cCtrlWLMWait = 0x0010;
##	const int	cCtrlWLMStartSilent = 0x0020;
##	const int	cCtrlWLMSilent = 0x0040;
##
##// Operation Mode Constants (for "Operation" and "GetOperationState" functions)
##	const int	cStop = 0;
##	const int	cAdjustment = 1;
##	const int	cMeasurement = 2;
##
##// Base Operation Constants (To be used exclusively, only one of this list at a time,
##// but still can be combined with "Measurement Action Addition Constants". See below.)
##	const int	cCtrlStopAll = cStop;
##	const int	cCtrlStartAdjustment = cAdjustment;
##	const int	cCtrlStartMeasurement = cMeasurement;
##	const int	cCtrlStartRecord = 0x0004;
##	const int	cCtrlStartReplay = 0x0008;
##	const int	cCtrlStoreArray = 0x0010;
##	const int	cCtrlLoadArray = 0x0020;
##
##// Additional Operation Flag Constants (combine with "Base Operation Constants" above.)
##	const int	cCtrlDontOverwrite = 0x0000;
##	const int	cCtrlOverwrite = 0x1000;  // don't combine with cCtrlFileDialog
##	const int	cCtrlFileGiven = 0x0000;
##	const int	cCtrlFileDialog = 0x2000; // don't combine with cCtrlOverwrite and cCtrlFileASCII
##	const int	cCtrlFileBinary = 0x0000; // *.smr, *.ltr
##	const int	cCtrlFileASCII = 0x4000;  // *.smx, *.ltx, don't combine with cCtrlFileDialog
##
##// Measurement Control Mode Constants
##	const int	cCtrlMeasDelayRemove = 0;
##	const int	cCtrlMeasDelayGenerally = 1;
##	const int	cCtrlMeasDelayOnce = 2;
##	const int	cCtrlMeasDelayDenyUntil = 3;
##	const int	cCtrlMeasDelayIdleOnce = 4;
##	const int	cCtrlMeasDelayIdleEach = 5;
##	const int	cCtrlMeasDelayDefault = 6;
##
##// Measurement Triggering Action Constants
##	const int	cCtrlMeasurementContinue = 0;
##	const int	cCtrlMeasurementInterrupt = 1;
##	const int	cCtrlMeasurementTriggerPoll = 2;
##	const int	cCtrlMeasurementTriggerSuccess = 3;
##
##// ExposureRange Constants
##	const int	cExpoMin = 0;
##	const int	cExpoMax = 1;
##	const int	cExpo2Min = 2;
##	const int	cExpo2Max = 3;
##

##
##// Measurement Range Constants
##	const int	cRange_250_410 = 4;
##	const int	cRange_250_425 = 0;
##	const int	cRange_300_410 = 3;
##	const int	cRange_350_500 = 5;
##	const int	cRange_400_725 = 1;
##	const int	cRange_700_1100 = 2;
##	const int	cRange_800_1300 = 6;
##	const int	cRange_900_1500 = cRange_800_1300;
##	const int	cRange_1100_1700 = 7;
##	const int	cRange_1100_1800 = cRange_1100_1700;
##
##// Unit Constants for Get-/SetResultMode, GetLinewidth, Convert... and Calibration
##	const int	cReturnWavelengthVac = 0;
##	const int	cReturnWavelengthAir = 1;
##	const int	cReturnFrequency = 2;
##	const int	cReturnWavenumber = 3;
##	const int	cReturnPhotonEnergy = 4;
##
##// Power Unit Constants
##	const int	cPower_muW = 0;
##	const int	cPower_dBm = 1;
##
##// Source Type Constants for Calibration
##	const int	cHeNe633 = 0;
##	const int	cHeNe1152 = 0;
##	const int	cNeL = 1;
##	const int	cOther = 2;
##	const int	cFreeHeNe = 3;
##
##// Unit Constants for Autocalibration
##	const int	cACOnceOnStart = 0;
##	const int	cACMeasurements = 1;
##	const int	cACDays = 2;
##	const int	cACHours = 3;
##	const int	cACMinutes = 4;
##
##
##// Return errorvalues of GetFrequency, GetWavelength and GetWLMVersion
##	const int	ErrNoValue = 0;
##	const int	ErrNoSignal = -1;
##	const int	ErrBadSignal = -2;
##	const int	ErrLowSignal = -3;
##	const int	ErrBigSignal = -4;
##	const int	ErrWlmMissing = -5;
##	const int	ErrNotAvailable = -6;
##	const int	InfNothingChanged = -7;
##	const int	ErrNoPulse = -8;
##	const int	ErrDiv0 = -13;
##	const int	ErrOutOfRange = -14;
##	const int	ErrUnitNotAvailable = -15;
##	const int	ErrMaxErr = ErrUnitNotAvailable;
##
##// Return errorvalues of GetTemperature and GetPressure
##	const int	ErrTemperature = -1000;
##	const int	ErrTempNotMeasured = ErrTemperature + ErrNoValue;
##	const int	ErrTempNotAvailable = ErrTemperature + ErrNotAvailable;
##	const int	ErrTempWlmMissing = ErrTemperature + ErrWlmMissing;
##
##// Return errorvalues of GetDistance
##	// real errorvalues are ErrDistance combined with those of GetWavelength
##	const int	ErrDistance = -1000000000;
##	const int	ErrDistanceNotAvailable = ErrDistance + ErrNotAvailable;
##	const int	ErrDistanceWlmMissing = ErrDistance + ErrWlmMissing;
##
##// Return flags of ControlWLMEx in combination with Show or Hide, Wait and Res = 1
##	const int	flServerStarted = 0x0001;
##	const int	flErrDeviceNotFound = 0x0002;
##	const int	flErrDriverError = 0x0004;
##	const int	flErrUSBError = 0x0008;
##	const int	flErrUnknownDeviceError = 0x0010;
##	const int	flErrWrongSN = 0x0020;
##	const int	flErrUnknownSN = 0x0040;
##	const int	flErrTemperatureError = 0x0080;
##	const int	flErrPressureError = 0x0100;
##	const int	flErrCancelledManually = 0x0200;
##	const int	flErrUnknownError = 0x1000;
	
