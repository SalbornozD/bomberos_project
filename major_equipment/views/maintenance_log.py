from django.utils                               import timezone
from django.shortcuts                           import render, get_object_or_404, redirect
from django.contrib.auth.decorators             import login_required

# MODELOS
from major_equipment.models.unit                import *
from major_equipment.models.maintenance_log     import *

# Utilidades
from ..utils.permission                          import *
from ..utils.calendar                            import *

# Librerias
from django.contrib                             import messages

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

@login_required # Crear solicitud de mantención
def view_create_maintenance_request(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)

    # Inicializamos contexto para GET o POST fallido
    form_data = {
        'description': '',
        'responsible_for_payment': ''
    }
    errors = {}

    if request.method == "POST":
        # 1. Recogemos datos
        description = request.POST.get('description', '').strip()
        resp_choice = request.POST.get('responsible_for_payment', '')

        form_data['description'] = description
        form_data['responsible_for_payment'] = resp_choice

        # 2. Validaciones
        if not description:
            errors['description'] = "La descripción es obligatoria."
        if resp_choice not in ("bomberos", "company"):
            errors['responsible_for_payment'] = "Debes seleccionar quién paga."

        # 3. Si pasa validación, creamos el MaintenanceLog
        if not errors:
            # Obtener la entidad “Cuerpo de Bomberos”
            # Ajusta este filtro a tu modelo: 
            # por ejemplo un flag is_institutional o un slug concreto.

            if resp_choice == "bomberos":
                entidad_pago = Entity.objects.get(type='ADMIN')
                print(entidad_pago)
            else:
                user = request.user
                print(user)
                entidad_pago = get_user_entity(user)
                print(entidad_pago)

            log = MaintenanceLog.objects.create(
                unit=unit,
                description=description,
                responsible_for_payment=entidad_pago,
                author=request.user
            )
            # Redirige, por ejemplo, al detalle de la solicitud o a la lista
            return redirect('major_equipment:unit_maintenance', unit_id=unit_id)

    # Renderizamos (GET o POST con errores)
    return render(request, 
                  "major_equipment/maintenance/forms/maintenance_form.html", 
                  {
                      'unit': unit,
                      'form_data': form_data,
                      'errors': errors,
                  })

@login_required  # Agregar cotización
def view_add_quotation(request, unit_id, log_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    maintenance_log = get_object_or_404(MaintenanceLog, pk=log_id)

    # Verificar si la solicitud de mantención es editable
    if not maintenance_log.editable:
        messages.error(request, "Esta solicitud ya no permite agregar cotizaciones.")
        return redirect("major_equipment:unit_maintenance", unit_id=unit.id)

    if request.method == "POST":
        quote_pdf = request.FILES.get("quote_pdf")
        cost = request.POST.get("cost")
        expiration_date = request.POST.get("expiration_date")
        comment = request.POST.get("comment", "")
        workshop = request.POST.get("workshop", "")

        if not quote_pdf or not cost or not expiration_date or not workshop:
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, "major_equipment/maintenance/forms/quote_form.html", {
                "unit": unit,
                "maintenance_log": maintenance_log,
            })

        # Guardar archivo PDF en File
        file_instance = File.objects.create(
            file=quote_pdf,
            short_name=quote_pdf.name  # Aquí usamos el nombre original del archivo
        )

        # Crear cotización
        Quotation.objects.create(
            log=maintenance_log,
            file=file_instance,
            cost=cost,
            expiration_date=expiration_date,
            comment=comment,
            workshop_name=workshop,
            author=request.user
        )

        messages.success(request, "Cotización registrada correctamente.")
        return redirect("major_equipment:unit_maintenance", unit_id=unit.id)

    # Si es GET
    return render(request, "major_equipment/maintenance/forms/quote_form.html", {
        "unit": unit,
        "maintenance_log": maintenance_log,
    })

@login_required # Listado de mantenciones.
def view_unit_maintenance(request, unit_id):
    data = {}
    unit = get_object_or_404(Unit, pk=unit_id)
    data["unit"] = unit
    data["maintenance_logs"] = MaintenanceLog.objects.filter(unit=unit).order_by("-creation_date")
    return render(request, "major_equipment/maintenance/unit_maintenance.html", data)

