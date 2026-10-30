"""
Test: Date of birth parsed in wrong locale order.

BUG: app.py line 274 iterates format strings:
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):

The form UI shows placeholder "DD/MM/YYYY" — the Indian date convention.
A citizen entering "04/06/1955" intends 4 June 1955 (DD/MM).
But the parser tries American format first: it sees April 6, 1955.
The wrong date of birth is stored permanently and affects:
  - Eligibility check (wrong age computed)
  - Status portal password (DOB as DDMMYYYY)

These tests verify that dates entered as DD/MM/YYYY are parsed correctly.
"""
import sys
import os
import pytest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


def parse_dob(dob_raw):
    """
    Mirror the date-parsing logic from handle_submission() so we can
    test it without a full HTTP request.
    """
    from datetime import datetime
    dob = None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            dob = datetime.strptime(dob_raw, fmt).date()
            break
        except ValueError:
            continue
    return dob


def parse_dob_correct(dob_raw):
    """
    Correct version: DD/MM/YYYY first.
    """
    from datetime import datetime
    dob = None
    for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
        try:
            dob = datetime.strptime(dob_raw, fmt).date()
            break
        except ValueError:
            continue
    return dob


def test_date_04_06_1955_parsed_as_june_4_not_april_6():
    """
    A citizen enters "04/06/1955" meaning 4 June 1955 (DD/MM/YYYY).
    The original parser returns 6 April 1955 (April 6, American format).

    This test asserts the CORRECT interpretation: 4 June 1955.
    It fails on the original code and passes after the format order is fixed.
    """
    result = parse_dob('04/06/1955')
    expected = date(1955, 6, 4)
    assert result == expected, (
        f"DOB '04/06/1955' should be parsed as {expected} (4 June, DD/MM/YYYY) "
        f"but got {result}. The parser tries %m/%d/%Y first (American convention) "
        f"even though the form clearly shows DD/MM/YYYY."
    )


def test_date_31_01_1960_only_valid_as_ddmmyyyy():
    """
    "31/01/1960" cannot be MM/DD (there is no 31st month).
    Both parsers should arrive at 31 January 1960.
    This is a sanity check that disambiguates correctly.
    """
    result = parse_dob('31/01/1960')
    expected = date(1960, 1, 31)
    assert result == expected, (
        f"DOB '31/01/1960' should be 31 January 1960, got {result}"
    )


def test_date_01_12_1958_parsed_as_december_1_not_january_12():
    """
    "01/12/1958" means 1 December 1958 in Indian convention.
    American format would give January 12, 1958.

    Fails on original code; passes after fix.
    """
    result = parse_dob('01/12/1958')
    expected = date(1958, 12, 1)
    assert result == expected, (
        f"DOB '01/12/1958' should be {expected} (1 December, DD/MM/YYYY) "
        f"but got {result} (January 12 — American interpretation)."
    )


def test_age_eligibility_uses_correct_dob():
    """
    If a 62-year-old citizen enters their DOB as DD/MM/YYYY and it is
    misread as MM/DD, the stored DOB may represent a different person's age.
    This test confirms the correct DOB produces correct age >= 60.
    """
    from datetime import datetime
    dob = parse_dob('15/03/1962')
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    assert dob == date(1962, 3, 15), (
        f"'15/03/1962' should parse to 15 March 1962, got {dob}"
    )
    assert age >= 60, f"Expected age >= 60, got {age} — wrong DOB parsing affects eligibility"
