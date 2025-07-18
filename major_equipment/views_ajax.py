from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed, QueryDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import json
import logging
from major_equipment.models import *
from .util import *
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from django.db import transaction
from datetime import datetime

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
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
    # GET → Obtener detalle de un reporte.
    # ----------------------------
    if request.method == "GET":

        # Solicitud de ID del reporte vía query string
        report_id = request.GET.get("report_id")

        if not report_id:
            return JsonResponse({"success": False, "error": "Se requiere el ID del reporte."}, status=400)

        report = get_object_or_404(MaintenanceReport, id=report_id)

        # Verificación de permisos.
        if not can_view_maintenance_report(user, report):
            return HttpResponseForbidden("No tienes permisos para ver este reporte.")
        
        data = {
            "id": report.id,
            "description": report.description,
            "created_at": report.created_at.strftime("%d-%m-%Y %H:%M"),
            "reported_by": report.reported_by.get_full_name() or report.reported_by.username,
            "editable": report.editable,
        }

        # Verificación de permisos para ver la unidad asociada al reporte.
        if can_view_unit(user, report.unit):
            data["unit"] = {
                "id": report.unit.id,
                "unit_number": report.unit.unit_number,
                "description": report.unit.short_description,
            }
        else:
            data["unit"] = {
                "id": "Sin acceso",
                "unit_number": None,
                "description": None,
            }
        

        # Retorno de datos del reporte
        return JsonResponse({
            "success": True,
            "report": data
        })

    # ----------------------------
    # POST, PUT, DELETE → requieren JSON válido
    # ----------------------------

    # Verificación de tipo de contenido
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Formato JSON inválido."}, status=400)

    # ----------------------------
    # POST → Crear reporte
    # ----------------------------
    if request.method == "POST":
        # Verificación de permisos para crear un reporte.
        if not can_create_maintenance_report(user):
            return HttpResponseForbidden("No tienes permisos para crear reportes.")
        
        # Obtención de los datos necesarios desde el payload y validaciones.
        unit_id = int(payload.get("unitId"))

        if not isinstance(unit_id, int) or unit_id <= 0:
            return JsonResponse({"success": False, "error": "El ID de la unidad debe ser un número entero positivo."}, status = 400)

        description = payload.get("description", "").strip()

        if not isinstance(description, str) or len(description) < 5:
            return JsonResponse({"success": False, "error": "La descripción debe ser una cadena de texto con al menos 5 caracteres."}, status=400)

        # Obtención de la unidad
        unit = get_object_or_404(MajorEquipment, id=unit_id)
        if not can_view_unit(user, unit):
            return HttpResponseForbidden("No tienes permisos para ver esta unidad.")
        
        # Creación del reporte en la base de datos.
        report = MaintenanceReport.objects.create(unit=unit, reported_by=user, description=description)

        # Retorno de respuesta exitosa.
        return JsonResponse(
            {
            "success": True,
            "message": "Reporte creado correctamente.",
            "report": {
                "id": report.id,
                "description": report.description,
                "created_at": report.created_at.strftime("%d-%m-%Y %H:%M"),
                "reported_by": report.reported_by.get_full_name() or report.reported_by.username,
                "editable": report.editable,
                "unit": str(report.unit),
            }
            },
            status=201)

    # ----------------------------
    # PUT / DELETE → Requieren ID
    # ----------------------------

    # Obtención del ID del reporte desde el payload
    report_id = payload.get("report_id")
    if not isinstance(report_id, int) or report_id <= 0:
        return JsonResponse({"success": False, "error": "El ID del reporte debe ser un número entero positivo."}, status = 400)

    # Obtención del reporte desde la Base de Datos.
    report = get_object_or_404(MaintenanceReport, id=report_id)

    # Verificación de estado editable del reporte. Si no es editable, no se puede modificar ni eliminar.
    # Esto con el fin de evitar modificaciones en reportes que han sido elevados a solicitudes de mantención.
    if not report.editable:
        return JsonResponse({"success": False, "error": "Este reporte no es editable."}, status=403)

    # ----------------------------
    # PUT → Editar reporte
    # ----------------------------
    if request.method == "PUT":
        # Verificación de permisos para editar el campo de descripción del reporte.
        if not can_edit_maintenance_report(user, report):
            return HttpResponseForbidden("No tienes permisos para editar este reporte.")
        
        # Obtención del campo descripción del payload.
        description = payload.get("description", "").strip()
        if not isinstance(description, str) or len(description) < 5:
            return JsonResponse({"success": False, "error": "La descripción debe ser una cadena de texto con al menos 5 caracteres."}, status=400)

        # Guardar la nueva descripción en el reporte.
        report.description = description
        report.save()

        # Retorno de respuesta exitosa.
        return JsonResponse({
            "success": True,
            "message": "Reporte actualizado correctamente.",
            "report": {
                "id": report.id,
                "description": report.description,
                "created_at": report.created_at.strftime("%d-%m-%Y %H:%M"),
                "reported_by": report.reported_by.get_full_name() or report.reported_by.username,
                "editable": report.editable,
                "unit": str(report.unit),
            }
        }, status=200)

    # ----------------------------
    # DELETE → Eliminar reporte
    # ----------------------------
    if request.method == "DELETE":
        # Verificación de permisos para eliminar el reporte.
        if not can_delete_maintenance_report(user, report):
            return HttpResponseForbidden("No tienes permisos para eliminar este reporte.")
        
        # Eliminación del reporte de la base de datos.
        report.delete()
        return JsonResponse({"success": True, "message": "Reporte eliminado correctamente."})

    return HttpResponseNotAllowed(["GET", "POST", "PUT", "DELETE"])

