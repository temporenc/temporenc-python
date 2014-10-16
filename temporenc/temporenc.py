
import collections
import struct
import sys


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

#
# Compatibility helpers
#

if sys.version_info[:2] <= (2, 6):
    # struct.unpack() does not handle bytearray() in Python < 2.7
    def unpack(fmt, value):
        return struct.unpack(fmt, buffer(value))
else:
    unpack = struct.unpack

if PY2:
    def to_bytes(value, size):
        if size <= 8:
            return struct.pack('>Q', value)[-size:]

        if size <= 10:
            return struct.pack(
                '>HQ',
                (value >> 64) & 0xffff,
                value & 0xffffffffffffffff)[-size:]

        # Temporenc values are always 3-10 bytes.
        assert False, "value too large"

else:
    def to_bytes(value, size):
        return value.to_bytes(size, 'big')


#
# Components and types
#
# Composite components like date and time are split to make the
# implementation simpler. Each component is a tuple with these
# components:
#
#   (name, size, mask, min_value, max_value, empty)
#

COMPONENT_YEAR = ('year', 12, 0xfff, 0, 4094, 4095)
COMPONENT_MONTH = ('month', 4, 0xf, 0, 11, 15)
COMPONENT_DAY = ('day', 5, 0x1f, 0, 30, 31)
COMPONENT_HOUR = ('hour', 5, 0x1f, 0, 23, 31)
COMPONENT_MINUTE = ('minute', 6, 0x3f, 0, 59, 63)
COMPONENT_SECOND = ('second', 6, 0x3f, 0, 60, 63)
COMPONENT_MILLISECOND = ('millisecond', 10, 0x3ff, 0, 999, None)
COMPONENT_MICROSECOND = ('microsecond', 20, 0xfffff, 0, 999999, None)
COMPONENT_NANOSECOND = ('nanosecond', 30, 0x3fffffff, 0, 999999999, None)
COMPONENT_PADDING_2 = ('padding', 2, 0x2, 0, 0, None)
COMPONENT_PADDING_4 = ('padding', 4, 0x4, 0, 0, None)
COMPONENT_PADDING_6 = ('padding', 6, 0x6, 0, 0, None)

SUPPORTED_TYPES = set(['D', 'T', 'DT', 'DTZ', 'DTS', 'DTSZ'])

TYPE_D = (COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY)
TYPE_T = (COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND)
TYPE_DT = (
    COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY,
    COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND)
TYPE_DTZ = ()  # TODO
TYPE_DTS_MS = (
    COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY,
    COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND,
    COMPONENT_MILLISECOND, COMPONENT_PADDING_4)
TYPE_DTS_US = (
    COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY,
    COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND,
    COMPONENT_MICROSECOND, COMPONENT_PADDING_2)
TYPE_DTS_NS = (
    COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY,
    COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND,
    COMPONENT_NANOSECOND)
TYPE_DTS_NONE = (
    COMPONENT_YEAR, COMPONENT_MONTH, COMPONENT_DAY,
    COMPONENT_HOUR, COMPONENT_MINUTE, COMPONENT_SECOND,
    COMPONENT_PADDING_6)
TYPE_DTSZ = ()  # TODO,


Value = collections.namedtuple('Value', [
    'year', 'month', 'day', 'hour', 'minute', 'second'])


def packb(
        type=None,
        year=None, month=None, day=None,
        hour=None, minute=None, second=None,
        millisecond=None, microsecond=None, nanosecond=None):
    """
    Pack date and time information into a byte string.

    :return: encoded temporenc value
    :rtype: bytes
    """

    # Automatically detect the most compact type if no type was specified.
    if type is None:
        has_d = not (year is None and month is None and day is None)
        has_t = not (hour is None and minute is None and second is None)
        has_s = not (millisecond is None and microsecond is None
                     and nanosecond is None)

        if has_s:
            type = 'DTS'
        elif has_d and has_t:
            type = 'DT'
        elif has_d:
            type = 'D'
        elif has_t:
            type = 'T'
        else:
            # No information at all, just use the smallest type
            type = 'D'

    elif type not in SUPPORTED_TYPES:
        raise ValueError("invalid temporenc type: {0!r}".format(type))

    # Month and day are stored off-by-one.
    if month is not None:
        month -= 1
    if day is not None:
        day -= 1

    padding = 0
    kwargs = locals()  # ugly, but it works :)

    # Byte packing
    if type == 'D':
        typespec = TYPE_D
        n = 0b100
        bits_used = 3

    elif type == 'T':
        typespec = TYPE_T
        n = 0b1010000
        bits_used = 7

    elif type == 'DT':
        typespec = TYPE_DT
        n = 0b00
        bits_used = 2

    elif type == 'DTS':
        bits_used = 4  # combined type tag and precision tag
        if nanosecond is not None:
            n = 0b0110
            typespec = TYPE_DTS_NS
        elif microsecond is not None:
            n = 0b0101
            typespec = TYPE_DTS_US
        elif millisecond is not None:
            n = 0b0100
            typespec = TYPE_DTS_MS
        else:
            n = 0b0111
            typespec = TYPE_DTS_NONE

    else:
        raise NotImplementedError()

    # Pack the components
    for name, size, mask, min_value, max_value, empty in typespec:
        value = kwargs[name]

        if value is None:
            value = empty
        elif not min_value <= value <= max_value:
            raise ValueError(
                "{0} {1:d} not in range [{2:d}, {3:d}]".format(
                    name, value, min_value, max_value))

        bits_used += size
        n <<= size
        n |= value

    assert bits_used % 8 == 0  # FIXME remove once all types are implemented
    return to_bytes(n, bits_used // 8)


def unpackb(value):
    if not 3 <= len(value) <= 10:
        raise ValueError("value must be between 3 and 10 bytes")

    # Individual bytes should be integers.
    if PY2:
        value = bytearray(value)

    # Detect the type and convert the value into a number
    first = value[0]

    if first <= 0b00111111:  # tag 00
        typespec = TYPE_DT
        value = value.rjust(8, b'\x00')
        (n,) = unpack('>Q', value.rjust(8, b'\x00'))

    elif first <= 0b01111111:  # tag 01
        raise NotImplementedError("DTS")

    elif first <= 0b10011111:  # tag 100
        typespec = TYPE_D
        (n,) = unpack('>L', value.rjust(4, b'\x00'))

    elif first <= 0b10100001:  # tag 1010000
        typespec = TYPE_T
        (n,) = unpack('>L', value.rjust(4, b'\x00'))

    elif first <= 0b10111111:
        raise ValueError("first byte does not contain a valid tag")

    elif first <= 0b11011111:  # tag 110
        raise NotImplementedError("DTZ")

    elif first <= 0b11111111:  # tag 111
        raise NotImplementedError("DTSZ")

    # Iteratively shift off components from the numerical value
    kwargs = dict.fromkeys(Value._fields)
    for name, size, mask, min_value, max_value, empty in reversed(typespec):
        decoded = n & mask
        n >>= size

        if decoded == empty:
            continue

        if not min_value <= decoded <= max_value:
            raise ValueError(
                "{0} {1:d} not in range [{2:d}, {3:d}]".format(
                    name, decoded, min_value, max_value))

        kwargs[name] = decoded

    # Both month and day are stored off-by-one.
    if kwargs['month'] is not None:
        kwargs['month'] += 1
    if kwargs['day'] is not None:
        kwargs['day'] += 1

    return Value(**kwargs)
