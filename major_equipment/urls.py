from django.urls import path
from .views import view_get_units, get_unit, get_maintenances_reports
from .views_ajax import maintenance_report_JSON
app_name = "major_equipment"

urlpatterns = [
    path("", view_get_units, name="unit_list"),
    path("<int:unit_id>/", get_unit, name="unit_detail"),
    path("maintenance-reports/", get_maintenances_reports, name="maintenance_report_list"),

    # AJAX URLs
    path("maintenance-report/JSON/", maintenance_report_JSON, name="maintenance_report_json"),
]