# StudyPal — Test Plan (Proposal Phase 5: Testing & Evaluation)

This covers the three testing activities named in the proposal: functional
testing of the full program, usability testing with a small group of
students, and testing of AI-generated recommendations for accuracy and
usefulness. It's written to be usable directly in the final report's
Testing/Evaluation section.

## 1. Functional testing

Approach: automated end-to-end tests against a live MySQL database (not
mocks), run at every development milestone rather than only at the end.

### 1.1 Automated test coverage (already executed — see commit history)

| Area | Test | Result |
|---|---|---|
| Auth | Register, login, logout; password stored as bcrypt hash, not plaintext | ✅ Pass |
| Auth | Second user cannot view/edit/delete a module or task they don't own (expect 404) | ✅ Pass |
| Module CRUD | Create, edit, delete; delete cascades to child tasks and study sessions | ✅ Pass |
| Task CRUD | Create/edit with all fields (title, due date, priority, difficulty, estimated hours, struggling flag); delete | ✅ Pass |
| Progress tracking | Logging partial hours updates status to in_progress; logging full hours (or "mark complete") sets status to completed | ✅ Pass |
| Dashboard | Stats (module count, completed/total tasks, overall %, overdue count) match direct DB queries | ✅ Pass |
| Recommendation engine | Ranking order matches expected priority for synthetic inputs (see §3) | ✅ Pass |
| Timetable generator | Daily allocations never exceed `daily_study_hours`; tasks that can't fit before their deadline are flagged "at risk" rather than silently dropped | ✅ Pass |
| Notes/summariser | Offline summarizer produces a shorter, coherent summary; OpenAI path is never called without both a configured key AND explicit per-request consent; API failure falls back to offline gracefully | ✅ Pass |
| Full user journey | Registration → module → tasks → recommendation → timetable → progress → logout, as one continuous flow | ✅ Pass (`docs/full_integration_test.py`) |

### 1.2 Manual functional checklist (for the report / a final pass before submission)

- [ ] Fresh install from `docker compose up --build` reaches a working login page
- [ ] Form validation: submitting empty/invalid fields (blank title, negative hours, out-of-range difficulty) shows a clear error and doesn't corrupt data
- [ ] Browser back/forward buttons after form submission don't cause duplicate records
- [ ] Session expiry / logout correctly blocks access to protected pages
- [ ] Mobile viewport (phone width) — nav and tables remain usable

## 2. Usability testing (small group of students)

Per the proposal's ethics section: "All user testing will be carried out
with test users informed as to what testing they will be carrying out and
test users given the opportunity to cease testing at any time without any
subsequent action taken."

### 2.1 Participants
- 4–6 fellow students (a small enough group to run and analyse manually,
  large enough to surface repeat patterns rather than one person's quirks).
- Recruited informally (classmates/coursemates); no compensation implied
  or required; participation is voluntary and can stop at any time.

### 2.2 Consent and briefing
- Each participant is told, before starting: what the app does, that
  their interactions are being observed for the study, that no personal
  data beyond what they choose to enter is retained beyond the test, and
  that they may stop at any point without needing to explain why.
- No screen recording without separate explicit consent; observation
  notes only, unless a participant opts into recording.

### 2.3 Tasks given to participants (a typical think-aloud session)
1. Register an account and log in.
2. Add a module for a real (or hypothetical) course you're taking.
3. Add two coursework tasks with different due dates and priorities.
4. Find out what the app recommends you study next, and say out loud
   whether that recommendation makes sense to you.
5. Generate a study timetable and give a first impression of it.
6. Mark a task as complete and check the dashboard updated.

### 2.4 Metrics collected
- **Task completion**: did they complete each step without help? (Y/N/with help)
- **Time on task** for steps 2–5 (rough, stopwatch-level, not lab-grade)
- **Errors/confusion points**: any UI element clicked in a way that
  clearly wasn't its intended use, or any point they got stuck
- **Subjective rating**: a short 5-point scale ("How useful did the
  recommendation feel?", "How clear was the dashboard?") — a lightweight
  stand-in for a full System Usability Scale, appropriate for this project's size
- **Open feedback**: one open question — "What would you change?"

### 2.5 What to do with the results
Findings get written up in the final report's Evaluation section as
qualitative themes (e.g. "3 of 5 participants didn't notice the
'struggling' checkbox on first use") plus the raw completion/time table —
not as a claim of statistical significance, which a sample this size
can't support.

## 3. AI recommendation accuracy & usefulness testing

Two levels, matching how the proposal frames "rule-based, could later
become ML": correctness of the mechanism, then perceived usefulness.

### 3.1 Correctness (automated, deterministic — already done)
Synthetic test cases with known expected orderings (see
`tests/test_engine_manual.py`), covering the individual scoring factors
and their interaction:

| Scenario | Expectation | Result |
|---|---|---|
| Overdue + high priority + difficult + struggling | Ranks #1 among all cases | ✅ 9.7/10, ranked #1 |
| Due in 20 days, low priority, easy | Ranks last | ✅ 3.4/10, ranked last |
| Due in 3 days, medium priority, half-progressed | Ranks between the two above | ✅ 6.2/10 |
| A completed task | Excluded from ranking entirely | ✅ Confirmed excluded |

This confirms the *mechanism* does what the weighting formula intends —
it does not, by itself, prove the weights are the "right" weights for
real students; that's what §3.2 is for.

### 3.2 Usefulness (qualitative, from the usability session in §2)
During the usability tasks, each participant sees their own top
recommendation and is asked directly: "Does this match what you'd
actually study next?" Disagreement is itself useful data — it's recorded
along with *why* they disagreed (e.g. "I'd do the easy one first to get
it out of the way"), which is exactly the kind of feedback that would
inform adjusting the scoring weights, or is worth including in the
report's Limitations section as an acknowledged simplification of how
real students actually prioritize (e.g. quick wins vs. hardest-first).

### 3.3 Known limitations to state explicitly in the report
- The scoring weights (urgency 0.35, progress 0.25, difficulty 0.20,
  priority 0.15, struggling 0.05) were set by design reasoning, not
  learned from data — an explicit, stated simplification consistent with
  the proposal's "starts rule-based" framing.
- The model has no way to learn from a student repeatedly ignoring its
  top recommendation; a v2 could log accept/ignore signals for a future
  ML-based version, as the proposal envisions.
- The timetable generator does not account for real-world scheduling
  conflicts (classes, other commitments) beyond the flat daily-hours
  capacity a student sets — a stated scope boundary, not a bug.
