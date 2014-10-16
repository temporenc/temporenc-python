
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
# Byte packing helpers
#

pack_4 = struct.Struct('>L').pack
pack_8 = struct.Struct('>Q').pack
pack_2_8 = struct.Struct('>HQ').pack


#
# Components and types
#
# Composite components like date and time are split to make the
# implementation simpler. Each component is a tuple with these
# components:
#
#   (name, size, mask, min_value, max_value, empty)
#

YEAR_MIN, YEAR_MAX, YEAR_EMPTY, YEAR_MASK = 0, 4094, 4095, 0xfff
MONTH_MIN, MONTH_MAX, MONTH_EMPTY, MONTH_MASK = 0, 11, 15, 0xf
DAY_MIN, DAY_MAX, DAY_EMPTY, DAY_MASK = 0, 30, 31, 0x1f
HOUR_MIN, HOUR_MAX, HOUR_EMPTY, HOUR_MASK = 0, 23, 31, 0x1f
MINUTE_MIN, MINUTE_MAX, MINUTE_EMPTY, MINUTE_MASK = 0, 59, 63, 0x3f
SECOND_MIN, SECOND_MAX, SECOND_EMPTY, SECOND_MASK = 0, 60, 63, 0x3f
MILLISECOND_MIN, MILLISECOND_MAX, MILLISECOND_MASK = 0, 999, 0x3ff
MICROSECOND_MIN, MICROSECOND_MAX, MICROSECOND_MASK = 0, 999999, 0xfffff
NANOSECOND_MIN, NANOSECOND_MAX, NANOSECOND_MASK = 0, 999999999, 0x3fffffff

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

    #
    # Type detection
    #

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

    #
    # Value checking
    #

    if year is None:
        year = YEAR_EMPTY
    elif not YEAR_MIN <= year <= YEAR_MAX:
        raise ValueError("'year' not within supported range")

    if month is None:
        month = MONTH_EMPTY
    else:
        month -= 1
        if not MONTH_MIN <= month <= MONTH_MAX:
            raise ValueError("'month' not within supported range")

    if day is None:
        day = DAY_EMPTY
    else:
        day -= 1
        if not DAY_MIN <= day <= DAY_MAX:
            raise ValueError("'day' not within supported range")

    if hour is None:
        hour = HOUR_EMPTY
    elif not HOUR_MIN <= hour <= HOUR_MAX:
        raise ValueError("'hour' not within supported range")

    if minute is None:
        minute = MINUTE_EMPTY
    elif not MINUTE_MIN <= minute <= MINUTE_MAX:
        raise ValueError("'minute' not within supported range")

    if second is None:
        second = SECOND_EMPTY
    elif not SECOND_MIN <= second <= SECOND_MAX:
        raise ValueError("'second' not within supported range")

    if (millisecond is not None
            and not MILLISECOND_MIN <= millisecond <= MILLISECOND_MAX):
        raise ValueError("'millisecond' not within supported range")

    if (microsecond is not None
            and not MICROSECOND_MIN <= microsecond <= MICROSECOND_MAX):
        raise ValueError("'microsecond' not within supported range")

    if (nanosecond is not None
            and not NANOSECOND_MIN <= nanosecond <= NANOSECOND_MAX):
        raise ValueError("'nanosecond' not within supported range")

    #
    # Byte packing
    #

    d = year << 9 | month << 5 | day
    t = hour << 12 | minute << 6 | second

    if type == 'D':
        # 100DDDDD DDDDDDDD DDDDDDDD
        return pack_4(0x800000 | d)[-3:]

    elif type == 'T':
        # 1010000T TTTTTTTT TTTTTTTT
        return pack_4(0xa00000 | t)[-3:]

    elif type == 'DT':
        # 00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
        # TTTTTTTT
        return pack_8(d << 17 | t)[-5:]

    elif type == 'DTS':
        if nanosecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS
            return pack_2_8(
                0b0110 << 4 | d >> 17,
                (d & 0x1ffff) << 47 | t << 30 | nanosecond)[-9:]
        elif microsecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00
            return pack_8(
                0b0101 << 60 | d << 39 | t << 22 | microsecond << 2)
        elif millisecond is not None:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSS0000
            return pack_8(
                0b0100 << 52 | d << 31 | t << 14 | millisecond << 4)[-7:]
        else:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TT000000
            return pack_8(0b0111 << 44 | d << 23 | t << 6)[-6:]

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
