#!/usr/bin/python

import types


def decode(b, offset=0):
    """
    Decode an encoded temporenc value.

    If `offset` is specified, decoding will start at that position.
    """
    # this code uses the longest possible compact format when
    # referencing individual bytes. this format looks like this:
    #
    #   eyyyyyyy yyyymmmm dddddhhh hhmmmmmm sssssspz  (bytes 0-4)
    #   pppppppp pppppppp pppppppp pppppppp zzzzzzzz  (bytes 5-9)
    #
    # if the input indicates that a component is not included, the
    # 'offset' variable will be adjusted accordingly so that the byte
    # numbering in the code always matches the above 10-byte format.

    assert len(b) - offset >= 3

    v = types.SimpleNamespace()  # todo: return proper container

    # byte 0: e------- (compact/extended flag)
    if b[offset+0] >> 7:
        raise NotImplementedError("extended format")

    # bytes 0-2: .yyyyyyy yyyymmmm dddddhhh (date and partial time)
    v.type = "DT"
    v.year = b[offset+0] << 4 | b[offset+1] >> 4
    v.hour = b[offset+2] & 0b111
    has_date = has_time = True
    if v.year >> 7 == 0b1111:
        # byte 0: -1111--- (special case for time only)
        has_date = False
        v.type = "T"
        v.year = v.month = v.day = None
        v.hour = b[offset+0] & 0b111
        offset -= 2
    elif v.hour == 0b111:
        # byte 2: -----111 (special case for date only)
        has_time = False
        v.type = "D"
        v.hour = v.minute = v.second = None
        offset -= 2

    if has_date:
        if v.year == 0b11101111111:
            v.year = None
        else:
            v.year = v.year + 1000
        v.month = b[offset+1] & 0b1111
        v.day = b[offset+2] >> 3 & 0b11111
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

    if has_time:
        # bytes 2-4: -----hhh hhmmmmmm ssssss-- (time)
        v.hour = v.hour << 2 | b[offset+3] >> 6
        v.minute = b[offset+3] & 0b111111
        v.second = b[offset+4] >> 2
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
    has_ms = has_tzoffset = False
    if has_time:
        has_ms = b[offset+4] & 0b10
        has_tzoffset = b[offset+4] & 0b01

    # byte 5-8: mmmmmmmm mmcuuuuu uuuuucnn nnnnnnnn (subsecond precision)
    has_us = has_ns = False
    v.ms = v.us = v.ns = None
    if has_ms:
        v.ms = b[offset+5] << 2 | b[offset+6] >> 6
        v.us = b[offset+6] & 0b11111
        if v.ms == 0b1111111111:
            v.ms = None
        elif v.ms >= 1000:
            raise ValueError("milliseconds out of range: {}".format(v.ms))
        elif v.second is None:
            raise ValueError("non-empty millisecond but empty second")
        has_us = b[offset+6] & 0b100000
    else:
        offset -= 4
    if has_us:
        v.us = v.us << 5 | b[offset+7] >> 3
        v.ns = b[offset+7] & 0b11
        if v.us == 0b1111111111:
            v.us = None
        elif v.us >= 1000:
            raise ValueError("microseconds out of range: {}".format(v.us))
        elif v.ms is None:
            raise ValueError("non-empty microseconds but empty milliseconds")
        has_ns = b[offset+7] & 0b100
    elif v.us:
        raise ValueError("nonzero padding after milliseconds")
    elif has_ms:
        offset -= 2
    if has_ns:
        v.ns = v.ns << 8 | b[offset+8]
        if v.ns == 0b1111111111:
            v.ns = None
        elif v.ns >= 1000:
            raise ValueError("nanoseconds out of range: {}".format(v.ns))
        elif v.us is None:
            raise ValueError("non-empty nanoseconds but empty microseconds")
    elif v.ns:
        raise ValueError("nonzero padding after microseconds")
    elif has_us:
        offset -= 1
    if v.second is not None:
        if v.ms is None:
            v.ms = 0
        if v.us is None:
            v.us = 0
        if v.ns is None:
            v.ns = 0
        v.us = v.ms * 1000 + v.us
        v.ns = v.us * 1000 + v.ns
    if has_ns:
        v.type += "9"
    elif has_us:
        v.type += "6"
    elif has_ms:
        v.type += "3"

    # byte 9: 0zzzzzzz
    if has_tzoffset:
        v.type += "+"
        tzoffset = b[offset+9]
        if tzoffset >> 7:
            raise ValueError('highest tzoffset bit must be 0')
        if tzoffset == 0b1111111:
            v.tzoffset = None
        else:
            v.tzoffset = 15 * (tzoffset - 64)
    else:
        offset -= 1

    return v, offset + 10


def decode_and_print(*numbers):
    decoded, n_consumed = decode(bytes(numbers))
    assert len(numbers) == n_consumed
    print(" ".join('{:08b}'.format(n) for n in numbers))
    print(decoded, n_consumed)
    print()


if __name__ == '__main__':

    # date only
    decode_and_print(
        0b00000000, 0b00000000, 0b00000111)
    decode_and_print(
        0b00000000, 0b00001011, 0b00000111)
    decode_and_print(
        0b00111111, 0b10010011, 0b00010111)

    # datetime
    decode_and_print(
        0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101100)

    # time only
    decode_and_print(0b01111101, 0b11111011, 0b11101100)

    # time only + tzoffset
    decode_and_print(0b01111101, 0b11111011, 0b11101101, 0b01001000)

    # datetime with milliseconds and tzoffset
    decode_and_print(
        0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
        0b00011110, 0b11000000,
        0b01001000)

    # datetime with microseconds and tzoffset
    decode_and_print(
        0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
        0b00011110, 0b11101110, 0b01000000,
        0b01001000)

    # datetime with nanoseconds and tzoffset
    decode_and_print(
        0b00000000, 0b00000000, 0b00000101, 0b11111011, 0b11101111,
        0b00011110, 0b11101110, 0b01000111, 0b00010101,
        0b01001000)

    # datetime with all fields present but empty
    decode_and_print(
        0b01110111, 0b11111111, 0b11111110, 0b11111111, 0b11111111,
        0b11111111, 0b11111111, 0b11111111, 0b11111111,
        0b01111111)

    # time only with all fields present but empty
    decode_and_print(
        0b01111110, 0b11111111, 0b11111100)

    # longer time only with all fields present but empty
    decode_and_print(
        0b01111110, 0b11111111, 0b11111111,
        0b11111111, 0b11111111, 0b11111111, 0b11111111,
        0b01111111)
