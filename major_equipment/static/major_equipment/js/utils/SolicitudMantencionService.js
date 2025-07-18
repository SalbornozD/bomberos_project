/**
 * Servicio de CRUD para Solicitudes de Mantencion
 * 
 * @class
 */
class SolicitudMantencionService {
    constructor(){
        this.api = new ApiClient('/major-equipment/maintenance-request/JSON/')
    }
}