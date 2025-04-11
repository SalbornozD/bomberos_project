document.querySelectorAll('.report-problem-btn').forEach(button => {
    button.addEventListener('click', () => {
        const unitID = button.dataset.unitId;

        const modalBody = `
            <input type="hidden" value="${unitID}">
            <div class="form-floating mt-3">
                <textarea class="form-control" placeholder="Descripción" id="problemDescription" name="problemDescription"></textarea>
                <label for="problemDescription">Descripción del desperfecto</label>
            </div>
        `;

        const send = () => {
            const description = document.getElementById("problemDescription").value.trim();

            if (!description) {
                showToast("La descripción no puede estar vacía.", "danger", "¡UPS!");
                return;
            }

            const data = {
                unitID: unitID,
                problemDescription: description
            };

            sendRequest(`/major-equipment/${unitID}/maintenance-report/JSON/`, 'POST', data)
                .then(response => {
                    if (response.success) {
                        closeModal();
                        showToast("Informe enviado con éxito.", "success");
                    } else {
                        showToast(response.error || "Ocurrió un error inesperado.", "danger");
                        console.warn("⚠️ Respuesta con error:", response);
                    }
                })
                .catch(error => handleError(error, "Envío de reporte de desperfecto"));
        };

        openModal("Reporte de desperfecto", modalBody, "Notificar", send);
    });
});
