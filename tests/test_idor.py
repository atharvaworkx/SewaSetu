"""
Test: IDOR (Insecure Direct Object Reference) on /application/<id>.

BUG: The view_application() route checks only session.get("logged_in")
before serving an application record. It does NOT verify that the
requested application belongs to the logged-in citizen.

Any authenticated citizen can change the integer ID in the URL and
read any other citizen's full record: name, DOB, mobile, bank account,
IFSC, village, block.

These tests verify the source code contains an ownership check in
view_application(), ensuring the application's mobile number matches
the session's portal_mobile.
"""
import re
import os


def get_app_source():
    path = os.path.join(os.path.dirname(__file__), '..', 'app', 'app.py')
    with open(path, encoding='utf-8') as f:
        return f.read()


def get_function_body(source, func_name):
    start = source.find(f'def {func_name}(')
    if start == -1:
        return ''
    end = source.find('\ndef ', start + 1)
    if end == -1:
        end = len(source)
    return source[start:end]


def test_view_application_has_ownership_check():
    """
    view_application() must compare the application's mobile number
    against session["portal_mobile"] before serving the record.

    Fails on original code (no ownership check present).
    Passes after fix.
    """
    source = get_app_source()
    body = get_function_body(source, 'view_application')
    assert body, "view_application function not found in app.py"

    has_ownership_check = bool(
        re.search(r'portal_mobile', body)
    )
    assert has_ownership_check, (
        "view_application() does not check that the application belongs to "
        "the logged-in citizen (session['portal_mobile']). "
        "Any authenticated citizen can view any other citizen's bank account "
        "and PII by incrementing the app_id in the URL. "
        "Fix: after fetching the row, verify row[mobile_index] == session['portal_mobile']."
    )


def test_view_application_returns_403_for_wrong_owner():
    """
    When the ownership check fails, view_application() must abort with 403,
    not silently serve the other citizen's data.

    Fails on original code; passes after fix.
    """
    source = get_app_source()
    body = get_function_body(source, 'view_application')

    has_403 = bool(re.search(r'abort\s*\(\s*403\s*\)', body))
    assert has_403, (
        "view_application() does not call abort(403) when ownership check fails. "
        "The fix must explicitly reject cross-citizen access with a 403 response."
    )


def test_view_application_does_not_trust_logged_in_alone():
    """
    The route must not gate access solely on session['logged_in'].
    It must also verify ownership.

    This is a belt-and-suspenders check: the fix must add ownership
    verification, not merely change which session key is checked.
    """
    source = get_app_source()
    body = get_function_body(source, 'view_application')

    has_ownership = bool(re.search(r'portal_mobile', body))
    has_403 = bool(re.search(r'abort\s*\(\s*403\s*\)', body))

    assert has_ownership and has_403, (
        "view_application() must check session['portal_mobile'] against "
        "the application's mobile number and call abort(403) on mismatch. "
        f"Ownership check present: {has_ownership}, 403 present: {has_403}."
    )
