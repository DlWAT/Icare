"""Tests for the function-string DSL parser."""

import pytest

from webapp.dsl import (
    ContinueEffect,
    DSLError,
    FadeEffect,
    StrobeEffect,
    UniformEffect,
    encode_fade,
    encode_strobe,
    encode_uniform,
    parse,
)


class TestParseEmpty:
    def test_empty_string_returns_none(self):
        assert parse("") is None

    def test_none_returns_none(self):
        assert parse(None) is None

    def test_pipe_returns_continue(self):
        assert isinstance(parse("|"), ContinueEffect)


class TestParseUniform:
    def test_basic(self):
        e = parse("uni_4_255_0_128")
        assert isinstance(e, UniformEffect)
        assert e.length == 4
        assert e.color == (255, 0, 128)

    def test_min_length_clamped_to_one(self):
        e = parse("uni_0_10_20_30")
        assert e.length == 1

    def test_wrong_arity(self):
        with pytest.raises(DSLError):
            parse("uni_4_255_0")

    def test_out_of_range_rgb(self):
        with pytest.raises(DSLError):
            parse("uni_4_300_0_0")


class TestParseFade:
    def test_basic(self):
        e = parse("fond_8_255_0_0_0_0_255")
        assert isinstance(e, FadeEffect)
        assert e.length == 8
        assert e.color_from == (255, 0, 0)
        assert e.color_to == (0, 0, 255)

    def test_wrong_arity(self):
        with pytest.raises(DSLError):
            parse("fond_8_1_2_3_4_5")


class TestParseStrobe:
    def test_with_freq(self):
        e = parse("str_2_255_255_0_120")
        assert isinstance(e, StrobeEffect)
        assert e.length == 2
        assert e.color == (255, 255, 0)
        assert e.freq == 120

    def test_without_freq_defaults_60(self):
        e = parse("str_2_255_255_0")
        assert isinstance(e, StrobeEffect)
        assert e.freq == 60


class TestUnknown:
    def test_unknown_prefix(self):
        with pytest.raises(DSLError):
            parse("foo_1_2_3")

    def test_garbage(self):
        with pytest.raises(DSLError):
            parse("uni_a_b_c_d")


class TestEncoders:
    def test_uniform_round_trip(self):
        token = encode_uniform(4, (10, 20, 30))
        assert token == "uni_4_10_20_30"
        assert parse(token) == UniformEffect(length=4, color=(10, 20, 30))

    def test_fade_round_trip(self):
        token = encode_fade(8, (1, 2, 3), (4, 5, 6))
        parsed = parse(token)
        assert isinstance(parsed, FadeEffect)
        assert parsed.length == 8

    def test_strobe_round_trip(self):
        token = encode_strobe(3, (255, 0, 0), 120)
        assert "str_3_255_0_0_120" == token
        parsed = parse(token)
        assert isinstance(parsed, StrobeEffect)
