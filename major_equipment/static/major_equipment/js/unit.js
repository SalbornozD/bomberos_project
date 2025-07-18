document.addEventListener("DOMContentLoaded", () => {
    // --- Nuevo reporte de mantención ---
    document.querySelectorAll('.report-btn').forEach(button => {
        button.addEventListener('click', () => {
            const unitID = button.dataset.unitId;
            const modalBody = `
                <div class="form-floating mt-3">
                    <textarea class="form-control" placeholder="Descripción" 
                              id="problemDescription" name="problemDescription"></textarea>
                    <label for="problemDescription">Descripción del desperfecto</label>
                </div>`;

            const send = () => {
                const description = document.getElementById("problemDescription").value.trim();
                if (!description) {
                    showToast("La descripción no puede estar vacía.", "danger", "¡UPS!");
                    return;
                }
                const data = { unit_id: unitID, problemDescription: description };

                sendRequest(`/major-equipment/maintenance-report/JSON/`, 'POST', data)
                    .then(response => {
                        if (response.success) {
                            window.location.reload();
                        } else {
                            showToast(response.error || "Ocurrió un error inesperado.", "danger");
                        }
                    })
                    .catch(error => handleError(error, "Creación de Reporte de Mantención"));
            };

            openModal(
                "Nuevo reporte de desperfecto",
                modalBody,
                [
                    { text: "Cancelar", class: "btn btn-light", dismiss: true },
                    { text: "Notificar", class: "btn btn-outline-dark", onClick: send }
                ]
            );
        });
    });

    // --- Nueva solicitud independiente ---
    const toolsBtn = document.querySelector('a[aria-label="Herramientas"], button[aria-label="Herramientas"]');
    if (toolsBtn) {
        toolsBtn.addEventListener('click', e => {
            e.preventDefault();
            // Tomamos el unitId del botón de reporte existente
            const reportBtn = document.querySelector('.report-btn');
            const unitID = reportBtn ? reportBtn.dataset.unitId : null;
            if (!unitID) {
                showToast("No se pudo determinar la unidad.", "danger");
                return;
            }
            openRequestModal(unitID);
        });
    }

    // --- Ver reporte ---
    document.querySelectorAll('.report-view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.reportId;
            sendRequest(`/major-equipment/maintenance-report/JSON/?id=${reportId}`, 'GET')
                .then(response => {
                    if (!response.success) {
                        showToast(response.error || "No se pudo cargar el reporte.", "danger");
                        return;
                    }
                    const rpt = response.report;
                    const body = `
                <div class="d-flex flex-row justify-content-between align-items-center">
                    <p><strong>Reportado por:</strong> ${rpt.reported_by}</p>
                    <p><strong>Fecha:</strong> ${rpt.created_at}</p>
                </div>
                <p><strong>Descripción:</strong></p>
                <p>${rpt.description}</p>`;

                    openModal(
                        `Reporte #${rpt.id}`,
                        body,
                        [{ text: "Cerrar", class: "btn btn-outline-dark", dismiss: true }]
                    );
                })
                .catch(error => handleError(error, "Cargando detalle de reporte"));
        });
    });

    // --- Editar reporte ---
    document.querySelectorAll('.report-edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.reportId;
            (async () => {
                try {
                    const response = await sendRequest(`/major-equipment/maintenance-report/JSON/?id=${reportId}`, 'GET');
                    if (!response.success) {
                        showToast(response.error || "No se pudo cargar el reporte.", "danger");
                        return;
                    }
                    const rpt = response.report;
                    const body = `
                <div class="form-floating">
                    <textarea class="form-control" id="editDescription" style="height:120px">${rpt.description}</textarea>
                    <label for="editDescription">Nueva descripción</label>
                </div>`;

                    openModal(
                        `Editar reporte #${rpt.id}`,
                        body,
                        [
                            { text: "Cerrar", class: "btn btn-outline-dark", dismiss: true },
                            {
                                text: "Actualizar",
                                class: "btn btn-success",
                                onClick: () => {
                                    const newDesc = document.getElementById("editDescription").value.trim();
                                    if (!newDesc) {
                                        showToast("La descripción no puede estar vacía.", "danger");
                                        return;
                                    }
                                    sendRequest(
                                        `/major-equipment/maintenance-report/JSON/`,
                                        'PUT',
                                        { id: reportId, problemDescription: newDesc }
                                    )
                                        .then(res => {
                                            if (res.success) {
                                                closeModal();
                                                showToast("Reporte actualizado correctamente.", "success");
                                                setTimeout(() => window.location.reload(), 500);
                                            } else {
                                                showToast(res.error || "Error al actualizar.", "danger");
                                            }
                                        })
                                        .catch(err => handleError(err, "Actualizando reporte"));
                                }
                            }
                        ]
                    );
                } catch (err) {
                    handleError(err, "Cargando reporte para edición");
                }
            })();
        });
    });

    // --- Eliminar reporte ---
    document.querySelectorAll('.report-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const reportId = btn.dataset.reportId;
            const deleteFn = () => {
                sendRequest(
                    `/major-equipment/maintenance-report/JSON/`,
                    'DELETE',
                    { id: reportId }
                )
                    .then(res => {
                        if (res.success) {
                            window.location.reload();
                        } else {
                            showToast(res.error || "Error al eliminar.", "danger");
                        }
                    })
                    .catch(err => handleError(err, "Eliminando reporte"));
            };

            openModal(
                `Eliminar reporte #${reportId}`,
                `<div class="p-3">¿Confirma que desea eliminar este reporte?</div>`,
                [
                    { text: "Cancelar", class: "btn btn-light", dismiss: true },
                    { text: "Aceptar", class: "btn btn-danger", onClick: deleteFn }
                ]
            );
        });
    });

    // --- Elevación desde cards ---
    document.getElementById("reports").addEventListener("click", e => {
        const btn = e.target.closest(".report-raise-btn");
        if (!btn) return;
        const reportId = btn.dataset.reportId;
        openRaiseModal(reportId);
    });

    // --- Ver Solicitud ---
    document.querySelectorAll('.request-view-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.requestId;
            try {
                const response = await sendRequest(`/major-equipment/maintenance-request/JSON/?request_id=${id}`, 'GET');
                if (!response.success) {
                    showToast(response.error || 'No se pudo cargar la solicitud', 'danger');
                    return;
                }
                const { report, request } = response.data;
                // Construcción del HTML del modal
                let reportHtml = '<p>Sin reporte asociado</p>';
                if (report) {
                    reportHtml = `
                <h6>Reporte asociado N°${report.id}</h6>
                <div class="d-flex justify-content-between">
                  <p><strong>Reportado por:</strong> ${report.reported_by}</p>
                  <p><strong>Fecha:</strong> ${report.created_at}</p>
                </div>
                <p><strong>Descripción:</strong><br>${report.description}</p>
              `;
                }
                // Descarga de cotización
                let quoteLink = '';
                if (request.quotation) {
                    quoteLink = `<a href="${request.quotation}" class="btn btn-sm btn-outline-dark mt-2" download>
                             Descargar cotización
                           </a>`;
                }
                const body = `
              ${reportHtml}
              <hr>
              <h6>Detalle de la solicitud</h6>
              <div class="d-flex justify-content-between">
                <p><strong>Solicitado por:</strong> ${request.requested_by}</p>
                <p><strong>Fecha:</strong> ${request.requested_at}</p>
              </div>
              <p><strong>Responsable de pago:</strong> ${request.responsible_for_payment}</p>
              <p><strong>Descripción:</strong><br>${request.description}</p>
              ${quoteLink}
            `;
                openModal(`Solicitud #${request.id}`, body, [
                    { text: 'Cerrar', class: 'btn btn-outline-dark', dismiss: true }
                ]);
            } catch (err) {
                handleError(err, `View request ID ${id}`);
            }
        });
    });

    // --- Editar solicitud ---
    document.querySelectorAll('.request-edit-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.requestId;
            try {
                const respGet = await sendRequest(`/major-equipment/maintenance-request/JSON/?request_id=${id}`, 'GET');
                if (!respGet.success) {
                    showToast(respGet.error || 'No se pudo cargar la solicitud', 'danger');
                    return;
                }
                const data = respGet.data.request;
                const entityJson = await sendRequest('/firebrigade/entities/JSON/', 'GET');
                if (!entityJson.success) {
                    showToast(entityJson.error || 'No se pudieron cargar las entidades', 'danger');
                    return;
                }
                const options = entityJson.entities
                    .map(e => `<option value="${e.id}" ${e.name === data.responsible_for_payment ? 'selected' : ''}>${e.name}</option>`)
                    .join('');
                const body = `
                    <form id="edit-request-form">
                      <div class="mb-3">
                        <label class="form-label">Descripción</label>
                        <textarea id="editReqDesc" name="description" class="form-control" rows="3">${data.description}</textarea>
                      </div>
                      <div class="mb-3">
                        <label class="form-label">Responsable de pago</label>
                        <select id="editReqResp" name="responsible_for_payment" class="form-select">
                          <option value="">-- selecciona --</option>
                          ${options}
                        </select>
                      </div>
                      <div class="mb-3">
                        <label class="form-label">Cotización (reemplazar)</label>
                        <input type="file" id="editQuotation" name="quotation" class="form-control">
                      </div>
                    </form>`;
                openModal(`Editar solicitud #${id}`, body, [
                    { text: 'Cerrar', class: 'btn btn-outline-dark', dismiss: true },
                    {
                        text: 'Actualizar',
                        class: 'btn btn-success',
                        onClick: async () => {
                            const formElem = document.getElementById('edit-request-form');
                            const formData = new FormData(formElem);
                            formData.append('request_id', id);
                            try {
                                const resp = await fetch(`/major-equipment/maintenance-request/JSON/?request_id=${id}`, {
                                    method: 'PUT',
                                    credentials: 'same-origin',
                                    headers: { 'X-CSRFToken': getCSRFTokenFromMeta() },
                                    body: formData
                                });
                                const result = await resp.json();
                                if (!result.success) {
                                    showToast(result.error || 'Error al actualizar.', 'danger');
                                } else {
                                    closeModal();
                                    showToast('Solicitud actualizada correctamente.', 'success');
                                    setTimeout(() => window.location.reload(), 500);
                                }
                            } catch (err) {
                                handleError(err, 'Actualizando solicitud');
                            }
                        }
                    }
                ]);
            } catch (err) {
                handleError(err, `Edit request ID ${id}`);
            }
        });
    });

    document.querySelectorAll('.request-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.requestId;

            const deleteFn = async () => {
                try {
                    const response = await sendRequest(
                        '/major-equipment/maintenance-request/JSON/',
                        'DELETE',
                        { request_id: id }
                    );

                    if (response.success) {
                        showToast('Solicitud eliminada correctamente.', 'success');
                        setTimeout(() => window.location.reload(), 500);
                    } else {
                        showToast(response.error || 'No se pudo eliminar la solicitud.', 'danger');
                    }
                } catch (err) {
                    handleError(err, `Eliminando solicitud ID ${id}`);
                }
            };

            openModal(
                `Eliminar solicitud #${id}`,
                `<div class="p-3">¿Estás seguro de que deseas eliminar esta solicitud?</div>`,
                [
                    { text: 'Cancelar', class: 'btn btn-light', dismiss: true },
                    { text: 'Eliminar', class: 'btn btn-danger', onClick: deleteFn }
                ]
            );
        });
    });

    // --- Aprobar solicitud ---
    document.querySelectorAll('.request-accept-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.requestId;

            openModal(
                `Aprobar solicitud #${id}`,
                `<div class="p-3">¿Confirmas que deseas aprobar esta solicitud?</div>`,
                [
                    { text: 'Cancelar', class: 'btn btn-light', dismiss: true },
                    {
                        text: 'Aprobar',
                        class: 'btn btn-success',
                        onClick: async () => {
                            try {
                                const response = await sendRequest(
                                    '/major-equipment/maintenance-request/approve/JSON/',
                                    'POST',
                                    { request_id: id }
                                );
                                if (response.success) {
                                    showToast('Solicitud aprobada correctamente.', 'success');
                                    setTimeout(() => window.location.reload(), 500);
                                } else {
                                    showToast(response.error || 'No se pudo aprobar.', 'danger');
                                }
                            } catch (err) {
                                handleError(err, `Aprobando solicitud #${id}`);
                            }
                        }
                    }
                ]
            );
        });
    });

    // --- Rechazar solicitud ---
    document.querySelectorAll('.request-decline-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.requestId;

            const body = `
        <div class="mb-3">
          <label for="rejectionReason" class="form-label">Motivo del rechazo</label>
          <textarea id="rejectionReason" class="form-control" rows="3" placeholder="Escribe el motivo..."></textarea>
        </div>
      `;

            openModal(
                `Rechazar solicitud #${id}`,
                body,
                [
                    { text: 'Cancelar', class: 'btn btn-light', dismiss: true },
                    {
                        text: 'Rechazar',
                        class: 'btn btn-danger',
                        onClick: async () => {
                            const reason = document.getElementById('rejectionReason').value.trim();
                            if (!reason) {
                                showToast('Debes ingresar un motivo.', 'danger');
                                return;
                            }

                            try {
                                const response = await sendRequest(
                                    '/major-equipment/maintenance-request/reject/JSON/',
                                    'POST',
                                    { request_id: id, reason }
                                );
                                if (response.success) {
                                    showToast('Solicitud rechazada correctamente.', 'success');
                                    setTimeout(() => window.location.reload(), 500);
                                } else {
                                    showToast(response.error || 'No se pudo rechazar.', 'danger');
                                }
                            } catch (err) {
                                handleError(err, `Rechazando solicitud #${id}`);
                            }
                        }
                    }
                ]
            );
        });
    });


});