@login_required # Detalle de mantención
def view_get_maintenance_log(request, unit_id, maintenance_log_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    data["maintenance_log"] = get_object_or_404(MaintenanceLog, pk=maintenance_log_id)
    data['quotations'] = Quotation.objects.filter(log=data["maintenance_log"]).order_by('-creation_date')
    data['can_create_meeting_workshop'] = True
    data['can_create_unit_shipment'] = True
    data['can_create_unit_reception'] = True
    return render(request, "major_equipment/maintenance/maintenance_log.html", data)

@login_required
def view_command_evaluation(request, unit_id, log_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    maintenance_log = get_object_or_404(MaintenanceLog, pk=log_id)
    quotations = Quotation.objects.filter(log=maintenance_log, deleted=False).order_by('-creation_date')

    if request.method == "POST":
        decision = request.POST.get("decision")

        # Aprueba Comandancia
        if decision == "accept":
            quotation_id = request.POST.get("quotation")
            command_observations = request.POST.get("success_observations", "").strip()

            if not quotation_id:
                messages.error(request, "Debe seleccionar una cotización para aprobar.")
            else:
                # Marcar cotización favorita (opcional)
                Quotation.objects.filter(log=maintenance_log).update(is_favorite=False)
                Quotation.objects.filter(pk=quotation_id).update(is_favorite=True)

                maintenance_log.approved_by_command = True
                maintenance_log.command_observations = command_observations
                maintenance_log.reviewed_by_command = request.user
                maintenance_log.command_reviewed_date = timezone.now()
                maintenance_log.save()

                messages.success(request, "Solicitud aprobada correctamente por Comandancia.")
                return redirect("major_equipment:unit_maintenance", unit.id)

        # Rechaza Comandancia
        elif decision == "reject":
            reject_reason = request.POST.get("reject_reason", "").strip()
            if not reject_reason:
                messages.error(request, "Debe indicar la razón del rechazo.")
            else:
                maintenance_log.approved_by_command = False
                maintenance_log.command_observations = reject_reason
                maintenance_log.reviewed_by_command = request.user
                maintenance_log.command_reviewed_date = timezone.now()
                maintenance_log.save()

                messages.success(request, "Solicitud rechazada correctamente por Comandancia.")
                return redirect("major_equipment:unit_maintenance", unit.id)
        else:
            messages.error(request, "Debe seleccionar si aprueba o rechaza la solicitud.")

    # Si es GET o hay errores, renderizamos de nuevo el formulario
    context = {
        "unit": unit,
        "maintenance_log": maintenance_log,
        "quotations": quotations,
    }
    return render(request, "major_equipment/maintenance/forms/evaluation_form.html", context)
    
@login_required
def view_admin_evaluation(request, unit_id, log_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    maintenance_log = get_object_or_404(MaintenanceLog, pk=log_id)
    quotations = Quotation.objects.filter(log=maintenance_log, deleted=False).order_by('-creation_date')

    if request.method == "POST":
        decision = request.POST.get("decision")

        if decision == "accept":
            # Observaciones al aprobar
            admin_observations = request.POST.get("success_observations", "").strip()

            maintenance_log.approved_by_admin = True  # Debes tener este campo o uno equivalente
            maintenance_log.admin_observations = admin_observations
            maintenance_log.reviewed_by_admin = request.user  # Si tienes un campo así
            maintenance_log.admin_reviewed_date = timezone.now()  # Igual que arriba
            maintenance_log.save()

            messages.success(request, "Solicitud aprobada correctamente por Administración.")
            return redirect("major_equipment:unit_maintenance", unit.id)

        elif decision == "reject":
            reject_reason = request.POST.get("reject_reason", "").strip()
            if not reject_reason:
                messages.error(request, "Debe indicar la razón del rechazo.")
            else:
                maintenance_log.approved_by_admin = False
                maintenance_log.admin_observations = reject_reason
                maintenance_log.reviewed_by_admin = request.user
                maintenance_log.admin_reviewed_date = timezone.now()
                maintenance_log.save()

                messages.success(request, "Solicitud rechazada correctamente por Administración.")
                return redirect("major_equipment:unit_maintenance", unit.id)
        else:
            messages.error(request, "Debe seleccionar si aprueba o rechaza la solicitud.")

    context = {
        "unit": unit,
        "maintenance_log": maintenance_log,
        "quotations": quotations,
        "evaluation_role": "administracion",  # opcional, para personalizar template si quieres
        "show_quotation_select": False,       # puedes usar esto en el template
    }
    return render(request, "major_equipment/maintenance/forms/evaluation_form.html", context)

@login_required
def view_create_meeting_workshop(request, unit_id, log_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    maintenance_log = get_object_or_404(MaintenanceLog, pk=log_id)

    form_data = {
        "dispatch_date": "",
        "estimated_return_date": "",
        "comments": "",
    }
    errors = {}

    if request.method == "POST":
        # Recoge datos del formulario
        dispatch_date = request.POST.get("dispatch_date", "").strip()
        estimated_return_date = request.POST.get("estimated_return_date", "").strip()
        comments = request.POST.get("comments", "").strip()

        # Sticky data
        form_data["dispatch_date"] = dispatch_date
        form_data["estimated_return_date"] = estimated_return_date
        form_data["comments"] = comments

        # Validaciones
        if not dispatch_date:
            errors["dispatch_date"] = "La fecha de despacho es obligatoria."
        if not estimated_return_date:
            errors["estimated_return_date"] = "La fecha estimada de retorno es obligatoria."
        # Validación de orden de fechas (si ambas están presentes)
        if dispatch_date and estimated_return_date and dispatch_date > estimated_return_date:
            errors["estimated_return_date"] = "La fecha de retorno no puede ser anterior al despacho."

        # Si pasa validación, crea el MeetingWorkshop
        if not errors:
            MeetingWorkshop.objects.create(
                log=maintenance_log,
                dispatch_date=dispatch_date,
                estimated_return_date=estimated_return_date,
                comments=comments,
                author=request.user,
            )
            messages.success(request, "Cita con el taller creada exitosamente.")
            return redirect("major_equipment:unit_maintenance", unit_id=unit.id)

    return render(
        request,
        "major_equipment/maintenance/forms/meeting_workshop_form.html",
        {
            "unit": unit,
            "maintenance_log": maintenance_log,
            "form_data": form_data,
            "errors": errors,
        }
    )

@login_required
def view_create_unit_shipment(request, unit_id, log_id, meeting_workshop_id):
    pass

def view_create_unit_reception(request, unit_id, log_id, meeting_workshop_id):
    pass







