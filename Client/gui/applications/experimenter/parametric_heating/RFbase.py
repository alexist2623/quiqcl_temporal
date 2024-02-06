"""
Created on Aug 26, 2021.
@author: Jiyong Kang
@Eittor: Junho Jeong
Now the RF source includes a parameter __number_of_channels.
Included classes:
    - SerialPortRFSource
    - SocketPortRFSource
"""

import serial, socket

class RFSource:
    """
    This class is an interface for interacting with RF source devices.
    - Every class implementing RFsource device should inherit this class.
    - Note that exceptions may occur in each method depending on devices.
    - Default units
        - power:        dBm
        - frequency:    Hz
        - phase:        degree
    """

    def __init__(self, min_power, max_power, min_freq, max_freq):
        # device properties
        self.__min_power = min_power
        self.__max_power = max_power
        self.__min_freq = min_freq
        self.__max_freq = max_freq
        self.__number_of_channels = 1

    def connect(self):
        """Connects to the device."""
        not_implemented('connect', self)

    def disconnect(self):
        """Disconnects from the device."""
        not_implemented('disconnect', self)

    def is_connected(self) -> bool:
        """Returns whether the device is currently connected."""
        not_implemented('is_connected', self)

    def enable_output(self):
        """Enables the output of the device."""
        not_implemented('enable_output', self)

    def disable_output(self):
        """Disables the output of the device."""
        not_implemented('disable_output', self)

    def is_output_enabled(self) -> bool:
        """Returns whether the device output is currently enabled."""
        not_implemented('is_output_enabled', self)

    def setPower(self, power: float):
        """Applies power as given, in dBm."""
        not_implemented('apply_power', self)

    def setFrequency(self, freq: float):
        """Applies frequency as given, in Hz."""
        not_implemented('apply_frequency', self)

    def setPhase(self, phase: float):
        """Applies phase as given, in degrees."""
        not_implemented('apply_phase', self)

    def getPower(self) -> float:
        """Returns the current power of the output in dBm."""
        not_implemented('read_power', self)

    def getFrequency(self) -> float:
        """Returns the current frequency of the output in Hz."""
        not_implemented('read_frequency', self)

    def getPhase(self) -> float:
        """Returns the current phase of the output in degrees."""
        not_implemented('read_phase', self)

    def is_locked(self) -> bool:
        """Returns whether the current output is locked."""
        not_implemented('is_locked', self)
        
    def lockFrequency(self, external_flag: int, frequency: float):
        """Determine the reference frequency: external/internal source."""
        not_implemented('lockFrequency', self)
        

    @property
    def min_power(self) -> float:
        """Returns minimum power limit of the device in dBm."""
        return self.__min_power

    @property
    def max_power(self) -> float:
        """Returns maximum power limit of the device in dBm."""
        return self.__max_power

    @property
    def min_frequency(self) -> float:
        """Returns minimum frequency limit of the device in Hz."""
        return self.__min_freq

    @property
    def max_frequency(self) -> float:
        """Returns maximum frequency limit of the device in Hz."""
        return self.__max_freq
    
    def check_range(self, val, min_, max_, label=None):
        """Checks the given value fits in the range [min_, max_].
        Raises:
            ValueError - val does not fit in the range.
        """
        if val > max_ or val < min_:
            raise ValueError('{}{} is out of range: min={}, max={}.'
                             .format('' if label is None else label + '=',
                                     val, min_, max_))