// ---------------------------
// Función: abrir modal de solicitud sin reporte
// ---------------------------
async function openRequestModal(unitId) {
    try {
        const entityJson = await sendRequest('/firebrigade/entities/JSON/', 'GET');
        if (!entityJson.success) throw { status: 400, text: JSON.stringify(entityJson) };
        const entities = entityJson.entities;

        const body = `
            <form id="request-form">
                <input type="hidden" name="unit_id" value="${unitId}">
                <div class="mb-3">
                    <label for="requestDescription" class="form-label">Detalle de la solicitud</label>
                    <textarea id="requestDescription" name="description" class="form-control" rows="3"></textarea>
                </div>
                <div class="mb-3">
                    <label for="responsibleForPayment" class="form-label">Responsable de pago</label>
                    <select id="responsibleForPayment" name="responsible_for_payment" class="form-select">
                        <option value="">-- selecciona --</option>
                        ${entities.map(e => `<option value="${e.id}">${e.name}</option>`).join('')}
                    </select>
                </div>
                <div class="mb-3">
                    <label for="quotation" class="form-label">Adjuntar cotización (opcional)</label>
                    <input type="file" id="quotation" name="quotation" class="form-control">
                </div>
            </form>`;

        openModal('Nueva Solicitud de Mantención', body, [
            { text: 'Cancelar', class: 'btn btn-outline-dark', dismiss: true },
            { text: 'Enviar Solicitud', class: 'btn btn-success', onClick: () => submitRequestForm(unitId) }
        ]);
    } catch (err) {
        handleError(err, "openRequestModal");
    }
}

// ---------------------------
// Función: enviar solicitud sin reporte
// ---------------------------
async function submitRequestForm(unitId) {
    try {
        const formElem = document.getElementById('request-form');
        const data = new FormData(formElem);
        data.append('unit_id', unitId);

        const resp = await fetch('/major-equipment/maintenance-request/JSON/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCSRFTokenFromMeta() },
            body: data
        });

        const json = await resp.json();
        if (!json.success) throw { status: resp.status, text: JSON.stringify(json) };
        window.location.reload();
    } catch (err) {
        handleError(err, "submitRequestForm");
    }
}

