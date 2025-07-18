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


    document.querySelectorAll(".btn-create-request").forEach(button => {
        button.addEventListener("click", async () => {
            const unitId = button.dataset.unit;
            const reportId = button.dataset.reportId;
    
            let reportData = null;
    
            try {
                const response = await sendRequest(`/major-equipment/maintenance-report/JSON/?id=${reportId}`, "GET");
                if (!response.success) {
                    showToast("No se pudo cargar el reporte.", "danger");
                    return;
                }
                reportData = response.report;
            } catch (error) {
                handleError(error, "Cargar descripción de reporte");
                return;
            }
    
            // Campos especiales para superuser
            const superuserFields = window.isSuperuser ? `
                <div class="form-floating mb-3">
                    <select class="form-select" name="entity_id" id="entity_id">
                        <option disabled selected>Selecciona una entidad</option>
                    </select>
                    <label for="entity_id">Entidad</label>
                </div>
    
                <div class="form-floating mb-3">
                    <select class="form-select" name="requested_by_id" id="requested_by_id" disabled>
                        <option disabled selected>Selecciona una entidad primero</option>
                    </select>
                    <label for="requested_by_id">Solicitante</label>
                </div>
            ` : "";
    
            const suggestedDescription = reportData?.description || "";
    
            const body = `
                <form id="requestForm" enctype="multipart/form-data">
                    <input type="hidden" name="unit_id" value="${unitId}">
                    <input type="hidden" name="report_id" value="${reportId}">
                    ${superuserFields}
    
                    <div class="form-floating mb-3">
                        <textarea class="form-control" id="description" name="description" placeholder="Descripción" style="height: 100px;">${suggestedDescription}</textarea>
                        <label for="description">Motivo de la solicitud</label>
                    </div>
    
                    <div class="form-floating mb-3">
                        <select class="form-select" id="responsible_for_payment" name="responsible_for_payment">
                            <option value="CUERPO">Cuerpo de bomberos</option>
                            <option value="ENTIDAD">Mi compañía</option>
                        </select>
                        <label for="responsible_for_payment">Responsable del pago</label>
                    </div>
    
                    <div class="mb-3">
                        <label for="quotation" class="form-label">Adjuntar cotización (opcional):</label>
                        <input type="file" class="form-control" id="quotation" name="quotation" accept=".pdf,.jpg,.png">
                    </div>
                </form>
            `;
    
            openModal("Crear solicitud de mantención", body, [
                { text: "Cancelar", class: "btn btn-secondary", dismiss: true },
                {
                    text: "Crear",
                    class: "btn btn-primary",
                    onClick: async () => {
                        const form = document.getElementById("requestForm");
                        const formData = new FormData(form);
    
                        if (!form.description.value.trim()) {
                            showToast("La descripción no puede estar vacía.", "danger");
                            return;
                        }
    
                        try {
                            const res = await fetch("/major-equipment/maintenance-request/JSON/", {
                                method: "POST",
                                headers: {
                                    'X-CSRFToken': getCSRFTokenFromMeta(),
                                },
                                body: formData,
                            }).then(response => response.json());
    
                            if (res.success) {
                                closeModal();
                                showToast("Solicitud creada correctamente.", "success");
                            } else {
                                showToast(res.error || "No se pudo crear la solicitud.", "danger");
                            }
                        } catch (error) {
                            handleError(error, "Crear solicitud mantención");
                        }
                    }
                }
            ]);
    
            // Si es superuser --> cargar entidades y usuarios dinámicamente
            if (window.isSuperuser) {
                try {
                    const entityRes = await sendRequest("/firebrigade/entities/JSON/", "GET");
                    if (entityRes.success) {
                        const entitySelect = document.getElementById("entity_id");
                        entityRes.entities.forEach(entity => {
                            const option = document.createElement("option");
                            option.value = entity.id;
                            option.textContent = entity.name;
                            entitySelect.appendChild(option);
                        });
    
                        entitySelect.addEventListener("change", async () => {
                            const selectedEntity = entitySelect.value;
                            const userSelect = document.getElementById("requested_by_id");
                            userSelect.innerHTML = '<option disabled selected>Cargando usuarios...</option>';
                            userSelect.disabled = true;
    
                            const userRes = await sendRequest(`/firebrigade/users/JSON/?entity_id=${selectedEntity}`, "GET");
    
                            if (userRes.success) {
                                userSelect.innerHTML = '';
                                userRes.users.forEach(user => {
                                    const option = document.createElement("option");
                                    option.value = user.id;
                                    option.textContent = user.username;
                                    userSelect.appendChild(option);
                                });
                                userSelect.disabled = false;
                            }
                        });
                    }
                } catch (error) {
                    handleError(error, "Cargar entidades y usuarios");
                }
            }
    
        });
    });

});