@login_required
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def maintenance_request_JSON(request):
    """
    API JSON para operaciones CRUD sobre solicitudes de mantención.

    URL: /major-equipment/maintenance-request/JSON/

    Métodos:
      - GET:
          • Consulta el detalle de una solicitud de mantención por ID.
          • Parámetro 'request_id' en query string.
      - POST:
          • Crea una nueva solicitud.
          • Cuerpo en JSON o multipart/form-data.
      - PUT:
          • Actualiza los campos de una solicitud existente.
          • Cuerpo en JSON o multipart/form-data.
          • Debe enviarse 'request_id' (en body o query string).
      - DELETE:
          • Elimina una solicitud existente.
          • Debe enviarse 'request_id' (en body o query string).

    Requiere autenticación. Verifica permisos según "major_equipment.utils".
    """

    user = request.user

    # === BLOQUE COMÚN: procesar parsed_data y parsed_files para POST, PUT y DELETE ===
    if request.method in ["POST", "PUT", "DELETE"]:
        content_type = request.content_type or ""
        parsed_data = {}
        parsed_files = {}

        try:
            if content_type.startswith("application/json"):
                raw_body = request.body.decode("utf-8") or "{}"
                parsed_data = json.loads(raw_body)

            elif content_type.startswith("multipart/form-data"):
                parser = MultiPartParser(request.META, request, request.upload_handlers)
                data_qdict, parsed_files = parser.parse()
                parsed_data = data_qdict.dict()

            else:
                # x-www-form-urlencoded o fallback
                data_qdict = request.POST
                if isinstance(data_qdict, QueryDict):
                    parsed_data = data_qdict.dict()
                else:
                    parsed_data = dict(data_qdict)
        except (json.JSONDecodeError, MultiPartParserError) as e:
            return JsonResponse(
                {"success": False, "error": f"Error procesando datos: {e}"},
                status=400
            )

        # Para PUT y DELETE, leer request_id
        request_id = parsed_data.get("request_id") or request.GET.get("request_id")
    else:
        # Solo para GET
        request_id = None
        parsed_data = {}
        parsed_files = {}

    # ===== GET =====
    if request.method == "GET":
        # 1) Leer 'request_id' de query string
        raw_id = request.GET.get("request_id")
        try:
            request_id = int(raw_id) if raw_id else None
        except (ValueError, TypeError):
            request_id = None

        if not request_id:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un ID válido."},
                status=400
            )

        # 2) Obtener la solicitud o 404
        maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

        # 3) Verificar permisos de visualización
        if not can_view_maintenance_request(user, maintenance_request):
            return JsonResponse(
                {"success": False, "error": "No tienes permisos para ver esta solicitud."},
                status=403
            )

        # 4) Construir payload de respuesta
        data = {
            "id": maintenance_request.id,
            "requested_by": get_user_string(maintenance_request.requested_by),
            "requested_at": maintenance_request.requested_at.strftime("%d-%m-%Y %H:%M"),
            "description": maintenance_request.description,
            "responsible_for_payment": maintenance_request.responsible_for_payment.name,
            "quotation": maintenance_request.quotation.url if maintenance_request.quotation else None,
            "approved_by_command": (
                get_user_string(maintenance_request.approved_by_command)
                if maintenance_request.approved_by_command else None
            ),
            "approved_at_command": (
                maintenance_request.approved_at_command.strftime("%d-%m-%Y %H:%M")
                if maintenance_request.approved_at_command else None
            ),
            "approved_by_admin": (
                get_user_string(maintenance_request.approved_by_admin)
                if maintenance_request.approved_by_admin else None
            ),
            "approved_at_admin": (
                maintenance_request.approved_at_admin.strftime("%d-%m-%Y %H:%M")
                if maintenance_request.approved_at_admin else None
            ),
            "rejection_reason": maintenance_request.rejection_reason or None,
            # Campos relacionados al taller
            "maintenance_start": (
                maintenance_request.maintenance_start.strftime("%Y-%m-%d")
                if maintenance_request.maintenance_start else None
            ),
            "workshop_name": maintenance_request.workshop_name or None,
            # Otros campos opcionales
            "maintenance_end": (
                maintenance_request.maintenance_end.strftime("%Y-%m-%d")
                if maintenance_request.maintenance_end else None
            ),
            "km": maintenance_request.km or None,
            "cost": maintenance_request.cost or None,
            "invoice_url": maintenance_request.invoice.url if maintenance_request.invoice else None,
            "comment": maintenance_request.comment or None,
            "state": maintenance_request.get_state(),
        }

        # 5) Incluir datos de reporte asociado si existe y permisos
        report = maintenance_request.report
        if report and can_view_maintenance_report(user, report):
            data["report"] = {
                "id": report.id,
                "description": report.description,
                "created_at": report.created_at.strftime("%d-%m-%Y %H:%M"),
                "reported_by": (
                    report.reported_by.get_full_name() or report.reported_by.username
                ),
                "editable": report.editable,
            }
        else:
            data["report"] = None

        # 6) Incluir datos de la unidad asociada si existe y permisos
        unit = maintenance_request.unit
        if unit and can_view_unit(user, unit):
            data["unit"] = {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "description": unit.short_description,
            }
        else:
            data["unit"] = None

        return JsonResponse({"success": True, "data": data}, status=200)

    # ===== POST =====
    if request.method == "POST":
        # 1) Verificar permiso de creación
        if not can_create_maintenance_request(user):
            return JsonResponse(
                {"success": False, "error": "No tienes permisos para crear solicitudes de mantención."},
                status=403
            )

        # 2) Extraer campos (puede venir report_id o unit_id)
        description = parsed_data.get("description", "").strip()
        report_id = parsed_data.get("report_id")
        unit_id = parsed_data.get("unit_id")
        resp_id = parsed_data.get("responsible_for_payment")

        # 3) Validar que venga exactamente report_id O unit_id (no ambos, no ninguno)
        if (not report_id and not unit_id) or (report_id and unit_id):
            return JsonResponse(
                {"success": False, "error": "Debes indicar solo report_id o unit_id."},
                status=400
            )

        # 4) Validar que description y responsible_for_payment existan
        if not description or not resp_id:
            return JsonResponse(
                {"success": False, "error": "Faltan campos obligatorios (description o responsible_for_payment)."},
                status=400
            )

        # 5) Validar longitud mínima de description
        if len(description) < 5:
            return JsonResponse(
                {"success": False, "error": "La descripción debe tener al menos 5 caracteres."},
                status=400
            )

        # 6) Convertir resp_id a entero
        try:
            resp_id = int(resp_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {"success": False, "error": "responsible_for_payment debe ser un número válido."},
                status=400
            )

        # 7) Validar existencia de la entidad de pago
        try:
            entity = Entity.objects.get(pk=resp_id)
        except Entity.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Entidad de pago inválida."},
                status=404
            )

        # 8) Campos opcionales de taller
        maintenance_start = None
        workshop_name = None
        raw_start = parsed_data.get("maintenance_start")
        if raw_start:
            try:
                maintenance_start = datetime.strptime(raw_start, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "error": "maintenance_start debe estar en formato YYYY-MM-DD."},
                    status=400
                )
        workshop_name = parsed_data.get("workshop_name", "").strip() or None

        # 9) Obtener archivo de cotización si existe
        quotation_file = parsed_files.get("quotation") if parsed_files else request.FILES.get("quotation")

        # 10) Crear la solicitud dentro de una transacción
        try:
            with transaction.atomic():
                if report_id:
                    # 10.a) Validar report_id
                    try:
                        report = MaintenanceReport.objects.select_for_update().get(pk=int(report_id))
                    except (ValueError, MaintenanceReport.DoesNotExist):
                        return JsonResponse(
                            {"success": False, "error": "Reporte no encontrado."},
                            status=404
                        )

                    if not report.editable:
                        return JsonResponse(
                            {"success": False, "error": "El reporte ya está vinculado a otra solicitud."},
                            status=400
                        )

                    # Obtener unidad desde el reporte y marcar report.editable = False
                    unit = report.unit
                    report.editable = False
                    report.save(update_fields=["editable"])

                else:
                    # 10.b) Validar unidad directamente
                    try:
                        unit = MajorEquipment.objects.get(pk=int(unit_id))
                        report = None
                    except (ValueError, MajorEquipment.DoesNotExist):
                        return JsonResponse(
                            {"success": False, "error": "Unidad no encontrada."},
                            status=404
                        )

                # 10.c) Crear la instancia de MaintenanceRequest
                maintenance_request = MaintenanceRequest.objects.create(
                    unit=unit,
                    report=report,
                    requested_by=user,
                    description=description,
                    responsible_for_payment=entity,
                    quotation=quotation_file,
                    maintenance_start=maintenance_start,
                    workshop_name=workshop_name,
                )

        except ValidationError as ve:
            return JsonResponse(
                {"success": False, "error": str(ve)},
                status=400
            )

        # 11) Responder con éxito
        return JsonResponse(
            {
                "success": True,
                "message": "Solicitud creada correctamente.",
                "maintenance_request_id": maintenance_request.id,
            },
            status=201
        )

    # ===== PUT =====
    if request.method == "PUT":
        # 1) Validar que venga un request_id válido
        try:
            request_id = int(request_id) if request_id else None
        except (ValueError, TypeError):
            request_id = None

        if not request_id:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un ID válido para actualizar."},
                status=400
            )

        # 2) Obtener la solicitud y validar permisos de edición
        maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
        if not can_edit_maintenance_request(user, maintenance_request):
            return JsonResponse(
                {"success": False, "error": "No tienes permisos para editar esta solicitud."},
                status=403
            )

        # 3) Campos que se pueden actualizar
        # — description
        if "description" in parsed_data:
            desc = parsed_data.get("description", "").strip()
            if desc:
                if len(desc) < 5:
                    return JsonResponse(
                        {"success": False, "error": "La descripción debe tener al menos 5 caracteres."},
                        status=400
                    )
                maintenance_request.description = desc

        # — responsible_for_payment
        if "responsible_for_payment" in parsed_data:
            try:
                resp_id = int(parsed_data.get("responsible_for_payment"))
                entity = Entity.objects.get(pk=resp_id)
                maintenance_request.responsible_for_payment = entity
            except (ValueError, TypeError, Entity.DoesNotExist):
                return JsonResponse(
                    {"success": False, "error": "Entidad de pago inválida."},
                    status=404
                )

        # — Cotización (archivo nuevo)
        quotation_file = parsed_files.get("quotation") if parsed_files else request.FILES.get("quotation")
        if quotation_file:
            maintenance_request.quotation = quotation_file

        # — Campos de taller
        if "maintenance_start" in parsed_data:
            raw_start = parsed_data.get("maintenance_start")
            if raw_start:
                try:
                    maintenance_request.maintenance_start = datetime.strptime(raw_start, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    return JsonResponse(
                        {"success": False, "error": "maintenance_start debe estar en formato YYYY-MM-DD."},
                        status=400
                    )

        if "workshop_name" in parsed_data:
            name = parsed_data.get("workshop_name", "").strip()
            maintenance_request.workshop_name = name or None

        if "maintenance_end" in parsed_data:
            raw_end = parsed_data.get("maintenance_end")
            if raw_end:
                try:
                    maintenance_request.maintenance_end = datetime.strptime(raw_end, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    return JsonResponse(
                        {"success": False, "error": "maintenance_end debe estar en formato YYYY-MM-DD."},
                        status=400
                    )

        if "km" in parsed_data:
            try:
                maintenance_request.km = int(parsed_data.get("km"))
            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "error": "km debe ser un número entero."},
                    status=400
                )

        if "cost" in parsed_data:
            try:
                maintenance_request.cost = int(parsed_data.get("cost"))
            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "error": "cost debe ser un número entero."},
                    status=400
                )

        if "comment" in parsed_data:
            maintenance_request.comment = parsed_data.get("comment", "").strip() or None

        # 4) Guardar cambios
        maintenance_request.save()

        return JsonResponse(
            {"success": True, "message": "Solicitud actualizada correctamente."},
            status=200
        )

    # ===== DELETE =====
    if request.method == "DELETE":
        # 1) Validar que venga un request_id válido
        try:
            request_id = int(request_id) if request_id else None
        except (ValueError, TypeError):
            request_id = None

        if not request_id:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un ID válido para eliminar."},
                status=400
            )

        # 2) Obtener la solicitud y validar permisos de eliminación
        maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
        if not can_delete_maintenance_request(user, maintenance_request):
            return JsonResponse(
                {"success": False, "error": "No tienes permisos para eliminar esta solicitud."},
                status=403
            )

        # 3) Al eliminar, si había un reporte vinculado, liberar su flag editable
        report = maintenance_request.report
        if report:
            report.editable = True
            report.save(update_fields=["editable"])

        maintenance_request.delete()
        return JsonResponse(
            {"success": True, "message": "Solicitud eliminada correctamente."},
            status=200
        )

    # ===== MÉTODO NO SOPORTADO =====
    return JsonResponse(
        {"success": False, "error": "Método no soportado."},
        status=405
    )


