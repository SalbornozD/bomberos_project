
// Funciones para manejar solicitudes de mantención

/**
 * Obtiene el detalle de una solicitud de mantención desde el backend
 * 
 * @param {number} requestId - ID del reporte a consultar.
 * @return {Promise<Object>} Detalle del reporte si es exitoso.
 * @throws {Object} Error con status y mensaje si falla la validación o el servidor.
 */
async function obtenerSolicitudDeMantencion(requestId) {
    // Validación del ID
    if (!requestId || typeof requestId !== "number" || requestId <= 0) {
        throw {
            status: 400,
            text: JSON.stringify({ error: "ID de reporte inválido o ausente." })
        };
    }

    // Construir la URL con query string
    const url = `/major-equipment/maintenance-request/JSON/?request_id=${requestId}`;

    try{
        // Enviar solicitud GET
        const response = await sendRequest(url, 'GET');

        // Evaluar respuesta del servidor

        if (response.success && response.data){
            
            return response.data;
        } else {
            console.error("Error al obtener la solicitud:", response);
            throw {
                status: 404,
                text: JSON.stringify(response)
            };
        }
    } catch (error) {
        // Mostrar toast y registrar error
        handleError(error, "Obtención de Solicitud");
        throw error;
    }
}

/**
 * Crea una solicitud de mantención mediante una petición POST al backend.
 * Usa sendRequest() cuando no hay archivo; usa fetch directamente cuando sí hay archivo.
 * 
 * @param {Object} params
 * @param {number|null} params.reportId               - ID del reporte asociado (si corresponde).
 * @param {number|null} params.unitId                 - ID de la unidad asociada (si no hay reporte).
 * @param {string} params.description                  - Descripción del problema (mínimo 5 caracteres).
 * @param {number} params.responsibleForPayment        - ID de la entidad responsable del pago.
 * @param {string|null} [params.maintenanceStart=null] - Fecha de envío a taller en formato "YYYY-MM-DD" (opcional).
 * @param {string|null} [params.workshopName=null]     - Nombre del taller al que se envía (opcional).
 * @param {File|null} [params.quotationFile=null]      - Archivo PDF de cotización (opcional).
 * @throws {Object} Error con `{ status, text }` si falla validación o el servidor retorna error.
 * @returns {Promise<Object>} Respuesta JSON del servidor si es exitosa.
 */
async function crearSolicitudDeMantencion({
    reportId = null,
    unitId = null,
    description,
    responsibleForPayment,
    maintenanceStart = null,
    workshopName = null,
    quotationFile = null,
}) {
    console.log("🚀 Creando solicitud de mantención...");
    console.log("Datos recibidos:", {
        reportId,
        unitId,
        description,
        responsibleForPayment,
        maintenanceStart,
        workshopName,
        quotationFile,
    });

    // --- 1) Validación previa de datos de entrada ---
    // a) description: cadena de al menos 5 caracteres
    if (!description || typeof description !== "string" || description.trim().length < 5) {
        throw {
            status: 400,
            text: JSON.stringify({ error: "La descripción debe tener al menos 5 caracteres." }),
        };
    }

    // b) responsibleForPayment: número entero mayor a 0
    if (
        typeof responsibleForPayment !== "number" ||
        !Number.isInteger(responsibleForPayment) ||
        responsibleForPayment <= 0
    ) {
        throw {
            status: 400,
            text: JSON.stringify({ error: "ID de entidad de pago inválido o ausente." }),
        };
    }

    // c) Validar que venga exactamente reportId O unitId (no ambos, no ninguno)
    const tieneReportId = typeof reportId === "number" && Number.isInteger(reportId) && reportId > 0;
    const tieneUnitId = typeof unitId === "number" && Number.isInteger(unitId) && unitId > 0;
    if ((tieneReportId && tieneUnitId) || (!tieneReportId && !tieneUnitId)) {
        throw {
            status: 400,
            text: JSON.stringify({ error: "Debes indicar solo reportId o unitId (exactamente uno)." }),
        };
    }

    // d) Si maintenanceStart viene, debe ser string en formato YYYY-MM-DD
    if (maintenanceStart !== null) {
        const regexDate = /^\d{4}-\d{2}-\d{2}$/;
        if (typeof maintenanceStart !== "string" || !regexDate.test(maintenanceStart)) {
            throw {
                status: 400,
                text: JSON.stringify({ error: "maintenanceStart debe tener formato YYYY-MM-DD." }),
            };
        }
    }

    // e) Si workshopName viene, debe ser string (puede quedar vacío para null)
    if (workshopName !== null && typeof workshopName !== "string") {
        throw {
            status: 400,
            text: JSON.stringify({ error: "workshopName debe ser texto válido." }),
        };
    }

    // f) Si quotationFile viene, debe ser un objeto File
    if (quotationFile !== null && !(quotationFile instanceof File)) {
        throw {
            status: 400,
            text: JSON.stringify({ error: "El archivo de cotización debe ser de tipo File (PDF)." }),
        };
    }

    const url = "/major-equipment/maintenance-request/JSON/";

    try {
        // --- 2) Caso SIN archivo de cotización: usamos sendRequest (envío JSON) ---
        if (!quotationFile) {
            // Construir objeto JSON que espera el backend
            const payload = {
                description: description.trim(),
                responsible_for_payment: responsibleForPayment,
            };
            if (tieneReportId) {
                payload.report_id = reportId;
            } else {
                payload.unit_id = unitId;
            }
            // Agregar campos opcionales de taller solo si vienen definidos
            if (maintenanceStart) {
                payload.maintenance_start = maintenanceStart;
            }
            if (workshopName) {
                payload.workshop_name = workshopName.trim();
            }

            // sendRequest se encarga de:
            // - poner Content-Type: application/json
            // - agregar X-CSRFToken
            // - serializar JSON
            const responseJson = await sendRequest(url, "POST", payload);

            // El backend devuelve { success: true, message: "...", maintenance_request_id: N }
            if (responseJson.success) {
                return responseJson;
            } else {
                // Cuando success: false, armamos mismo formato de error
                throw {
                    status: 400,
                    text: JSON.stringify(responseJson),
                };
            }
        }

        // --- 3) Caso CON archivo de cotización: construimos FormData y enviamos con fetch ---
        {
            // 3.a) Construir FormData
            const formData = new FormData();
            formData.append("description", description.trim());
            formData.append("responsible_for_payment", String(responsibleForPayment));

            if (tieneReportId) {
                formData.append("report_id", String(reportId));
            } else {
                formData.append("unit_id", String(unitId));
            }

            // Agregar campos opcionales de taller
            if (maintenanceStart) {
                formData.append("maintenance_start", maintenanceStart);
            }
            if (workshopName) {
                formData.append("workshop_name", workshopName.trim());
            }

            formData.append("quotation", quotationFile);

            // 3.b) Obtener CSRF token para Django
            const csrftoken = getCSRFTokenFromMeta(); 
            //    (se asume que getCSRFTokenFromMeta() lee <meta name="csrf-token" content="...">)

            // 3.c) Preparar encabezados. Importante: NO establecer Content-Type a multipart/form-data; 
            //     el navegador se encarga de armar el boundary correcto.
            const headers = {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrftoken,
            };

            // 3.d) Ejecutar fetch
            const respuestaRaw = await fetch(url, {
                method: "POST",
                headers: headers,
                body: formData,
                credentials: "include", // si usas sesión Django en cookies
            });

            // 3.e) Si el status es error (no 2xx), leer texto y arrojar
            if (!respuestaRaw.ok) {
                const textoError = await respuestaRaw.text();
                let detalle;
                try {
                    detalle = JSON.parse(textoError);
                } catch {
                    detalle = { error: textoError };
                }
                throw {
                    status: respuestaRaw.status,
                    text: JSON.stringify(detalle),
                };
            }

            // 3.f) Parsear JSON de respuesta exitosa
            const responseJson = await respuestaRaw.json();

            if (responseJson.success) {
                return responseJson;
            } else {
                throw {
                    status: 400,
                    text: JSON.stringify(responseJson),
                };
            }
        }
    } catch (error) {
        // --- 4) Manejo de error: mostrar toast, loguear, etc. ---
        console.error("Error en crearSolicitudDeMantencion:", error);
        throw error;
    }
}

