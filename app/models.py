from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    daily_study_hours = db.Column(db.Float, nullable=False, default=2.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    modules = db.relationship(
        "Module", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    study_sessions = db.relationship(
        "StudySession", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    notes = db.relationship(
        "Note", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Module(db.Model):
    __tablename__ = "modules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship(
        "Task", backref="module", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def progress_percent(self):
        """Aggregate progress across all tasks in this module, weighted by
        estimated hours (so a big task's completion matters more than a
        tiny one's)."""
        total_estimated = sum(t.estimated_hours for t in self.tasks)
        if not total_estimated:
            return 0
        total_completed = sum(t.hours_completed for t in self.tasks)
        return min(round((total_completed / total_estimated) * 100), 100)

    @property
    def completed_task_count(self):
        return sum(1 for t in self.tasks if t.status == "completed")

    def __repr__(self):
        return f"<Module {self.name}>"


class Task(db.Model):
    __tablename__ = "tasks"

    PRIORITY_LEVELS = ("low", "medium", "high")
    STATUS_VALUES = ("not_started", "in_progress", "completed")

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.Enum(*PRIORITY_LEVELS, name="priority_enum"), default="medium")
    difficulty = db.Column(db.Integer, default=3)  # 1 (easy) - 5 (very hard)
    estimated_hours = db.Column(db.Float, nullable=False)
    hours_completed = db.Column(db.Float, default=0)
    is_struggling = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(*STATUS_VALUES, name="status_enum"), default="not_started")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    study_sessions = db.relationship(
        "StudySession", backref="task", lazy=True, cascade="all, delete-orphan"
    )
    notes = db.relationship("Note", backref="task", lazy=True)

    @property
    def remaining_hours(self):
        return max(self.estimated_hours - self.hours_completed, 0)

    @property
    def progress_percent(self):
        if not self.estimated_hours:
            return 0
        return min(round((self.hours_completed / self.estimated_hours) * 100), 100)

    def __repr__(self):
        return f"<Task {self.title}>"


class StudySession(db.Model):
    """A study block: either a *planned* block produced by the timetable
    generator (is_completed=False, started_at/ended_at both null), or a
    real recorded study session — either timed live (Start/Stop Session:
    started_at set when started, ended_at + allocated_hours filled in
    automatically when stopped) or logged in one shot (allocated_hours
    set directly, e.g. the remaining-hours top-up when a task is marked
    complete). is_completed=True marks it as something that actually
    happened, vs. a planned block that hasn't happened yet.
    """

    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    allocated_hours = db.Column(db.Float, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        """A live Start/Stop Session timer that's running right now."""
        return self.started_at is not None and self.ended_at is None

    def __repr__(self):
        return f"<StudySession task={self.task_id} date={self.scheduled_date}>"


class Note(db.Model):
    """Optional: backs the note-summariser / study-aid chatbot stretch goal."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Note {self.id}>"
