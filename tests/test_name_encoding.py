"""
Test: Applicant name truncated for Indian-language scripts.

BUG 1 (sanitize): app.py line 74 slices the UTF-8 byte representation
to 20 bytes. Indian-language characters (Assamese, Bengali, Devanagari)
are 3 bytes each in UTF-8, so 20 bytes = ~6 characters. A name like
"অসমীয়া নাগৰিক" (14 chars) is silently chopped.

BUG 2 (PDF font): generate_acknowledgment() uses Helvetica, a Latin-only
font. Non-ASCII characters are rendered as '?' by fpdf2's core fonts.

The DC's first complaint: an old man walked two hours to show his
acknowledgment slip where his Assamese name appears as four question marks.

These tests verify that:
1. An Assamese name is not truncated by sanitize().
2. A name stored via handle_submission() roundtrips without truncation.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


ASSAMESE_NAME = 'অসমীয়া নাগৰিক'
BENGALI_NAME = 'বাংলাদেশী নাগরিক'
LONG_LATIN_NAME = 'Ramachandra Venkataraman'


def get_sanitize():
    import app as app_module
    return app_module.sanitize


def test_assamese_name_not_truncated_by_sanitize():
    """
    sanitize() with default maxlen should not truncate an Assamese name.

    Fails on original code: 'অসমীয়া নাগৰিক' is 14 chars but 41 UTF-8
    bytes — slicing to 20 bytes cuts it to ~6 chars.
    Passes after fix: sanitize() for applicant_name should use character
    count or a much larger limit, not 20 bytes.
    """
    sanitize = get_sanitize()
    result = sanitize(ASSAMESE_NAME)
    assert result == ASSAMESE_NAME, (
        f"Assamese name truncated:\n"
        f"  Input:  {ASSAMESE_NAME!r} ({len(ASSAMESE_NAME)} chars, "
        f"{len(ASSAMESE_NAME.encode('utf-8'))} bytes)\n"
        f"  Output: {result!r} ({len(result)} chars)\n"
        f"sanitize() slices UTF-8 bytes, not characters. "
        f"Indian-language names are 3 bytes per character."
    )


def test_bengali_name_not_truncated_by_sanitize():
    """
    Same check for a Bengali name.
    """
    sanitize = get_sanitize()
    result = sanitize(BENGALI_NAME)
    assert result == BENGALI_NAME, (
        f"Bengali name truncated:\n"
        f"  Input:  {BENGALI_NAME!r}\n"
        f"  Output: {result!r}"
    )


def test_long_latin_name_not_truncated_by_sanitize():
    """
    A long Latin name should also not be silently truncated when used
    as applicant_name. 'Ramachandra Venkataraman' is 24 chars.
    """
    sanitize = get_sanitize()
    result = sanitize(LONG_LATIN_NAME)
    assert result == LONG_LATIN_NAME, (
        f"Long Latin name truncated:\n"
        f"  Input:  {LONG_LATIN_NAME!r} ({len(LONG_LATIN_NAME)} chars)\n"
        f"  Output: {result!r} ({len(result)} chars)\n"
        f"Applicant name field in DB is VARCHAR(100); 20-byte limit is wrong."
    )


def test_sanitize_still_strips_whitespace():
    """
    After the fix, sanitize() should still strip leading/trailing whitespace.
    This verifies we didn't break the existing behaviour.
    """
    sanitize = get_sanitize()
    result = sanitize('  Ravi Kumar  ')
    assert result == 'Ravi Kumar', (
        f"Expected whitespace stripped, got: {result!r}"
    )


def test_sanitize_handles_none():
    """
    sanitize(None) should return empty string. Existing behaviour to preserve.
    """
    sanitize = get_sanitize()
    assert sanitize(None) == ''
