import binascii

import temporenc


def from_hex(s):
    """Compatibility helper like bytes.fromhex() in Python 3"""
    return binascii.unhexlify(s.replace(' ', ''))


def test_type_d():

    actual = temporenc.packb(type='D', year=1983, month=1, day=15)
    expected = from_hex('8f 7e 0e')
    assert actual == expected

    parsed = temporenc.unpackb(expected)
    assert parsed.year == 1983
    assert parsed.month == 1
    assert parsed.day == 15
    assert parsed.hour is None


def test_type_t():
    actual = temporenc.packb(type='T', hour=18, minute=25, second=12)
    expected = from_hex('a1 26 4c')
    assert actual == expected

    parsed = temporenc.unpackb(expected)
    assert parsed.hour == 18
    assert parsed.minute == 25
    assert parsed.second == 12
    assert parsed.year is None


def test_type_dt():

    actual = temporenc.packb(
        type='DT',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12)
    expected = from_hex('1e fc 1d 26 4c')
    assert actual == expected

    parsed = temporenc.unpackb(expected)
    assert parsed.year == 1983
    assert parsed.month == 1
    assert parsed.day == 15
    assert parsed.hour == 18
    assert parsed.minute == 25
    assert parsed.second == 12
    # assert parsed.microsecond is None


def test_type_dts():

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, millisecond=123)
    dts_ms = from_hex('47 bf 07 49 93 07 b0')
    assert actual == dts_ms

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, microsecond=123456)
    dts_us = from_hex('57 bf 07 49 93 07 89 00')
    assert actual == dts_us

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12, nanosecond=123456789)
    dts_ns = from_hex('67 bf 07 49 93 07 5b cd 15')
    assert actual == dts_ns

    actual = temporenc.packb(
        type='DTS',
        year=1983, month=1, day=15,
        hour=18, minute=25, second=12)
    dts_none = from_hex('77 bf 07 49 93 00')
    assert actual == dts_none


def test_type_detection():

    # Type D
    assert len(temporenc.packb(year=1983)) == 3

    # Type T
    assert len(temporenc.packb(hour=18)) == 3

    # Type DT
    assert len(temporenc.packb(year=1983, hour=18)) == 5

    # Type DTS
    assert len(temporenc.packb(millisecond=0)) == 7
    assert len(temporenc.packb(microsecond=0)) == 8
    assert len(temporenc.packb(nanosecond=0)) == 9
