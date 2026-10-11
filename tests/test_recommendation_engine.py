"""Rule-based scoring engine (app/recommendations/engine.py) — pure
functions, no DB or app context needed."""
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
    t.progress_percent = (
        min(round((hours_completed / estimated_hours) * 100), 100) if estimated_hours else 0
    )
    return t


def test_overdue_task_scores_maximum_urgency():
    overdue = make_task("Overdue", days_until_due=-3, priority="medium",
                         difficulty=3, estimated_hours=4)
    far_off = make_task("Far off", days_until_due=30, priority="medium",
                         difficulty=3, estimated_hours=4)
    overdue_score, _ = score_task(overdue, today=TODAY)
    far_off_score, _ = score_task(far_off, today=TODAY)
    assert overdue_score > far_off_score


def test_higher_priority_scores_higher_all_else_equal():
    low = make_task("Low", days_until_due=10, priority="low", difficulty=3, estimated_hours=4)
    high = make_task("High", days_until_due=10, priority="high", difficulty=3, estimated_hours=4)
    assert score_task(high, today=TODAY)[0] > score_task(low, today=TODAY)[0]


def test_struggling_flag_adds_a_boost():
    plain = make_task("Plain", days_until_due=10, priority="medium", difficulty=3, estimated_hours=4)
    struggling = make_task("Struggling", days_until_due=10, priority="medium",
                            difficulty=3, estimated_hours=4, is_struggling=True)
    assert score_task(struggling, today=TODAY)[0] > score_task(plain, today=TODAY)[0]


def test_nearly_finished_task_scores_lower_than_barely_started():
    barely_started = make_task("Barely started", days_until_due=10, priority="medium",
                                difficulty=3, estimated_hours=10, hours_completed=1)
    nearly_done = make_task("Nearly done", days_until_due=10, priority="medium",
                             difficulty=3, estimated_hours=10, hours_completed=9)
    assert score_task(barely_started, today=TODAY)[0] > score_task(nearly_done, today=TODAY)[0]


def test_rank_tasks_excludes_completed_and_sorts_descending():
    tasks = [
        make_task("Overdue high struggling", days_until_due=-1, priority="high",
                  difficulty=5, estimated_hours=8, hours_completed=1, is_struggling=True),
        make_task("Due far, low priority", days_until_due=20, priority="low",
                  difficulty=1, estimated_hours=2),
        make_task("Due soon, half done", days_until_due=3, priority="medium",
                  difficulty=3, estimated_hours=6, hours_completed=3),
        make_task("Already completed", days_until_due=1, priority="high",
                  difficulty=5, estimated_hours=5, hours_completed=5, status="completed"),
    ]

    ranked = rank_tasks(tasks, today=TODAY)

    assert len(ranked) == 3
    assert all(r["task"].status != "completed" for r in ranked)
    assert ranked[0]["task"].title == "Overdue high struggling"
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_tasks_handles_empty_list():
    assert rank_tasks([], today=TODAY) == []
