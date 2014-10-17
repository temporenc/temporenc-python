
import struct
import sys


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

#
# Byte packing helpers
#

pack_4 = struct.Struct('>L').pack
pack_8 = struct.Struct('>Q').pack
pack_2_8 = struct.Struct('>HQ').pack


def unpack_4(value, _unpack=struct.Struct('>L').unpack):
    return _unpack(value.rjust(4, b'\x00'))[0]


def unpack_8(value, _unpack=struct.Struct('>Q').unpack):
    return _unpack(value.rjust(8, b'\x00'))[0]


#
# Components and types
#
# Composite components like date and time are split to make the
# implementation simpler. Each component is a tuple with these
# components:
#
#   (name, size, mask, min_value, max_value, empty)
#

SUPPORTED_TYPES = set(['D', 'T', 'DT', 'DTZ', 'DTS', 'DTSZ'])

D_MASK = 0x1fffff
T_MASK = 0x1ffff
Z_MASK = 0x7f

YEAR_MIN, YEAR_MAX, YEAR_EMPTY, YEAR_MASK = 0, 4094, 4095, 0xfff
MONTH_MIN, MONTH_MAX, MONTH_EMPTY, MONTH_MASK = 0, 11, 15, 0xf
DAY_MIN, DAY_MAX, DAY_EMPTY, DAY_MASK = 0, 30, 31, 0x1f
HOUR_MIN, HOUR_MAX, HOUR_EMPTY, HOUR_MASK = 0, 23, 31, 0x1f
MINUTE_MIN, MINUTE_MAX, MINUTE_EMPTY, MINUTE_MASK = 0, 59, 63, 0x3f
SECOND_MIN, SECOND_MAX, SECOND_EMPTY, SECOND_MASK = 0, 60, 63, 0x3f
MILLISECOND_MIN, MILLISECOND_MAX, MILLISECOND_MASK = 0, 999, 0x3ff
MICROSECOND_MIN, MICROSECOND_MAX, MICROSECOND_MASK = 0, 999999, 0xfffff
NANOSECOND_MIN, NANOSECOND_MAX, NANOSECOND_MASK = 0, 999999999, 0x3fffffff
TIMEZONE_MIN, TIMEZONE_MAX, TIMEZONE_EMPTY, TIMEZONE_MASK = 0, 126, 127, Z_MASK

D_LENGTH = 3
T_LENGTH = 3
DT_LENGTH = 5
DTZ_LENGTH = 6
DTS_LENGTHS = [7, 8, 9, 6]    # indexed by precision bits
DTSZ_LENGTHS = [8, 9, 10, 7]  # idem


#
# Public API
#

class Value(object):
    """
    Container for representing parsed temporenc value.

    Instances of this class represent a parsed temporenc value.

    This class must not be instantiated directly; use one of the
    unpacking functions like ``unpackb()`` instead. The only reason this
    class is part of the public API is to enable applications code like
    ``isinstance(x, temporenc.Value)``.
    """
    __slots__ = [
        'year', 'month', 'day',
        'hour', 'minute', 'second',
        'millisecond', 'microsecond', 'nanosecond',
        'tz_hour', 'tz_minute', 'tz_offset']

    def __init__(self, year, month, day, hour, minute, second, millisecond,
                 microsecond, nanosecond, tz_hour, tz_minute, tz_offset):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.millisecond = millisecond
        self.microsecond = microsecond
        self.nanosecond = nanosecond
        self.tz_hour = tz_hour
        self.tz_minute = tz_minute
        self.tz_offset = tz_offset


def packb(
        type=None,
        year=None, month=None, day=None,
        hour=None, minute=None, second=None,
        millisecond=None, microsecond=None, nanosecond=None,
        tz_offset=None):
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
        has_z = tz_offset is not None

        if has_z and has_s:
            type = 'DTSZ'
        elif has_z:
            type = 'DTZ'
        elif has_s:
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

    if tz_offset is None:
        tz_offset = TIMEZONE_EMPTY
    else:
        z, remainder = divmod(tz_offset, 15)
        if remainder:
            raise ValueError("'tz_offset' must be a multiple of 15")
        z += 64
        if not TIMEZONE_MIN <= z <= TIMEZONE_MAX:
            raise ValueError("'tz_offset' not within supported range")

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

    elif type == 'DTZ':
        # 110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
        # TTTTTTTT TZZZZZZZ
        return pack_8(0b110 << 45 | d << 24 | t << 7 | z)[-6:]

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

    elif type == 'DTSZ':
        if nanosecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS SZZZZZZZ
            return pack_2_8(
                0b11110 << 11 | d >> 10,
                (d & 0x3ff) << 54 | t << 37 | nanosecond << 7 | z)
        elif microsecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
            # ZZZZZZ00
            return pack_2_8(
                0b11101 << 3 | d >> 18,
                (d & 0x3ffff) << 46 | t << 29 | microsecond << 9 | z << 2)[-9:]
        elif millisecond is not None:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000
            return pack_8(
                0b11100 << 59 | d << 38 | t << 21 | millisecond << 11 | z << 4)
        else:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTZZZZZ ZZ000000
            return pack_8(0b11111 << 51 | d << 30 | t << 13 | z << 6)[-7:]


