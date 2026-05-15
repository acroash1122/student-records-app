import pytest
from app import create_app
from models import db as _db
from config import TestConfig


@pytest.fixture(scope='session')
def app():
    """Create a test application using in-memory SQLite — no MySQL needed."""
    application = create_app(TestConfig)
    yield application


@pytest.fixture(scope='session')
def _db_session(app):
    """Create all tables once per session, drop them at the end."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture
def client(app, _db_session):
    """Fresh test client for each test."""
    return app.test_client()