def _parse_request_body(request):
    """
    Retorna (parsed_data, parsed_files) igual que en maintenance_request_JSON.
    parsed_data es un dict; parsed_files es un dict de archivos.
    """
    content_type = request.content_type or ""
    parsed_data = {}
    parsed_files = {}

    try:
        if content_type.startswith("application/json"):
            raw_body = request.body.decode("utf-8") or "{}"
            parsed_data = json.loads(raw_body)

        elif content_type.startswith("multipart/form-data"):
            parser = MultiPartParser(request.META, request, request.upload_handlers)
            data_qdict, parsed_files = parser.parse()
            parsed_data = data_qdict.dict()

        else:
            data_qdict = request.POST
            if isinstance(data_qdict, QueryDict):
                parsed_data = data_qdict.dict()
            else:
                parsed_data = dict(data_qdict)
    except (json.JSONDecodeError, MultiPartParserError) as e:
        raise ValidationError(f"Error procesando datos: {e}")

    return parsed_data, parsed_files


# ================================================================
# Endpoint 1: Aprobación / Rechazo desde Comandancia
# ================================================================
@login_required
@require_http_methods(["POST"])
def maintenance_request_comandancia(request):
    """
    Permite a usuarios con permiso 'approve_maintenance_as_command' aprobar o rechazar
    una solicitud de mantención. JSON esperado:
      {
        "request_id": <int>,
        "action": "accept" | "reject",
        // si action == "reject", también:
        "reason": "<texto motivo>"
      }
    """
    user = request.user

    # 1) Parsear cuerpo
    try:
        parsed_data, parsed_files = _parse_request_body(request)
    except ValidationError as ve:
        return JsonResponse({"success": False, "error": str(ve)}, status=400)

    # 2) Leer campos obligatorios
    request_id = parsed_data.get("request_id")
    action = parsed_data.get("action")

    # 3) Validar request_id
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "request_id inválido."}, status=400)

    # 4) Obtener la solicitud o 404
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # 5) Verificar permiso de Comandancia
    if not user.has_perm("major_equipment.approve_maintenance_as_command"):
        return JsonResponse({"success": False, "error": "No tienes permiso para aprobar como Comandancia."}, status=403)

    # 6) Verificar que la solicitud no esté ya rechazada o aprobada completamente
    if maintenance_request.rejection_reason:
        return JsonResponse({"success": False, "error": "La solicitud ya fue rechazada."}, status=400)
    if maintenance_request.approved_by_command:
        return JsonResponse({"success": False, "error": "La solicitud ya fue aprobada por Comandancia."}, status=400)

    # 7) Acción accept / reject
    if action == "accept":
        try:
            maintenance_request.approve_by_command(user)
        except PermissionError as pe:
            return JsonResponse({"success": False, "error": str(pe)}, status=403)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error al aprobar: {e}"}, status=400)

        return JsonResponse(
            {"success": True, "message": "Solicitud aprobada por Comandancia."},
            status=200
        )

    elif action == "reject":
        reason = parsed_data.get("reason", "").strip()
        if not reason:
            return JsonResponse({"success": False, "error": "Debes indicar un motivo de rechazo."}, status=400)

        # Aquí no usamos el método model.reject (que exige ambos permisos),
        # sino que asignamos rejection_reason directamente
        maintenance_request.rejection_reason = reason
        maintenance_request.save(update_fields=["rejection_reason"])

        return JsonResponse(
            {"success": True, "message": "Solicitud rechazada por Comandancia."},
            status=200
        )

    else:
        return JsonResponse(
            {"success": False, "error": "Acción inválida. Usa 'accept' o 'reject'."},
            status=400
        )

