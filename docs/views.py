from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import File

@login_required
def protected_file(request, file_id):
    archivo = get_object_or_404(File, id=file_id)
    try:
        return FileResponse(archivo.file.open('rb'), as_attachment=True)
    except Exception:
        raise Http404("Archivo no encontrado.")
