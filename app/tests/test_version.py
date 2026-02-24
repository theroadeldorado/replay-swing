"""Tests for version parsing and comparison."""

from version import parse_version, is_newer


def test_parse_simple():
    assert parse_version("1.2.3") == ((1, 2, 3), "")


def test_parse_with_prefix():
    assert parse_version("v1.2.3") == ((1, 2, 3), "")


def test_parse_with_suffix():
    assert parse_version("v0.1.1-beta") == ((0, 1, 1), "beta")


def test_parse_short_version():
    assert parse_version("1.0") == ((1, 0, 0), "")


def test_newer_major():
    assert is_newer("2.0.0", "1.0.0") is True


def test_newer_minor():
    assert is_newer("1.1.0", "1.0.0") is True


def test_newer_patch():
    assert is_newer("1.0.2", "1.0.1") is True


def test_not_newer_same():
    assert is_newer("1.0.0", "1.0.0") is False


def test_not_newer_older():
    assert is_newer("0.9.0", "1.0.0") is False


def test_stable_beats_prerelease():
    assert is_newer("1.0.0", "1.0.0-beta") is True


def test_prerelease_not_newer_than_stable():
    assert is_newer("1.0.0-beta", "1.0.0") is False


def test_prerelease_not_newer_than_same_prerelease():
    assert is_newer("1.0.0-beta", "1.0.0-beta") is False
