"""Rule-based "what to study next" scoring engine.

Implements Phase 4 of the proposal's methodology: a weighted scoring
function over deadline urgency, task difficulty, unfinished progress and
priority (plus a small boost for topics the student flagged as
struggling with). This starts rule-based, as the proposal allows, and is
structured so the weights (or the scoring function itself) could later be
swapped for a learned model without touching the callers.
"""
from datetime import date

# Weights sum to 1.0 so the final score is directly interpretable as a
# percentage-like 0-10 value. Tuned so an overdue, high-priority,
# barely-started task clearly outranks a low-priority task due next month.
WEIGHTS = {
    "urgency": 0.35,
    "difficulty": 0.20,
    "progress": 0.25,
    "priority": 0.15,
    "struggling": 0.05,
}

PRIORITY_SCORES = {"low": 1 / 3, "medium": 2 / 3, "high": 1.0}

# Urgency saturates at this many days out — a task due today scores 1.0,
# a task due in URGENCY_HORIZON_DAYS or more scores close to 0.
URGENCY_HORIZON_DAYS = 14


def _urgency_score(task, today):
    days_left = (task.due_date - today).days
    if days_left <= 0:
        return 1.0  # due today or overdue: maximum urgency
    return max(0.0, 1 - (days_left / URGENCY_HORIZON_DAYS))


def _difficulty_score(task):
    return task.difficulty / 5.0


def _progress_score(task):
    """Unfinished progress: a task that's barely started scores high,
    one that's nearly done scores low, so effort goes where it's needed."""
    return 1 - (task.progress_percent / 100.0)


def _priority_score(task):
    return PRIORITY_SCORES.get(task.priority, PRIORITY_SCORES["medium"])


def _struggling_score(task):
    return 1.0 if task.is_struggling else 0.0


def score_task(task, today=None):
    """Return (score_out_of_10, breakdown_dict) for a single task."""
    today = today or date.today()

    factors = {
        "urgency": _urgency_score(task, today),
        "difficulty": _difficulty_score(task),
        "progress": _progress_score(task),
        "priority": _priority_score(task),
        "struggling": _struggling_score(task),
    }

    weighted_sum = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(weighted_sum * 10, 2)

    breakdown = {k: round(v, 2) for k, v in factors.items()}
    breakdown["days_left"] = (task.due_date - today).days
    return score, breakdown


def explain(task, breakdown):
    """Turn a score breakdown into the plain-language reasons the proposal
    asks for (e.g. "deadline is close, difficulty is high, progress is
    low"), so a student sees why a task was recommended, not just a number."""
    reasons = []

    days_left = breakdown["days_left"]
    if days_left < 0:
        reasons.append("it's overdue")
    elif days_left == 0:
        reasons.append("it's due today")
    elif days_left <= 3:
        reasons.append("deadline is close")

    if task.difficulty >= 4:
        reasons.append("difficulty is high")

    if task.progress_percent < 25:
        reasons.append("progress is low")

    if task.priority == "high":
        reasons.append("priority is high")

    if task.is_struggling:
        reasons.append("you marked this topic as struggling")

    if not reasons:
        reasons.append("it's next in line based on your workload")

    return ", ".join(reasons)


def rank_tasks(tasks, today=None):
    """Rank a list of (incomplete) tasks by recommendation score, highest
    first. Returns a list of dicts: {task, score, breakdown, reason}."""
    today = today or date.today()
    ranked = []
    for task in tasks:
        if task.status == "completed":
            continue
        score, breakdown = score_task(task, today)
        reason = explain(task, breakdown)
        ranked.append({"task": task, "score": score, "breakdown": breakdown, "reason": reason})

    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked
