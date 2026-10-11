import os
from app import create_app
from app.extensions import db
from app.db_migrations import ensure_schema_migrations

app = create_app(os.environ.get("FLASK_ENV", "development"))

# Local dev (not going through Docker/wait_for_db.py) still needs any new
# columns patched onto an existing database — see app/db_migrations.py.
with app.app_context():
    ensure_schema_migrations(db)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
