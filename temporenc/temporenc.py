
import struct

SUPPORTED_TYPES = set([
    'D',
    'T',
    'DT',
    'DTZ',
    'DTS',
    'DTSZ',
])

STRUCT_32 = struct.Struct('>L')


def packb(type=None, year=None, month=None, day=None):
    """
    Pack date and time information into a byte string.

    :return: encoded temporenc value
    :rtype: bytes
    """

    # Input validation
    if type not in SUPPORTED_TYPES:
        raise ValueError("invalid temporenc type: {0!r}".format(type))

    if year is None:
        year = 4095
    elif not 0 <= year <= 4094:
        raise ValueError("'year' not in supported range")

    if month is None:
        month = 15
    elif not 1 <= month <= 12:
        raise ValueError("'month' not in supported range")

    if day is None:
        day = 31
    elif not 1 <= day <= 31:
        raise ValueError("'day' not in supported range")

    # Component packing
    if 'D' in type:
        d = (year << 9) | (month - 1 << 5) | (day - 1)

    # Byte packing
    if type == 'D':
        # Format: 100DDDDD DDDDDDDD DDDDDDDD
        return STRUCT_32.pack(0b100 << 21 | d)[1:]

    raise NotImplementedError()