# ================================================================
# Endpoint 2: Aprobación / Rechazo desde Administración
# ================================================================
@login_required
@require_http_methods(["POST"])
def maintenance_request_administracion(request):
    """
    Permite a usuarios con permiso 'approve_maintenance_as_admin' aprobar o rechazar
    una solicitud de mantención. JSON esperado:
      {
        "request_id": <int>,
        "action": "accept" | "reject",
        // si action == "reject", también:
        "reason": "<texto motivo>"
      }
    """
    user = request.user

    # 1) Parsear cuerpo
    try:
        parsed_data, parsed_files = _parse_request_body(request)
    except ValidationError as ve:
        return JsonResponse({"success": False, "error": str(ve)}, status=400)

    # 2) Leer campos obligatorios
    request_id = parsed_data.get("request_id")
    action = parsed_data.get("action")

    # 3) Validar request_id
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "request_id inválido."}, status=400)

    # 4) Obtener la solicitud o 404
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # 5) Verificar permiso de Administración
    if not user.has_perm("major_equipment.approve_maintenance_as_admin"):
        return JsonResponse({"success": False, "error": "No tienes permiso para aprobar como Administración."}, status=403)

    # 6) Verificar que la solicitud no esté ya rechazada o aprobada por admin
    if maintenance_request.rejection_reason:
        return JsonResponse({"success": False, "error": "La solicitud ya fue rechazada."}, status=400)
    if maintenance_request.approved_by_admin:
        return JsonResponse({"success": False, "error": "La solicitud ya fue aprobada por Administración."}, status=400)

    # 7) Acción accept / reject
    if action == "accept":
        try:
            maintenance_request.approve_by_admin(user)
        except PermissionError as pe:
            return JsonResponse({"success": False, "error": str(pe)}, status=403)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error al aprobar: {e}"}, status=400)

        return JsonResponse(
            {"success": True, "message": "Solicitud aprobada por Administración."},
            status=200
        )

    elif action == "reject":
        reason = parsed_data.get("reason", "").strip()
        if not reason:
            return JsonResponse({"success": False, "error": "Debes indicar un motivo de rechazo."}, status=400)

        # Si ya hubo aprobación por comandancia, mantenemos ese campo y solo agregamos rejection_reason
        maintenance_request.rejection_reason = reason
        maintenance_request.save(update_fields=["rejection_reason"])

        return JsonResponse(
            {"success": True, "message": "Solicitud rechazada por Administración."},
            status=200
        )

    else:
        return JsonResponse(
            {"success": False, "error": "Acción inválida. Usa 'accept' o 'reject'."},
            status=400
        )
    
