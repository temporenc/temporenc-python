import binascii

import temporenc


def from_hex(s):
    """Compatibility helper like bytes.fromhex() in Python 3"""
    return binascii.unhexlify(s.replace(' ', ''))


def test_date():

    actual = temporenc.packb(type='D', year=1983, month=1, day=15)
    expected = from_hex('8f 7e 0e')
    assert actual == expected

    parsed = temporenc.unpackb(expected)
    assert parsed.year == 1983
    assert parsed.month == 1
    assert parsed.day == 15
    assert parsed.hour is None