class SerialPortRFSource(RFSource):
    """
    This class is an abstract class for the devices which use serial port
    communication.
    Package 'serial' is required.
    This inherits RFSource, hence a lot of abstract methods exist.
    However, some of them are implemented(overridden):
    - connect
    - disconnect
    - is_connected
    These are an additional public property which is not in RFSource interface:
    - port (setter, getter)
    Moreover, this class provides some protected methods:
    - _send_command
    - _query_command
    """
    def __init__(self, min_power, max_power, min_freq, max_freq,
                 port=None, **serial_kwargs):
        """Initializes object properties.
        serial.Serial object is created without connection.
        Even if the given port is not None, Serial constructor calls open()
        when the port is not None, hence it gives the port after construction.
        Params:
            port - serial port name e.g. 'COM32'.
                   when it is None, it can be set later.
            **serial_kwargs - keyword arguments for Serial constructor.
        """
        super().__init__(min_power, max_power, min_freq, max_freq)
        self.__connected = False
        self.__com = serial.Serial(port=None, **serial_kwargs)
        self.__com.port = port
        
    def connect(self):
        """
        Raises:
            serial.SerialException - port is None or given device is not found.
        """
        self.__com.open()
        self.__connected = True

    def disconnect(self):
        self.__com.close()
        self.__connected = False

    @property
    def is_connected(self) -> bool:
        return self.__connected
    

    @property
    def port(self):
        return self.__com.port

    @port.setter
    def port(self, port):
        """Sets serial port.
        When the port is currently open, the current port is closed and it
        opens the given port.
        """
        self.__com.port = port

    """
    Protected methods
    Methods below are for classes which inherit this class.
    """
    def _send_command(self, cmd, encoding='ascii') -> bool:
        """Sends the given command to the serial port.
        Command terminator should be included in cmd, i.e., this method does
        not append the terminator.
        Params:
            cmd - command in type of str or bytes.
            encoding - it is possible to indicate other encoding if it is not
                       ascii encoding.
        Raises:
            TypeError - type(cmd) is not str nor bytes.
            serial.SerialException - the serial port is not open.
            serial.SerialTimeoutException - in case of write timeout,
                                            if it is set.
        Returns:
            whether the command is written successfully.
            (by comparing the number of written bytes)
        """
        if isinstance(cmd, str):
            byte_cmd = cmd.encode(encoding)
        elif isinstance(cmd, bytes):
            byte_cmd = cmd
        else:
            raise TypeError('command should be str or bytes type.')

        written = self.__com.write(byte_cmd)

        return written == len(byte_cmd)

    def _query_command(self, cmd, encoding='ascii',
                       terminator='\r\n', size=1, trim=True):
        """Sends query with the given command to the serial port, and receives
        the response.
        Command terminator should be included in cmd, i.e., this method does
        not append the terminator. The given terminator will be used for
        receiving response, and trimming it. It can take multiple responses,
        indicated by size parameter.
        If the given terminator is None, it receives the given size number of
        bytes instead. In this case, trim has no effect.
        Params:
            cmd - command in type of str or bytes.
            encoding - it is possible to indicate other encoding if it is not
                       ascii encoding.
            terminator - terminator sequence of the command syntax.
            size - the number of bytes if terminator is None.
                   the number of responses o.w.
            trim - if flag is set, the terminators in response is trimmed.
        Raises:
            IOError - failed to completely send the command.
            ValueError - size is not a positive integer.
            TypeError - type(cmd) is not str nor bytes.
            serial.SerialException - the serial port is not open.
            serial.SerialTimeoutException - in case of write timeout,
                                            if it is set.
        Returns:
            the query response(s) in the same type of cmd.
            if terminator is not None and size > 1, they are packed in a list.
        """
        if not isinstance(size, int) or size < 1:
            raise ValueError('size shuold be a positive integer.')

        if not self._send_command(cmd, encoding):
            raise IOError('failed to completely send the command.')

        response = []

        if terminator is None:
            # read size bytes
            response.append(self.__com.read(size))

        else:
            if not isinstance(terminator, bytes):
                terminator = terminator.encode(encoding)
            len_terminator = len(terminator)

            # take size responses
            for _ in range(size):
                res = self.__com.read_until(terminator)
                if trim:
                    # trim the terminator part at the end
                    res = res[:-len_terminator]
                response.append(res)

        if isinstance(cmd, str):
            # match the response type
            response = [res.decode(encoding) for res in response]

        # return in a list only if there are multiple responses
        if len(response) > 1:
            return response
        else:
            return response[0]
        
    def _get_comport(self, serial_number):
        from serial.tools import list_ports
        for dev in list_ports.comports():
            if serial_number == dev.serial_number:
                return self.device
            
        raise ValueError ("Couldn't find the device that has the serial number (%s)." % serial_number)

