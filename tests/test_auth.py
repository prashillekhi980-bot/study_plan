"""Auth blueprint: registration, login, logout, password hashing."""
from app.models import User
from tests.conftest import register, login


def test_register_creates_user(client, db):
    resp = register(client)
    assert resp.status_code == 302

    user = User.query.filter_by(email="student@example.com").first()
    assert user is not None
    assert user.name == "Student"


def test_password_is_hashed_not_stored_plain(client, db):
    register(client)
    user = User.query.filter_by(email="student@example.com").first()
    assert user.password_hash != "TestPass123!"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_register_rejects_mismatched_confirm_password(client, db):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Student",
            "email": "student@example.com",
            "password": "TestPass123!",
            "confirm_password": "SomethingElse!",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302  # redirected back to the register form
    assert User.query.filter_by(email="student@example.com").count() == 0


def test_register_rejects_missing_required_fields(client, db):
    resp = client.post(
        "/auth/register",
        data={"name": "", "email": "student@example.com",
              "password": "TestPass123!", "confirm_password": "TestPass123!"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert User.query.count() == 0


def test_register_rejects_duplicate_email(client, db):
    register(client)
    resp = register(client, name="Someone Else")
    assert resp.status_code == 302

    assert User.query.filter_by(email="student@example.com").count() == 1


def test_login_with_correct_credentials_succeeds(client, db):
    """A brand-new user (no modules yet) is routed to the first-time
    setup wizard rather than an empty dashboard — see app/onboarding."""
    register(client)
    resp = login(client)
    assert resp.status_code == 302
    assert "/setup" in resp.headers["Location"]


def test_login_with_existing_modules_goes_straight_to_dashboard(client, db):
    from app.extensions import db as _db
    from app.models import Module, User

    register(client)
    user = User.query.filter_by(email="student@example.com").first()
    _db.session.add(Module(user_id=user.id, name="Databases"))
    _db.session.commit()

    resp = login(client)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_with_wrong_password_fails(client, db):
    register(client)
    resp = login(client, password="WrongPassword!")
    assert resp.status_code == 200  # re-renders login form with a flash error


def test_login_with_unknown_email_fails(client, db):
    resp = login(client, email="nobody@example.com")
    assert resp.status_code == 200


def test_dashboard_requires_login(client, db):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_logout_ends_session(client, db):
    register(client)
    login(client)
    client.get("/auth/logout")

    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