/**
 * Edita una solicitud de mantención existente mediante una petición PUT al backend.
 * Usa sendRequest() cuando no hay archivos nuevos; usa fetch con FormData cuando sí hay alguno.
 * 
 * @param {Object} params
 * @param {number} params.requestId                   - ID de la solicitud a editar (requerido).
 * @param {string|null} [params.description]           - Nueva descripción (mínimo 5 caracteres).
 * @param {number|null} [params.responsibleForPayment] - ID de la entidad responsable de pago.
 * @param {string|null} [params.maintenanceStart]      - Fecha de envío a taller en formato "YYYY-MM-DD" (opcional).
 * @param {string|null} [params.workshopName]          - Nombre del taller (opcional).
 * @param {string|null} [params.maintenanceEnd]        - Fecha de término en formato "YYYY-MM-DD" (opcional).
 * @param {number|null} [params.km]                    - Kilometraje (opcional, entero ≥ 0).
 * @param {number|null} [params.cost]                  - Costo (opcional, entero ≥ 0).
 * @param {string|null} [params.comment]               - Comentarios (opcional).
 * @param {File|null} [params.quotationFile=null]      - Nuevo archivo de cotización (opcional).
 * @param {File|null} [params.invoiceFile=null]        - Nuevo archivo de factura (opcional).
 * @throws {Object} Error con `{ status, text }` si falla validación o el servidor retorna error.
 * @returns {Promise<Object>} Respuesta JSON del servidor si es exitosa.
 */
async function editarSolicitudDeMantencion({
  requestId,
  description = null,
  responsibleForPayment = null,
  maintenanceStart = null,
  workshopName = null,
  maintenanceEnd = null,
  km = null,
  cost = null,
  comment = null,
  quotationFile = null,
  invoiceFile = null,
}) {
  console.log("🚀 Editando solicitud de mantención...");
  console.log("Datos recibidos para edición:", {
    requestId,
    description,
    responsibleForPayment,
    maintenanceStart,
    workshopName,
    maintenanceEnd,
    km,
    cost,
    comment,
    quotationFile,
    invoiceFile,
  });

  // --- 1) Validaciones previas ---
  if (typeof requestId !== "number" || !Number.isInteger(requestId) || requestId <= 0) {
    throw { status: 400, text: JSON.stringify({ error: "requestId inválido o ausente." }) };
  }

  // a) description: si viene definido, mínimo 5 caracteres
  if (description !== null) {
    if (typeof description !== "string" || description.trim().length < 5) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "La descripción debe tener al menos 5 caracteres." }),
      };
    }
  }

  // b) responsibleForPayment: si viene definido, debe ser entero > 0
  if (responsibleForPayment !== null) {
    if (
      typeof responsibleForPayment !== "number" ||
      !Number.isInteger(responsibleForPayment) ||
      responsibleForPayment <= 0
    ) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "ID de entidad de pago inválido." }),
      };
    }
  }

  // c) Fechas (si vienen definidas) deben tener formato YYYY-MM-DD
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (maintenanceStart !== null) {
    if (typeof maintenanceStart !== "string" || !dateRegex.test(maintenanceStart)) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "maintenanceStart debe tener formato YYYY-MM-DD." }),
      };
    }
  }
  if (maintenanceEnd !== null) {
    if (typeof maintenanceEnd !== "string" || !dateRegex.test(maintenanceEnd)) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "maintenanceEnd debe tener formato YYYY-MM-DD." }),
      };
    }
  }

  // d) km y cost (si vienen) deben ser enteros ≥ 0
  if (km !== null) {
    if (typeof km !== "number" || !Number.isInteger(km) || km < 0) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "km debe ser un número entero ≥ 0." }),
      };
    }
  }
  if (cost !== null) {
    if (typeof cost !== "number" || !Number.isInteger(cost) || cost < 0) {
      throw {
        status: 400,
        text: JSON.stringify({ error: "cost debe ser un número entero ≥ 0." }),
      };
    }
  }

  // e) comment: si viene, debe ser string
  if (comment !== null && typeof comment !== "string") {
    throw {
      status: 400,
      text: JSON.stringify({ error: "comment debe ser texto." }),
    };
  }

  // f) Archivo de cotización (si viene) debe ser File
  if (quotationFile !== null && !(quotationFile instanceof File)) {
    throw {
      status: 400,
      text: JSON.stringify({ error: "quotationFile debe ser un objeto File." }),
    };
  }

  // g) Archivo de factura (si viene) debe ser File
  if (invoiceFile !== null && !(invoiceFile instanceof File)) {
    throw {
      status: 400,
      text: JSON.stringify({ error: "invoiceFile debe ser un objeto File." }),
    };
  }

  const url = "/major-equipment/maintenance-request/JSON/";

  try {
    // — ¿hay archivos nuevos?
    const tieneArchivo = quotationFile !== null || invoiceFile !== null;

    if (!tieneArchivo) {
      // 2.a) Payload JSON
      const payload = { request_id: requestId };

      if (description !== null) payload.description = description.trim();
      if (responsibleForPayment !== null)
        payload.responsible_for_payment = responsibleForPayment;
      if (maintenanceStart !== null) payload.maintenance_start = maintenanceStart;
      if (workshopName !== null) payload.workshop_name = workshopName.trim();
      if (maintenanceEnd !== null) payload.maintenance_end = maintenanceEnd;
      if (km !== null) payload.km = km;
      if (cost !== null) payload.cost = cost;
      if (comment !== null) payload.comment = comment.trim();

      // Enviar con sendRequest
      const responseJson = await sendRequest(url, "PUT", payload);

      if (responseJson.success) {
        return responseJson;
      } else {
        throw { status: 400, text: JSON.stringify(responseJson) };
      }
    } else {
      // 2.b) Payload FormData (multipart) para incluir archivos
      const formData = new FormData();
      formData.append("request_id", String(requestId));

      if (description !== null) formData.append("description", description.trim());
      if (responsibleForPayment !== null)
        formData.append("responsible_for_payment", String(responsibleForPayment));
      if (maintenanceStart !== null) formData.append("maintenance_start", maintenanceStart);
      if (workshopName !== null) formData.append("workshop_name", workshopName.trim());
      if (maintenanceEnd !== null) formData.append("maintenance_end", maintenanceEnd);
      if (km !== null) formData.append("km", String(km));
      if (cost !== null) formData.append("cost", String(cost));
      if (comment !== null) formData.append("comment", comment.trim());
      if (quotationFile !== null) formData.append("quotation", quotationFile);
      if (invoiceFile !== null) formData.append("invoice", invoiceFile);

      // Obtener CSRF token
      const csrftoken = getCSRFTokenFromMeta();

      const responseRaw = await fetch(url, {
        method: "PUT",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
          // NO se setea Content-Type; el navegador agrega el boundary automáticamente
        },
        body: formData,
        credentials: "include",
      });

      if (!responseRaw.ok) {
        const textoError = await responseRaw.text();
        let detalle;
        try {
          detalle = JSON.parse(textoError);
        } catch {
          detalle = { error: textoError };
        }
        throw { status: responseRaw.status, text: JSON.stringify(detalle) };
      }

      const responseJson = await responseRaw.json();
      if (responseJson.success) {
        return responseJson;
      } else {
        throw { status: 400, text: JSON.stringify(responseJson) };
      }
    }
  } catch (error) {
    console.error("Error en editarSolicitudDeMantencion:", error);
    throw error;
  }
}


