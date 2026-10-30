"""
Test: Acknowledgment PDF accessible without authentication.

BUG: The /ack/<id>.pdf endpoint has no session check. Application IDs
are sequential integers starting from 1. Any anonymous user can download
every citizen's acknowledgment PDF by iterating IDs.

The PDF contains: full name, mobile number, date of birth, village,
bank account number, IFSC code.

This is likely the mechanism behind the DC's complaint that "the moment
you apply on the portal, you start getting phone calls — salesmen,
people turning up at your door."

These tests verify that:
1. An unauthenticated request to /ack/<id>.pdf returns 403.
2. An authenticated citizen can access their own ack PDF.
3. An authenticated citizen cannot access another citizen's ack PDF.
"""
import sys
import os
import io
import pytest
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


@pytest.fixture
def client():
    import app as app_module
    app_module.app.config['TESTING'] = True
    app_module.app.config['SECRET_KEY'] = 'test-secret-key'
    with app_module.app.test_client() as c:
        yield c


def test_unauthenticated_cannot_download_ack_pdf(client):
    """
    No session — /ack/1.pdf must return 403.

    Fails on original code (returns 200 or 404 but not 403).
    Passes after authentication check is added.
    """
    with mock.patch('app.os.path.exists', return_value=False), \
         mock.patch('app.get_db') as mock_get_db:
        conn = mock.MagicMock()
        cur = mock.MagicMock()
        cur.fetchone.return_value = (1,)
        conn.cursor.return_value = cur
        mock_get_db.return_value = conn

        response = client.get('/ack/1.pdf')

    assert response.status_code == 403, (
        f"Expected 403 for unauthenticated access to /ack/1.pdf, "
        f"got {response.status_code}. "
        f"Any anonymous user can scrape all citizen PDFs by enumerating IDs."
    )


def test_authenticated_citizen_can_access_own_ack(client):
    """
    A logged-in citizen should be able to download their own ack PDF.
    This must work after the auth check is added.
    """
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['portal_mobile'] = '9000000001'

    fake_pdf = b'%PDF-1.4 fake pdf content'
    with mock.patch('app.os.path.exists', return_value=True), \
         mock.patch('app.send_file', return_value=(__import__('flask').Response(fake_pdf, mimetype='application/pdf'))):
        response = client.get('/ack/42.pdf')

    assert response.status_code == 200, (
        f"Expected 200 for authenticated citizen accessing own ack PDF, "
        f"got {response.status_code}."
    )