def unpackb(value):
    if not 3 <= len(value) <= 10:
        raise ValueError("value must be between 3 and 10 bytes")

    #
    # Unpack components
    #

    first = value[0]
    if PY2:
        first = ord(first)

    d = t = z = millisecond = microsecond = nanosecond = None

    if first <= 0b00111111:
        # Type DT, tag 00

        if not len(value) == DT_LENGTH:
            raise ValueError(
                "DT value must be {0:d} bytes; got {1:d}".format(
                    DT_LENGTH, len(value)))

        # 00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
        # TTTTTTTT
        n = unpack_8(value)
        d = n >> 17 & D_MASK
        t = n & T_MASK

    elif first <= 0b01111111:
        # Type DTS, tag 01

        precision = first >> 4 & 0b11

        if not len(value) == DTS_LENGTHS[precision]:
            raise ValueError(
                "DTS value with precision {0:02b} must be {1:d} bytes; "
                "got {2:d}".format(
                    precision, DTS_LENGTHS[precision], len(value)))

        # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
        # TTTTTTTT TT...... (first 6 bytes)
        n = unpack_8(value[:6]) >> 6
        d = n >> 17 & D_MASK
        t = n & T_MASK

        # Extract S component from last 4 bytes
        n = unpack_4(value[-4:])
        if precision == 0b00:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSS0000
            millisecond = n >> 4 & MILLISECOND_MASK
        elif precision == 0b01:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00
            microsecond = n >> 2 & MICROSECOND_MASK
        elif precision == 0b10:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS
            nanosecond = n & NANOSECOND_MASK
        elif precision == 0b11:
            # 01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
            # TTTTTTTT TT000000
            pass

    elif first <= 0b10011111:
        # Type D, tag 100

        if not len(value) == D_LENGTH:
            raise ValueError(
                "D value must be {0:d} bytes; got {1:d}".format(
                    D_LENGTH, len(value)))

        # 100DDDDD DDDDDDDD DDDDDDDD
        d = unpack_4(value) & D_MASK

    elif first <= 0b10100001:
        # Type T, tag 1010000

        if not len(value) == T_LENGTH:
            raise ValueError(
                "T value must be {0:d} bytes; got {1:d}".format(
                    T_LENGTH, len(value)))

        # 1010000T TTTTTTTT TTTTTTTT
        t = unpack_4(value) & T_MASK

    elif first <= 0b10111111:
        raise ValueError("first byte does not contain a valid tag")

    elif first <= 0b11011111:
        # Type DTZ, tag 110

        if not len(value) == DTZ_LENGTH:
            raise ValueError(
                "DTZ value must be {0:d} bytes; got {1:d}".format(
                    DTZ_LENGTH, len(value)))

        # 110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
        # TTTTTTTT TZZZZZZZ
        n = unpack_8(value)
        d = n >> 24 & D_MASK
        t = n >> 7 & T_MASK
        z = n & Z_MASK

    elif first <= 0b11111111:
        # Type DTSZ, tag 111

        precision = first >> 3 & 0b11

        if not len(value) == DTSZ_LENGTHS[precision]:
            raise ValueError(
                "DTSZ value with precision {0:02b} must be {1:d} bytes; "
                "got {2:d}".format(
                    precision, DTSZ_LENGTHS[precision], len(value)))

        # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
        # TTTTTTTT TTT..... (first 6 bytes)
        n = unpack_8(value[:6]) >> 5
        d = n >> 17 & D_MASK
        t = n & T_MASK

        # Extract S and Z components from last 5 bytes
        n = unpack_8(value[-5:])
        if precision == 0b00:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000
            millisecond = n >> 11 & MILLISECOND_MASK
            z = n >> 4 & Z_MASK
        elif precision == 0b01:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
            # ZZZZZZ00
            microsecond = n >> 9 & MICROSECOND_MASK
            z = n >> 2 & Z_MASK
        elif precision == 0b10:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
            # SSSSSSSS SZZZZZZZ
            nanosecond = n >> 7 & NANOSECOND_MASK
            z = n & Z_MASK
        elif precision == 0b11:
            # 111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
            # TTTTTTTT TTTZZZZZ ZZ000000
            z = n >> 6 & Z_MASK

    #
    # Split D and T components
    #

    if d is None:
        year = month = day = None
    else:
        year = d >> 9 & YEAR_MASK
        if year == YEAR_EMPTY:
            year = None

        month = d >> 5 & MONTH_MASK
        month = None if month == MONTH_EMPTY else month + 1

        day = d & DAY_MASK
        day = None if day == DAY_EMPTY else day + 1

    if t is None:
        hour = minute = second = None
    else:
        hour = t >> 12 & HOUR_MASK
        if hour == HOUR_EMPTY:
            hour = None

        minute = t >> 6 & MINUTE_MASK
        if minute == MINUTE_EMPTY:
            minute = None

        second = t & SECOND_MASK
        if second == SECOND_EMPTY:
            second = None

    #
    # Normalize time zone offset
    #

    if z is None:
        tz_hour = tz_minute = tz_offset = None
    else:
        tz_offset = 15 * (z - 64)
        tz_hour, tz_minute = divmod(tz_offset, 60)

    #
    # Sub-second fields are either all None, or none are None.
    #

    if millisecond is not None:
        microsecond = millisecond * 1000
        nanosecond = microsecond * 1000
    elif microsecond is not None:
        millisecond = microsecond // 1000
        nanosecond = microsecond * 1000
    elif nanosecond is not None:
        microsecond = nanosecond // 1000
        millisecond = microsecond // 1000

    return Value(
        year, month, day,
        hour, minute, second,
        millisecond, microsecond, nanosecond,
        tz_hour, tz_minute, tz_offset,
    )
