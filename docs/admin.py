from django.contrib import admin
from .models import File, FileVencible

# Register your models here.

admin.site.register(File)
admin.site.register(FileVencible)