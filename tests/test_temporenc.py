import binascii

import temporenc


def from_hex(s):
    """Compatibility helper like bytes.fromhex() in Python 3"""
    return binascii.unhexlify(s.replace(' ', ''))


def test_type_d():

    actual = temporenc.packb(type='D', year=1983, month=1, day=15)
    expected = from_hex('8f 7e 0e')
    assert actual == expected

    v = temporenc.unpackb(expected)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (None, None, None)


def test_type_t():

    actual = temporenc.packb(type='T', hour=18, minute=25, second=12)
    expected = from_hex('a1 26 4c')
    assert actual == expected

    v = temporenc.unpackb(expected)
    assert (v.year, v.month, v.day) == (None, None, None)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)


def test_type_dt():

    actual = temporenc.packb(
        type='DT',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12)
    expected = from_hex('1e fc 1d 26 4c')
    assert actual == expected

    v = temporenc.unpackb(expected)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)


def test_type_dtz():

    # Note: hour is adjusted for UTC

    actual = temporenc.packb(
        type='DTZ',
        year=1983, month=1, day=15,
        hour=17, minute=25, second=12,
        tz_offset=60)
    expected = from_hex('cf 7e 0e 8b 26 44')
    assert actual == expected

    v = temporenc.unpackb(expected)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (17, 25, 12)
    assert (v.tz_hour, v.tz_minute, v.tz_offset) == (1, 0, 60)


def test_type_dts():

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, millisecond=123)
    dts_ms = from_hex('47 bf 07 49 93 07 b0')
    assert actual == dts_ms
    v = temporenc.unpackb(dts_ms)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)
    assert v.millisecond == 123
    assert v.microsecond == 123000
    assert v.nanosecond == 123000000

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, microsecond=123456)
    dts_us = from_hex('57 bf 07 49 93 07 89 00')
    assert actual == dts_us
    v = temporenc.unpackb(dts_us)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)
    assert v.millisecond == 123
    assert v.microsecond == 123456
    assert v.nanosecond == 123456000

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, nanosecond=123456789)
    dts_ns = from_hex('67 bf 07 49 93 07 5b cd 15')
    assert actual == dts_ns
    v = temporenc.unpackb(dts_ns)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)
    assert v.millisecond == 123
    assert v.microsecond == 123456
    assert v.nanosecond == 123456789

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12)
    dts_none = from_hex('77 bf 07 49 93 00')
    assert actual == dts_none
    v = temporenc.unpackb(dts_none)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (18, 25, 12)
    assert v.millisecond is None
    assert v.microsecond is None
    assert v.nanosecond is None


def test_type_detection():

    # Empty value, so should result in the smallest type
    assert len(temporenc.packb()) == 3

    # Type D
    assert len(temporenc.packb(year=1983)) == 3
    assert temporenc.unpackb(temporenc.packb(year=1983)).year == 1983

    # Type T
    assert len(temporenc.packb(hour=18)) == 3
    assert temporenc.unpackb(temporenc.packb(hour=18)).hour == 18

    # Type DT
    assert len(temporenc.packb(year=1983, hour=18)) == 5

    # Type DTS
    assert len(temporenc.packb(millisecond=0)) == 7
    assert len(temporenc.packb(microsecond=0)) == 8
    assert len(temporenc.packb(nanosecond=0)) == 9

    # Type DTZ
    assert len(temporenc.packb(year=1983, hour=18, tz_offset=120)) == 6
