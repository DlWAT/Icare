"""Tests for the minimal OSC codec."""

import pytest

from webapp.osc import decode, encode


def test_int_round_trip():
    address, args = decode(encode("/live/song/set/tempo", 128))
    assert address == "/live/song/set/tempo"
    assert args == [128]


def test_float_round_trip():
    address, args = decode(encode("/live/song/set/tempo", 128.5))
    assert address == "/live/song/set/tempo"
    assert args == [128.5]


def test_string_round_trip_and_padding():
    for text in ("", "a", "abc", "abcd", "abcde", "INTRO"):
        address, args = decode(encode("/live/scene/set/name", 3, text))
        assert address == "/live/scene/set/name"
        assert args == [3, text]


def test_mixed_arguments():
    _, args = decode(encode("/x", 1, 2.0, "three"))
    assert args == [1, 2.0, "three"]


def test_message_is_padded_to_four_bytes():
    assert len(encode("/x")) % 4 == 0
    assert len(encode("/x", "hello")) % 4 == 0


def test_rejects_bad_address():
    with pytest.raises(ValueError):
        encode("no-slash")


def test_bare_address_decodes_to_no_args():
    assert decode(b"/live/test\x00\x00") == ("/live/test", [])
