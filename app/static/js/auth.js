// Show/hide toggle for password fields on the login and register forms.
// Each `.password-wrapper` (see templates/auth/_password_field.html) has
// its own independent toggle button, so on the register page the
// password and confirm-password fields can be revealed separately.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".password-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
            var wrapper = button.closest(".password-wrapper");
            var input = wrapper.querySelector("input");
            var eyeIcon = button.querySelector(".icon-eye");
            var eyeOffIcon = button.querySelector(".icon-eye-off");

            var willReveal = input.type === "password";
            input.type = willReveal ? "text" : "password";

            // Open-eye icon = "click to reveal" (shown while masked).
            // Slashed-eye icon = "click to hide" (shown while revealed).
            eyeIcon.classList.toggle("is-hidden", willReveal);
            eyeOffIcon.classList.toggle("is-hidden", !willReveal);
            button.setAttribute("aria-label", willReveal ? "Hide password" : "Show password");
            button.setAttribute("aria-pressed", String(willReveal));
        });
    });
});
