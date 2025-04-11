from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse, Http404
from django.conf import settings
import os

def index(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    data = {}
    data['title'] = "Cuerpo de bomberos Quintero"

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('check-remember-me') == 'on'

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if remember_me:
                request.session.set_expiry(None)
            else:
                request.session.set_expiry(0)
            return redirect('main:home')
        else:
            data['message_error'] = "Usuario y/o contraseña incorrectos."

    return render(request, 'main/index.html', data)

def logout_view(request):
    logout(request)
    return redirect('main:index')

def home(request):
    data = {}
    # Configuración general de la página.
    data['title'] = f'Home | Bomberos Quinero'
    return render(request, 'main/home.html', data)

def serve_pdf_file(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        response = FileResponse(open(full_path, 'rb'), content_type='application/pdf')
        response['X-Frame-Options'] = 'ALLOWALL'
        return response
    else:
        raise Http404("Archivo no encontrado")