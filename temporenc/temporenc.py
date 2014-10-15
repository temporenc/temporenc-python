
import collections
import struct
import sys


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# Compatibility hack:
# struct.unpack() does not handle bytearray() in Python < 2.7
if sys.version_info[:2] <= (2, 6):
    def unpack(fmt, value):
        return struct.unpack(fmt, buffer(value))
else:
    unpack = struct.unpack


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

# Components descriptions; composite components like date and time are
# split to make the implementation simpler. Each component is a tuple
# with these components:
#   (name, size, mask, min-value, max-value, empty-value)
COMPONENT_YEAR = ('year', 12, 0b111111111111, 0, 4094, 4095)
COMPONENT_MONTH = ('month', 4, 0b1111, 0, 11, 15)
COMPONENT_DAY = ('day', 5, 0b11111, 0, 30, 31)
COMPONENT_HOUR = ('hour', 5, 0b11111, 0, 23, 31)
COMPONENT_MINUTE = ('minute', 6, 0b111111, 0, 59, 63)
COMPONENT_SECOND = ('second', 6, 0b111111, 0, 60, 63)

# Type descriptions
TYPES = {
    'D': (
        COMPONENT_YEAR,
        COMPONENT_MONTH,
        COMPONENT_DAY),
    'T': (
        COMPONENT_HOUR,
        COMPONENT_MINUTE,
        COMPONENT_SECOND),
    'DT': (
        COMPONENT_YEAR,
        COMPONENT_MONTH,
        COMPONENT_DAY,
        COMPONENT_HOUR,
        COMPONENT_MINUTE,
        COMPONENT_SECOND),
}

# Magic values indicating empty parts
YEAR_EMPTY = 4095
MONTH_EMPTY = 15
DAY_EMPTY = 31
HOUR_EMPTY = 31
MINUTE_EMPTY = 63
SECOND_EMPTY = 63


Value = collections.namedtuple('Value', [
    'year', 'month', 'day', 'hour', 'minute', 'second'])


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


def unpackb(value):
    if not 3 <= len(value) <= 10:
        raise ValueError("value must be between 3 and 10 bytes")

    # Individual bytes should be integers.
    if PY2:
        value = bytearray(value)

    # Detect the type and convert the value into a number
    first = value[0]

    if first <= 0b00111111:  # tag 00
        type = TYPES['DT']
        value = value.rjust(8, b'\x00')
        (n,) = unpack('>Q', value.rjust(8, b'\x00'))

    elif first <= 0b01111111:  # tag 01
        raise NotImplementedError("DTS")

    elif first <= 0b10011111:  # tag 100
        type = TYPES['D']
        (n,) = unpack('>L', bytes(value.rjust(4, b'\x00')))

    elif first <= 0b10100001:  # tag 1010000
        type = TYPES['T']
        (n,) = unpack('>L', bytes(value.rjust(4, b'\x00')))

    elif first <= 0b10111111:
        raise ValueError("first byte does not contain a valid tag")

    elif first <= 0b11011111:  # tag 110
        raise NotImplementedError("DTZ")

    elif first <= 0b11111111:  # tag 111
        raise NotImplementedError("DTSZ")

    # Iteratively shift off components from the numerical value
    kwargs = dict.fromkeys(Value._fields)
    for name, size, mask, min_value, max_value, empty_value in reversed(type):
        decoded = n & mask
        if decoded == empty_value:
            continue

        if not min_value <= decoded <= max_value:
            raise ValueError(
                "{0} {1:d} not in range [{2:d}, {3:d}]".format(
                    name, decoded, min_value, max_value))
        kwargs[name] = decoded
        n >>= size

    # Both month and day are stored off-by-one.
    if kwargs.get('month') is not None:
        kwargs['month'] += 1
    if kwargs.get('day') is not None:
        kwargs['day'] += 1

    return Value(**kwargs)
