from django.urls import path
from .views import *
# from .views_ajax import maintenance_report_JSON, maintenance_request_JSON, maintenance_request_administracion, maintenance_request_comandancia, finish_maintenance_request_JSON

app_name = "major_equipment"

urlpatterns = [
    # Retornan Template
    path("", view_get_units, name="unit_list"),
    path("<int:unit_id>/", view_get_unit, name="unit_detail"),
    path("<int:unit_id>/reports/", view_unit_reports, name="unit_reports"),
    path("<int:unit_id>/fuel/", view_unit_fuel, name="unit_fuel"),
    path("<int:unit_id>/maintenance/", view_unit_maintenance, name="unit_maintenance"),

    # REPORTES
    path("<int:unit_id>/reports/create/", view_create_report, name="create_report"),

    # COMBUSTIBLE
    path("<int:unit_id>/fuel/create/", view_create_fuel, name="create_fuel"),
]
    
#     # Reportes de mantención
#     path("maintenance-report/JSON/", maintenance_report_JSON, name="maintenance_report_json"),
    
#     # Solicitudes de mantención
#     path("maintenance-request/JSON/", maintenance_request_JSON, name="maintenance_request_json"),
#     path("maintenance-request/administracion/", maintenance_request_administracion, name="maintenance_request_administracion"),
#     path("maintenance-request/comandancia/", maintenance_request_comandancia, name="maintenance_request_comandancia"),
#     path("finish-maintenance-request/JSON/", finish_maintenance_request_JSON, name="finish_maintenance_request_json"),