/* ------------------------------------------------- */

/**
 * Abre el modal de creación de un reporte de mantención.
 * En el modal, el usuario ingresa la descripción del reporte.
 *
 * @param {number} unitId - ID de la unidad del reporte.
 */
function mostrarModalCrearReporte(unitId) {
    let tituloModal = "Nuevo reporte de mantención";
    let constenidoModal = `
        <form>
            <div class="mb-3">
                <label for="description" class="form-label">Descripción</label>
                <textarea class="form-control" id="new-report-description" rows="2" required></textarea>
            </div>
        </form>
    `
    const apiReportes = new ReporteMantencionService();
    
    const botones = [
        {
            text: "Cancelar",
            class: "btn btn-outline-dark",
            dismiss: true
        },
        {
            text: "Enviar",
            class: "btn btn-outline-success",
            dismiss: true,
            onClick: async () => {
                try {
                    // Obtenemos la descripción desde el formulario.
                    const description = document.getElementById("new-report-description").value.trim();
                    
                    // Validación de la información
                    if (!description || description.length < 5) throw new Error("La descripción debe tener al menos 5 caracteres.");

                    // Enviamos la petición 
                    const respuesta = await apiReportes.crear({
                        unitId: unitId,
                        description: description
                    });

                    // Mostramos un Toast de confirmación
                    showToast("Reporte creado correctamente. Actualizando…", "success");
                    setTimeout(() => {
                        location.reload();
                    }, 2000); // Espera de 2 segundos.

                } catch (error) {
                    console.error(error)
                };

                
            }
        }
    ]

    openModal(tituloModal,constenidoModal,botones);
}

/**
 * Abre el modal para editar un reporte (En este modo solo se
 * permite editar la descripción del reporte)
 * @param {Object} report 
 */
async function mostrarModalEditarReporte(reportId) {
    const apiReport = new ReporteMantencionService();
    const report = await apiReport.obtener(reportId);
    console.log(report)

    const tituloModal = `Editar reporte N°${report.id}`;
    const contenidoModal = `
        <form>
            <div class="mb-3">
                <label for="nuevaDescripcion" class="form-label">Descripción</label>
                <textarea class="form-control" id="nuevaDescripcion" rows="4" required>${report.description}</textarea>
            </div>
        </form>
    `;
    const botones = [
        {
            text: "Cancelar",
            class: "btn btn-outline-dark",
            dismiss: true
        },
        {
            text: "Modificar",
            class: "btn btn-outline-success",
            onClick: async () => {
                const apiReportes = new ReporteMantencionService();
                const nuevaDescripcion = document.getElementById("nuevaDescripcion").value.trim();

                if (nuevaDescripcion.length < 5) {
                    showToast("La descripción debe tener al menos 5 caracteres.", "warning", "Descripción inválida");
                    return;
                }

                try {
                    const resultado = await apiReportes.editar({
                        reportId: report.id,
                        description: nuevaDescripcion
                    });

                    closeModal();

                } catch (error) {
                    console.error("❌ Error al actualizar:", error);
                }
            }
        }
    ];

    openModal(tituloModal, contenidoModal, botones);
}

/**
 * Abre el modal para eliminar un reporte.
 * @param {*} reportId 
 */
function mostrarModalConfirmarEliminacionReporte(reportId) {
    const tituloModal = "¿Deseas eliminar el reporte?";
    const apiReportes = new ReporteMantencionService();
    const contenidoModal = `
        <p>¿Estás seguro que deseas eliminar el reporte <strong>N°${reportId}</strong>?</p>
        <p class="text-danger">Esta acción no se puede deshacer.</p>
    `;
    
    const botones = [
        {
            text: "Cancelar",
            class: "btn btn-outline-dark",
            dismiss: true
        },
        {
            text: "Eliminar",
            class: "btn btn-danger",
            onClick: async () => {
                try {
                    const resultado = await apiReportes.eliminar(reportId);
                    location.reload();

                } catch (error) {
                    console.error("Error al eliminar:", error);
                }
            }
        }

    ]

    openModal(tituloModal, contenidoModal, botones);
}

/**
 * Abre el modal para ver información detallada de un reporte
 * de mantención.
 * 
 * @param {number} reportId 
 */
async function mostrarModalVerReporte(reportId) {
    const apiReportes = new ReporteMantencionService();
    const respuesta = await apiReportes.obtener(reportId);

    const tituloModal = `Reporte de mantención N°${reportId}`;
    const contenidoModal = `
        <div>
            <div class="d-flex flex-row justify-content-between align-items-center mb-3">
                <p><strong>Reportado por:</strong> ${respuesta.reported_by}</p>
                <p><strong>Fecha:</strong> ${respuesta.created_at}</p>
            </div>
        </div>
        <div class="d-flex flex-column">
            <p><strong>Descripción:</strong></p>
            <p>${respuesta.description}</p>
        </div>
    `
    const botones = [
        {
            text: "Eliminar",
            class: "btn btn-outline-danger",
            onClick: () => mostrarModalConfirmarEliminacionReporte(reportId)
        },
        {
            text: "Editar",
            class: "btn btn-outline-dark",
            onClick: () => mostrarModalEditarReporte(reportId)
        },
        {
            text: "Cerrar",
            class: "btn btn-outline-dark",
            dismiss: true
        }
    ]
    
    openModal(tituloModal, contenidoModal, botones);

}




/**
 * Abre un modal con un formulario para editar una solicitud de mantención.
 * Pre-carga los datos actuales de la solicitud y, al enviar, llama a editarSolicitudDeMantencion().
 * 
 * @param {number} requestId - ID de la solicitud de mantención a editar.
 */
