"""Timetable blueprint — auto-generated study schedule (proposal: "the
web application will automatically produce a study timetable for all of
the study tasks within the application, adding them to the relevant
study days").
"""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.timetable.generator import generate_timetable, get_timetable_by_day

timetable_bp = Blueprint("timetable", __name__, url_prefix="/timetable")

# How many days to show at minimum, even if most are empty — makes the
# view read as an actual week-at-a-glance calendar rather than a bare
# list of only the days that happen to have a session scheduled.
DISPLAY_WINDOW_DAYS = 7
# Hard cap so a plan with sessions scheduled far in the future (e.g. an
# at-risk task overflowing past its deadline) doesn't stretch the view
# into a very long horizontal scroll.
MAX_DISPLAY_DAYS = 21


def _fill_display_window(days, today):
    """Pad `days` (only the dates that actually have sessions) out to a
    full calendar window starting today, so free days show up as empty
    columns instead of being skipped entirely."""
    if not days:
        return []

    sessions_by_date = {d["date"]: d["sessions"] for d in days}
    last_scheduled = max(sessions_by_date.keys())

    window_end = max(today + timedelta(days=DISPLAY_WINDOW_DAYS - 1), last_scheduled)
    window_end = min(window_end, today + timedelta(days=MAX_DISPLAY_DAYS - 1))

    filled = []
    current = today
    while current <= window_end:
        sessions = sessions_by_date.get(current, [])
        filled.append({
            "date": current,
            "sessions": sessions,
            "total_hours": round(sum(s.allocated_hours for s in sessions), 2),
            "is_today": current == today,
        })
        current += timedelta(days=1)
    return filled


@timetable_bp.route("/")
@login_required
def view_timetable():
    days = get_timetable_by_day(current_user)
    display_days = _fill_display_window(days, date.today())
    return render_template("timetable/view.html", days=display_days, user=current_user)


@timetable_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    result = generate_timetable(current_user)
    if result["sessions_created"] == 0:
        flash("No pending tasks to schedule — add some tasks first.", "error")
    else:
        msg = f"Timetable regenerated: {result['sessions_created']} study block(s) scheduled."
        if result["at_risk_tasks"]:
            names = ", ".join(r["task"].title for r in result["at_risk_tasks"])
            msg += f" ⚠ At risk of missing deadline (not enough daily hours): {names}."
        flash(msg, "success" if not result["at_risk_tasks"] else "error")
    return redirect(url_for("timetable.view_timetable"))


@timetable_bp.route("/settings", methods=["POST"])
@login_required
def update_daily_hours():
    try:
        hours = float(request.form.get("daily_study_hours", 2))
        if hours <= 0:
            raise ValueError
    except ValueError:
        flash("Daily study hours must be a positive number.", "error")
        return redirect(url_for("timetable.view_timetable"))

    current_user.daily_study_hours = hours
    db.session.commit()
    flash(f"Daily study hours set to {hours}h. Regenerate the timetable to apply it.", "success")
    return redirect(url_for("timetable.view_timetable"))
