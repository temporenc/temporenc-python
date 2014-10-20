import binascii
import datetime
import io

import pytest

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


def test_type_dtsz():

    # Note: hour is adjusted for UTC

    actual = temporenc.packb(
        type='DTSZ',
        year=1983, month=1, day=15,
        hour=17, minute=25, second=12, millisecond=123,
        tz_offset=60)
    dtsz_ms = from_hex('e3 df 83 a2 c9 83 dc 40')
    assert actual == dtsz_ms
    v = temporenc.unpackb(dtsz_ms)
    assert (v.year, v.month, v.day) == (1983, 1, 15)
    assert (v.hour, v.minute, v.second) == (17, 25, 12)
    assert v.millisecond == 123
    assert v.microsecond == 123000
    assert v.nanosecond == 123000000
    assert (v.tz_hour, v.tz_minute, v.tz_offset) == (1, 0, 60)

    actual = temporenc.packb(
        type='DTSZ',
        year=1983, month=1, day=15,
        hour=17, minute=25, second=12, microsecond=123456,
        tz_offset=60)
    dtsz_us = from_hex('eb df 83 a2 c9 83 c4 81 10')
    assert actual == dtsz_us
    assert temporenc.unpackb(dtsz_us).microsecond == 123456
    assert (v.tz_hour, v.tz_minute, v.tz_offset) == (1, 0, 60)

    actual = temporenc.packb(
        type='DTSZ',
        year=1983, month=1, day=15,
        hour=17, minute=25, second=12, nanosecond=123456789,
        tz_offset=60)
    dtsz_ns = from_hex('f3 df 83 a2 c9 83 ad e6 8a c4')
    assert actual == dtsz_ns
    assert temporenc.unpackb(dtsz_ns).nanosecond == 123456789
    assert (v.tz_hour, v.tz_minute, v.tz_offset) == (1, 0, 60)

    actual = temporenc.packb(
        type='DTSZ',
        year=1983, month=1, day=15,
        hour=17, minute=25, second=12,
        tz_offset=60)
    dtsz_none = from_hex('fb df 83 a2 c9 91 00')
    assert actual == dtsz_none
    v = temporenc.unpackb(dtsz_none)
    assert v.millisecond is None
    assert v.millisecond is None
    assert v.millisecond is None
    assert (v.tz_hour, v.tz_minute, v.tz_offset) == (1, 0, 60)


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

    # Type DTSZ
    assert len(temporenc.packb(millisecond=0, tz_offset=120)) == 8


def test_type_empty_values():
    v = temporenc.unpackb(temporenc.packb(type='DTS'))
    assert (v.year, v.month, v.day) == (None, None, None)
    assert (v.hour, v.minute, v.second) == (None, None, None)
    assert (v.millisecond, v.microsecond, v.nanosecond) == (None, None, None)
    assert v.tz_offset is None


def test_incorrect_sizes():

    # Too long
    with pytest.raises(ValueError):
        temporenc.unpackb(temporenc.packb(year=1983) + b'foo')
    with pytest.raises(ValueError):
        temporenc.unpackb(temporenc.packb(millisecond=0) + b'foo')

    # Too short
    with pytest.raises(ValueError):
        temporenc.unpackb(temporenc.packb(year=1983)[:-1])
    with pytest.raises(ValueError):
        temporenc.unpackb(temporenc.packb(millisecond=0)[:-1])


def test_unpack_bytearray():
    ba = bytearray((0x8f, 0x7e, 0x0e))
    assert temporenc.unpackb(ba) is not None


def test_stream_unpacking():
    # This stream contains two values and one byte of trailing data
    fp = io.BytesIO(from_hex('8f 7e 0e 8f 7e 0f ff'))
    assert temporenc.unpack(fp).day == 15
    assert fp.tell() == 3
    assert temporenc.unpack(fp).day == 16
    assert fp.tell() == 6
    assert fp.read() == b'\xff'


def test_stream_packing():
    fp = io.BytesIO()
    assert temporenc.pack(fp, year=1983) == 3
    assert temporenc.pack(fp, year=1984) == 3
    assert fp.tell() == 6
    assert len(fp.getvalue()) == 6


def test_wrong_type():
    with pytest.raises(ValueError):
        temporenc.packb(type="foo", year=1983)


