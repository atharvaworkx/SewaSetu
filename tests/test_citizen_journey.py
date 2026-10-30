"""
Test: Citizen journey fixes — widowed applicants and captcha verification.

1. Widowed applicant should not be forced to provide husband's current employer.
2. Captcha on /apply must be validated to prevent automated SMS abuse.
"""
import sys
import os
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


def test_apply_rejects_incorrect_captcha(client):
    """
    Submitting an incorrect captcha on /apply must be rejected and not issue an OTP.
    """
    with client.session_transaction() as sess:
        sess['captcha_answer'] = 14

    with mock.patch('app.get_db') as mock_db, \
         mock.patch('app.send_sms') as mock_sms:
        response = client.post('/apply', data={
            'mobile': '9876543210',
            'captcha': '99'
        }, follow_redirects=True)

    mock_sms.assert_not_called()
    assert b'Incorrect captcha' in response.data or response.status_code == 200
