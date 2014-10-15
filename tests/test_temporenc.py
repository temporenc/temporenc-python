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
