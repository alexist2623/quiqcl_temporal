def range_check(value, upper_bound, name, lower_bound=0):
    """Checks whether the given value is in the valid range.
    
    Raises:
        ValueError - when value is not in [lower_bound, upper_bound].
    """
    if value > upper_bound or value < lower_bound:
        raise ValueError(f'{name} (={value}) is out of range: '
                         f'[{lower_bound}, {upper_bound}].')

def exact_check(value, expected, name):
    """Checks whether the given value is exactly the expected value.

    Raises:
        ValueError - when value != expected.
    """
    if value != expected:
        raise ValueError(f'Unexpected {name} (={value}); '
                         f'expected {expected}.')

def to_byte_list(value, byte):
    """Splits the given int value by 1-byte into a list of each byte.

    For example, 0x012345 is decomposed into [0x01, 0x23, 0x45] (byte=3).

    Args:
        value: int - Target value to be decomposed.
        byte: int - Total number of bytes, hence the length of the returned
                    list will be equal to byte argument.
                    When the given byte is not enough to represent the given
                    value, the higher bytes, i.e., more significant bytes,
                    are ignored.

    Returns:
        list(int) - A list of int, where each element is each byte(8-bit value)
                    of the given value.
    """
    byte_list = []
    for _ in range(byte):
        byte_list.append(value & 0xff)
        value >>= 8
    byte_list.reverse()

    return byte_list

def to_bit_list(value, bit=8):
    """Decomposes the given value into a bit-string, in fact an int list.

    For example, 5 is decomposed into [0, 0, 0, 0, 0, 1, 0, 1] (bit=8).

    Args:
        value: int - Target value to be decomposed.
        bit: int - Total number of bits, hence the length of the returned
                   list will be equal to 'bit' argument.
                   When the given 'bit' is not enough to represent the given
                   value, the higher bits, i.e., more significant bits,
                   are ignored.

    Returns:
        list(int) - A list of int, where each element is each bit of 'value'.
    """
    # "{:08b}".format(value) when bit=8.
    bit_string = (f"{{:0{bit}b}}").format(value)[-bit:]
    return list(map(int, bit_string))

def decode_to_int(unicode_string: str) -> int:
    """Decodes the given unicode string into an integer value.

    Each character is translated into a 8-bit integer and concatenated,
    hence a len(unicode_string)-byte integer is produced.

    Returns:
        int - Decoded integer value.
    """
    value = 0
    for byte in map(ord, unicode_string):
        value <<= 8
        value |= byte
    return value

def decode_to_list(unicode_string: str) -> list:
    """Decodes the given unicode string into an integer list.

    Each character is translated into a 8-bit integer, and those
    integers construct a list.

    Returns:
        list(int) - Decoded integer list, whose length is len(unicode_string).
    """
    return list(map(ord, unicode_string))

def encode_int(value: int, size: int) -> str:
    """Encodes the given integer value into a unicode string.

    This would be helpful when making a packet for modified BTF message
    with an integer value.

    Args:
        size - The length of the resulting string, which indicates
               the desired byte count.

    Returns:
        str - Encoded unicode string.
    """
    return encode_list(to_byte_list(value, size))

def encode_list(byte_list: list) -> str:
    """Similar to encode_int(), but for lists."""
    return ''.join(map(chr, byte_list))

def decode_packet(packet):
    """Decodes and decomposes the given 8-byte packet into a 4-tuple of int.

    Args:
        packet: str - The encoded 8-byte unicode string.

    Returns:
        tuple(int) - The decoded packet.
    """
    # decompose the packet into four 2-byte elements
    decomposed = (packet[i:i+2] for i in range(0, 8, 2))

    return tuple(map(decode_to_int, decomposed))
