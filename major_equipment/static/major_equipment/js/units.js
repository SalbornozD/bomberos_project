document.querySelectorAll('.report-problem-btn').forEach(button => {
    button.addEventListener('click', () => {
        const unitID = button.dataset.unitId;

        const modalBody = `
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
                unit_id: unitID,  // IMPORTANTE: ahora va en el body
                problemDescription: description
            };

            sendRequest(`/major-equipment/maintenance-report/JSON/`, 'POST', data)
                .then(response => {
                    if (response.success) {
                        closeModal();
                        showToast("Reporte creado correctamente.", "success");
                    } else {
                        showToast(response.error || "Ocurrió un error inesperado.", "danger");
                        console.warn("⚠️ Respuesta con error:", response);
                    }
                })
                .catch(error => handleError(error, "Creación de Reporte de Mantención"));
        };

        openModal("Nuevo reporte de desperfecto", modalBody, [
            { text: "Cancelar", class: "btn btn-light", dismiss: true },
            { text: "Notificar", class: "btn btn-success", onClick: send }
        ]);
    });
});
