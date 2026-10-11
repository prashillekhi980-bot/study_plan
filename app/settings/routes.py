"""Settings blueprint — account/profile management (proposal Step 15:
view profile, update daily study availability, change password, manage
account/session, logout).

Name and email are shown read-only here — they're set at registration
and can't be edited afterward, so there's no update-profile route.

Daily study hours can also be edited inline from the Timetable page
(same `timetable.update_daily_hours` endpoint) — Settings is the single
place that also covers profile and password, since those don't belong
anywhere else in the app.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db, bcrypt

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def view_settings():
    return render_template("settings/view.html", user=current_user)


@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("settings.view_settings"))

    if not new_password or new_password != confirm_password:
        flash("New passwords don't match.", "error")
        return redirect(url_for("settings.view_settings"))

    current_user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    flash("Password changed.", "success")
    return redirect(url_for("settings.view_settings"))
