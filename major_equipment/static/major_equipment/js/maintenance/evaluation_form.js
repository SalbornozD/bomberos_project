document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll('input[name="decision"]');
    const successOnly = document.getElementById("success-only");
    const rejectOnly = document.getElementById("reject-only");
    const guardarBtn = document.getElementById("guardar-btn");

    radios.forEach(radio => {
        radio.addEventListener("change", function () {
            if (this.checked) {
                guardarBtn.classList.remove("no-display");

                if (this.id === "btnradio1") {
                    successOnly.classList.add("no-display");
                    rejectOnly.classList.remove("no-display");
                } else if (this.id === "btnradio2") {
                    successOnly.classList.remove("no-display");
                    rejectOnly.classList.add("no-display");
                }
            }
        });
    });
});
