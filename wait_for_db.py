"""Wait for the MySQL container to accept connections, then ensure all
tables exist (via SQLAlchemy metadata — equivalent to running schema.sql,
since docker-compose already applies schema.sql once at DB init, but this
also lets the app boot standalone against ANY empty MySQL instance)."""
import time
import sys
from sqlalchemy.exc import OperationalError

from app import create_app
from app.extensions import db
from app.db_migrations import ensure_schema_migrations

MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2

app = create_app("development")

for attempt in range(1, MAX_RETRIES + 1):
    try:
        with app.app_context():
            db.session.execute(db.text("SELECT 1"))
            db.create_all()
            ensure_schema_migrations(db)
        print("Database is ready.")
        sys.exit(0)
    except OperationalError:
        print(f"Database not ready yet (attempt {attempt}/{MAX_RETRIES}), retrying...")
        time.sleep(RETRY_DELAY_SECONDS)

print("Could not connect to the database after multiple retries.")
sys.exit(1)
