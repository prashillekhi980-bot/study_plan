// Replaces the native window.confirm() dialog with a themed modal for
// any destructive/session-ending action. An element opts in with
// data-confirm="<message>" — a <form> (e.g. delete) or an <a> (e.g.
// logout). The action only proceeds if the user clicks "Confirm".
document.addEventListener("DOMContentLoaded", function () {
    var overlay = document.getElementById("confirm-modal-overlay");
    if (!overlay) return; // page doesn't extend base.html's authenticated layout

    var messageEl = document.getElementById("confirm-modal-message");
    var confirmBtn = document.getElementById("confirm-modal-confirm");
    var cancelBtn = document.getElementById("confirm-modal-cancel");
    var pendingAction = null;
    var lastFocused = null;

    function openModal(message, onConfirm) {
        messageEl.textContent = message;
        pendingAction = onConfirm;
        lastFocused = document.activeElement;
        overlay.classList.add("is-open");
        confirmBtn.focus();
    }

    function closeModal() {
        overlay.classList.remove("is-open");
        pendingAction = null;
        if (lastFocused && typeof lastFocused.focus === "function") {
            lastFocused.focus();
        }
    }

    confirmBtn.addEventListener("click", function () {
        var action = pendingAction;
        closeModal();
        if (action) action();
    });

    cancelBtn.addEventListener("click", closeModal);

    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) closeModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("is-open")) {
            closeModal();
        }
    });

    // Delete forms etc: intercept submit, re-submit for real on confirm.
    // form.submit() (unlike a submit button click) does not re-fire the
    // "submit" event, so this can't loop.
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            openModal(form.getAttribute("data-confirm"), function () {
                form.submit();
            });
        });
    });

    // Logout etc: intercept click, navigate for real on confirm.
    document.querySelectorAll("a[data-confirm]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            openModal(link.getAttribute("data-confirm"), function () {
                window.location.href = link.href;
            });
        });
    });
});
