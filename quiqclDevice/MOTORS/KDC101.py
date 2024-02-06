"""
A module for controlling KDC101 motor device.

@author: Jiyong Kang
@email: kangz12345@snu.ac.kr
"""

from ctypes import cdll, c_int, c_short, c_long, c_char_p, c_ushort, c_ulong, pointer
from time import sleep

from os import getcwd, chdir
from os.path import abspath, dirname

def load_dll(dll_path='C:/Program Files/Thorlabs/Kinesis'):
        """Loads the dynamic linked library.

        __lib is a static singleton, hence only one or no instance exists.
        Due to some working directory issues with resolving the DLL path,
        this method changes the working directory temporarily to load the DLL.

        This function should be called before using any of KDC101 instances.

        Parameters
        ----------
        dll_path : str
            you have to provide the path for the Thorlabs Kinesis software
        """
        # save the current working directory
        cwd = getcwd()

        # change the working directory to 'here' and load the DLL
        chdir(dll_path)
        try:
            lib = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")
        except:
            lib = cdll.LoadLibrary(dll_path + "/Thorlabs.MotionControl.KCube.DCServo.dll")

        # restore the original working directory
        chdir(cwd)

        return lib

class KDC101:
    """
    A class representing a KDC101 instance

    Methods
    -------
    get_serial_number       : () => str
    get_position            : [bool] => float
    get_acc_and_vel         : () => (int, int)

    set_acc_and_vel         : [int, int] => ()
    
    needs_home              : () => bool
    
    print_msg               : Any => ()
    open                    : [bool] => KDC101
    close                   : () => ()
    start_polling           : [int] => int
    stop_polling            : () => ()
    open_and_start_polling  : [int] => KDC101
    home                    : [bool, bool] => bool
    move_to_position        : number [, bool, bool] => (int, int, int)
    move_relative           : number [, bool, bool] => (int, int, int)
    stop_profiled           : () => ()
    """

    # device unit / millimeter
    DEVUNIT_RATIO = 34304

    # DLL object - will be loaded later.
    __lib = None
    try:
        __lib = load_dll()
    except Exception as err:
        print("KDC101: failed to load dll.")
        print(str(err))

    # Constants
    class MessageType:
        GENERIC_DEVICE = 0
        GENERIC_MOTOR = 2
        GENERIC_DC_MOTOR = 3

    class MessageId:
        class GenericDevice:
            SETTINGS_INITIALIZED = 0
            SETTINGS_UPDATED = 1
            SETTINGS_EXTERN = 2
            ERROR = 3
            CLOSE = 4
            SETTINGS_RESET = 5
        class GenericMotor:
            HOMED = 0
            MOVED = 1
            STOPPED = 2
            LIMIT_UPDATED = 3
        class GenericDCMotor:
            ERROR = 0
            STATUS = 1


    def load_dll(dll_path):
        """Loads the dynamic linked library.

        __lib is a static singleton, hence only one or no instance exists.
        Due to some working directory issues with resolving the DLL path,
        this method changes the working directory temporarily to load the DLL.

        This function should be called before using any of KDC101 instances.

        Parameters
        ----------
        dll_path : str
            you have to provide the path for the Thorlabs Kinesis software
        """
        if KDC101.__lib is None:
            KDC101.__lib = load_dll(dll_path)

    def get_serial_number(self):
        return self.__serno.value.decode()

    def get_position(self, in_devunit=False):
        """Gets the current position of the motor.

        Parameters
        ----------
        in_devunit : bool (default False)
            if this flag is set, returns pos in device unit
            o.w., returns pos in millimeter

        Returns
        -------
        float if in_devunit==False
            current position in millimeters
        int if in_devunit==True
            current position in device unit
        """
        pos = self.__lib.CC_GetPosition(self.__serno)
        if not in_devunit:
            pos = self.__convert_to_mm(pos)
        return pos

    def get_acc_and_vel(self):
        """Gets acceleration and max-velocity of the motor.

        Returns
        -------
        tuple (int, int)
            (acceleration, max-velocity) in device unit.
        """
        acc, vel = c_int(), c_int()
        err = self.__lib.CC_GetVelParams(self.__serno, pointer(acc), pointer(vel))
        if err != 0:
            raise ErrorCodeException(err)

        return acc.value, vel.value

    def set_acc_and_vel(self, acc=None, vel=None):
        """Sets acceleration and max-velocity of the motor.

        Parameters
        ----------
        acc : int (optional)
            desired acceleration
            no change if it is None
        vel : int (optional)
            desired max-velocity
            no change if it is None
        """
        if acc is None and vel is None:
            self.print_msg("Warning: no change for acceleration and max-velocity.")
            return

        elif acc is None or vel is None:
            current_acc_vel = self.get_acc_and_vel()
            if acc is None:
                acc = current_acc_vel[0]
            elif vel is None:
                vel = current_acc_vel[1]

        err = self.__lib.CC_SetVelParams(self.__serno, c_int(acc), c_int(vel))
        if err != 0:
            raise ErrorCodeException(err)

    def needs_home(self):
        """Returns whether this device needs homing.
        """
        return not bool(self.__lib.CC_CanMoveWithoutHomingFirst(self.__serno))

    def print_msg(self, msg):
        """Prints message with its serial number to identify itself.

        """
        print("KDC101[S.N. {}]: {}".format(self.__serno.value.decode(), msg))

    def open(self, auto_build=True):
        """Opens the device to communicate.
        
        Raises
        ------
        ErrorCodeException - error when opening

        Returns
        -------
        KDC101
            returns self
        """
        err = self.__lib.CC_Open(self.__serno)
        if err != 0:
            if err == 2 or err == 7:
                # FT_DeviceNotFound (2) or FT_DeviceNotPresent (7)
                if auto_build:
                    self.print_msg("Warning: error code {}".format(err))
                    self.print_msg("  - building device list...")
                    self.__build_device_list()
                    return self.open(auto_build=False)
                else:
                    raise ErrorCodeException(err)
            raise ErrorCodeException(err)
        return self

    def close(self):
        """Closes the device communication.

        """
        self.__lib.CC_Close(self.__serno)

    def start_polling(self, interval=200):
        """Starts the internal polling loop to keep track on the device status.
        
        Parameters
        ----------
        interval : int (default 200)
            The polling rate in milliseconds
        
        Raises
        ------
        ValueError - zero or negative interval

        Returns
        -------
        int
            if success, current polling interval in milliseconds.
            zero if polling is not started.
            if the interval is different, returns negated current value.
        """
        if interval <= 0:
            raise ValueError("polling interval must be positive integer.")

        success = self.__lib.CC_StartPolling(self.__serno, c_int(interval))
        sleep(2)  # for stability
        if success != 1:
            return -self.__lib.CC_PollingDuration(self.__serno)
        else:
            return interval

    def stop_polling(self):
        """Stops the internal polling loop.

        """
        self.__lib.CC_StopPolling(self.__serno)

    def open_and_start_polling(self, interval=200):
        """Opens and starts polling.

        This method can be useful in with statement.

        Raises
        ------
        FailedException - failed to start polling

        Returns
        -------
        KDC101
            returns self
        """
        self.open()
        set_interval = self.start_polling(interval)
        if set_interval == 0:
            raise FailedException("start polling")
        elif set_interval < 0:
            self.print_msg("Warning: the polling interval is not set.")
            self.print_msg("  - current value: {}ms.".format(set_interval))

        return self

    def home(self, force=False, verbose=False):
        """Homes the device - device will find 'home' and calibrates its
        zero position.

        Waits until the homing process is finished.
        
        Parameters
        ----------
        force : bool (default False)
            forces to home regardless the motor needs it or not

        Returns
        -------
        bool
            whether the device is homed properly or not
        """
        if not self.needs_home():
            self.print_msg("Warning: the device does not need homing.")
            if not force:
                self.print_msg("  - skip homing...")
                return

        if verbose:
            self.print_msg("start homing...")

        self.__clear_message_queue()
        err = self.__lib.CC_Home(self.__serno)
        if err != 0:
            raise ErrorCodeException(err)

        # wait for the homing process is complete
        _, msg_id, _ = self.__wait_for([(2, 0), (2, 2)], verbose=verbose)

        if verbose and msg_id == KDC101.MessageId.GenericMotor.HOMED:
            self.print_msg("homed.")

        return msg_id == KDC101.MessageId.GenericMotor.HOMED

    def move_to_position(self, pos, in_devunit=False, verbose=False):
        """Moves the motor to the certain position.
        
        Waits until the moving process is finished.

        Parameters
        ----------
        pos : number
            desired destination position of the motor in millimeters
            if in_devunit is True, this is in device unit(check DEVUNIT_RATIO)
        in_devunit : bool (default False)
            if this flag is set, pos is interpretted in device unit
            o.w., pos is interpretted in millimeter
        verbose : bool (default False)
            if this flag is set, status message is displayed
        """
        pos = self.__convert_to_devunit(pos, in_devunit)

        if verbose:
            self.print_msg("moving to {:0.4f}mm..."
                           .format(self.__convert_to_mm(pos)))

        self.__clear_message_queue()
        err = self.__lib.CC_MoveToPosition(self.__serno, c_int(pos))
        if err != 0:
            raise ErrorCodeException(err)

        # wait for the moving process is complete
        res = self.__wait_for_move(verbose=verbose)

        if verbose:
            self.print_msg("moved.")

        return res

    def move_relative(self, disp, in_devunit=False, verbose=False):
        """Moves the motor relatively by the given displacement.

        Waits until the moving process is finished.

        Parameters
        ----------
        disp : number
            desired displacement from the current position in millimeters
            if in_devunit is True, this is in device unit(check DEVUNIT_RATIO)
        in_devunit : bool (default False)
            if this flag is set, disp is interpretted in device unit
            o.w., disp is interpretted in millimeter
        verbose : bool (default False)
            if this flag is set, status message is displayed
        """
        disp = self.__convert_to_devunit(disp, in_devunit)

        if verbose:
            self.print_msg("moving by {:0.4f}mm..."
                           .format(self.__convert_to_mm(disp)))

        self.__clear_message_queue()
        err = self.__lib.CC_MoveRelative(self.__serno, c_int(disp))
        if err != 0:
            raise ErrorCodeException(err)

        # wait for the moving process is complete
        res = self.__wait_for_move(verbose=verbose)

        if verbose:
            self.print_msg("moved.")

        return res

    def stop_profiled(self):
        """Stop the device with its motion profile.
        """
        err = self.__lib.CC_StopProfiled(self.__serno)
        if err != 0:
            raise ErrorCodeException(err)

    def __build_device_list(self):
        """Builds device list to find devices.

        Raises
        ------
        FailedException - failed to build the device list
        """
        if self.__lib.TLI_BuildDeviceList() != 0:
            raise FailedException("build the device list.")

    def __convert_to_devunit(self, value, in_devunit=False):
        """Converts value into device unit.
        
        Parameters
        ----------
        value : number
            it may be already in device unit
        in_devunit : bool (default False)
            whether value is in device unit or not

        Returns
        -------
        int
            converted integer value in device unit
        """
        if not in_devunit:
            value *= self.DEVUNIT_RATIO
        elif not isinstance(value, int):
            self.print_msg(("Warning: non-integer value ({}) is given "
                            + "in device unit.").format(value))
        return int(value)

    def __convert_to_mm(self, value, in_devunit=True):
        """Converts value into millimeters.
        
        Parameters
        ----------
        value : number
            it may be already in millimeters
        in_devunit : bool (default True)
            whether value is in device unit or not

        Returns
        -------
        float
            converted floating point value in millimeters
        """
        if in_devunit:
            value /= self.DEVUNIT_RATIO
        return value

    def __init__(self, serno: str, force_load_dll=True):
        """
        Parameters
        ----------
        serno : str
            The serial number of the device

        force_load_dll : bool (default True)
            This is for debugging and developping.
            If this is False, then it does not raise Error even if it fails
            to load the DLL.
        """
        self.__serno = c_char_p(serno.encode())

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop_polling()
        self.close()

    def __del__(self):
        self.stop_polling()
        self.close()

    def __wait_for(self, target_tuples, verbose=True):
        """Waits for the message which has the target message type
        and id. Multiple targets can be passed within a list.

        Parameters
        ----------
        target_tuples : list of tuples (target_mtype, target_mid)
            target message type and id tuples
            if there is only one tuple, it can be simply passed by itself
        verbose : bool (default True)
            whether to print the received messages or not

        Returns
        -------
        tuple (int, int, int)
            whole matched target message information
            (target_mtype, target_mid, target_mdata)
        """
        if not isinstance(target_tuples, list):
            target_tuples = [target_tuples]

        mtype, mid = c_short(), c_short()
        mdata = c_long()
        while True:
            self.__lib.CC_WaitForMessage(self.__serno, pointer(mtype),
                                         pointer(mid), pointer(mdata))
            if verbose:
                self.print_msg("  - received message[{}][{}]: {}"
                               .format(mtype.value, mid.value, mdata.value))
            if (mtype.value, mid.value) in target_tuples:
                return mtype.value, mid.value, mdata.value

    def __wait_for_move(self, verbose=False):
        """Waits for a moving process to be finished.

        If the motor reaches its revolution limit, show warning message.

        Parameters
        ----------
        verbose : bool (default False)
            it is passed to the function __wait_for
        """
        res = self.__wait_for([(2, 1), (2, 2), (2, 3)], verbose=verbose)
        if res[1] == 2 and verbose:
            # message id 2 : Stopped
            self.print_msg("The motor has been stopped.")
        if res[1] == 3:
            # message id 3 : LimitUpdated - reached rev limit
            self.print_msg("Warning: the motor has reached its revolution limit.")
            self.print_msg("  - current position: {:0.4f}mm."
                           .format(self.get_position()))

        return res

    def __clear_message_queue(self):
        """Clears the device message queue.

        """
        self.__lib.CC_ClearMessageQueue(self.__serno)


class ErrorCodeException(Exception):
    def __init__(self, err_code, message=None):
        self.__err_code = err_code
        if message is None:
            message = "error code {} is received.".format(err_code)
        super().__init__(message)

    def get_code(self):
        return self.__err_code


class FailedException(Exception):
    def __init__(self, failed_action: str):
        super().__init__("failed to {}.".format(failed_action))
