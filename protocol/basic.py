"""
This module implements BasicProtocol.
For encodings, 'latin-1' is used since it can handle up to 255
while 'utf-8' cannot.

**BasicProtocol** - this description is mainly from the verilog file.

Note that '\x10' is DLE (Data Link Escape) character in ASCII table.

'!' <byte_count> <ASCII_string> '\r' '\n' : Command format.
    <byte_count> is a "single" hexadecimal ASCII which indicates the
        length of <ASCII_string>, hence it is in range [1, 15].
        E.g. 'b' means 11 characters excluding terminators('\r\n').
    If <ASCII_string> contains a byte corresponding to decimal value 16 ('\x10'),
        '\x10\x10' should be sent, and '\x10\x10' sequence is counted as one byte.
    <examples>
     - "!3RUN\r\n" is "RUN" command
     - "!5TEST\x10\x10\r\n" is {"TEST", 8'h10} command which has no meaning

'#' <num_digits> <byte_count> <raw_data> '\r' '\n': Modified BTF
    BTF means 'Binary Transfer Format' (IEEE 488.2 # format).
    <num_digits> is a "single" hexadecial ASCII.
        E.g. 'a' means that following ten characters will represent <byte_count>.
    <byte_count> is hexadecimal number written in ASCII.
        E.g. '15' means that the block size is 21 bytes.
            This length excludes terminators('\r\n')
    Generally BTF is used by a following CMD rather than by itself.
    If <raw_data> contains a byte corresponding to decimal value 16 ('\x10'),
        '\x10\x10' should be sent, and '\x10\x10' sequence is counted as one byte.
    <examples>
    - "#20aABCDE+WXYZ\r\n" means block length is 10 and block data is "ABCDE+WXYZ"
    - "#14A\x10\x10\x00B\r\n" means block length is 4 and the block data is
        {"A", 8'h10, 8'h00, "B"}

The following 5 messages are special escape sequences and can be recognized
    even in the middle of the above messages.

'\x10'+'C': Clear the input buffer and reset the FSM to the IDLE state. 
    The device will send back '\x10'+'C'.

'\x10'+'R': Read the current status of 32 bits.
    This will also clear the input buffer and reset the FSM.
    The device will send back '\x10'+'R' + <32 bits> + '\r\n'.

The following 3 messages are for debugging, hence normal devices might
not support these escape sequences for better synthesis performance.

'\x10'+'T': Set trigger setting.

'\x10'+'A': Arm trigger.

'\x10'+'W': Read the captured waveform data.
    This will also clear the transmitter buffer and reset the FSM.
    The device will send back '\x10'+'W'.
    TODO: the waveform data?
"""

import serial
import util


# constants
CMD_RX_BUFFER_BYTES = 0xf
BTF_RX_BUFFER_BYTES = 0x100
TERMINATOR_STRING = '\r\n'

class EscapeSequenceException(Exception):
        """This exception indicates that an escape sequence is detected
        reading bytes from the serial port communication.

        There is a special attribute self.escape_R_data which contains
        the data after the escape-read sequence '\x10R'.
        """
        def __init__(self, escape_char):
            self.escape_char = escape_char
            self.escape_R_data = None

        def __str__(self):
            return f'\\x10{self.escape_char} is detected.'


def new_serial(port=None, write_timeout=0):
    """Returns a new proper Serial object for BasicProtocol."""
    return serial.Serial(
        port=port,
        baudrate=57600,
        timeout=1,                      # read timeout
        parity=serial.PARITY_NONE,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_TWO,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
        write_timeout=write_timeout     # non-blocking write by default
    )

def query(com, cmd, modified_BTF=None, expect=None):
    """Sends a query to the device and receives a message.
    
    Since the reading timeout is 1 sec, we need to be careful when querying.
    If we do non-blocking write (write_timeout=0), we might not get the
    response message in 1 sec.

    Therefore, it would be safer to wait for the write buffer to be emptied.
    
    For more detailed behavior and the argument description, please refer to
    send_command(), send_mod_BTF(), and read_next_message().

    Args:
        cmd - Desired command string.
        modified_BTF - A 'payload' for the query command, if any.
        expect - Expected response message signature character, if any.

    Returns:
        (str, str) - If expect is None; (signatrue character, received data).
        str - If expected signature character is received; Only the data.
    """
    if modified_BTF is not None:
        send_mod_BTF(com, modified_BTF)
    send_command(com, cmd)

    while com.out_waiting > 7200:
        time.sleep(0.1)

    return read_next_message(com, expect=expect)

