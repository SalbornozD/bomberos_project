/**
 * Cliente HTTP genérico para peticiones AJAX con CSRF y FormData.
 */
class ApiClient {
    /**
     * @param {string} baseUrl - URL base para los endpoints.
     */
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.csrfToken = this._getCsrfTokenFromMeta();
    }

    /**
     * Extrae el token CSRF de la meta tag.
     * @private
     * @returns {string}
     */
    _getCsrfTokenFromMeta() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    /**
     * Construye y envía una petición HTTP.
     * @param {{url?: string, method?: string, data?: object|FormData}} options
     * @returns {Promise<any>}
     */
    async request({ url = '', method = 'GET', data = null }) {
        const fullUrl = this.baseUrl + url;
        const headers = { 'X-CSRFToken': this.csrfToken };
        let body;

        if (data instanceof FormData) {
            body = data; // El navegador añade Content-Type multipart/form-data
        } else if (data) {
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(data);
        }

        const response = await fetch(fullUrl, { method, headers, body });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${text}`);
        }
        return await response.json();
    }

    get(url = '') {
        return this.request({ url, method: 'GET' });
    }
    post(url = '', data) {
        return this.request({ url, method: 'POST', data });
    }
    put(url = '', data) {
        return this.request({ url, method: 'PUT', data });
    }
    delete(url = '') {
        return this.request({ url, method: 'DELETE' });
    }
}

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


function openModal(titleContent, bodyContent, buttons = []) {
    const modal = document.getElementById("dynamicModal");
    const title = document.getElementById("modalTitle");
    const body = document.getElementById("modalBody");
    const footer = document.getElementById("modalFooter");

    if (!modal || !title || !body || !footer) {
        console.error("Faltan elementos del modal.");
        return;
    };

    // Limpiar y asignar contenido.
    title.textContent = titleContent || "";
    body.innerHTML = bodyContent || "";
    footer.innerHTML = "";

    // Crear los botones dinámicos
    buttons.forEach(({ text = "Botón", class: btnClass = "btn btn-dark", onClick, dismiss, id, icon, attrs = {} }) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = btnClass;
        button.textContent = "";

        if (icon) {
            const iconElem = document.createElement("i");
            iconElem.className = icon;
            button.appendChild(iconElem);
            button.appendChild(document.createTextNode(" " + text));
        } else {
            button.textContent = text;
        }

        if (id) button.id = id;
        if (dismiss) button.setAttribute("data-bs-dismiss", "modal");
        if (typeof onClick === "function") button.addEventListener("click", onClick);

        // Atributos personalizados (ej: data-*)
        for (const [key, value] of Object.entries(attrs)) {
            button.setAttribute(key, value);
        }

        footer.appendChild(button);
    });

    // Mostral el modal
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modal);
    modalInstance.show();
};

function closeModal() {
    const modal = document.getElementById("dynamicModal");

    if (!modal) return;

    const modalInstance = bootstrap.Modal.getInstance(modal);
    if (modalInstance) {
        modalInstance.hide();
    }

    // Espera a que la animación termine antes de limpiar
    modal.addEventListener('hidden.bs.modal', function handleClose() {
        document.getElementById("modalTitle").innerHTML = "";
        document.getElementById("modalBody").innerHTML = "";
        document.getElementById("modalFooter").innerHTML = "";
        modal.removeEventListener('hidden.bs.modal', handleClose); // Evitar duplicaciones
    });
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
