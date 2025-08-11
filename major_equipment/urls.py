from django.urls import path
from .views import *

app_name = "major_equipment"

urlpatterns = [
    # UNIDADES
    path("units/", view_get_units, name="units"),
    path("units/<int:unit_id>/", view_get_unit, name="unit"),
    
    # Imagenes de las unidades
    path('unit-image/<int:image_id>/', protected_unit_image, name='unit_image'),

    # REPORTES
    path("reports/create/", view_create_report, name="create_report"),
    path("reports/", view_unit_reports, name="unit_reports"),
    path("reports/<int:report_id>/", view_get_report, name="get_report"),

    path("<int:unit_id>/reports/<int:report_id>/PDF/", view_generate_report_pdf, name="get_report_pdf"),

    # COMBUSTIBLE
    path("<int:unit_id>/fuel/create/", view_create_fuel, name="create_fuel"),
    path("<int:unit_id>/fuel/", view_unit_fuel, name="unit_fuel"),
    path("<int:unit_id>/fuel/<int:fuel_log_id>/", view_get_fuel_log, name="get_fuel_log"),

    # Mantenciones
    path("<int:unit_id>/maintenance/create/", view_create_maintenance_request, name="create_maintenance_request"),
    path("<int:unit_id>/maintenance/<int:log_id>/quote/create/", view_add_quotation, name="add_quotation"),
    path("<int:unit_id>/maintenance/<int:log_id>/command-evaluation/", view_command_evaluation, name="command_evaluation"),
    path("<int:unit_id>/maintenance/<int:log_id>/admin-evaluation/", view_admin_evaluation, name="admin_evaluation"),
    path("<int:unit_id>/maintenance/", view_unit_maintenance, name="unit_maintenance"),
    path("<int:unit_id>/maintenance/<int:maintenance_log_id>/", view_get_maintenance_log, name="get_maintenance_log"),
    path("<int:unit_id>/maintenance/<int:log_id>/meeting-workshop/create/", view_create_meeting_workshop, name="create_meeting_workshop"),
]