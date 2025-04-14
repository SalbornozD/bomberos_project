document.addEventListener("DOMContentLoaded", () => {

    // Ver Detalle
    document.querySelectorAll('.btn-view-report').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.id;

            sendRequest(`/major-equipment/maintenance-report/JSON/?id=${reportId}`)
                .then(data => {
                    if (!data.success) {
                        showToast(data.error, "danger");
                        return;
                    }

                    const content = `
                        <div class="d-flex flex-column gap-3">
                            <div>
                                <span class="d-flex flex-row justify-content-between align-items-center mb-2">
                                    <p><strong>Reportado por:</strong> ${data.report.reported_by}</p>
                                    <p>${data.report.created_at}</p>
                                </span>
                                <p><strong>Unidad:</strong> ${data.report.unit}</p>
                            </div>
                            <div>
                                <p><strong>Detalle:</strong><br>${data.report.description}</p>
                            </div>
                        </div>
                    `;

                    openModal(`Detalle reporte N°${reportId}`, content, [
                        { text: "Cerrar", class: "btn btn-light", dismiss: true }
                    ]);
                })
                .catch(error => handleError(error, "Detalle Reporte"));
        });
    });


    // Editar Reporte
    document.querySelectorAll('.btn-edit-report').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.id;
            const unitName = btn.dataset.unitname;  // opcional si lo tienes en el botón

            sendRequest(`/major-equipment/maintenance-report/JSON/?id=${reportId}`)
                .then(data => {
                    if (!data.success) {
                        showToast(data.error, "danger");
                        return;
                    }

                    const content = `
                        <div class="d-flex flex-column gap-3">
                            <div>
                                <span class="d-flex flex-row justify-content-between align-items-center mb-2">
                                    <p><strong>Reportado por:</strong> ${data.report.reported_by}</p>
                                    <p>${data.report.created_at}</p>
                                </span>
                                <p><strong>Unidad:</strong> ${data.report.unit}</p>
                            </div>
                            <div>
                                <label class="form-label"><strong>Descripción:</strong></label>
                                <textarea class="form-control" id="editDescription">${data.report.description}</textarea>
                            </div>
                        </div>
                    `;

                    openModal(`Editar reporte N°${reportId}`, content, [
                        { text: "Cancelar", class: "btn btn-outline-danger", dismiss: true },
                        {
                            text: "Guardar Cambios",
                            class: "btn btn-success",
                            onClick: () => {
                                const newDescription = document.getElementById("editDescription").value.trim();

                                if (!newDescription) {
                                    showToast("La descripción no puede estar vacía.", "warning");
                                    return;
                                }

                                sendRequest(`/major-equipment/maintenance-report/JSON/`, 'PUT', {
                                    id: reportId,
                                    problemDescription: newDescription
                                })
                                    .then(res => {
                                        if (res.success) {
                                            location.reload();
                                        } else {
                                            showToast(res.error, "danger");
                                        }
                                    })
                                    .catch(error => handleError(error, "Editar Reporte"));
                            }
                        }
                    ]);
                })
                .catch(error => handleError(error, "Cargar Reporte para Editar"));
        });
    });


    // Eliminar Reporte
    document.querySelectorAll('.btn-delete-report').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.id;

            const content = `<p>¿Estás seguro que deseas eliminar este reporte?</p>`;

            openModal(`Eliminar reporte N°${reportId}`, content, [
                { text: "Cancelar", class: "btn btn-light", dismiss: true },
                {
                    text: "Eliminar",
                    class: "btn btn-danger",
                    onClick: () => {
                        sendRequest(`/major-equipment/maintenance-report/JSON/`, 'DELETE', {
                            id: reportId
                        })
                            .then(res => {
                                if (res.success) {
                                    location.reload();
                                } else {
                                    showToast(res.error, "danger");
                                }
                            })
                            .catch(error => handleError(error, "Eliminar Reporte"));
                    }
                }
            ]);
        });
    });

});
