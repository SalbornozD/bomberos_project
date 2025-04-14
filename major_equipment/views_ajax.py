from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import json
import logging

from major_equipment.models import MajorEquipment, MaintenanceReport
from major_equipment.utils import (
    can_create_maintenance_report,
    can_view_maintenance_report,
    can_edit_maintenance_report,
    can_delete_maintenance_report,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
@csrf_exempt  # si estás usando JS sin CSRF token
def maintenance_report_JSON(request):
    """
    API JSON para operaciones CRUD sobre reportes de mantención.

    Métodos:
        - GET: Obtener detalle de un reporte por ID (parámetro en query string).
        - POST: Crear un nuevo reporte (unit_id y description en JSON body).
        - PUT: Editar un reporte existente (id y nueva description en JSON body).
        - DELETE: Eliminar un reporte existente (id en JSON body).

    Requiere autenticación. Verifica permisos definidos en major_equipment.utils.
    """

    user = request.user

    # ----------------------------
    # GET → Obtener detalle
    # ----------------------------
    if request.method == "GET":
        report_id = request.GET.get("id")

        if not report_id:
            return JsonResponse({"success": False, "error": "Se requiere el ID del reporte."}, status=400)

        report = get_object_or_404(MaintenanceReport, id=report_id)

        if not can_view_maintenance_report(user, report):
            return HttpResponseForbidden("No tienes permisos para ver este reporte.")

        return JsonResponse({
            "success": True,
            "report": {
                "id": report.id,
                "description": report.description,
                "created_at": report.created_at.strftime("%d-%m-%Y %H:%M"),
                "reported_by": report.reported_by.get_full_name() or report.reported_by.username,
                "editable": report.editable,
                "unit": str(report.unit),
            }
        })

    # ----------------------------
    # POST, PUT, DELETE → requieren JSON válido
    # ----------------------------
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Formato JSON inválido."}, status=400)

    # ----------------------------
    # POST → Crear reporte
    # ----------------------------
    if request.method == "POST":
        if not can_create_maintenance_report(user):
            return HttpResponseForbidden("No tienes permisos para crear reportes.")

        unit_id = payload.get("unit_id")
        description = payload.get("problemDescription", "").strip()

        if not unit_id or not description:
            return JsonResponse({"success": False, "error": "Se requiere ID de unidad y descripción."}, status=400)

        unit = get_object_or_404(MajorEquipment, id=unit_id)

        MaintenanceReport.objects.create(unit=unit, reported_by=user, description=description)

        return JsonResponse({"success": True, "message": "Reporte creado correctamente."}, status=201)

    # ----------------------------
    # PUT / DELETE → Requieren ID
    # ----------------------------
    report_id = payload.get("id")
    if not report_id:
        return JsonResponse({"success": False, "error": "Se requiere el ID del reporte."}, status=400)

    report = get_object_or_404(MaintenanceReport, id=report_id)

    if not report.editable:
        return JsonResponse({"success": False, "error": "Este reporte no se puede modificar/eliminar."}, status=403)

    # ----------------------------
    # PUT → Editar reporte
    # ----------------------------
    if request.method == "PUT":
        permission_level = can_edit_maintenance_report(user, report)

        if not permission_level:
            return HttpResponseForbidden("No tienes permisos para editar este reporte.")

        if permission_level == "description":
            description = payload.get("problemDescription", "").strip()
            if not description:
                return JsonResponse({"success": False, "error": "La descripción es obligatoria."}, status=400)

            report.description = description
            report.save()

            return JsonResponse({"success": True, "message": "Reporte actualizado correctamente."})

        elif permission_level == "all":
            
            description = payload.get("problemDescription", "").strip()
            if not description:
                return JsonResponse({"success": False, "error": "La descripción es obligatoria."}, status=400)

            report.description = description
            report.save()

            return JsonResponse({"success": True, "message": "Reporte actualizado correctamente."})

    # ----------------------------
    # DELETE → Eliminar reporte
    # ----------------------------
    if request.method == "DELETE":
        if not can_delete_maintenance_report(user, report):
            return HttpResponseForbidden("No tienes permisos para eliminar este reporte.")

        report.delete()
        return JsonResponse({"success": True, "message": "Reporte eliminado correctamente."})

    return HttpResponseNotAllowed(["GET", "POST", "PUT", "DELETE"])
