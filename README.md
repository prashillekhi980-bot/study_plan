# StudyPal — AI-Based Personalised Study Planner

A full-stack web app that helps university students manage modules,
coursework deadlines, and study time, with a rule-based "what to study
next" recommendation engine and an auto-generated study timetable.

## Stack
- **Backend:** Python, Flask (application factory + blueprints)
- **Database:** MySQL/MariaDB via SQLAlchemy
- **Auth:** Flask-Login + Flask-Bcrypt (hashed passwords, never plaintext)
- **Frontend:** HTML/CSS/JS (server-rendered Jinja2 templates)

## Project layout
```
app/
  auth/            registration, login, logout
  modules/         module CRUD
  tasks/           task CRUD (coursework, deadlines, priority, difficulty)
  timetable/       auto-generated study schedule
  recommendations/ scoring engine + dashboard ("what to study next")
  templates/       Jinja2 templates
  static/          CSS/JS
  models.py        SQLAlchemy models (User, Module, Task, StudySession, Note)
  config.py        environment-based configuration
  extensions.py    shared Flask extension instances
docs/
  schema_design.md  entity/field rationale
  schema.sql        raw DDL
  erd.png           entity-relationship diagram
  wireframe_*.png   low-fi wireframes (login, dashboard, tasks, timetable)
```

## Setup

### Option A — Docker (recommended)
Requires Docker Desktop (or Docker Engine + Compose) installed and running.
```bash
docker compose up --build
```
This starts a MariaDB container (schema auto-applied from `docs/schema.sql`
on first run) and the Flask app, wired together — no local Python or MySQL
install needed. Visit http://localhost:5001. Data persists in a Docker
volume (`db_data`) across restarts; `docker compose down -v` wipes it.

To override the default dev credentials, create a `.env` file in the
project root (same keys as `.env.example`) before running `docker compose up`.

### Option B — Local Python + MySQL
```bash
cp .env.example .env        # then fill in DB credentials
pip install -r requirements.txt
mysql -u root -p < docs/schema.sql   # or let SQLAlchemy create tables
python run.py
```

## Development phases (see docs/schema_design.md for schema rationale)
1. Research & requirements, DB schema, wireframes — **done**
2. Auth + module/task CRUD — in progress
3. Recommendation scoring engine + timetable generator
4. Frontend polish + full integration
5. Testing (functional, usability, recommendation accuracy)
6. Optional: note summariser / chatbot; final report

## Data privacy
Passwords are hashed with bcrypt and never stored in plaintext. No data is
shared with third parties, except an optional, consent-gated OpenAI API
call for the note-summariser stretch feature — the core recommendation
engine does not depend on any external API
