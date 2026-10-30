"""
Test: SQL injection vulnerability in the reset_password endpoint.

BUG: app.py lines 446 and 449 build SQL queries using Python string
formatting (% operator) instead of psycopg2 parameterized queries:

    cur.execute("SELECT mobile FROM portal_users WHERE mobile = '%s'" % mobile)
    cur.execute("SELECT dob FROM applications WHERE mobile = '%s' LIMIT 1" % mobile)

An attacker can supply a mobile value containing SQL metacharacters
to manipulate the query logic, dump data, or cause errors.

This test inspects the source code for the unsafe pattern and confirms
it is absent after the fix.
"""
import re
import os


def get_app_source():
    path = os.path.join(os.path.dirname(__file__), '..', 'app', 'app.py')
    with open(path, encoding='utf-8') as f:
        return f.read()


UNSAFE_PATTERN = re.compile(
    r'cur\.execute\s*\(\s*["\'].*%s.*["\'].*%\s*\w',
    re.DOTALL
)

RESET_PASSWORD_UNSAFE = re.compile(
    r"WHERE mobile = '%s'\"?\s*%\s*mobile",
    re.DOTALL
)


def test_no_string_formatted_sql_in_reset_password():
    """
    Confirm that reset_password() does not use Python % string formatting
    to embed user input into SQL queries.

    Fails against original code; passes after parameterization fix.
    """
    source = get_app_source()
    reset_block_start = source.find('def reset_password()')
    assert reset_block_start != -1, "reset_password function not found in app.py"

    next_def = source.find('\ndef ', reset_block_start + 1)
    if next_def == -1:
        next_def = len(source)
    reset_block = source[reset_block_start:next_def]

    match = RESET_PASSWORD_UNSAFE.search(reset_block)
    assert match is None, (
        "reset_password() contains SQL built via Python string formatting:\n"
        f"  {match.group(0)!r}\n"
        "This is a SQL injection vulnerability. Use parameterized queries:\n"
        '  cur.execute("SELECT mobile FROM portal_users WHERE mobile = %s", (mobile,))'
    )


def test_reset_password_uses_parameterized_queries():
    """
    Confirm that reset_password() passes mobile as a tuple argument
    to cur.execute() rather than embedding it in the query string.

    Fails against original code; passes after fix.
    """
    source = get_app_source()
    reset_block_start = source.find('def reset_password()')
    next_def = source.find('\ndef ', reset_block_start + 1)
    if next_def == -1:
        next_def = len(source)
    reset_block = source[reset_block_start:next_def]

    parameterized = re.search(
        r'cur\.execute\s*\(.*WHERE mobile\s*=\s*%s.*,\s*\(',
        reset_block,
        re.DOTALL
    )
    assert parameterized is not None, (
        "reset_password() does not appear to use parameterized queries. "
        "Expected pattern: cur.execute('... WHERE mobile = %s', (mobile,))"
    )
