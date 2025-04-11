from django.urls import path
from .views import index, home, logout_view, serve_pdf_file

app_name = 'main'

urlpatterns = [
    path('', index, name="index"),
    path('logout/', logout_view, name="logout"),
    path('home/', home, name="home"),
    path('ver-pdf/<path:path>/', serve_pdf_file, name='ver_pdf'),
]