def send_command(com, cmd):
    """Constructs a message following the protocol with the given
    command string, and sends it to the device.

    Args:
        com - serial.Serial object.
        cmd - Desired command string. Its length should be less than
              or equal to CMD_RX_BUFFER_BYTES.

    Raises:
        ValueError - from check_range, when the length of cmd exceeds
                     CMD_RX_BUFFER_BYTES.
        serial.SerialException - when there is no connection.
    """
    length = len(cmd)
    util.range_check(length, CMD_RX_BUFFER_BYTES, 'CMD length')

    header = f'!{length:x}'
    body = cmd.replace('\x10', '\x10\x10')
    send_message(com, header, body)

def send_mod_BTF(com, modified_BTF):
    """Constructs a modified BTF format message following the protocol
    with the given data, and sends it to the device.

    Args:
        modified_BTF: str or list(int)
            - A modified BTF format packet in str or list of int.
              When it is list, each element is one byte.

    Raises:
        ValueError - from check_range, when the length of modified_BTF
                     exceeds BTF_RX_BUFFER_BYTES.
        serial.SerialException - when there is no connection.
    """
    length = len(modified_BTF)
    util.range_check(length, BTF_RX_BUFFER_BYTES, 'Modified BTF length')

    byte_count_string = f'{length:x}'
    num_digits = len(byte_count_string)
    header = f'#{num_digits:x}{byte_count_string}'

    if not isinstance(modified_BTF, str):
        # convert list(int) into str
        modified_BTF = util.encode_list(modified_BTF)

    body = modified_BTF.replace('\x10', '\x10\x10')
    send_message(com, header, body)

def send_message(com, header: str, body: str):
    """Concatenates the given header and body, and appends the
    terminator at the end. The constructed message is then encoded
    into bytes by encoding='latin-1', and is sent via serial port.
    """
    message = ''.join([header, body, TERMINATOR_STRING])
    com.write(message.encode('latin-1'))

def read_next_message(com, expect=None):
    """Reads the next message following the protocol.

    The signature character of message is either '!' or '#'.

    When an escape sequence is detected, this method checks the escape
    character and when it is 'R', it reads additional 5 bytes and store it
    in the exception object's escape_R_data attribute. Then raises the
    exception again, propagating the exception.

    Args:
        expect: str - The expected message type, i.e., the expected
                      signature character. If the received message type
                      is not the expected one, a RuntimeError occurs.
                      If it is None, the received signature character is
                      returned with the data.
    
    Raises:
        RuntimeError - check_terminator() may raise it.
                     | if expect is not None, signature character mismatch.
                     | no message is read.
                     | unknown signature character. 
        EscapeSequenceException - when an escape sequence is detected.

    Returns:
        (str, str) - When expect is None;
                     A 2-tuple of signature character and data.
                     The signature character '0' means that there is no
                     message to read, and 'E' means that an unknown
                     signature character is received.
        str - When the expected signature character is received, returns
              only the data.
    """
    try:
        sig_char = read_next(com)
        data = ''

        if sig_char == '!':
            # CMD
            len_data = int(read_next(com), 16)
            data = read_next(com, len_data)
            check_terminator(com)

        elif sig_char == '#':
            # Modified BTF
            num_digits = int(read_next(com), 16)
            byte_count = int(read_next(com, num_digits), 16)
            data = read_next(com, byte_count)
            check_terminator(com)

    except EscapeSequenceException as e:
        if e.escape_char == 'R':
            data = [ord(read_next(com)) for _ in range(5)]
            check_terminator(com)
            e.escape_R_data = data

        raise e

    if expect is not None:
        if expect != sig_char:
            raise RuntimeError(f'Expected signature character is {expect} '
                               f'but {sig_char} is received.')
        return data

    elif sig_char == '!' or sig_char == '#':
        return (sig_char, data)

    elif sig_char == '':
        raise RuntimeError('No message to read.')

    else:
        raise RuntimeError(f'Unknown signature character: {sig_char}.')

def read_next(com, size=1):
    """Reads several bytes from the seiral port,
    repeatedly calling read_next_char().

    Args:
        size - desired number of bytes to read.

    Raises:
        EscapeSequenceException
            - might be raised by read_next_char().

    Returns:
        str - A received string. The length of the string might be less
              than the given size argument, when timeout occurs.
    """
    return ''.join((read_next_char(com) for _ in range(size)))

