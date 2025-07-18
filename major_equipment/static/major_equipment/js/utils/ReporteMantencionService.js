/**
 * Servicio de CRUD para reportes de mantención.
 */
class ReporteMantencionService {
    constructor() {
        this.api = new ApiClient('/major-equipment/maintenance-report/JSON/');
    }

    /**
     * Obtiene un reporte por su ID.
     * @param {number} reportId
     * @returns {Promise<Object>}
     */
    async obtener(reportId) {
        reportId = parseInt(reportId);
        if (!reportId || typeof reportId !== 'number') throw new Error('ID de reporte inválido');
        const response = await this.api.get(`?report_id=${reportId}`);
        return response.report;
    }

    /**
     * Crea un nuevo reporte.
     * @param {{ unitId: number, description: string }} data
     * @returns {Promise<Object>}
     */
    async crear({ unitId, description }) {
        unitId = parseInt(unitId);
        if (!unitId || typeof unitId !== 'number') throw new Error('ID de reporte inválido');
        
        const desc = description?.trim();
        if (!desc || desc.length < 5) throw new Error('La descripción debe tener al menos 5 caracteres');

        const payload = { unitId, description: desc };
        return await this.api.post('', payload);
    }

    /**
     * Actualiza un reporte existente.
     * @param {{ reportId: number, description: string }} data
     * @returns {Promise<Object>}
     */
    async editar({ reportId, description }) {
        reportId = parseInt(reportId);

        if (!reportId || typeof reportId !== 'number') {
            throw new Error('ID de reporte inválido o ausente');
        }
        
        const desc = description?.trim();
        if (!desc || desc.length < 5) {
            throw new Error('La descripción debe tener al menos 5 caracteres');
        }

        const payload = { reportId, description: desc };
        return await this.api.put('', payload);
    }

    /**
     * Elimina un reporte por su ID.
     * @param {number} report_id
     * @returns {Promise<Object>}
     */
    async eliminar(report_id) {
        if (!report_id || typeof report_id !== 'number') {
            throw new Error('ID de reporte inválido o ausente');
        }
        // Mandamos el ID en query string para DELETE
        return await this.api.delete(`?report_id=${report_id}`);
    }
}
