from django.urls import path
from .views_ajax import entities_JSON, users_JSON

app_name = "firebrigade"

urlpatterns = [
    path("entities/JSON/", entities_JSON, name="entities_json"),
    path("users/JSON/", users_JSON, name="users_json"),
]

