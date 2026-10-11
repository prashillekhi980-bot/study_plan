from flask import Flask
from app.config import config_by_name
from app.extensions import db, bcrypt, login_manager


def create_app(config_name="development"):
    """Application factory. Keeps the app importable for tests without
    side effects, and lets config vary by environment (dev/test/prod)."""

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.modules.routes import modules_bp
    from app.tasks.routes import tasks_bp
    from app.timetable.routes import timetable_bp
    from app.recommendations.routes import recommendations_bp
    from app.notes.routes import notes_bp
    from app.settings.routes import settings_bp
    from app.onboarding.routes import onboarding_bp
    from app.progress.routes import progress_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(progress_bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("recommendations.dashboard"))
        return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_active_study_session():
        """Makes the current user's running Start/Stop Session timer (if
        any) available to every template, so base.html can show a live
        badge in the nav no matter which page the student is on."""
        from flask_login import current_user
        from app.tasks.routes import _get_active_session

        if current_user.is_authenticated:
            return {"active_study_session": _get_active_session()}
        return {"active_study_session": None}

    return app
