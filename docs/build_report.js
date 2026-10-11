const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageBreak, TableOfContents, LevelFormat, ExternalHyperlink,
  Header, Footer, PageNumber, NumberFormat, VerticalAlign
} = require("docx");

// ---------- helpers ----------
const FONT = "Calibri";
const GREY = "666666";
const BLUE = "2E5496";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 200 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 150 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}
function pRuns(runs, opts = {}) {
  return new Paragraph({ spacing: { after: 160, line: 276 }, children: runs, ...opts });
}
function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "main-bullets", level },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [new TextRun({ text, italics: true, size: 20, color: GREY, font: FONT })],
  });
}
function image(path, width, height) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    children: [new ImageRun({ type: "png", data, transformation: { width, height } })],
  });
}
function codeBlock(lines) {
  return new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
    },
    spacing: { after: 200 },
    children: lines.flatMap((line, i) => {
      const run = new TextRun({ text: line || " ", font: "Consolas", size: 18 });
      return i === 0 ? [run] : [new TextRun({ break: 1 }), run];
    }),
  });
}
function cell(text, opts = {}) {
  const { bold = false, width = 2000, shading = null, align = AlignmentType.LEFT } = opts;
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shading ? { type: ShadingType.CLEAR, fill: shading } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold, size: 20, font: FONT })],
    })],
  });
}
function table(headerRow, rows, widths) {
  const totalWidth = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headerRow.map((t, i) => cell(t, { bold: true, width: widths[i], shading: "4472C4" === "" ? null : "D9E2F3" })),
      }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) => cell(String(t), { width: widths[i] })) })),
    ],
  });
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }

// ---------- image sizing (pre-computed from actual file dimensions) ----------
const IMG = {
  erd: [550, 275],
  wireframeDash: [550, 285],
  dashRec: [500, 391],
  timetable: [500, 391],
  tasksShot: [520, 366],
  finalJourney: [500, 391],
};

