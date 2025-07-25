from django.urls import path
from .views import *
# from .views_ajax import maintenance_report_JSON, maintenance_request_JSON, maintenance_request_administracion, maintenance_request_comandancia, finish_maintenance_request_JSON

app_name = "major_equipment"

urlpatterns = [
    # Retornan Template
    path("", view_get_units, name="unit_list"),
    path("<int:unit_id>/", view_get_unit, name="unit_detail"),

    # REPORTES
    path("<int:unit_id>/reports/create/", view_create_report, name="create_report"),
    path("<int:unit_id>/reports/", view_unit_reports, name="unit_reports"),
    path("<int:unit_id>/reports/<int:report_id>/", view_get_report, name="get_report"),

    path("<int:unit_id>/reports/<int:report_id>/PDF/", view_generate_report_pdf, name="get_report_pdf"),

    # COMBUSTIBLE
    path("<int:unit_id>/fuel/create/", view_create_fuel, name="create_fuel"),
    path("<int:unit_id>/fuel/", view_unit_fuel, name="unit_fuel"),
    path("<int:unit_id>/fuel/<int:fuel_log_id>/", view_get_fuel_log, name="get_fuel_log"),

    # Mantenciones
    path("<int:unit_id>/maintenance/create/", view_create_maintenance_request, name="create_maintenance_request"),
    path("<int:unit_id>/maintenance/<int:log_id>/quote/create/", view_add_quotation, name="add_quotation"),
    path("<int:unit_id>/maintenance/", view_unit_maintenance, name="unit_maintenance"),
    path("<int:unit_id>/maintenance/<int:maintenance_log_id>/", view_get_maintenance_log, name="get_maintenance_log")
]
    
#     # Reportes de mantención
#     path("maintenance-report/JSON/", maintenance_report_JSON, name="maintenance_report_json"),
    
#     # Solicitudes de mantención
#     path("maintenance-request/JSON/", maintenance_request_JSON, name="maintenance_request_json"),
#     path("maintenance-request/administracion/", maintenance_request_administracion, name="maintenance_request_administracion"),
#     path("maintenance-request/comandancia/", maintenance_request_comandancia, name="maintenance_request_comandancia"),
#     path("finish-maintenance-request/JSON/", finish_maintenance_request_JSON, name="finish_maintenance_request_json"),
