"""
Test: Broken authorization on admin approve and reject endpoints.

BUG: admin_approve() and admin_reject() check session.get("logged_in"),
but this flag is also set to True when a *citizen* logs in at /status.
Any authenticated citizen can POST to /admin/approve/<their_app_id>
and approve their own application without staff review.

These tests inspect the source code to confirm the correct session key
("admin") is checked, not the shared "logged_in" key.
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


def test_admin_approve_checks_admin_session_key():
    """
    admin_approve() must check session.get("admin"), not session.get("logged_in").

    The "logged_in" key is shared between citizen login and admin login.
    Checking "admin" ensures only staff can approve applications.

    Fails on original code (checks "logged_in"); passes after fix.
    """
    source = get_app_source()
    body = get_function_body(source, 'admin_approve')
    assert body, "admin_approve function not found in app.py"

    uses_logged_in = bool(re.search(r'session\.get\(["\']logged_in["\']', body))
    uses_admin = bool(re.search(r'session\.get\(["\']admin["\']', body))

    assert not uses_logged_in, (
        "admin_approve() checks session['logged_in'] which is set for ANY "
        "logged-in user including citizens. A citizen can approve their own "
        "application by POSTing to /admin/approve/<id>. "
        "Fix: check session.get('admin') instead."
    )
    assert uses_admin, (
        "admin_approve() does not check session.get('admin'). "
        "It must verify the request comes from an admin session."
    )


def test_admin_reject_checks_admin_session_key():
    """
    admin_reject() must check session.get("admin"), not session.get("logged_in").

    Fails on original code; passes after fix.
    """
    source = get_app_source()
    body = get_function_body(source, 'admin_reject')
    assert body, "admin_reject function not found in app.py"

    uses_logged_in = bool(re.search(r'session\.get\(["\']logged_in["\']', body))
    uses_admin = bool(re.search(r'session\.get\(["\']admin["\']', body))

    assert not uses_logged_in, (
        "admin_reject() checks session['logged_in'] which is set for ANY "
        "logged-in user including citizens. Fix: check session.get('admin')."
    )
    assert uses_admin, (
        "admin_reject() does not check session.get('admin')."
    )


def test_admin_approve_does_not_allow_citizen_session():
    """
    Verify via source analysis that the approve route would return 403
    to a session that only has 'logged_in' set (not 'admin').

    Cross-check: the route must abort or redirect when admin key is absent.
    """
    source = get_app_source()
    body = get_function_body(source, 'admin_approve')

    has_403_or_abort = bool(
        re.search(r'abort\s*\(\s*403\s*\)', body) or
        re.search(r'redirect.*admin_login', body)
    )
    assert has_403_or_abort, (
        "admin_approve() does not appear to return 403 or redirect to login "
        "when the session lacks admin privileges."
    )