const doc = new Document({
  numbering: {
    config: [{
      reference: "main-bullets",
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ],
    }],
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 } }, // A4
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "StudyPal — Final Project Report", size: 16, color: GREY, font: FONT })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 16, color: GREY, font: FONT }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: FONT }),
          ],
        })],
      }),
    },
    children: [
      // ===================== TITLE PAGE =====================
      new Paragraph({ spacing: { before: 1600 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "AI-Based Personalised Study Planner", bold: true, size: 44, font: FONT, color: BLUE })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 400 },
        children: [new TextRun({ text: "for University Students (“StudyPal”)", bold: true, size: 32, font: FONT, color: BLUE })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 800 },
        children: [new TextRun({ text: "Final Project Report", size: 28, font: FONT, italics: true })],
      }),
      table(
        ["Field", "Detail"],
        [
          ["Candidate Number", "0415915"],
          ["Student", "Subham Chaudhary"],
          ["Supervisor", "Prof. Paul Sant"],
          ["Programme", "MSc Project in Computer Science"],
          ["Project Topics", "Artificial Intelligence, Web Development, Database Systems, Educational Technology, Scheduling Algorithms"],
          ["Report Date", "September 2026"],
        ],
        [3200, 6300]
      ),
      pageBreak(),

      // ===================== ABSTRACT =====================
      h1("Abstract"),
      p("University students routinely juggle multiple modules, each with its own coursework deadlines, difficulty levels, and estimated workloads. Prior research and common experience both point to two recurring failure modes: studying in a suboptimal order (tackling whatever feels easiest rather than what is most urgent or important) and procrastination that leads to last-minute cramming. StudyPal is a full-stack web application designed to address both problems directly."),
      p("The system lets a student register, organise their studies into modules, and record coursework tasks with a due date, priority, estimated difficulty, and estimated hours required. From this data, StudyPal produces two AI-assisted outputs: a ranked “what to study next” recommendation, generated by a transparent, rule-based scoring engine that weighs deadline urgency, difficulty, unfinished progress, stated priority, and self-reported struggling topics; and an automatically generated study timetable that allocates each task's remaining hours across the days available before its deadline, respecting the student's own stated daily study capacity."),
      p("The application was built with Python (Flask) on the backend, MySQL/MariaDB for persistence, and server-rendered HTML/CSS/JavaScript on the frontend, containerised with Docker for portable deployment. An optional note-summariser feature was also implemented, using an offline rule-based text summarizer by default and an explicitly consent-gated OpenAI API integration as a stretch enhancement — in line with the project's data-minimisation and informed-consent commitments."),
      p("The system was tested at every development milestone against a live database rather than with mocks: automated end-to-end tests cover authentication, authorisation boundaries between users, full CRUD lifecycles, the correctness of the recommendation engine's ranking on known synthetic cases, and the timetable generator's capacity constraints. This report documents the requirements, design, implementation, testing methodology and results, data-privacy and ethical considerations, and the limitations and future work that remain."),
      pageBreak(),

      // ===================== TABLE OF CONTENTS =====================
      h1("Table of Contents"),
      new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
      pageBreak(),

      // ===================== 1. INTRODUCTION =====================
      h1("1. Introduction"),
      h2("1.1 Background and Motivation"),
      p("Time management and study planning are persistent challenges for university students, who must balance multiple modules, competing deadlines, and varying levels of difficulty across coursework. Poor time management and last-minute cramming are widely reported to increase student stress and reduce academic performance (ResearchGate, 2025). For students who also work part-time to support themselves financially, the cost of poor time management is not only academic but economic — time lost to inefficient studying is time that cannot be spent earning."),
      p("Existing calendar and to-do-list tools let students record deadlines, but they do not tell a student what to actually do with their limited study time on a given day, nor do they adapt to a task's difficulty or how much progress has already been made on it. StudyPal was conceived to fill that specific gap: not a calendar, but a prioritisation engine."),
      h2("1.2 Problem Statement"),
      p("Students need a tool that: (1) centralises coursework across all of their modules in one place; (2) tells them, at any given moment, what they should study next, based on more than just a due date; and (3) turns that prioritisation into a concrete daily study plan rather than leaving the student to work it out manually."),
      h2("1.3 Aims and Objectives"),
      p("The project's objectives, taken directly from the original project proposal, were to deliver:"),
      bullet("A fully functional study planner web application with user authentication."),
      bullet("The ability to add, edit and delete modules (e.g. Software Development, AI, Web Technologies)."),
      bullet("Coursework tasks with a title, due date, priority, and estimated study hours."),
      bullet("A study timetable generator that automatically allocates tasks to study days."),
      bullet("Progress tracking, so a student can mark tasks complete and see overall progress."),
      bullet("A rule-based AI recommendation system for “what to study next”, based on a scoring model (urgency, difficulty, unfinished progress, priority)."),
      bullet("(Optional) A note summariser / study-aid feature."),
      bullet("A database holding users, modules, tasks, deadlines and study sessions."),
      bullet("This final report, covering design, implementation, testing, evaluation, ethics and limitations."),
      h2("1.4 Report Structure"),
      p("Section 2 sets out the functional and non-functional requirements. Section 3 covers system design, including the database schema, UI wireframes, and the design of the recommendation and timetabling algorithms. Section 4 describes the implementation. Section 5 presents the testing methodology and results. Section 6 addresses data privacy and ethics. Section 7 discusses limitations and future work, and Section 8 concludes."),
      pageBreak(),

      // ===================== 2. REQUIREMENTS =====================
      h1("2. Requirements"),
      h2("2.1 Functional Requirements"),
      table(
        ["ID", "Requirement"],
        [
          ["FR1", "Users can register and log in; passwords are never stored in plaintext."],
          ["FR2", "Users can create, edit and delete modules."],
          ["FR3", "Users can create, edit and delete tasks within a module, each with a due date, priority, difficulty, estimated hours, and an optional “struggling with this topic” flag."],
          ["FR4", "Users can log partial study hours against a task or mark it fully complete."],
          ["FR5", "The system automatically generates a ranked “what to study next” recommendation from a transparent scoring model."],
          ["FR6", "The system automatically generates a study timetable, allocating remaining task hours across available study days."],
          ["FR7", "The dashboard displays overall and per-module progress, overdue tasks, and upcoming deadlines."],
          ["FR8", "(Optional) Users can attach free-text notes to a task and request a summary of them."],
        ],
        [1200, 8300]
      ),
      h2("2.2 Non-Functional Requirements"),
      table(
        ["ID", "Requirement"],
        [
          ["NFR1", "Security: passwords hashed with bcrypt; every module/task action is scoped to its owning user and returns 404 (not merely hidden) if another user attempts access."],
          ["NFR2", "Privacy: no data is shared with third parties, with one explicit, consent-gated exception (the optional OpenAI summarisation call)."],
          ["NFR3", "Usability: a clean, uncluttered dashboard; consistent navigation across all pages; basic mobile responsiveness."],
          ["NFR4", "Portability: the application must be deployable via Docker/Docker Compose without manual environment setup."],
          ["NFR5", "Maintainability: the codebase is organised into Flask blueprints by feature area, with a documented database schema."],
        ],
        [1200, 8300]
      ),
      h2("2.3 Data Requirements"),
      p("The system must persist: user accounts; modules (owned by a user); tasks (belonging to a module, carrying due date, priority, difficulty, estimated/completed hours, and a struggling flag); generated study sessions (the timetable, linking a task to a scheduled date and an allocated number of hours); and, optionally, free-text notes and their summaries. Full schema details are given in Section 3.3."),
      pageBreak(),

      // ===================== 3. SYSTEM DESIGN =====================
      h1("3. System Design"),
      h2("3.1 Development Methodology"),
      p("The project followed an Agile, iterative methodology (Atlassian, 2024), structured as six phases: (1) research and requirements gathering; (2) database schema design and wireframing; (3) core full-stack development — authentication, module and task management; (4) the AI recommendation engine and timetable generator; (5) testing and evaluation; and (6) the optional advanced-AI note summariser. Each phase was completed, tested against a live database, and committed to version control before the next began, so that at every point in development the application was in a working state."),
      h2("3.2 System Architecture"),
      p("The backend is a Python Flask application built with the application-factory pattern and organised into feature-based blueprints — auth, modules, tasks, timetable, recommendations, and notes — each owning its own routes and, where relevant, templates. This keeps each feature area independently testable and avoids a single monolithic routes file. SQLAlchemy provides the object-relational mapping layer over a MySQL/MariaDB database, with Flask-Login managing session-based authentication and Flask-Bcrypt handling password hashing."),
      p("A student's request flows: browser → Flask route (blueprint) → SQLAlchemy model / business-logic module (e.g. the scoring engine or timetable generator) → MySQL, with the rendered Jinja2 template returned to the browser. The recommendation engine and timetable generator are deliberately implemented as plain Python modules independent of Flask, so they can be unit-tested with synthetic data with no web server or database required (see Section 5.3)."),
      h2("3.3 Database Design"),
      p("Five entities were identified: users, modules, tasks, study_sessions (the generated timetable) and an optional notes table. The full rationale for each design decision is documented in the project's schema_design.md; the key decisions are summarised here."),
      bullet("hours_completed is stored as a raw value (not just a percentage) on each task, so both the progress bar and the recommendation engine's “unfinished progress” scoring factor derive from the same source of truth, and remain correct if estimated_hours is later edited."),
      bullet("is_struggling is a boolean flag on each task, directly satisfying the proposal's requirement that students can flag “topics they are struggling with”, and is folded into the recommendation score as a boost."),
      bullet("study_sessions is a separate table from tasks, because a single task's remaining hours are frequently split across multiple study days by the timetable generator."),
      bullet("The optional notes table is fully decoupled from the rest of the schema (nullable foreign key to tasks) so the core application functions identically whether or not the note-summariser feature is used."),
      image("erd.png", ...IMG.erd),
      caption("Figure 1. Entity-relationship diagram for the StudyPal database."),
      h2("3.4 User Interface Design"),
      p("Low-fidelity wireframes were produced before implementation for the four core screens: login/registration, the main dashboard, module and task management, and the auto-generated timetable. These established the information hierarchy — in particular, that the “what to study next” recommendation should be the first thing a returning student sees on the dashboard, ahead of raw task lists."),
      image("wireframe_02_dashboard.png", ...IMG.wireframeDash),
      caption("Figure 2. Original dashboard wireframe, showing the recommendation panel as the primary focus."),
      h2("3.5 Recommendation Engine Design"),
      p("The scoring model follows the proposal's specification directly: a weighted combination of deadline urgency, task difficulty, unfinished progress, and stated priority, with an additional boost for tasks the student has flagged as a struggling topic. The weights were chosen by design reasoning (an explicit, stated simplification — see Section 7) so that deadline urgency dominates, difficulty and progress carry moderate weight, and priority and the struggling flag act as smaller tie-breakers:"),
      table(
        ["Factor", "Weight", "Definition"],
        [
          ["Urgency", "0.35", "1.0 if overdue, decaying linearly to 0 at 14+ days before the deadline"],
          ["Unfinished progress", "0.25", "1 − (hours completed ÷ estimated hours)"],
          ["Difficulty", "0.20", "Self-rated 1–5, normalised to 0–1"],
          ["Priority", "0.15", "Low = 0.33, Medium = 0.67, High = 1.0"],
          ["Struggling flag", "0.05", "1.0 if flagged, else 0"],
        ],
        [2400, 1400, 5700]
      ),
      p("The final score (0–10) is the weighted sum multiplied by 10. This design deliberately starts rule-based, as the original proposal specifies, with the scoring function isolated in its own module precisely so that it could later be replaced by a learned model (e.g. via scikit-learn, as identified as a resource in the proposal) without changing any caller."),
      h2("3.6 Timetable Generation Algorithm Design"),
      p("The timetable generator uses a greedy allocation strategy: incomplete tasks are visited in recommendation-score order (most urgent/important first), and each task's remaining hours are packed into the earliest available days that still have spare capacity, up to the student's self-reported daily_study_hours limit. Rather than silently failing when a task cannot be fully scheduled before its deadline, the algorithm continues allocating into the days immediately following the deadline and reports the task as “at risk”, so the student is warned rather than misled by an incomplete plan that looks complete."),
      pageBreak(),

      // ===================== 4. IMPLEMENTATION =====================
      h1("4. Implementation"),
      h2("4.1 Technology Stack"),
      p("A conventional full-stack architecture was chosen (Sprintzeal, 2025), balancing rapid development with the AI/ML resources named in the proposal:"),
      table(
        ["Layer", "Technology", "Rationale"],
        [
          ["Backend", "Python 3.11, Flask", "Lightweight, explicit routing, large ecosystem; matches the proposal's named resources"],
          ["ORM / Database", "SQLAlchemy, MySQL/MariaDB", "Relational integrity for foreign keys (user → module → task → session); SQLAlchemy chosen partly because it also integrates cleanly with scikit-learn for a future ML upgrade path"],
          ["Auth", "Flask-Login, Flask-Bcrypt", "Session-based auth with industry-standard adaptive password hashing"],
          ["Frontend", "Jinja2, HTML/CSS/JavaScript", "Server-rendered pages, no build step, fast iteration"],
          ["Containerisation", "Docker, Docker Compose", "Reproducible environment: app + database start together with one command"],
          ["Optional AI", "OpenAI API (consent-gated)", "Higher-quality note summarisation when explicitly opted into"],
        ],
        [1800, 2600, 5100]
      ),
      h2("4.2 Project Structure"),
      p("The codebase is organised by feature, not by file type:"),
      codeBlock([
        "app/",
        "  auth/            registration, login, logout",
        "  modules/         module CRUD",
        "  tasks/           task CRUD, progress tracking",
        "  timetable/       timetable generator + view",
        "  recommendations/ scoring engine + dashboard",
        "  notes/           optional note summariser",
        "  models.py        SQLAlchemy models",
        "  config.py        environment-based configuration",
        "  templates/, static/",
        "docs/              schema design, ERD, wireframes, test plan",
        "tests/             standalone engine tests",
        "Dockerfile, docker-compose.yml, wait_for_db.py",
      ]),
      h2("4.3 Authentication and Authorisation"),
      p("Passwords are hashed with bcrypt (via Flask-Bcrypt) before storage; plaintext is never written to the database, which was directly verified during testing by inspecting the stored value. Every module and task route enforces ownership: a helper checks that the requested record's owning user matches the currently logged-in user, and returns HTTP 404 — not merely a hidden UI element — if not. This was verified with a live cross-account test (Section 5.2)."),
      h2("4.4 Module and Task Management"),
      p("Full CRUD is implemented for both modules and tasks. Progress tracking is handled by two actions: logging a partial number of hours against a task (which updates its status to “in progress” once any hours are logged, and to “completed” once hours_completed reaches estimated_hours), or marking a task fully complete in one action. A computed progress_percent property on both Task and Module drives the visual progress bars shown throughout the UI."),
      h2("4.5 Recommendation Engine Implementation"),
      p("The scoring engine (app/recommendations/engine.py) is a small, dependency-free module implementing the design in Section 3.5:"),
      codeBlock([
        "def score_task(task, today=None):",
        "    factors = {",
        "        \"urgency\": _urgency_score(task, today),",
        "        \"difficulty\": task.difficulty / 5.0,",
        "        \"progress\": 1 - (task.progress_percent / 100.0),",
        "        \"priority\": PRIORITY_SCORES[task.priority],",
        "        \"struggling\": 1.0 if task.is_struggling else 0.0,",
        "    }",
        "    weighted_sum = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)",
        "    return round(weighted_sum * 10, 2), factors",
      ]),
      p("The dashboard displays the top three ranked recommendations along with a visible breakdown of each contributing factor, so a student can see why a task was recommended rather than receiving an opaque score."),
      h2("4.6 Timetable Generator Implementation"),
      p("The generator (app/timetable/generator.py) clears the student's existing timetable and rebuilds it from scratch on each regeneration, iterating ranked tasks and packing hours into a per-day capacity map. Tasks that cannot be fully scheduled before their deadline given the student's daily hour limit are collected and surfaced to the UI as an explicit warning, rather than being silently dropped."),
      h2("4.7 Optional Note Summariser"),
      p("The optional Phase 6 feature was implemented with two tiers, exactly as the proposal frames it (“this feature can start off with a set of predefined rules”): a default, fully offline extractive summarizer using word-frequency sentence scoring (a classical technique in the tradition of Luhn's automatic abstracting method — Luhn, 1958), which requires no API key and sends no data anywhere; and an optional OpenAI-powered summary, used only when an API key is configured on the server AND the student explicitly checks a consent box on that specific request. If the OpenAI call fails for any reason, the system falls back to the offline summary rather than erroring."),
      h2("4.8 Containerisation"),
      p("A Dockerfile and docker-compose.yml were written to run the Flask application alongside a MariaDB container, with the database schema applied automatically on first start and a wait_for_db.py startup script that retries the database connection so the stack can be brought up from a completely cold start with a single docker compose up --build command. Note: due to network restrictions in the development sandbox used to build this project, the final container build could not be executed in that environment; the compose configuration was validated statically (docker compose config) and is intended to be verified on a machine with unrestricted internet access before relying on it for submission or demonstration."),
      h2("4.9 Working Application"),
      image("app_dashboard_recommendations.png", ...IMG.dashRec),
      caption("Figure 3. Dashboard showing ranked recommendations with score breakdowns."),
      image("app_timetable.png", ...IMG.timetable),
      caption("Figure 4. Auto-generated study timetable, grouped by day."),
      image("app_tasks.png", ...IMG.tasksShot),
      caption("Figure 5. Task management view, showing priority, difficulty, and progress."),
      pageBreak(),

      // ===================== 5. TESTING & EVALUATION =====================
      h1("5. Testing and Evaluation"),
      p("Testing followed the proposal's Phase 5 plan: functional testing of the full program, usability testing with a small group of students, and testing of the AI recommendations for accuracy and usefulness. Full detail is in the project's test_plan.md; results are summarised here."),
      h2("5.1 Functional Testing"),
      p("Testing was carried out continuously against a live MySQL database (not mocked) at every development milestone, using a combination of direct HTTP requests, database queries to confirm the resulting state, and a Playwright browser-automation script for full user-journey verification."),
      table(
        ["Area", "Result"],
        [
          ["Registration / login / logout", "Pass — bcrypt hash confirmed in the database, not plaintext"],
          ["Cross-user authorisation", "Pass — a second account receives HTTP 404 attempting to access another user's module or task"],
          ["Module CRUD", "Pass — including cascade delete to child tasks and study sessions"],
          ["Task CRUD and progress tracking", "Pass — status transitions (not started → in progress → completed) confirmed"],
          ["Dashboard statistics", "Pass — all figures cross-checked against direct database queries"],
          ["Recommendation ranking", "Pass — see Section 5.3"],
          ["Timetable generation", "Pass — see Section 5.4"],
          ["Note summariser", "Pass — see Section 5.5"],
          ["Full user journey (10-step automated walkthrough)", "Pass — all steps"],
        ],
        [3200, 6300]
      ),
      h2("5.2 Recommendation Engine Accuracy Testing"),
      p("The scoring engine was tested with synthetic tasks constructed to have known, unambiguous expected orderings:"),
      table(
        ["Scenario", "Score", "Rank"],
        [
          ["Overdue, high priority, difficulty 5, struggling", "9.7 / 10", "1st"],
          ["Due in 3 days, medium priority, 50% progressed", "6.2 / 10", "2nd"],
          ["Due in 20 days, low priority, difficulty 1", "3.4 / 10", "3rd (last)"],
          ["Already completed", "—", "Excluded from ranking"],
        ],
        [4900, 1800, 2800]
      ),
      p("All four assertions passed, confirming the scoring mechanism behaves as the weighting design intends. This confirms correctness of the mechanism, not that the specific weights match every real student's intuitive prioritisation — that distinction, and its implications, is discussed in Section 7."),
      h2("5.3 Timetable Generator Testing"),
      p("Across a generated 7-block schedule, daily allocated hours never exceeded the student's configured daily capacity. The generator correctly identified and flagged, as “at risk”, both an already-overdue task and a task that could not be fully completed before its deadline given the available daily hours, while correctly leaving a comfortably-scheduled task unflagged."),
      h2("5.4 Note Summariser Testing"),
      p("The offline summarizer was tested against a six-sentence paragraph of realistic study notes on database normalisation; it correctly selected the two most content-dense sentences as a coherent two-sentence summary. The consent-gating logic was verified directly at the code level: with no API key configured, the system always uses the offline summarizer regardless of the consent flag; with a key configured but consent not given, no external call is made; and with both a key and consent, a failed API call (e.g. an invalid key) falls back to the offline summary rather than crashing or exposing an error to the user."),
      h2("5.5 Usability Testing"),
      p("A usability testing protocol was designed per the proposal's ethics commitments (informed participants, free to stop at any time): 4–6 fellow students would be asked to complete a set list of tasks — register, add a module, add tasks, review the recommendation, generate a timetable, mark a task complete — while thinking aloud, with completion, time-on-task, and a short subjective usefulness rating recorded for each step. This protocol (full detail in test_plan.md) is designed and ready to run, but had not been conducted with real student participants at the time of writing this report; running it, and incorporating the findings, is recommended before final submission."),
      h2("5.6 Summary of Known Limitations in Testing"),
      bullet("The OpenAI-powered summarisation path could not be tested against the live API (no API key was available in the development environment); its logic was verified up to the point of the external call, and its failure-handling path was verified directly."),
      bullet("The Docker deployment could not be built and run end-to-end in the development sandbox due to network policy restrictions; only static configuration validation was possible."),
      bullet("Usability testing with real students (Section 5.5) is designed but not yet executed."),
      pageBreak(),

      // ===================== 6. DATA PRIVACY AND ETHICS =====================
      h1("6. Data Privacy and Ethics"),
      p("The project's approach to data privacy and ethical conduct, as committed to in the original proposal, was implemented and verified as follows:"),
      table(
        ["Commitment (from proposal)", "Implementation status"],
        [
          ["Passwords stored hashed (bcrypt), never plaintext", "Implemented and verified — stored hash inspected directly in the database"],
          ["No data shared with third parties, except an optional, consent-gated OpenAI call for summarisation", "Implemented — the OpenAI path requires both a server-configured key AND explicit per-request student consent; verified no external call occurs otherwise"],
          ["Students informed in advance and able to object to the OpenAI feature", "Implemented in the UI — the consent checkbox is presented per note, with a plain-language explanation of what will be sent externally"],
          ["Not used for grading or academic assessment", "By design — the system has no grading, scoring-of-students, or academic-status functionality of any kind"],
          ["User testing conducted with informed, free-to-withdraw participants", "Protocol designed (Section 5.5); pending execution with real participants"],
          ["Data minimisation — only necessary fields are stored", "Implemented — the schema stores only the fields required to drive the scheduling and recommendation features (Section 3.3)"],
        ],
        [4200, 5300]
      ),
      pageBreak(),

      // ===================== 7. LIMITATIONS & FUTURE WORK =====================
      h1("7. Limitations and Future Work"),
      h2("7.1 Limitations"),
      bullet("The recommendation engine's weights (urgency 0.35, progress 0.25, difficulty 0.20, priority 0.15, struggling 0.05) were set by design reasoning, not learned from real usage data. This is an explicit, stated simplification consistent with the proposal's “starts rule-based” framing, not an oversight."),
      bullet("The system has no mechanism to learn from a student repeatedly ignoring its top recommendation; there is currently no feedback loop."),
      bullet("The timetable generator allocates purely against a flat daily-hours capacity and has no awareness of a student's actual calendar (lectures, work shifts, other commitments)."),
      bullet("Usability testing with real students has been designed but not yet executed (Section 5.5)."),
      bullet("The Docker deployment path is written and statically validated but not yet confirmed to build and run successfully end-to-end, due to sandbox network restrictions during development."),
      bullet("The optional OpenAI summarisation path has not been exercised against the live API."),
      h2("7.2 Future Work"),
      bullet("Replace or augment the rule-based scoring weights with a model trained on logged accept/ignore signals from real usage, as originally envisioned in the proposal (the codebase already isolates the scoring function to make this substitution straightforward, and SQLAlchemy was partly chosen for its compatibility with scikit-learn)."),
      bullet("Extend the timetable generator to import calendar data (e.g. via an iCal feed) so generated study blocks avoid known commitments."),
      bullet("Conduct the designed usability study with a real cohort of students and incorporate the findings into a second design iteration."),
      bullet("Verify and, if necessary, fix the Docker deployment on unrestricted infrastructure."),
      pageBreak(),

      // ===================== 8. CONCLUSION =====================
      h1("8. Conclusion"),
      p("This project set out to build an AI-assisted study planner that goes beyond a simple calendar, by prioritising a student's coursework and turning that prioritisation into a concrete daily study plan. Every core deliverable from the original proposal was implemented and tested against a live database: authentication, full module and task management, progress tracking, a rule-based recommendation engine, an automatic timetable generator, and the optional note-summariser stretch feature, delivered with an explicit, verified consent gate around its one external data dependency."),
      p("The system was built and verified incrementally, with each feature area tested end-to-end before the next was started, rather than assembled and tested only at the end. The honest gaps that remain — real-student usability testing, live verification of the Docker deployment, and live testing of the OpenAI summarisation path — are stated plainly in Section 7 rather than glossed over, and represent the clearest next steps for the project."),
      pageBreak(),

      // ===================== REFERENCES =====================
      h1("References"),
      p("Accenture, 2024. Cybersecurity consulting. [Online] Available at: https://www.accenture.com/gb-en/services/cybersecurity [Accessed 01 May 2026]."),
      p("Atlassian, 2024. Understanding the Agile methodology. [Online] Available at: https://www.atlassian.com/agile [Accessed 01 May 2026]."),
      p("GRC Solutions, 2023. A global leader in privacy guidance, audits, tools, training and software. [Online] Available at: https://grcsolutions.io/data-privacy/ [Accessed 01 May 2026]."),
      p("Luhn, H.P., 1958. The Automatic Creation of Literature Abstracts. IBM Journal of Research and Development, 2(2), pp.159–165."),
      p("OWASP, 2023. Password Storage Cheat Sheet. [Online] Available at: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html [Accessed 23 September 2026]."),
      p("Pallets Projects, 2024. Flask Documentation. [Online] Available at: https://flask.palletsprojects.com/ [Accessed 23 September 2026]."),
      p("ResearchGate, 2025. AI-Powered Smart Study Planner: Enhancing Personalized Learning Through Intelligent Scheduling. [Online] Available at: https://www.researchgate.net/publication/391661197 [Accessed 01 May 2026]."),
      p("Sprintzeal, 2025. What is Full Stack Development? Understanding the Basics and Beyond. [Online] Available at: https://www.sprintzeal.com/blog/full-stack-development [Accessed 01 May 2026]."),

      pageBreak(),
      h1("Appendix A: Full Automated Integration Test"),
      p("The following steps were executed as a single automated Playwright script against the live application and database, simulating a complete new-user journey. All steps passed."),
      bullet("1. Register a new account → redirected to login."),
      bullet("2. Log in → redirected to dashboard."),
      bullet("3. Top navigation renders with Dashboard / Modules / Timetable links."),
      bullet("4. Create a module (“Software Development”) → visible in the module list."),
      bullet("5. Add two tasks, one overdue/high-priority/struggling, one low-priority/future-dated → both visible."),
      bullet("6. Log partial hours on the overdue task → progress bar updates to the correct percentage."),
      bullet("7. Return to the dashboard → the overdue/struggling task is ranked as the #1 recommendation."),
      bullet("8. Generate a timetable → schedule renders, grouped by day."),
      bullet("9. Mark the second task complete → dashboard's completed-task count updates correctly."),
      bullet("10. Log out → redirected to login."),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("StudyPal_Final_Report.docx", buf);
  console.log("Report written: StudyPal_Final_Report.docx");
});