@login_required
@require_http_methods(["POST"])
def finish_maintenance_request_JSON(request):
    """
    Endpoint para “concluir” (finalizar) una solicitud de mantención.
    Requiere multipart/form-data si se va a subir archivo de factura; en caso contrario,
    puede enviarse un formulario sin la parte de 'invoice'.

    Parámetros esperados en request.POST (todos como strings):
      - request_id           : ID de la solicitud a concluir (obligatorio).
      - maintenance_start    : Fecha de inicio de mantención (YYYY-MM-DD) (obligatorio).
      - maintenance_end      : Fecha de fin de mantención (YYYY-MM-DD) (obligatorio).
      - workshop_name        : Nombre del taller (obligatorio).
      - km                   : Kilometraje al momento de la mantención (entero) (obligatorio).
      - cost                 : Costo de la mantención (entero) (obligatorio).
      - comment              : Comentarios adicionales (opcional).
    Parámetros esperados en request.FILES:
      - invoice              : Archivo de factura (opcional).

    Flujo:
      1. Verifica que el usuario tenga permiso "major_equipment.finish_maitenance".
      2. Valida que `request_id` esté presente y sea entero.
      3. Busca la instancia de MaintenanceRequest; si no existe, retorna 404.
      4. Verifica que esté aprobada por Comandancia y por Administración y no tenga razón de rechazo.
      5. Valida los campos de fecha y numéricos.
      6. Guarda los datos de conclusión en la solicitud y retorna éxito.
    """

    # 1. Permiso para finalizar la solicitud
    if not request.user.has_perm("major_equipment.finish_maitenance"):
        return JsonResponse(
            {"success": False, "error": "No tienes permiso para finalizar solicitudes de mantención."},
            status=403
        )

    # 2. Obtener y validar request_id
    request_id_str = request.POST.get("request_id")
    if not request_id_str:
        return JsonResponse(
            {"success": False, "error": "Falta el parámetro 'request_id'."},
            status=400
        )

    try:
        request_id = int(request_id_str)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "'request_id' debe ser un número entero."},
            status=400
        )

    # 3. Buscar la solicitud de mantención
    try:
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
    except MaintenanceRequest.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Solicitud de mantención no encontrada."},
            status=404
        )

    # 4. Verificar que la solicitud esté aprobada por ambos y no esté rechazada
    if maintenance_request.rejection_reason:
        return JsonResponse(
            {"success": False, "error": "La solicitud ya fue rechazada; no puede concluirse."},
            status=400
        )
    if not maintenance_request.approved_by_command or not maintenance_request.approved_by_admin:
        return JsonResponse(
            {
                "success": False,
                "error": "La solicitud debe estar aprobada por Comandancia y por Administración antes de finalizarla."
            },
            status=400
        )

    # Opcional: si ya se han llenado fechas de inicio/fin, podría considerarse ya concluida
    if maintenance_request.maintenance_start and maintenance_request.maintenance_end:
        return JsonResponse(
            {"success": False, "error": "Esta solicitud ya fue finalizada previamente."},
            status=400
        )

    # 5. Obtener y validar los campos de finalización
    # Fechas
    start_str = request.POST.get("maintenance_start")
    end_str   = request.POST.get("maintenance_end")
    if not start_str or not end_str:
        return JsonResponse(
            {"success": False, "error": "Debes enviar 'maintenance_start' y 'maintenance_end'."},
            status=400
        )

    try:
        maintenance_start = datetime.date.fromisoformat(start_str)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Formato inválido para 'maintenance_start'. Debe ser YYYY-MM-DD."},
            status=400
        )

    try:
        maintenance_end = datetime.date.fromisoformat(end_str)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Formato inválido para 'maintenance_end'. Debe ser YYYY-MM-DD."},
            status=400
        )

    if maintenance_end < maintenance_start:
        return JsonResponse(
            {"success": False, "error": "'maintenance_end' no puede ser anterior a 'maintenance_start'."},
            status=400
        )

    # Texto y numéricos
    workshop_name = request.POST.get("workshop_name", "").strip()
    km_str        = request.POST.get("km")
    cost_str      = request.POST.get("cost")

    if not workshop_name or not km_str or not cost_str:
        return JsonResponse(
            {
                "success": False,
                "error": "Debes enviar 'workshop_name', 'km' y 'cost' para finalizar la solicitud."
            },
            status=400
        )

    try:
        km = int(km_str)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "'km' debe ser un número entero."},
            status=400
        )

    try:
        cost = int(cost_str)
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "'cost' debe ser un número entero."},
            status=400
        )

    comment = request.POST.get("comment", "").strip()

    # 6. Si se subió una factura (invoice), la asignamos; en caso contrario, no tocar ese campo.
    invoice_file = request.FILES.get("invoice")
    if invoice_file:
        maintenance_request.invoice = invoice_file

    # 7. Asignar valores a los campos del modelo
    maintenance_request.maintenance_start = maintenance_start
    maintenance_request.maintenance_end = maintenance_end
    maintenance_request.workshop_name = workshop_name
    maintenance_request.km = km
    maintenance_request.cost = cost
    maintenance_request.comment = comment
    maintenance_request.editable = False

    # Guardamos la instancia
    maintenance_request.save()

    return JsonResponse(
        {"success": True, "message": "Solicitud de mantención finalizada correctamente."}
    )