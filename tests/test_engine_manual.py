"""Manual sanity check for the scoring engine using plain objects (no DB
needed) — confirms the math behaves as intended before wiring it into
routes. Run with: python3 tests/test_engine_manual.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from types import SimpleNamespace
from app.recommendations.engine import score_task, rank_tasks

TODAY = date(2026, 9, 23)


def make_task(title, days_until_due, priority, difficulty, estimated_hours,
              hours_completed=0, is_struggling=False, status="not_started"):
    t = SimpleNamespace()
    t.title = title
    t.due_date = TODAY + timedelta(days=days_until_due)
    t.priority = priority
    t.difficulty = difficulty
    t.estimated_hours = estimated_hours
    t.hours_completed = hours_completed
    t.is_struggling = is_struggling
    t.status = status
    t.progress_percent = min(round((hours_completed / estimated_hours) * 100), 100) if estimated_hours else 0
    return t


tasks = [
    make_task("Overdue high-priority struggling task", days_until_due=-1,
              priority="high", difficulty=5, estimated_hours=8, hours_completed=1, is_struggling=True),
    make_task("Due in 20 days, low priority, barely started", days_until_due=20,
              priority="low", difficulty=1, estimated_hours=2),
    make_task("Due in 3 days, medium priority, half done", days_until_due=3,
              priority="medium", difficulty=3, estimated_hours=6, hours_completed=3),
    make_task("Already completed (should be excluded)", days_until_due=1,
              priority="high", difficulty=5, estimated_hours=5, hours_completed=5, status="completed"),
]

print("=== Individual scores ===")
for t in tasks:
    s, b = score_task(t, today=TODAY)
    print(f"{t.title:55s} score={s:5.2f}  breakdown={b}")

print("\n=== Ranked (excludes completed) ===")
ranked = rank_tasks(tasks, today=TODAY)
for i, r in enumerate(ranked, 1):
    print(f"#{i} {r['task'].title:55s} score={r['score']}")

assert ranked[0]["task"].title.startswith("Overdue"), "Overdue struggling task should rank #1"
assert all(r["task"].status != "completed" for r in ranked), "Completed tasks must be excluded"
assert len(ranked) == 3, "Should rank exactly 3 non-completed tasks"
print("\nAll assertions passed.")