async function mostrarModalEditarSolicitud(requestId) {
  // 1) Validar requestId
  if (typeof requestId !== "number" || !Number.isInteger(requestId) || requestId <= 0) {
    console.error("requestId inválido:", requestId);
    return;
  }

  // 2) Obtener datos actuales de la solicitud
  let datos;
  try {
    datos = await obtenerSolicitudDeMantencion(requestId);
  } catch (error) {
    console.error("❌ No se pudo cargar la solicitud:", error);
    handleError(error, "Carga de Solicitud para Edición");
    return;
  }

  // 3) Construir contenido HTML del formulario pre-llenado
  const contenido = `
    <form id="form-edit-request">
      <!-- Descripción -->
      <div class="mb-3">
        <label for="edit-description" class="form-label"><strong>Descripción</strong></label>
        <textarea
          id="edit-description"
          class="form-control"
          rows="3"
          required
        >${datos.description || ""}</textarea>
      </div>

      <!-- Entidad responsable de pago (solo lectura) -->
      <div class="mb-3">
        <label for="edit-responsible" class="form-label"><strong>Entidad de Pago</strong></label>
        <input
          type="text"
          id="edit-responsible"
          class="form-control"
          value="${datos.responsible_for_payment}"
          disabled
        />
      </div>

      <!-- Fecha de envío a taller -->
      <div class="mb-3">
        <label for="edit-maintenance-start" class="form-label"><strong>Fecha de envío a taller</strong></label>
        <input
          type="date"
          id="edit-maintenance-start"
          class="form-control"
          value="${datos.maintenance_start || ""}"
        />
      </div>

      <!-- Nombre del Taller -->
      <div class="mb-3">
        <label for="edit-workshop-name" class="form-label"><strong>Nombre del Taller</strong></label>
        <input
          type="text"
          id="edit-workshop-name"
          class="form-control"
          value="${datos.workshop_name || ""}"
        />
      </div>

      <!-- Fecha de término -->
      <div class="mb-3">
        <label for="edit-maintenance-end" class="form-label"><strong>Fecha de término (opcional)</strong></label>
        <input
          type="date"
          id="edit-maintenance-end"
          class="form-control"
          value="${datos.maintenance_end || ""}"
        />
      </div>

      <!-- Kilometraje -->
      <div class="mb-3">
        <label for="edit-km" class="form-label"><strong>Kilometraje (opcional)</strong></label>
        <input
          type="number"
          id="edit-km"
          class="form-control"
          min="0"
          value="${datos.km !== null ? datos.km : ""}"
        />
      </div>

      <!-- Costo -->
      <div class="mb-3">
        <label for="edit-cost" class="form-label"><strong>Costo (opcional)</strong></label>
        <input
          type="number"
          id="edit-cost"
          class="form-control"
          min="0"
          value="${datos.cost !== null ? datos.cost : ""}"
        />
      </div>

      <!-- Comentarios -->
      <div class="mb-3">
        <label for="edit-comment" class="form-label"><strong>Comentarios (opcional)</strong></label>
        <textarea
          id="edit-comment"
          class="form-control"
          rows="2"
        >${datos.comment || ""}</textarea>
      </div>

      <!-- Cotización (archivo) -->
      <div class="mb-3">
        <label for="edit-quotation" class="form-label"><strong>Cotización (opcional)</strong></label>
        <input
          type="file"
          id="edit-quotation"
          class="form-control"
          accept="application/pdf"
        />
        ${ datos.quotation 
            ? `<small class="form-text text-muted">Archivo actual: 
                 <a href="${datos.quotation}" target="_blank">Ver cotización</a>
               </small>`
            : ""
        }
      </div>

      <!-- Factura (archivo) -->
      <div class="mb-3">
        <label for="edit-invoice" class="form-label"><strong>Factura (opcional)</strong></label>
        <input
          type="file"
          id="edit-invoice"
          class="form-control"
          accept="application/pdf"
        />
        ${ datos.invoice_url 
            ? `<small class="form-text text-muted">Archivo actual: 
                 <a href="${datos.invoice_url}" target="_blank">Ver factura</a>
               </small>`
            : ""
        }
      </div>
    </form>
  `;

  // 4) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-dark",
      dismiss: true,
    },
    {
      text: "Guardar Cambios",
      class: "btn btn-outline-success",
      onClick: async () => {
        console.log("🚀 Guardando cambios en solicitud de mantención...");

        // a) Obtener valores de los inputs
        const descInput       = document.getElementById("edit-description");
        const startInput      = document.getElementById("edit-maintenance-start");
        const workshopInput   = document.getElementById("edit-workshop-name");
        const endInput        = document.getElementById("edit-maintenance-end");
        const kmInput         = document.getElementById("edit-km");
        const costInput       = document.getElementById("edit-cost");
        const commentInput    = document.getElementById("edit-comment");
        const quoteInput      = document.getElementById("edit-quotation");
        const invoiceInput    = document.getElementById("edit-invoice");

        const description        = descInput.value.trim();
        const maintenanceStart   = startInput.value ? startInput.value : null;
        const workshopName       = workshopInput.value.trim() ? workshopInput.value.trim() : null;
        const maintenanceEnd     = endInput.value ? endInput.value : null;
        const kmValue            = kmInput.value ? parseInt(kmInput.value, 10) : null;
        const costValue          = costInput.value ? parseInt(costInput.value, 10) : null;
        const commentValue       = commentInput.value.trim() ? commentInput.value.trim() : null;
        const quotationFileEdit  = quoteInput.files.length ? quoteInput.files[0] : null;
        const invoiceFileEdit    = invoiceInput.files.length ? invoiceInput.files[0] : null;

        // b) Validaciones
        if (!description || description.length < 5) {
          showToast("La descripción debe tener al menos 5 caracteres.", "warning");
          return;
        }
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (maintenanceStart !== null && !dateRegex.test(maintenanceStart)) {
          showToast("Fecha de envío inválida (YYYY-MM-DD).", "warning");
          return;
        }
        if (maintenanceEnd !== null && !dateRegex.test(maintenanceEnd)) {
          showToast("Fecha de término inválida (YYYY-MM-DD).", "warning");
          return;
        }
        if (kmValue !== null && (isNaN(kmValue) || kmValue < 0)) {
          showToast("Kilometraje debe ser un entero ≥ 0.", "warning");
          return;
        }
        if (costValue !== null && (isNaN(costValue) || costValue < 0)) {
          showToast("Costo debe ser un entero ≥ 0.", "warning");
          return;
        }

        // c) Llamar a editarSolicitudDeMantencion
        try {
          const respuesta = await editarSolicitudDeMantencion({
            requestId: requestId,
            description: description,
            // responsibleForPayment se omite si no se cambia
            maintenanceStart: maintenanceStart,
            workshopName: workshopName,
            maintenanceEnd: maintenanceEnd,
            km: kmValue,
            cost: costValue,
            comment: commentValue,
            quotationFile: quotationFileEdit,
            invoiceFile: invoiceFileEdit,
          });

          // d) Manejar respuesta
          showToast("Solicitud actualizada correctamente.", "success");
          closeModal();
          location.reload();
        } catch (error) {
          console.error("❌ Error al actualizar la solicitud:", error);
          handleError(error, "Actualización de Solicitud");
        }
      }
    }
  ];

  // 5) Abrir el modal
  openModal(`Editar Solicitud N°${requestId}`, contenido, botones);
}


/**
 * Abre un modal para confirmar la eliminación de una solicitud de mantención.
 * Si el usuario confirma, llama al endpoint DELETE para borrar la solicitud.
 *
 * @param {number} requestId - ID de la solicitud a eliminar.
 */
function mostrarModalConfirmarEliminacionSolicitud(requestId) {
  // 1) Validar requestId
  if (typeof requestId !== "number" || !Number.isInteger(requestId) || requestId <= 0) {
    console.error("requestId inválido para eliminación:", requestId);
    return;
  }

  // 2) Construir contenido HTML del modal
  const contenido = `
    <p>¿Estás seguro de que deseas eliminar la solicitud de mantención N°${requestId}?</p>
    <p class="text-danger"><strong>Esta acción no se puede deshacer.</strong></p>
  `;

  // 3) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-secondary",
      dismiss: true
    },
    {
      text: "Eliminar",
      class: "btn btn-outline-danger",
      onClick: async () => {
        console.log("🗑️ Eliminando solicitud:", requestId);

        try {
          // 4) Invocar endpoint DELETE
          const url = "/major-equipment/maintenance-request/JSON/";
          // Enviar request_id en JSON para que el backend lo lea
          const response = await sendRequest(url, "DELETE", { request_id: requestId });

          if (response.success) {
            showToast("Solicitud eliminada correctamente.", "success");
            closeModal();
            // Recargar para actualizar la lista (puede ajustarse a un reload parcial si lo deseas)
            location.reload();
          } else {
            // Si el servidor devolvió success: false, mostramos mensaje de error
            throw { status: 400, text: JSON.stringify(response) };
          }
        } catch (error) {
          console.error("❌ Error al eliminar la solicitud:", error);
          handleError(error, "Eliminación de Solicitud");
        }
      }
    }
  ];

  // 5) Abrir el modal de confirmación
  openModal(`Eliminar Solicitud N°${requestId}`, contenido, botones);
}

/**
 * Abre un modal para confirmar la aprobación de una solicitud de mantención como Comandancia.
 * Al confirmar, envía un POST a /major-equipment/maintenance-request/comandancia/ con action="accept".
 *
 * @param {number} requestId - ID de la solicitud que se va a aprobar.
 */
