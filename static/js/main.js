// ============================
// FUNCIONES GENERALES
// ============================

// Abre el menú lateral (navbar)
function openMenuNavbar() {
    const sideMenuNavbar = document.getElementById("sideMenuNavbar");
    const bloqWindow = document.getElementById("bloqWindow");
    sideMenuNavbar.style.right = "0";
    bloqWindow.style.display = "block";
}

// Cierra el menú lateral (navbar)
function closeMenuNavbar() {
    const sideMenuNavbar = document.getElementById("sideMenuNavbar");
    const bloqWindow = document.getElementById("bloqWindow");
    sideMenuNavbar.style.right = "-320px";
    bloqWindow.style.display = "none";
}

// Obtiene el token CSRF desde una etiqueta <meta>
function getCSRFTokenFromMeta() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
}

// Enviar solicitud AJAX con manejo de CSRF y validación de respuesta
function sendRequest(url, method = 'GET', data = {}) {
    return new Promise((resolve, reject) => {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
            options.headers['X-CSRFToken'] = getCSRFTokenFromMeta();
            options.body = JSON.stringify(data);
        }

        fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        reject({
                            status: response.status,
                            text: text
                        });
                    });
                }
                return response.text();
            })
            .then(text => {
                try {
                    const jsonData = JSON.parse(text);
                    resolve(jsonData);
                } catch (error) {
                    console.error("Respuesta no válida como JSON:", text);
                    resolve({
                        success: false,
                        error: "Respuesta del servidor no válida."
                    });
                }
            })
            .catch(error => reject(error));
    });
}

// Manejo global de errores para mostrar toast y log completo en consola
function handleError(error, context = "") {
    let mensajeUsuario = "Ha ocurrido un error inesperado.";
    let mensajeConsola = {
        contexto: context || "Sin contexto",
        errorOriginal: error
    };

    if (error && typeof error === 'object') {
        if (error.status === 403) {
            showToast("No tiene permisos para realizar esta acción.", "danger", "¡UPS! No tienes permisos.")
        } else if (error.status === 404) {

            mensajeUsuario = "No encontrado (404)";
            showToast(mensajeUsuario, "danger");
        } else if (error.status === 500) {
            mensajeUsuario = "Error interno del servidor (500)";
            showToast(mensajeUsuario, "danger");
        } else if (error.status) {
            try {
                const parsed = JSON.parse(error.text);
                mensajeUsuario = parsed.error || `Error ${error.status}`;
            } catch (e) {
                mensajeUsuario = `Error ${error.status}`;
            }
            showToast(mensajeUsuario, "danger", "¡UPS!");
        } else {
            mensajeUsuario = "Error de red o conexión.";
            showToast(mensajeUsuario, "danger");
        }

        mensajeConsola.status = error.status;
        mensajeConsola.textoCrudo = error.text;
    } else {
        mensajeUsuario = "Error desconocido.";
        showToast(mensajeUsuario, "danger");
    }
    
    console.error("🛑 Error detectado:", mensajeConsola);
}

// Muestra una notificación tipo toast (Bootstrap 5)
function showToast(message, type = 'success', title = 'Notificación') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');

    toast.className = `toast border-0 show mb-2`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // Iconos por tipo
    let iconHTML = '';
    switch (type) {
        case 'success':
            iconHTML = '✅';
            break;
        case 'danger':
            iconHTML = '❌';
            break;
        case 'warning':
            iconHTML = '⚠️';
            break;
        case 'info':
            iconHTML = 'ℹ️';
            break;
        default:
            iconHTML = '🔔';
    }

    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <span class="me-2">${iconHTML}</span>
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Cerrar"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Cierra y limpia el modal dinámico
function closeModal() {
    const modal = document.getElementById("dynamicModal");
    const modalInstance = bootstrap.Modal.getInstance(modal);
    if (modalInstance) {
        modalInstance.hide();
    }
    setTimeout(() => {
        document.getElementById("modalTitle").innerHTML = "";
        document.getElementById("modalBody").innerHTML = "";
        document.getElementById("modalSubmitButton").innerHTML = "";
    }, 300);
}

// Abre un modal con contenido dinámico
function openModal(titleContent, bodyContent, submitButtonContent, submitButtonFunction) {
    document.getElementById("modalTitle").innerText = titleContent;
    document.getElementById("modalBody").innerHTML = bodyContent;

    const oldButton = document.getElementById("modalSubmitButton");
    const newButton = oldButton.cloneNode(true);
    oldButton.replaceWith(newButton);

    newButton.innerText = submitButtonContent;

    if (submitButtonFunction) {
        newButton.addEventListener('click', submitButtonFunction);
    }

    const modal = document.getElementById("dynamicModal");
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modal);
    modalInstance.show();
}

// ============================
// INICIALIZACIÓN DEL NAVBAR
// ============================

document.addEventListener("DOMContentLoaded", () => {
    const btnMenuNavbar = document.getElementById("btnMenuNavbar");
    const btnCloseMenuNavbar = document.getElementById("btnCloseMenuNavbar");
    const bloqWindow = document.getElementById("bloqWindow");

    if (btnMenuNavbar) btnMenuNavbar.addEventListener("click", openMenuNavbar);
    if (btnCloseMenuNavbar) btnCloseMenuNavbar.addEventListener("click", closeMenuNavbar);
    if (bloqWindow) bloqWindow.addEventListener("click", closeMenuNavbar);
});
