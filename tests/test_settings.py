"""Settings blueprint: read-only profile, password change."""
from app.models import User
from app.extensions import bcrypt
from tests.conftest import login


def test_settings_requires_login(client, db):
    resp = client.get("/settings/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_profile_name_and_email_are_not_editable(client, db, registered_user):
    """Name and email are fixed at registration — Settings only displays
    them as plain text (Full name / Email rows), not editable fields, and
    there's no route left to change them."""
    resp = client.get("/settings/")
    assert resp.status_code == 200
    assert b"Full name" in resp.data
    assert registered_user.name.encode() in resp.data
    assert registered_user.email.encode() in resp.data
    assert b'name="name"' not in resp.data
    assert b'name="email"' not in resp.data

    # The old update-profile endpoint no longer exists.
    resp = client.post(
        "/settings/profile",
        data={"name": "New Name", "email": "new@example.com"},
        follow_redirects=False,
    )
    assert resp.status_code == 404

    user = User.query.get(registered_user.id)
    assert user.name == registered_user.name
    assert user.email == registered_user.email


def test_change_password_with_correct_current_password(client, db, registered_user):
    resp = client.post(
        "/settings/password",
        data={
            "current_password": "TestPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    user = User.query.get(registered_user.id)
    assert bcrypt.check_password_hash(user.password_hash, "NewPass456!")


def test_change_password_rejects_wrong_current_password(client, db, registered_user):
    resp = client.post(
        "/settings/password",
        data={
            "current_password": "WrongPassword!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    user = User.query.get(registered_user.id)
    assert bcrypt.check_password_hash(user.password_hash, "TestPass123!")