function mostrarModalAprobarComandancia(requestId) {
  // 1) Validar requestId
  if (typeof requestId !== "number" || !Number.isInteger(requestId) || requestId <= 0) {
    console.error("requestId inválido para aprobar:", requestId);
    return;
  }

  // 2) Construir contenido HTML del modal
  const contenido = `
    <p>¿Estás seguro de que deseas <strong>aprobar</strong> la solicitud de mantención N°${requestId} como Comandancia?</p>
    <p>Esta acción no se podrá deshacer.</p>
  `;

  // 3) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-secondary",
      dismiss: true
    },
    {
      text: "Aprobar",
      class: "btn btn-outline-success",
      onClick: async () => {
        console.log("✅ Aprobando solicitud como Comandancia:", requestId);

        try {
          const url = "/major-equipment/maintenance-request/comandancia/";
          const payload = {
            request_id: requestId,
            action: "accept"
          };
          const response = await sendRequest(url, "POST", payload);

          if (response.success) {
            showToast("Solicitud aprobada por Comandancia.", "success");
            closeModal();
            location.reload();
          } else {
            throw { status: 400, text: JSON.stringify(response) };
          }
        } catch (error) {
          console.error("❌ Error al aprobar como Comandancia:", error);
          handleError(error, "Aprobación Comandancia");
        }
      }
    }
  ];

  // 4) Abrir el modal
  openModal(`Aprobar Solicitud N°${requestId}`, contenido, botones);
}

/**
 * Abre un modal para rechazar una solicitud de mantención como Comandancia,
 * solicitando un motivo. Al confirmar, envía un POST a
 * /major-equipment/maintenance-request/comandancia/ con action="reject" y reason.
 *
 * @param {string} rawIdConPrefijo - ID de la solicitud con letra prefijo (por ejemplo "S123" o "R123").
 */
function mostrarModalRechazarComandancia(rawIdConPrefijo) {
  // 1) Extraer sólo la parte numérica del ID (quita cualquier carácter no dígito)
  const numericPart = rawIdConPrefijo.replace(/\D/g, "");
  const requestId = numericPart ? parseInt(numericPart, 10) : null;
  if (!requestId) {
    console.error("requestId inválido para rechazo:", rawIdConPrefijo);
    return;
  }

  // 2) Construir contenido HTML del modal: textarea para motivo de rechazo
  const contenido = `
    <form id="form-rechazo-comandancia">
      <div class="mb-3">
        <label for="rechazo-reason" class="form-label">
          <strong>Motivo de rechazo</strong>
        </label>
        <textarea
          id="rechazo-reason"
          class="form-control"
          rows="3"
          placeholder="Escribe aquí el motivo del rechazo..."
          required
        ></textarea>
      </div>
    </form>
  `;

  // 3) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-secondary",
      dismiss: true
    },
    {
      text: "Rechazar",
      class: "btn btn-outline-danger",
      onClick: async () => {
        // Obtener el motivo ingresado
        const reasonInput = document.getElementById("rechazo-reason");
        const reason = reasonInput.value.trim();

        if (!reason) {
          showToast("Debes indicar un motivo para el rechazo.", "warning");
          return;
        }

        console.log("⛔ Rechazando solicitud como Comandancia:", requestId, "Motivo:", reason);

        try {
          const url = "/major-equipment/maintenance-request/comandancia/";
          const payload = {
            request_id: requestId,
            action: "reject",
            reason: reason
          };

          const response = await sendRequest(url, "POST", payload);

          if (response.success) {
            showToast("Solicitud rechazada por Comandancia.", "success");
            closeModal();
            location.reload();
          } else {
            throw { status: 400, text: JSON.stringify(response) };
          }
        } catch (error) {
          console.error("❌ Error al rechazar como Comandancia:", error);
          handleError(error, "Rechazo Comandancia");
        }
      }
    }
  ];

  // 4) Abrir el modal
  openModal(`Rechazar Solicitud N°${requestId}`, contenido, botones);
}

/**
 * Abre un modal para confirmar la aprobación de una solicitud de mantención como Administración.
 * Al confirmar, envía un POST a /major-equipment/maintenance-request/administracion/ con action="accept".
 *
 * @param {string} rawIdConPrefijo - ID de la solicitud con letra prefijo (por ejemplo "S123" o "R123").
 */
function mostrarModalAprobarAdministracion(rawIdConPrefijo) {
  // 1) Extraer sólo la parte numérica del ID (quita cualquier carácter no dígito)
  const numericPart = rawIdConPrefijo.replace(/\D/g, "");
  const requestId = numericPart ? parseInt(numericPart, 10) : null;
  if (!requestId) {
    console.error("requestId inválido para aprobar como Administración:", rawIdConPrefijo);
    return;
  }

  // 2) Construir contenido HTML del modal
  const contenido = `
    <p>¿Estás seguro de que deseas <strong>aprobar</strong> la solicitud de mantención N°${requestId} como Administración?</p>
    <p>Esta acción no se podrá deshacer.</p>
  `;

  // 3) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-secondary",
      dismiss: true
    },
    {
      text: "Aprobar",
      class: "btn btn-outline-primary",
      onClick: async () => {
        console.log("✅ Aprobando solicitud como Administración:", requestId);

        try {
          const url = "/major-equipment/maintenance-request/administracion/";
          const payload = {
            request_id: requestId,
            action: "accept"
          };

          const response = await sendRequest(url, "POST", payload);

          if (response.success) {
            showToast("Solicitud aprobada por Administración.", "success");
            closeModal();
            location.reload();
          } else {
            throw { status: 400, text: JSON.stringify(response) };
          }
        } catch (error) {
          console.error("❌ Error al aprobar como Administración:", error);
          handleError(error, "Aprobación Administración");
        }
      }
    }
  ];

  // 4) Abrir el modal
  openModal(`Aprobar Solicitud N°${requestId}`, contenido, botones);
}

/**
 * Abre un modal para rechazar una solicitud de mantención como Administración,
 * solicitando un motivo. Al confirmar, envía un POST a
 * /major-equipment/maintenance-request/administracion/ con action="reject" y reason.
 *
 * @param {string} rawIdConPrefijo - ID de la solicitud con letra prefijo (por ejemplo "S123").
 */
function mostrarModalRechazarAdministracion(rawIdConPrefijo) {
  // 1) Extraer solo la parte numérica del ID (elimina cualquier carácter no dígito)
  const numericPart = rawIdConPrefijo.replace(/\D/g, "");
  const requestId = numericPart ? parseInt(numericPart, 10) : null;
  if (!requestId) {
    console.error("requestId inválido para rechazo (Administración):", rawIdConPrefijo);
    return;
  }

  // 2) Construir contenido HTML del modal con textarea para motivo
  const contenido = `
    <form id="form-rechazo-administracion">
      <div class="mb-3">
        <label for="rechazo-reason-admin" class="form-label">
          <strong>Motivo de rechazo</strong>
        </label>
        <textarea
          id="rechazo-reason-admin"
          class="form-control"
          rows="3"
          placeholder="Escribe aquí el motivo del rechazo..."
          required
        ></textarea>
      </div>
    </form>
  `;

  // 3) Configurar botones del modal
  const botones = [
    {
      text: "Cancelar",
      class: "btn btn-outline-secondary",
      dismiss: true
    },
    {
      text: "Rechazar",
      class: "btn btn-outline-danger",
      onClick: async () => {
        // Obtener el motivo ingresado
        const reasonInput = document.getElementById("rechazo-reason-admin");
        const reason = reasonInput.value.trim();

        if (!reason) {
          showToast("Debes indicar un motivo para el rechazo.", "warning");
          return;
        }

        console.log("⛔ Rechazando solicitud como Administración:", requestId, "Motivo:", reason);

        try {
          const url = "/major-equipment/maintenance-request/administracion/";
          const payload = {
            request_id: requestId,
            action: "reject",
            reason: reason
          };

          const response = await sendRequest(url, "POST", payload);

          if (response.success) {
            showToast("Solicitud rechazada por Administración.", "success");
            closeModal();
            location.reload();
          } else {
            throw { status: 400, text: JSON.stringify(response) };
          }
        } catch (error) {
          console.error("❌ Error al rechazar como Administración:", error);
          handleError(error, "Rechazo Administración");
        }
      }
    }
  ];

  // 4) Abrir el modal
  openModal(`Rechazar Solicitud N°${requestId}`, contenido, botones);
}

