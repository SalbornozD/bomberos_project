document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("login-modal");
    const btn = document.querySelector(".login-button");
    const closeBtn = document.getElementById("close-login-modal");

    btn.addEventListener("click", () => {
        modal.style.display = "flex";
    });

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    window.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });
});