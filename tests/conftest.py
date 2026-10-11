"""Shared pytest fixtures for the whole suite.

Tests run against the app's TestingConfig (in-memory SQLite, see
app/config.py) rather than the real MySQL database, so the suite is fast,
isolated, and safe to run anywhere without a DB server. This is a
different (and complementary) layer of verification to the manual
live-MySQL testing used throughout development: these tests catch
regressions automatically and repeatedly; the live testing proved the
feature against the real stack the one time it mattered most (each
feature's initial build). SQLite lacks MySQL's ENUM type, but SQLAlchemy
emulates Task/priority and Task/status as CHECK-constrained VARCHAR
columns automatically, so the same model definitions work unchanged.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date, timedelta

from app import create_app
from app.extensions import db as _db
from app.models import User, Module, Task


@pytest.fixture()
def app():
    """A fresh Flask app + in-memory database for each test function."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


def register(client, email="student@example.com", password="TestPass123!", name="Student"):
    return client.post(
        "/auth/register",
        data={"name": name, "email": email, "password": password, "confirm_password": password},
        follow_redirects=False,
    )


def login(client, email="student@example.com", password="TestPass123!"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


@pytest.fixture()
def registered_user(client, db):
    """Registers and logs in one user via the real HTTP routes (so the
    ownership/ownership.py layer is exercised the same way a browser
    would hit it), returning the persisted User row."""
    register(client)
    login(client)
    return User.query.filter_by(email="student@example.com").first()


@pytest.fixture()
def other_user(db):
    """A second user, created directly in the DB (not logged in), used
    to prove ownership checks block cross-user access."""
    from app.extensions import bcrypt
    user = User(
        name="Other Student",
        email="other@example.com",
        password_hash=bcrypt.generate_password_hash("TestPass123!").decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def module(db, registered_user):
    m = Module(user_id=registered_user.id, name="Databases", description="Test module")
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture()
def task(db, module):
    t = Task(
        module_id=module.id,
        title="Learn SQL joins",
        due_date=date.today() + timedelta(days=7),
        priority="high",
        difficulty=3,
        estimated_hours=5,
    )
    db.session.add(t)
    db.session.commit()
    return t
