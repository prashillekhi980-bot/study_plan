import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    """Base configuration. Values are read from environment variables so
    secrets never live in source control (see .env.example). Only
    non-secret values get a hardcoded fallback; the password never does."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # MySQL/MariaDB connection, built from discrete env vars so credentials
    # never need to be committed to git.
    DB_USER = os.environ.get("DB_USER", "planner_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME", "study_planner")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional stretch feature (note summariser / chatbot). Left unset by
    # default; the AI recommendation engine does not depend on this.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