def read_next_char(com):
    """Reads one byte from the serial port, and converts it to a character.

    If '\x10' is detected, it reads another byte and if it is '\x10' again,
    just return '\x10'. Otherwise, it raises an exception.

    Note that the timeout is set to 1, hence if there is no incoming byte
    for more than 1sec, then this might return an empty byte.

    Raises:
        EscapeSequenceException
            - when an escape sequence is read that is not '\x10\x10'.

    Returns:
        str - Received character.
    """
    first_char = com.read(1).decode('latin-1')
    if first_char == '\x10':
        second_char = com.read(1).decode('latin-1')
        if second_char == '\x10':
            return '\x10'
        else:
            raise EscapeSequenceException(second_char)
    else:
        return first_char

def check_terminator(com):
    """Checks whether the following string is the terminator string.

    Raises:
        RuntimeError - when the received terminator does not match.
    """
    terminator = read_next(com, len(TERMINATOR_STRING))
    if terminator != TERMINATOR_STRING:
        raise RuntimeError(
            f'Terminator string does not match. '\
            f'Expected: {TERMINATOR_STRING}, received: {terminator}.'
        )

def escape(com, escape_char):
    """Sends an escape sequence with the given escape character to the device.

    The device will send back with the proper response.
        
    Raises:
        RuntimeError - when the expected response is not received.
    
    Returns when escape_char == 'C':
        None
    Returns when escape_char == 'R':
        (str, list(str)) - status bits and data which is a list of four
                           8-digit bit-strings.
    """
    if isinstance(escape_char, str):
        escape_byte = escape_char.encode('latin-1')

    com.write(b'\x10' + escape_byte)
    try:
        res = read_next_message(com)

    except EscapeSequenceException as e:
        if e.escape_char == escape_char:
            if escape_char == 'R':
                data = [f'{byte:08b}' for byte in e.escape_R_data]
                return (data[4], data[:4])

            # TODO: 'T', 'A', 'W'.

            return None # OK
        else:
            res = repr(e)

    except RuntimeError as e:
        res = repr(e)

    raise RuntimeError(f'Unexpected response: {res}')


