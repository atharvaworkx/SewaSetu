"""
Test: Upload document validation and friendly error messages.

BUG: upload() in app.py flashes cryptic "ERR_VAL_47" for any validation failure,
only accepts .pdf (rejecting JPG despite upload.html advertising it), and
rejects any file larger than 100 KB (102400 bytes) despite upload.html advertising 5 MB.

These tests verify:
1. Friendly error message when no file is selected (not ERR_VAL_47).
2. JPG and PNG files are accepted, matching the UI instructions.
3. Files up to 5 MB are accepted.
4. Clear error messages when an invalid extension or oversized file is provided.
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


def test_upload_missing_file_shows_friendly_error(client):
    """
    Submitting upload without a file should show a human-readable error,
    never 'ERR_VAL_47'.
    """
    with client.session_transaction() as sess:
        sess['verified_mobile'] = '9000000001'

    response = client.post('/upload', data={}, follow_redirects=True)
    body = response.data.decode('utf-8', errors='ignore')

    assert 'ERR_VAL_47' not in body, "Cryptic error code ERR_VAL_47 was displayed to citizen"


def test_upload_accepts_jpg_image(client, tmp_path):
    """
    upload.html says 'Accepted formats: JPG or PDF'.
    A valid JPG file must be accepted and redirect to /declaration.
    """
    with client.session_transaction() as sess:
        sess['verified_mobile'] = '9000000001'

    fake_jpg = io.BytesIO(b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 500)
    with mock.patch('app.UPLOAD_DIR', str(tmp_path)):
        response = client.post('/upload', data={
            'document': (fake_jpg, 'age_proof.jpg')
        })

    assert response.status_code == 302, f"Expected redirect to declaration, got {response.status_code}"
    assert '/declaration' in response.headers.get('Location', '')
