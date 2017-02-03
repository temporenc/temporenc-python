
import types

# TODO: time only
# TODO: date+time
# TODO: utc offseb
# TODO: subsecond precision


def decode(b, pos=0):
    assert len(b) - pos >= 3

    v = types.SimpleNamespace()  # todo: proper container

    # longest possible compact format:
    # eyyyyyyy yyyymmmm dddddhhh hhmmmmmm sssssspz
    # pppppppp pppppppp pppppppp pppppppp zzzzzzzz

    # byte 0: e------- (compact/extended flag)
    if b[pos+0] >> 7:
        raise NotImplementedError("extended format")

    v.year = b[pos+0] << 4 | b[pos+1] >> 4
    if v.year >> 7 == 0b1111:
        # time only, byte 0: -1111---
        v.year = v.month = v.day = None
        pos -= 2  # skip two bytes, otherwise same
    else:
        # date and time, bytes 0-2: .yyyyyyy yyyymmmm ddddd...
        if v.year == 0b11101111111:
            v.year = None
        else:
            v.year = v.year + 1000
        v.month = b[pos+1] & 0b1111
        v.day = b[pos+2] >> 3 & 0b11111
        if v.month == 0b1111:
            v.month = None
        elif v.month <= 11:
            v.month = v.month + 1
        else:
            raise ValueError("month out of range: {}".format(v.month))
        if v.day == 0b11111:
            v.day = None
        elif v.day <= 30:
            v.day = v.day + 1
        else:
            raise ValueError("day out of range: {}".format(v.day))

    # date only, byte 2: -----111
    # fixme: this gets confused when also detected as time only format
    v.hour = b[pos+2] & 0b111
    if v.hour == 0b111:
        v.hour = None
        pos -= 7
        return v, pos + 10

    # bytes 2-4: -----hhh hhmmmmmm ssssss--
    v.hour = v.hour << 2 | b[pos+3] >> 6
    v.minute = b[pos+3] & 0b111111
    v.second = b[pos+4] >> 2
    if v.hour == 0b11011:  # not 0b11111; see date-only format
        v.hour = None
    elif v.hour > 23:
        raise ValueError("hour out of range: {}".format(v.hour))
    if v.minute == 0b111111:
        v.minute = None
    elif v.minute > 59:
        raise ValueError("minute out of range: {}".format(v.minute))
    if v.second == 0b111111:
        v.second = None
    elif v.second > 60:  # allow leap second
        raise ValueError("second out of range: {}".format(v.second))

    # byte 4: ------so (subsecond and tzoffset flags)
    has_ms = b[pos+4] & 0b10
    has_tzoffset = b[pos+4] & 0b01

    # byte 5-8: mmmmmmmm mmcuuuuu uuuuucnn nnnnnnnn (subsecond precision)
    has_us = has_ns = False
    v.ms = v.us = v.ns = None
    if has_ms:
        v.ms = b[pos+5] << 2 | b[pos+6] >> 6
        v.us = b[pos+6] & 0b11111
        if v.ms == 0b1111111111:
            v.ms = None
        elif v.ms >= 1000:
            raise ValueError("milliseconds out of range: {}".format(v.ms))
        elif v.second is None:
            raise ValueError("non-empty millisecond but empty second")
        has_us = b[pos+6] & 0b100000
    else:
        pos -= 4
    if has_us:
        v.us = v.us << 5 | b[pos+7] >> 3
        v.ns = b[pos+7] & 0b11
        if v.us == 0b1111111111:
            v.us = None
        elif v.us >= 1000:
            raise ValueError("microseconds out of range: {}".format(v.us))
        elif v.ms is None:
            raise ValueError("non-empty microseconds but empty milliseconds")
        has_ns = b[pos+7] & 0b100
    elif v.us:
        raise ValueError("nonzero padding after milliseconds")
    elif has_ms:
        pos -= 2
    if has_ns:
        v.ns = v.ns << 8 | b[pos+8]
        if v.ns == 0b1111111111:
            v.ns = None
        elif v.ns >= 1000:
            raise ValueError("nanoseconds out of range: {}".format(v.ns))
        elif v.us is None:
            raise ValueError("non-empty nanoseconds but empty microseconds")
    elif v.ns:
        raise ValueError("nonzero padding after microseconds")
    elif has_us:
        pos -= 1

    if v.second is not None:
        if v.ms is None:
            v.ms = 0
        if v.us is None:
            v.us = 0
        if v.ns is None:
            v.ns = 0
        v.us = v.ms * 1000 + v.us
        v.ns = v.us * 1000 + v.ns

    # byte 9: 0zzzzzzz
    if has_tzoffset:
        tzoffset = b[pos+9]
        if tzoffset >> 7:
            raise ValueError('highest tzoffset bit must be 0')
        if tzoffset == 0b1111111:
            v.tzoffset = None
        else:
            v.tzoffset = 15 * (tzoffset - 64)
    else:
        pos -= 1

    return v, pos + 10


def debug_print(*numbers):
    print(decode(bytes(numbers)))


# date only
debug_print(
    0b00000000, 0b00000000, 0b00000111)
debug_print(
    0b00000000, 0b00001011, 0b00000111)
debug_print(
    0b00111111, 0b10010011, 0b00010111)

# datetime
debug_print(
    0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101100)

# time only
debug_print(0b01111101, 0b11111011, 0b11101100)

# time only + tzoffset
debug_print(0b01111101, 0b11111011, 0b11101101, 0b01001000)

# datetime with milliseconds and tzoffset
debug_print(
    0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
    0b00011110, 0b11000000, 0b01001000)

# datetime with microseconds and tzoffset
debug_print(
    0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
    0b00011110, 0b11101110, 0b01000000, 0b01001000)

# datetime with nanoseconds and tzoffset
debug_print(
    0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
    0b00011110, 0b11101110, 0b01000111, 0b00010101, 0b01001000)

# datetime with all fields present but empty
debug_print(
    0b01110111, 0b11111111, 0b11111110, 0b11111111, 0b11111111,
    0b11111111, 0b11111111, 0b11111111, 0b11111111, 0b01111111)

# lots of ones fixme broken
debug_print(
    0b01111111, 0b11111111, 0b11111111, 0b11111111, 0b11111111,
    0b11111111, 0b11111111, 0b11111111, 0b11111111, 0b01111111)
