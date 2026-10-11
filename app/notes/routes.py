"""Notes blueprint — optional note-summariser / study-aid feature
(proposal Phase 6). Scoped through the parent task's or note's owner,
via the shared ownership checks in app.ownership.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Note
from app.notes.summarizer import summarize
from app.ownership import get_owned_task_or_404, get_owned_note_or_404

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")


@notes_bp.route("/task/<int:task_id>")
@login_required
def list_notes(task_id):
    task = get_owned_task_or_404(task_id)
    notes = Note.query.filter_by(task_id=task.id, user_id=current_user.id).order_by(Note.created_at.desc()).all()
    api_configured = bool(current_app.config.get("OPENAI_API_KEY"))
    return render_template("notes/list.html", task=task, notes=notes, api_configured=api_configured)


@notes_bp.route("/task/<int:task_id>/new", methods=["POST"])
@login_required
def new_note(task_id):
    task = get_owned_task_or_404(task_id)
    content = request.form.get("content", "").strip()

    if not content:
        flash("Note content can't be empty.", "error")
        return redirect(url_for("notes.list_notes", task_id=task_id))

    note = Note(task_id=task.id, user_id=current_user.id, content=content)
    db.session.add(note)
    db.session.commit()
    flash("Note saved.", "success")
    return redirect(url_for("notes.list_notes", task_id=task_id))


@notes_bp.route("/<int:note_id>/summarize", methods=["POST"])
@login_required
def summarize_note(note_id):
    """Generates a summary for a note. Defaults to the offline, rule-based
    summarizer (no data leaves the server). Only uses the OpenAI API if
    the student explicitly checks the consent box on THIS request AND a
    key is configured — per the proposal's data-privacy commitment that
    students are informed and can object in advance."""
    note = get_owned_note_or_404(note_id)

    consent_given = request.form.get("consent_to_external_api") == "on"
    api_key = current_app.config.get("OPENAI_API_KEY")

    summary, method = summarize(note.content, api_key=api_key, consent=consent_given)
    note.summary = summary
    db.session.commit()

    if method == "openai":
        flash("Summary generated using the OpenAI API (as you consented).", "success")
    else:
        flash("Summary generated using the built-in offline summarizer — no data was sent externally.", "success")

    return redirect(url_for("notes.list_notes", task_id=note.task_id))


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    note = get_owned_note_or_404(note_id)
    task_id = note.task_id
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for("notes.list_notes", task_id=task_id))
