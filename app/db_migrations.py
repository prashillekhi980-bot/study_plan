"""Tiny, idempotent schema patcher.

This project has no migration framework (Alembic, etc.) — `db.create_all()`
only creates tables that don't exist yet, it never alters an existing
table's columns. That's fine as long as the schema never changes after a
database has been created, but the Start/Stop Session timer feature needs
two new nullable columns on `study_sessions` (`started_at`, `ended_at`)
that an already-running database won't have.

`ensure_schema_migrations()` checks for those columns and adds them with a
plain `ALTER TABLE` if missing, so it's safe to call on every app startup
— a fresh database (already created with the new columns via schema.sql
or db.create_all()) is a no-op, and an existing one is patched once. It's
called from wait_for_db.py (Docker's startup path) and from run.py (local
dev), so either path picks up the change automatically.
"""
from sqlalchemy import inspect, text


def ensure_schema_migrations(db):
    inspector = inspect(db.engine)
    if "study_sessions" not in inspector.get_table_names():
        return  # table doesn't exist yet — create_all() will make it with every column

    existing_columns = {c["name"] for c in inspector.get_columns("study_sessions")}
    with db.engine.begin() as conn:
        if "started_at" not in existing_columns:
            conn.execute(text("ALTER TABLE study_sessions ADD COLUMN started_at DATETIME NULL"))
        if "ended_at" not in existing_columns:
            conn.execute(text("ALTER TABLE study_sessions ADD COLUMN ended_at DATETIME NULL"))