class BasicProtocol:
    """This class implements the basic commands in BasicProtocol.

    BasicProtocol device has 'bit pattern' of PATTERN_BYTES bytes,
    and we can read and/or update the bit pattern. Be aware of the indices,
    since it is started from 1, not 0, and the lower index indicates
    that the bit is more significant.
    
    Attributes
    - com: serial.Serial    # for serial port communication
    - PATTERN_BYTES: int    # bit pattern size
    - PATTERN_BITS: int     # PATTERN_BYTES * 8

    Public methods
    - adjust_intensity: int => ()
    - read_intensity: [,bool] => int
    - read_DNA: () => str

    Protected 'macro' methods - these are for convenience.
    - _send_command: str => ()
    - _send_mod_BTF: list(int) or str => ()
    - _read_next_message: () => (str, str)
    """

    def __init__(self, port_or_com=None, pattern_bytes=4):
        """Initialize the serial.Serial object.

        Args:
            port_or_com: str or serial.Serial
                - Set self.com object by the given serial port name or Serial
                  object itself. When it is None, a new Serial object is
                  created with its port=None.
                  When the given port is already open, it will raise an
                  exception.
            pattern_bytes: int
                - The bit pattern size which can be read by read_bit_pattern()
                  and updated by update_bit_pattern().
        """
        if isinstance(port_or_com, serial.Serial):
            self.com = port_or_com
        else:
            self.com = new_serial(port_or_com)

        # Read/Update bit pattern
        self.PATTERN_BYTES = pattern_bytes
        self.PATTERN_BITS = pattern_bytes * 8

    def read_IDN(self):
        """Reads the identification string of the device.
        Usually it will returns the name of the device and its version.
        E.g., 'Protocol v1_02'.

        Note that this is not enough to identify which board is this,
        since different boards with the same bitstream will return the
        same identification string.

        To identify each board, read_DNA() would be helpful.
        
        Returns:
            str - Received identification string.
        """
        return self._query('*IDN?', expect='!')

    def read_DNA(self):
        """Reads the DNA port.

        The device DNA is a 57-bit number, hence it is represented in
        a 15-digit hexadecimal format.

        Returns:
            str - received device DNA in a hexadecimal representation.
            None - when the device DNA is not ready yet.
        """
        dna = self._query('*DNA_PORT?', expect='!')
        
        dna_hex_str = ''.join(f'{ord(char):02X}' for char in dna)

        # the first 4 bits represent whether DNA_PORT reading is done.
        if dna_hex_str[0] == '1':
            return dna_hex_str[1:]
        else:
            return None

    def test(self):
        """Test command which does nothing.

        This is for checking that the '\x10\x10' is working properly.
        """
        self._send_command('\x10TEST\x10')

    def adjust_intensity(self, value: int):
        """Adjusts the LED intensity.

        Args:
            value - unsigned one byte integer (0-255).

        Raises:
            ValueError - when value is invalid.
        """
        util.range_check(value, 255, 'Intensity value')

        self._send_mod_BTF([value])
        self._send_command('ADJ INTENSITY')

    def read_intensity(self, verbose=True):
        """Reads the LED intensity.

        Args:
            verbose - if True, it prints out the intensity.

        Returns:
            int - received LED intensity value.
        """
        data = self._query('READ INTENSITY', expect='!')

        intensity = ord(data)
        if verbose:
            print(f'read_intensity: Current intensity is {intensity}')

        return intensity

    def capture_BTF_buffer(self):
        """Captures the snapshot of BTF buffer of the device."""
        self._send_command('CAPTURE BTF')

    def set_BTF_buffer_read_count(self, n: int):
        """Sets the number of bytes to read from the captured BTF buffer."""
        util.range_check(n, BTF_RX_BUFFER_BYTES, 'BTF buffer read count')
        self._send_mod_BTF(util.encode_int(n, 2))
        self._send_command('BTF READ COUNT')

    def read_BTF_buffer(self):
        """Reads the captured BTF buffer.
        The number of bytes to be read is set by set_BTF_buffer_read_count().
        To capture BTF buffer, capture_BTF_buffer() should be called
        in advance.

        Returns:
            str - Captured BTF buffer snapshot. This will be encoded in
                  unicode, hence decode_to_int() or decode_to_list() might
                  be helpful.
        """
        return self._query('READ BTF', expect='#')

    def update_bit_pattern(self, index_value_pairs):
        """Updates the bit pattern.

        Note that the indexing order is reversed and counting from 1, not 0.
        Which means that index i will be translated to 2**(max_index-i).

        Args:
            index_value_pairs: list((int, int)) -
                A list of tuples which indicate the specific bit index and
                the desired value(1 or 0). Only the bits that are indicated
                in this list will be updated, while the others stay the same.
        """
        max_index = self.PATTERN_BITS
        mask_pattern = 0
        bit_pattern = 0
        for index, value in index_value_pairs:
            powered = 1 << (max_index - index)
            mask_pattern |= powered
            bit_pattern |= value * powered

        mask_list = util.to_byte_list(mask_pattern, self.PATTERN_BYTES)
        bit_list = util.to_byte_list(bit_pattern, self.PATTERN_BYTES)

        self._send_mod_BTF(mask_list + bit_list)
        self._send_command('UPDATE BITS')

    def read_bit_pattern(self, index=None):
        """Reads the current bit pattern.

        When index is an integer, return the bit value.
        When index is a list, return a dictionary whose keys are indices.
        When index is None, returns a list which contains the whole bits.

        Args:
            index: int or list(int) - The index/indices of target bit(s).

        Returns:
            int or dict(int: int) or list(int)
        """
        pattern = self._query('READ BITS', expect='!')

        bit_list = [None]   # placeholder for index 0
        for byte in util.decode_to_list(pattern):
            bit_list.extend(util.to_bit_list(byte))

        if index is None:
            return bit_list

        elif isinstance(index, int):
            return bit_list[index]

        else:
            return {i: bit_list[i] for i in index}

    def _query(self, cmd, modified_BTF=None, expect=None):
        """Macro for query to self.com."""
        return query(self.com, cmd, modified_BTF, expect)

    def _send_command(self, cmd):
        """Macro for send_command to self.com."""
        send_command(self.com, cmd)

    def _send_mod_BTF(self, modified_BTF):
        """Macro for send_mod_BTF to self.com."""
        send_mod_BTF(self.com, modified_BTF)

    def _read_next_message(self, expect=None):
        """Macro for read_next_message from self.com."""
        return read_next_message(self.com, expect=expect)

    def _escape(self, escape_char):
        """Macro for escape from self.com."""
        return escape(self.com, escape_char)