def test_out_of_range_values():
    with pytest.raises(ValueError):
        temporenc.packb(year=123456)

    with pytest.raises(ValueError):
        temporenc.packb(month=-12)

    with pytest.raises(ValueError):
        temporenc.packb(day=1234)

    with pytest.raises(ValueError):
        temporenc.packb(hour=1234)

    with pytest.raises(ValueError):
        temporenc.packb(minute=1234)

    with pytest.raises(ValueError):
        temporenc.packb(second=1234)

    with pytest.raises(ValueError):
        temporenc.packb(millisecond=1000)

    with pytest.raises(ValueError):
        temporenc.packb(microsecond=1000000)

    with pytest.raises(ValueError):
        temporenc.packb(nanosecond=10000000000)

    with pytest.raises(ValueError):
        temporenc.packb(tz_offset=1050)

    with pytest.raises(ValueError):
        temporenc.packb(tz_offset=13)  # not a full quarter


def test_unpacking_bogus_data():
    with pytest.raises(ValueError):
        # First byte can never occur in valid values.
        temporenc.unpackb(from_hex('bb 12 34'))


def test_native_packing():

    with pytest.raises(ValueError):
        temporenc.packb(object())

    # datetime.date => D
    actual = temporenc.packb(datetime.date(1983, 1, 15))
    expected = from_hex('8f 7e 0e')
    assert actual == expected

    # datetime.datetime => DTS, unless told otherwise
    actual = temporenc.packb(datetime.datetime(
        1983, 1, 15, 18, 25, 12, 123456))
    expected = from_hex('57 bf 07 49 93 07 89 00')
    assert actual == expected

    actual = temporenc.packb(
        datetime.datetime(1983, 1, 15, 18, 25, 12),
        type='DT')
    expected = from_hex('1e fc 1d 26 4c')
    assert actual == expected

    # datetime.time => DTS, unless told otherwise
    assert len(temporenc.packb(datetime.datetime.now().time())) == 8
    actual = temporenc.packb(
        datetime.time(18, 25, 12),
        type='T')
    expected = from_hex('a1 26 4c')
    assert actual == expected


def test_native_packing_with_overrides():
    actual = temporenc.packb(
        datetime.datetime(1984, 1, 16, 18, 26, 12, 123456),
        year=1983, day=15, minute=25)
    expected = from_hex('57 bf 07 49 93 07 89 00')
    assert actual == expected


def test_native_unpacking():
    value = temporenc.unpackb(temporenc.packb(
        year=1983, month=1, day=15))
    assert value.date() == datetime.date(1983, 1, 15)

    value = temporenc.unpackb(temporenc.packb(
        year=1983, month=1, day=15,
        hour=1, minute=2, second=3, microsecond=456))
    assert value.datetime() == datetime.datetime(1983, 1, 15, 1, 2, 3, 456)

    value = temporenc.unpackb(temporenc.packb(
        year=1983, month=1, day=15,  # will be ignored
        hour=1, minute=2, second=3, microsecond=456))
    assert value.time() == datetime.time(1, 2, 3, 456)

    value = temporenc.unpackb(temporenc.packb(year=1234))
    with pytest.raises(ValueError):
        value.time()

    value = temporenc.unpackb(temporenc.packb(hour=14))
    with pytest.raises(ValueError):
        value.date()


def test_string_conversion():

    # Date only
    value = temporenc.unpackb(temporenc.packb(year=1983, month=1, day=15))
    assert str(value) == "1983-01-15"
    value = temporenc.unpackb(temporenc.packb(year=1983, day=15))
    assert str(value) == "1983-??-15"

    # Time only
    value = temporenc.unpackb(temporenc.packb(hour=1, minute=2, second=3))
    assert str(value) == "01:02:03"
    value = temporenc.unpackb(temporenc.packb(
        hour=1, second=3, microsecond=12340))
    assert str(value) == "01:??:03.01234"

    # Date and time
    value = temporenc.unpackb(temporenc.packb(
        year=1983, month=1, day=15,
        hour=18, minute=25))
    assert str(value) == "1983-01-15 18:25:??"

    # Very contrived example...
    value = temporenc.unpackb(temporenc.packb(microsecond=1250))
    assert str(value) == "??:??:??.00125"
