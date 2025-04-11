from django.urls import path
from . import views

app_name = "major_equipment"

urlpatterns = [
    path("", views.get_units, name="unit_list"),
    path("<int:unit_id>/", views.get_unit, name="unit_detail"),
]