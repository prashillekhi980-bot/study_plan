"""Shared ownership-check helpers.

Every resource in this app (module, task, note) ultimately belongs to a
user, and every route that touches one must confirm the current user is
that owner before doing anything else. This was previously duplicated
almost verbatim across the modules/tasks/notes blueprints; consolidating
it here means there's exactly one place that defines what "owns" means
for each resource, and one place to fix if that logic ever needs to change.

Each helper raises a 404 (not 403) on a mismatch — deliberately not
revealing to an unauthorized user that the resource exists at all.
"""
from flask import abort
from flask_login import current_user
from app.models import Module, Task, Note, StudySession


def get_owned_module_or_404(module_id):
    module = Module.query.get_or_404(module_id)
    if module.user_id != current_user.id:
        abort(404)
    return module


def get_owned_task_or_404(task_id):
    task = Task.query.get_or_404(task_id)
    if task.module.user_id != current_user.id:
        abort(404)
    return task


def get_owned_note_or_404(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(404)
    return note


def get_owned_study_session_or_404(session_id):
    study_session = StudySession.query.get_or_404(session_id)
    if study_session.user_id != current_user.id:
        abort(404)
    return study_session