/**
 * Envía los datos necesarios para “finalizar” una solicitud de mantención
 * al endpoint `/major-equipment/finish-maintenance-request/JSON/`.
 * 
 * Parámetros:
 *   - params.requestId        : (number) ID de la MaintenanceRequest a concluir.
 *   - params.maintenanceStart : (string) Fecha de inicio de mantención en formato "YYYY-MM-DD".
 *   - params.maintenanceEnd   : (string) Fecha de fin de mantención en formato "YYYY-MM-DD".
 *   - params.workshopName     : (string) Nombre del taller.
 *   - params.km               : (number) Kilometraje al momento de la mantención.
 *   - params.cost             : (number) Costo de la mantención.
 *   - params.comment          : (string, opcional) Comentarios adicionales.
 *   - params.invoiceFile      : (File, opcional) Objeto File de la factura (por ejemplo, tomado desde un `<input type="file">`).
 * 
 */
async function finishMaintenanceRequest(params) {
  // 1. Construir un FormData para enviar multipart/form-data (motor de Django espera esto para archivos).
  const formData = new FormData();
  formData.append("request_id", params.requestId);
  formData.append("maintenance_start", params.maintenanceStart);
  formData.append("maintenance_end", params.maintenanceEnd);
  formData.append("workshop_name", params.workshopName);
  formData.append("km", params.km);
  formData.append("cost", params.cost);

  // Campos opcionales
  if (params.comment) {
    formData.append("comment", params.comment);
  }
  if (params.invoiceFile instanceof File) {
    formData.append("invoice", params.invoiceFile);
  }

  // 2. Obtener el CSRF token desde las cookies (si usas la protección estándar de Django).
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // ¿Esta cookie comienza con el nombre que buscamos?
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  // 3. Realizar la petición HTTP POST al endpoint
  const response = await fetch("/major-equipment/finish-maintenance-request/JSON/", {
    method: "POST",
    headers: {
      // No definimos Content-Type porque fetch lo establece automáticamente al usar FormData.
      "X-CSRFToken": csrftoken
    },
    body: formData
  });

  // 4. Leer la respuesta JSON
  const data = await response.json();

  // 5. Si la respuesta no es OK (HTTP 2xx), lanzar un error
  if (!response.ok) {
    // Si el backend devolvió {"success": false, "error": "...mensaje..."}
    const errorMessage = data.error || "Error desconocido al finalizar la solicitud.";
    throw new Error(errorMessage);
  }

  // 6. Si sale todo bien, devolvemos el JSON completo al llamador
  return data; // Ejemplo: { success: true, message: "Solicitud de mantención finalizada correctamente." }
};