class SocketRFSource(RFSource):
    """
    This class is an abstract class for the devices which use socket
    communication.
    Package 'socket' is required.
    This inherits RFSource, hence a lot of abstract methods exist.
    However, some of them are implemented(overridden):
    - connect
    - disconnect
    - is_connected
    These are additional public properties which are not in RFSource interface:
    - tcp_ip (getter, setter)
    - tcp_port (getter, setter)
    Moreover, this class provides some protected methods:
    - _send_command
    - _query_command
    """
    def __init__(
        self, min_power, max_power, min_freq, max_freq, tcp_ip="", tcp_port=0
    ):
        """
        Initializes object properties.
        Params:
            tcp_ip (str) - IP address. When it is None, it can be set later.
            tcp_port (int or str) - Port number. __tcp_port will be set in int
        Raises:
            TypeError - tcp_port shoule be either number type or string of number
        """
        super().__init__(min_power, max_power, min_freq, max_freq)
        self.__connected = False
        self.__tcp_ip = tcp_ip
        self.tcp_port = tcp_port

    def connect(self, *args, **kwargs):
        """Connects to the server with its ip address and port number.
        Args:
            Every argument will be passed to socket.create_connection().
        """
        self.__socket = socket.create_connection(
            (self.__tcp_ip, self.__tcp_port), *args, **kwargs)
        self.__connected = True

    def disconnect(self):
        self.__socket.close()
        self.__connected = False

    def is_connected(self):
        return self.__connected

    @property
    def tcp_ip(self):
        return self.__tcp_ip

    @tcp_ip.setter
    def tcp_ip(self, tcp_ip):
        self.__tcp_ip = tcp_ip

    @property
    def tcp_port(self) -> int:
        return self.__tcp_port

    @tcp_port.setter
    def tcp_port(self, tcp_port):
        """
        Raises:
            TypeError - tcp_port shoule be either number type or string of number
        """
        try:
            self.__tcp_port = int(tcp_port)
        except:
            TypeError("tcp_port shoule be either number type or string of number")

    def _send_command(self, cmd, encoding="ascii"):
        """Sends the given command to the socket.
        Command terminator should be included in cmd, i.e., this method does
        not append the terminator.
        Params:
            cmd - Command in type of str or bytes.
            encoding - It is possible to indicate other encoding if it is not
                       ascii encoding.
        Raises:
            TypeError - Type of cmd is not str nor bytes.
            OSError - The socket is not connected.
            socket.timeout - In case of send timeout, if it has been set.
        Returns:
            whether the command has been sent successfully.
            (by comparing the number of bytes sent)
        """
        if isinstance(cmd, str):
            byte_cmd = cmd.encode(encoding)
        elif isinstance(cmd, bytes):
            byte_cmd = cmd
        else:
            raise TypeError("command should be str or bytes type.")

        sent = self.__socket.send(byte_cmd)

        return sent == len(byte_cmd)

    def _query_command(
            self, cmd, encoding="ascii", terminator="\n", size=1, bufsize=1024, trim=True):
        """Sends the given command to the socket, and receives the response.
        Command terminator should be included in cmd, i.e., this method does
        not append the terminator. The given terminator will be used for
        receiving and trimming response data. It can take multiple responses,
        indicated by size parameter.
        Params:
            cmd - Command in type of str or bytes.
            encoding - It is possible to indicate other encoding if it is not
                       ascii encoding.
            terminator - Terminator sequence of the command syntax.
            size - The number of bytes if terminator is None.
                    The number of responses o.w.
            bufsize - The maximum number of bytes to be received at once.
            trim - If the flag is set, the terminator in the response data will be trimmed.
        Raises:
            IOError - Failed to completely send the command.
            ValueError - size is not a positive integer.
            TypeError - Type of cmd is not str nor bytes.
            OSError - The socket is not connected
            socket.timeout - In case of send timeout if it has been set.
        Returns:
            the query response(s) in the same type of cmd.
            If terminator is not None and size > 1, they are packed in a list.
        """
        if not isinstance(size, int) or size < 1:
            raise ValueError("size shuold be a positive integer.")

        if not self._send_command(cmd, encoding):
            raise IOError("failed to completely send the command.")

        response = []

        if terminator is None:
            # read size bytes
            res = self.__socket.recv(size)
            while len(res) < size:
                res += self.__socket.recv(size - len(res))
            response.append(res)

        else:
            if not isinstance(terminator, bytes):
                terminator = terminator.encode(encoding)

            # take size responses

            tmp = ""
            incomplete_word = tmp.encode(encoding)
            # repeat until all data has been received
            while len(response) < size:
                res = self.__socket.recv(bufsize)
                res_list = res.split(terminator)
                # combine the incomplete word from the previous loop with the first word
                res_list[0] = incomplete_word + res_list[0]
                # The last word is empty or incomplete
                response.extend(res_list[:-1])
                incomplete_word = res_list[-1]
                if not trim:
                    response = [(r + terminator) for r in response]

        if isinstance(cmd, str):
            # match the response type
            response = [res.decode(encoding) for res in response]

        # return in a list only if there are multiple responses
        if len(response) > 1:
            return response
        else:
            return response[0]




def not_implemented(func, obj):
    """Raises NotImplementedError with the given function name.
    This is a helper function, which is NOT included in RFSource class.
    """
    raise NotImplementedError("method '{}' is not supported on device '{}'"
                              .format(func, obj.__class__.__name__))