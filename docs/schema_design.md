# Database Schema Design — AI-Based Personalised Study Planner

Matches proposal deliverables: users, modules, tasks (with deadline, priority,
estimated hours), study sessions/timetable, and support for the "struggling
topics" and optional note-summariser features.

## Entities

### 1. `users`
| Field | Type | Notes |
|---|---|---|
| id | INT, PK, AUTO_INCREMENT | |
| name | VARCHAR(100) | |
| email | VARCHAR(150), UNIQUE, NOT NULL | login identifier |
| password_hash | VARCHAR(255), NOT NULL | bcrypt hash, never plaintext |
| daily_study_hours | FLOAT, DEFAULT 2.0 | hours/day the student can study — feeds the timetable generator |
| created_at | DATETIME | |

### 2. `modules`
| Field | Type | Notes |
|---|---|---|
| id | INT, PK, AUTO_INCREMENT | |
| user_id | INT, FK → users.id | |
| name | VARCHAR(120), NOT NULL | e.g. "Software Development" |
| description | TEXT, NULLABLE | |
| created_at | DATETIME | |

### 3. `tasks`
| Field | Type | Notes |
|---|---|---|
| id | INT, PK, AUTO_INCREMENT | |
| module_id | INT, FK → modules.id | |
| title | VARCHAR(150), NOT NULL | coursework/task title |
| description | TEXT, NULLABLE | |
| due_date | DATE, NOT NULL | |
| priority | ENUM('low','medium','high'), DEFAULT 'medium' | |
| difficulty | INT (1–5), DEFAULT 3 | self-rated |
| estimated_hours | FLOAT, NOT NULL | total study hours needed |
| hours_completed | FLOAT, DEFAULT 0 | drives "progress" scoring factor |
| is_struggling | BOOLEAN, DEFAULT FALSE | proposal: "topics they are struggling with" |
| status | ENUM('not_started','in_progress','completed'), DEFAULT 'not_started' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 4. `study_sessions` (generated timetable entries)
| Field | Type | Notes |
|---|---|---|
| id | INT, PK, AUTO_INCREMENT | |
| task_id | INT, FK → tasks.id | |
| user_id | INT, FK → users.id | denormalized for fast per-user timetable queries |
| scheduled_date | DATE, NOT NULL | which study day this block falls on |
| allocated_hours | FLOAT, NOT NULL | hours assigned to the task on that day |
| is_completed | BOOLEAN, DEFAULT FALSE | |
| created_at | DATETIME | |

### 5. `notes` (optional — supports the note-summariser/chatbot stretch goal)
| Field | Type | Notes |
|---|---|---|
| id | INT, PK, AUTO_INCREMENT | |
| task_id | INT, FK → tasks.id, NULLABLE | |
| user_id | INT, FK → users.id | |
| content | TEXT | raw notes |
| summary | TEXT, NULLABLE | AI-generated summary (only sent to OpenAI API with consent, per ethics section) |
| created_at | DATETIME | |

## Relationships
- `users` 1—N `modules`
- `modules` 1—N `tasks`
- `tasks` 1—N `study_sessions`
- `users` 1—N `study_sessions` (denormalized)
- `users`/`tasks` 1—N `notes`

## Design rationale
- **hours_completed vs. a single progress %** — storing raw completed hours (rather than just a percent) lets both the progress bar *and* the recommendation engine's "unfinished progress" scoring factor derive from the same source of truth, and survives estimated_hours being edited later.
- **is_struggling flag** — directly satisfies the proposal's mention of students flagging "topics they are struggling with," and can be folded into the recommendation scoring as a priority booster.
- **study_sessions separate from tasks** — a single task can span multiple study days (e.g. a 6-hour task split across 3 days), so sessions need their own table rather than a single scheduled-date column on tasks.
- **notes table isolated and nullable** — keeps the optional chatbot/summariser feature fully decoupled; the core app functions with this table empty/unused, matching the proposal's note that the OpenAI-dependent feature "is not necessary for the AI recommendation system core to function."
