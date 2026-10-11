// Live-ticking display for a running Start/Stop Session timer. The
// server is the source of truth (it stamps `started_at` when a session
// starts and computes the real elapsed time from started_at/ended_at
// when it's stopped) — this script only recomputes "now minus
// started_at" every second for display, purely client-side, so nothing
// here can drift the actual logged hours.
//
// Multiple `.session-timer` elements can be on the page at once (the nav
// banner plus the same session's row on a task list/detail page), all
// sharing the same data-started-at, so every one of them is ticked.
document.addEventListener("DOMContentLoaded", function () {
    var timers = document.querySelectorAll(".session-timer[data-started-at]");
    if (!timers.length) return;

    function pad(n) {
        return String(n).padStart(2, "0");
    }

    function tick() {
        timers.forEach(function (el) {
            var startedAt = new Date(el.getAttribute("data-started-at"));
            var diffSeconds = Math.max(0, Math.floor((Date.now() - startedAt.getTime()) / 1000));
            var hours = Math.floor(diffSeconds / 3600);
            var minutes = Math.floor((diffSeconds % 3600) / 60);
            var seconds = diffSeconds % 60;
            el.textContent = pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);
        });
    }

    tick();
    setInterval(tick, 1000);
});
