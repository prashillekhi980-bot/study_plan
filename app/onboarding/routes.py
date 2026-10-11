"""Onboarding blueprint — first-time student setup (proposal Step 2):
confirm basic info, set daily study availability, add initial modules,
before the student ever sees an empty dashboard.

There's no dedicated "has completed setup" flag in the schema (this app
has no migration tooling — see wait_for_db.py — so adding a column would
require a manual ALTER TABLE on every existing database). Instead the
wizard is offered whenever a logged-in student has zero modules, which is
exactly the "empty dashboard" case the proposal wants to avoid, and is
harmless to show again for a student who later deletes every module.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Module

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/setup")


@onboarding_bp.route("/", methods=["GET", "POST"])
@login_required
def setup_wizard():
    # Already set up (has at least one module) — nothing to do here.
    if Module.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for("recommendations.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            daily_hours = float(request.form.get("daily_study_hours", 2))
            if daily_hours <= 0:
                raise ValueError
        except ValueError:
            flash("Daily study hours must be a positive number.", "error")
            return redirect(url_for("onboarding.setup_wizard"))

        module_names = [
            n.strip() for n in request.form.getlist("module_name") if n.strip()
        ]

        if name:
            current_user.name = name
        current_user.daily_study_hours = daily_hours

        for module_name in module_names:
            db.session.add(Module(user_id=current_user.id, name=module_name))

        db.session.commit()

        if module_names:
            flash(f"Welcome, {current_user.name}! Added {len(module_names)} module(s) to get you started.", "success")
        else:
            flash(f"Welcome, {current_user.name}! Add a module whenever you're ready.", "success")
        return redirect(url_for("recommendations.dashboard"))

    return render_template("onboarding/setup.html", user=current_user)


@onboarding_bp.route("/skip", methods=["POST"])
@login_required
def skip_setup():
    """Lets a student go straight to an empty dashboard and add modules
    manually later, rather than being forced through the wizard. Recorded
    in the session (not the DB) so it only lasts until they log out."""
    session["setup_skipped"] = True
    return redirect(url_for("recommendations.dashboard"))