// ============================================
// Funcion MAIN
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // ========================================
    // Elementos del DOM 
    // ========================================

    // Boton para crear un nuevo reporte de mantención.
    const newReportButton = document.getElementById('btn-new-report');
    if (!newReportButton) console.error("Botón para crear un nuevo reporte de mantención no encontrado.");
    newReportButton.addEventListener("click", () => {
        const unitId = parseInt(newReportButton.dataset.id, 10);
        mostrarModalCrearReporte(unitId);
    })

    // Boton para crear una nueva solicitud de mantención sin un reporte asociado.
    const btnNewRequest = document.getElementById("btn-new-request");

        









    // Si usas todos los tooltips de la página
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
    });

    // Boton para crear un nuevo reporte de mantención
    

    // Botones para obtener el detalle de un reporte.
    document.querySelectorAll(".btn-report").forEach(button => {
        button.addEventListener("click", async (e) => {
            const id = button.dataset.id;
            const reportId = parseInt(id.slice(1));
            if (!reportId) return;
            mostrarModalVerReporte(reportId);  
            
            /*try {
                

                // Obtener detalles del reporte por ID
                const reporte = await obtenerReporteDeMantencion(id);

                // Construir contenido HTML del modal
                const contenido = `
                    
                `;

                // Abrir el modal con los datos del reporte
                openModal(`Reporte de mantención N°${reporte.id}`, contenido, [
                    ,
                    
                ]);
            } catch (error) {
                console.error("❌ Error al cargar el reporte:", error);
                // Ya se maneja visualmente con handleError
            }*/
        });
    });
    
    // Botones para obtener el detalle de una solicitud de mantención.
    document.querySelectorAll(".btn-request").forEach(button => {
        button.addEventListener("click", async (e) => {
            let id = button.dataset.id;
            id = parseInt(id.slice(1));
            
            if (!id) return;

            try {
                // Obtener detalles de la solicitud de mantención por ID
                const solicitud = await obtenerSolicitudDeMantencion(id);
                
                // Construir contenido HTML del modal
                const contenido = `
                    <div class="d-flex flex-column gap-3">
                        ${solicitud.report ? 
                            `
                            <div class="d-flex flex-column">
                                <h5 class="mb-1">Reporte asociado</h5>
                                <div class="row">
                                    <p class="col-6"><strong>Autor:</strong> ${solicitud.report.reported_by}</p>
                                    <p class="col-6"><strong>Fecha:</strong> ${solicitud.report.created_at}</p>
                                </div>
                                <p class="mb-1"><strong>Descripción:</strong></p>
                                <p>${solicitud.report.description}</p>
                            </div>
                            <hr>
                            ` : `
                            <div>
                                <p class="text-muted text-center">No hay reporte asociado a esta solicitud.</p>
                            </div>

                            `
                        }
                        <!-- Información general -->
                        <div class="d-flex flex-column">
                            <h5 class="mb-1">Información general</h5>
                            <div class="row">
                                <p class="col-6"><strong>Solicitante:</strong> ${solicitud.requested_by}</p>
                                <p class="col-6"><strong>Fecha:</strong> ${solicitud.requested_at}</p>
                            </div>
                            <div class="row">
                                <p class="col-6"><strong>Inicio mantención:</strong> ${solicitud.maintenance_start || '--'}</p>
                                <p class="col-6"><strong>Fin mantención:</strong> ${solicitud.maintenance_end || '--'}</p>
                            </div>
                            <div class="row">
                                <p class="col-6"><strong>Taller:</strong> ${solicitud.workshop_name || '--'}</p>
                                <p class="col-6"><strong>Km al ingreso:</strong> ${solicitud.km !== null ? solicitud.km : '--'}</p>
                            </div>
                            <div class="d-flex flex-column">
                                <p class="mb-2"><strong>Descripción:</strong></p>
                                <p>${solicitud.description}</p>
                            </div>
                        </div>
                        
                        <!-- Información financiera -->
                        <div class="d-flex flex-column">
                            <h5 class="mb-1">Información financiera</h5>
                            <p><strong>Responsable de pago:</strong> ${solicitud.responsible_for_payment}</p>
                            <div class="row">
                                <p class="col-6"><strong>Costo estimado:</strong> ${solicitud.cost !== null ? `$${solicitud.cost}` : '--'}</p>
                                <p class="col-6">
                                    <strong>Cotización: </strong>
                                    ${solicitud.quotation
                                        ? `<a href="${solicitud.quotation}" target="_blank">Ver cotización</a>`
                                        : 'No disponible'
                                    }
                                </p>
                            </div>
                            <p>
                                <strong>Factura:</strong>
                                ${solicitud.invoice_url
                                    ? `<a href="${solicitud.invoice_url}" target="_blank">Ver factura</a>`
                                    : 'No disponible'
                                }
                            </p>
                            <p><strong>Comentario:</strong> ${solicitud.comment || '--'}</p>
                        </div>

                        <!-- Sección de aprobaciones -->
                        <div class="d-flex flex-column mb-3">
                            <h5 class="mb-1">Estado de la solicitud</h5>
                            
                            ${solicitud.rejection_reason ? 
                                `
                                <p><strong> Rechazada </strong></p>
                                <p><strong>Motivo de rechazo:</strong> ${solicitud.rejection_reason}</p>` :
                                `
                                <div class="row">
                                    <div class="col-6">
                                        <p><strong>Comandancia</strong></p>
                                        ${solicitud.approved_by_command ? 
                                            `<p>${solicitud.approved_by_command}</p>
                                                <p class="text-muted">${solicitud.approved_at_command}</p>` :
                                                `<p>Pendiente</p>`
                                        }
                                    </div>
                                    <div class="col-6">
                                        <p><strong>Administración</strong></p>
                                        ${solicitud.approved_by_admin ? 
                                            `<p>${solicitud.approved_by_admin}</p>
                                                <p class="text-muted">${solicitud.approved_at_admin}</p>` :
                                                `<p>Pendiente</p>`
                                        }
                                    </div>
                                </div>
                                `
                            }

                        </div>

                        <!-- Fechas de mantenimiento, taller y kilometraje -->
                        <div class="d-flex flex-column mb-3">
                        
                        </div>
                    </div>
                `;
                
                let botones;

                if (solicitud.state === "Pendiente") {
                  botones = [
                    {
                        text: "Eliminar",
                        class: "btn btn-outline-danger",
                        onClick: () => mostrarModalConfirmarEliminacionSolicitud(solicitud.id)
                    },
                    {
                        text: "Editar",
                        class: "btn btn-outline-dark",
                        onClick: () => mostrarModalEditarSolicitud(solicitud.id)
                    },
                    {
                        text: "Cerrar",
                        class: "btn btn-outline-dark",
                        dismiss: true
                    }
                  ]
                } else {
                  const botones = [
                    {
                        text: "Cerrar",
                        class: "btn btn-outline-dark",
                        dismiss: true
                    }
                    
                  ]
                }


                // Abrir el modal con los datos de la solicitud
                openModal(`Solicitud de mantención N°${solicitud.id}`, contenido, botones);
            } catch (error) {
                console.error("❌ Error al cargar la solicitud:", error);
                // Ya se maneja visualmente con handleError
            }
        });
    });

    // Botones para crear una nueva solicitud de mantención a partir de un reporte
    document.querySelectorAll(".new-request-by-report").forEach(button => {
        button.addEventListener("click", async (e) => {
            // 1) Obtener reportIdRaw (por ejemplo "R246")
            const reportIdRaw = button.dataset.reportId;  

            // Si no viene nada, abortamos
            if (!reportIdRaw) {
                console.error("Debes tener reportId en el botón.");
                return;
            }

            // 2) Extraer sólo la parte numérica de reportIdRaw
            //    Esto convierte "R246"  →  246
            const reportId = parseInt(reportIdRaw.replace(/\D/g, ""), 10);

            // Validar que el número extraído sea válido (> 0)
            if (!reportId || isNaN(reportId)) {
                console.error("reportId no es un número válido tras eliminar prefijo. reportIdRaw:", reportIdRaw);
                return;
            }

            // 3) Traer la lista de entidades para poblar el <select>
            let entidades = [];
            try {
                const entities = await sendRequest("/firebrigade/entities/JSON/", "GET");
                if (entities.success && Array.isArray(entities.entities)) {
                    entidades = entities.entities;
                } else {
                    console.error("Error al obtener entidades:", entities);
                    entidades = [];
                }
            } catch (err) {
                console.error("No se pudo cargar la lista de entidades:", err);
                handleError(
                    { status: 500, text: JSON.stringify({ error: "No se cargaron entidades." }) },
                    "Carga de Entidades"
                );
                return;
            }

            // 4) Construir el HTML del <select> de entidades
            const options = entidades
                .map(e => `<option value="${e.id}">${e.name}</option>`)
                .join("");

            // 5) Crear el contenido del modal
            const contenido = `
                <form id="form-request-from-report">
                    <div class="mb-3">
                        <label for="select-responsible-report" class="form-label">
                            <strong>Entidad de Pago</strong>
                        </label>
                        <select id="select-responsible-report" class="form-select" required>
                            <option value="">Seleccione...</option>
                            ${options}
                        </select>
                    </div>

                    <div class="mb-3">
                        <label for="input-description-report" class="form-label">
                            <strong>Descripción</strong>
                        </label>
                        <textarea
                            id="input-description-report"
                            class="form-control"
                            rows="3"
                            placeholder="Describa el problema (al menos 5 caracteres)"
                            required
                        ></textarea>
                    </div>

                    <div class="mb-3">
                        <label for="input-maintenance-start-report" class="form-label">
                            <strong>Fecha de envío a taller (opcional)</strong>
                        </label>
                        <input
                            type="date"
                            id="input-maintenance-start-report"
                            class="form-control"
                            placeholder="YYYY-MM-DD"
                        />
                    </div>

                    <div class="mb-3">
                        <label for="input-workshop-name-report" class="form-label">
                            <strong>Nombre del Taller (opcional)</strong>
                        </label>
                        <input
                            type="text"
                            id="input-workshop-name-report"
                            class="form-control"
                            placeholder="Ingrese el nombre del taller"
                        />
                    </div>

                    <div class="mb-3">
                        <label for="input-quotation-report" class="form-label">
                            <strong>Cotización (opcional)</strong>
                        </label>
                        <input
                            type="file"
                            id="input-quotation-report"
                            class="form-control"
                            accept="application/pdf"
                        />
                    </div>
                </form>
            `;

            // 6) Configurar los botones del modal
            const botones = [
                {
                    text: "Cancelar",
                    class: "btn btn-outline-dark",
                    dismiss: true,
                },
                {
                    text: "Crear",
                    class: "btn btn-outline-success",
                    onClick: async () => {
                        console.log("🚀 Creando solicitud de mantención basada en reporte...");

                        // a) Obtener valores de los inputs
                        const respSelect    = document.getElementById("select-responsible-report");
                        const descInput     = document.getElementById("input-description-report");
                        const startInput    = document.getElementById("input-maintenance-start-report");
                        const workshopInput = document.getElementById("input-workshop-name-report");
                        const quoteInput    = document.getElementById("input-quotation-report");

                        const responsibleForPayment = parseInt(respSelect.value, 10);
                        const description           = descInput.value.trim();
                        const maintenanceStart      = startInput.value ? startInput.value : null;
                        const workshopName          = workshopInput.value.trim() ? workshopInput.value.trim() : null;
                        const quotationFile         = quoteInput.files.length ? quoteInput.files[0] : null;

                        // b) Validaciones de los campos del formulario
                        if (!responsibleForPayment || isNaN(responsibleForPayment)) {
                            showToast("Por favor, selecciona una entidad de pago válida.", "warning");
                            return;
                        }
                        if (description.length < 5) {
                            showToast("La descripción debe tener al menos 5 caracteres.", "warning");
                            return;
                        }
                        if (maintenanceStart !== null) {
                            const regexDate = /^\d{4}-\d{2}-\d{2}$/;
                            if (!regexDate.test(maintenanceStart)) {
                                showToast("La fecha de envío debe tener formato YYYY-MM-DD.", "warning");
                                return;
                            }
                        }

                        // c) Llamar a crearSolicitudDeMantencion con reportId
                        try {
                            const respuesta = await crearSolicitudDeMantencion({
                                reportId: reportId,     // <-- numérico, p.ej. 246
                                unitId: null,           // <-- unitId no es requerido aquí
                                description: description,
                                responsibleForPayment: responsibleForPayment,
                                maintenanceStart: maintenanceStart,
                                workshopName: workshopName,
                                quotationFile: quotationFile,
                            });

                            // d) Si todo salió bien:
                            showToast("Solicitud de mantención creada desde reporte con éxito.", "success");
                            closeModal();
                            location.reload();
                        } catch (error) {
                            console.error("❌ Error al crear la solicitud desde reporte:", error);
                            handleError(error, "Creación de Solicitud desde Reporte");
                        }
                    },
                },
            ];

            // 7) Abrir el modal
            openModal(`Crear Solicitud desde Reporte N°${reportId}`, contenido, botones);
        });
    });

    document.querySelectorAll(".btn-aprobar-comandancia").forEach(button => {
        button.addEventListener("click", () => {
            // rawId puede venir con una letra, p. ej. "R123"
            const rawId = button.dataset.requestId; 
            if (!rawId) {
            console.error("Falta data-request-id en el botón de aprobar.");
            return;
            }
            // Extraer sólo la parte numérica (eliminar cualquier carácter no dígito)
            const numericPart = rawId.replace(/\D/g, "");
            const requestId = numericPart ? parseInt(numericPart, 10) : null;

            if (requestId) {
            mostrarModalAprobarComandancia(requestId);
            } else {
            console.error("requestId inválido tras quitar prefijo. rawId:", rawId);
            }
        });
    });

    document.querySelectorAll(".btn-rechazar-comandancia").forEach(button => {
        button.addEventListener("click", () => {
            const rawId = button.dataset.requestId;  // p.ej. "S457" o "R123"
            if (!rawId) {
            console.error("Falta data-request-id en el botón de rechazar.");
            return;
            }
            // Extraer sólo dígitos: "S457" → "457"
            const numericPart = rawId.replace(/\D/g, "");
            const requestId = numericPart ? parseInt(numericPart, 10) : null;
            if (requestId) {
            mostrarModalRechazarComandancia(rawId);
            } else {
            console.error("requestId inválido tras quitar prefijo. rawId:", rawId);
            }
        });
    });

    // Handler para “Aprobar como Administración”
    document.querySelectorAll(".btn-aprobar-administracion").forEach(button => {
        button.addEventListener("click", () => {
        const rawId = button.dataset.requestId; // p. ej. "S123" o "R123"
        if (!rawId) {
            console.error("Falta data-request-id en el botón de aprobar (Administración).");
            return;
        }
        mostrarModalAprobarAdministracion(rawId);
        });
    });

    // Handler para “Rechazar como Administración”
    document.querySelectorAll(".btn-rechazar-administracion").forEach(button => {
        button.addEventListener("click", () => {
        const rawId = button.dataset.requestId; // p. ej. "S123" o "R123"
        if (!rawId) {
            console.error("Falta data-request-id en el botón de rechazar (Administración).");
            return;
        }
        mostrarModalRechazarAdministracion(rawId);
        });
    });

    // Seleccionamos todos los botones “Finalizar”
  document.querySelectorAll(".btn-finish-request").forEach(btn => {
    btn.addEventListener("click", () => {
      const requestIdConPrefijo = btn.dataset.requestId;
      const numericPart = requestIdConPrefijo.replace(/\D/g, "");
      const requestId = numericPart ? parseInt(numericPart, 10) : null;

      // 1) Armamos el contenido HTML del formulario dentro del modal
      const formHtml = `
        <form id="form-finish-maintenance" enctype="multipart/form-data" novalidate>
          <div class="mb-3">
            <label for="maintenanceStart" class="form-label">Fecha inicio</label>
            <input type="date" class="form-control" id="maintenanceStart" name="maintenance_start" required>
          </div>
          <div class="mb-3">
            <label for="maintenanceEnd" class="form-label">Fecha fin</label>
            <input type="date" class="form-control" id="maintenanceEnd" name="maintenance_end" required>
          </div>
          <div class="mb-3">
            <label for="workshopName" class="form-label">Nombre del taller</label>
            <input type="text" class="form-control" id="workshopName" name="workshop_name" required>
          </div>
          <div class="mb-3">
            <label for="kmField" class="form-label">Kilometraje</label>
            <input type="number" class="form-control" id="kmField" name="km" min="0" required>
          </div>
          <div class="mb-3">
            <label for="costField" class="form-label">Costo (en pesos)</label>
            <input type="number" class="form-control" id="costField" name="cost" min="0" required>
          </div>
          <div class="mb-3">
            <label for="commentField" class="form-label">Comentarios (opcional)</label>
            <textarea class="form-control" id="commentField" name="comment" rows="3"></textarea>
          </div>
          <div class="mb-3">
            <label for="invoiceField" class="form-label">Factura (archivo) (opcional)</label>
            <input type="file" class="form-control" id="invoiceField" name="invoice" accept=".pdf,.jpg,.png">
          </div>
        </form>
      `;

      // 2) Configuramos el modal con openModal(título, contenidoHTML, botones)
      openModal(
        "Finalizar solicitud de mantención #" + requestId,
        formHtml,
        [
          {
            text: "Cancelar",
            class: "btn btn-outline-secondary",
            dismiss: true
          },
          {
            text: "Enviar",
            class: "btn btn-primary",
            // Esta función se ejecuta cuando se hace clic en “Enviar”
            onClick: async () => {
              // Tomamos el formulario dentro del modal
              const form = document.getElementById("form-finish-maintenance");
              
              // Validamos campos requeridos
              const maintenanceStart = document.getElementById("maintenanceStart").value;
              const maintenanceEnd   = document.getElementById("maintenanceEnd").value;
              const workshopName     = document.getElementById("workshopName").value.trim();
              const kmValue          = document.getElementById("kmField").value;
              const costValue        = document.getElementById("costField").value;
              const commentValue     = document.getElementById("commentField").value.trim();
              const invoiceInput     = document.getElementById("invoiceField");

              if (
                !maintenanceStart ||
                !maintenanceEnd ||
                !workshopName ||
                !kmValue ||
                !costValue
              ) {
                alert("Por favor completa todos los campos obligatorios.");
                return;
              }

              // Empaquetamos en params para la función finishMaintenanceRequest
              const params = {
                requestId: parseInt(requestId, 10),
                maintenanceStart,
                maintenanceEnd,
                workshopName,
                km: parseInt(kmValue, 10),
                cost: parseInt(costValue, 10),
                comment: commentValue || undefined
              };

              // Si el usuario cargó un archivo, lo agregamos
              if (invoiceInput.files.length > 0) {
                params.invoiceFile = invoiceInput.files[0];
              }

              try {
                // Deshabilitamos temporalmente el botón “Enviar” para evitar dobles clic
                const sendButton = document.querySelector(".modal-footer .btn.btn-primary");
                sendButton.disabled = true;
                sendButton.textContent = "Enviando...";

                // Llamamos al endpoint
                const result = await finishMaintenanceRequest(params);
                
                // Cerrar el modal (suponiendo que openModal genera un modal Bootstrap con atributo data-bs-dismiss)
                document.querySelector(".modal .btn[data-bs-dismiss]").click();

                // Mostrar mensaje de éxito (puedes cambiar por Toast, Alert, etc.)
                alert(result.message || "Solicitud finalizada con éxito.");

                // Opcional: recargar la página para reflejar cambios
                window.location.reload();
              } catch (err) {
                // Volver a habilitar el botón si hubo error
                document.querySelector(".modal-footer .btn.btn-primary").disabled = false;
                document.querySelector(".modal-footer .btn.btn-primary").textContent = "Enviar";
                alert("Error: " + err.message);
              }
            }
          }
        ]
      );
    });
  });
});
