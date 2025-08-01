from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    path('archivo/<int:file_id>/', views.protected_file, name='protected_file'),
]
