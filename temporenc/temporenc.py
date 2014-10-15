
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
STRUCT_32_16 = struct.Struct('>LH')

# Magic values indicating empty parts
YEAR_EMPTY = 4095
MONTH_EMPTY = 15
DAY_EMPTY = 31
HOUR_EMPTY = 31
MINUTE_EMPTY = 63
SECOND_EMPTY = 63


def packb(
        type=None,
        year=None, month=None, day=None,
        hour=None, minute=None, second=None):
    """
    Pack date and time information into a byte string.

    :return: encoded temporenc value
    :rtype: bytes
    """

    # Input validation
    if type not in SUPPORTED_TYPES:
        raise ValueError("invalid temporenc type: {0!r}".format(type))

    if year is None:
        year = YEAR_EMPTY
    elif not 0 <= year <= 4094:
        raise ValueError("'year' not in supported range")

    if month is None:
        month = MONTH_EMPTY
    elif not 1 <= month <= 12:
        raise ValueError("'month' not in supported range")

    if day is None:
        day = DAY_EMPTY
    elif not 1 <= day <= 31:
        raise ValueError("'day' not in supported range")

    if hour is None:
        hour = HOUR_EMPTY
    elif not 0 <= hour <= 23:
        raise ValueError("'hour' not in supported range")

    if minute is None:
        minute = MINUTE_EMPTY
    elif not 0 <= minute <= 59:
        raise ValueError("'minute' not in supported range")

    if second is None:
        second = SECOND_EMPTY
    elif not 1 <= second <= 60:
        raise ValueError("'second' not in supported range")

    # Component packing
    if 'D' in type:
        d = (year << 9) | (month - 1 << 5) | (day - 1)
    if 'T' in type:
        t = (hour << 12) | (minute << 6) | (second)

    # Byte packing
    if type == 'D':
        # Format: 100DDDDD DDDDDDDD DDDDDDDD
        return STRUCT_32.pack(0b100 << 21 | d)[1:]
    elif type == 'T':
        # Format: 1010000T TTTTTTTT TTTTTTTT
        return STRUCT_32.pack(0b1010000 << 17 | t)[1:]
    elif type == 'DT':
        # Format: 00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT TTTTTTTT
        return STRUCT_32_16.pack(d << 1 | t >> 16, t & 0xffff)[1:]

    raise NotImplementedError()
