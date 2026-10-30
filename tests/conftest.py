"""
conftest.py — shared pytest fixtures for Sewa Setu tests.

Provides a Flask test client and session helpers that avoid
needing a live database for unit-level tests.
"""
import sys
import os
import ast
import types
import pytest

# Python 3.14 compatibility for Werkzeug 2.2 / Flask 2.2 AST usage
class _Str(ast.Constant):
    def __init__(self, s="", *args, **kwargs):
        super().__init__(value=s)
        self.s = s

class _Num(ast.Constant):
    def __init__(self, n=0, *args, **kwargs):
        super().__init__(value=n)
        self.n = n

class _Bytes(ast.Constant):
    def __init__(self, s=b"", *args, **kwargs):
        super().__init__(value=s)
        self.s = s

if not hasattr(ast, "Str"):
    ast.Str = _Str
if not hasattr(ast, "Num"):
    ast.Num = _Num
if not hasattr(ast, "Bytes"):
    ast.Bytes = _Bytes
if not hasattr(ast, "NameConstant"):
    ast.NameConstant = ast.Constant

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


@pytest.fixture
def app_client():
    """
    Return a Flask test client with the app configured for testing.
    Database calls are not mocked here; individual tests handle that.
    """
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        'database': {'host': 'localhost', 'port': '5432',
                     'name': 'sewasetu', 'user': 'sewasetu',
                     'password': 'sewasetu123'},
        'app': {'secret_key': 'test-secret',
                'sms_gateway_url': 'http://localhost:8025',
                'otp_validity_seconds': '300',
                'upload_dir': '/tmp/sewasetu-test-uploads'},
        'pension': {'min_age': '60', 'sla_days': '15',
                    'scheme_deadline': '2099-12-31 23:59'},
    })

    import unittest.mock as mock
    with mock.patch('configparser.ConfigParser.read', return_value=None), \
         mock.patch('configparser.ConfigParser.get', side_effect=lambda s, k: cfg.get(s, k)), \
         mock.patch('configparser.ConfigParser.getint', side_effect=lambda s, k: cfg.getint(s, k)):
        import importlib
        import app as app_module
        importlib.reload(app_module)
        app_module.app.config['TESTING'] = True
        app_module.app.config['SECRET_KEY'] = 'test-secret'
        with app_module.app.test_client() as client:
            yield client
