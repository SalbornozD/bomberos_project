from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class File(models.Model):
    """
    Representa un archivo genérico del sistema. Valida que solo se suban archivos en formatos PDF, DOC, DOCX, XLS y XLSX.
    """
    file = models.FileField(
        upload_to='documentos/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])]
    )
    short_name = models.CharField(max_length=100)

    def __str__(self):
        return self.short_name

    def clean(self):
        super().clean()
        uploaded_file = self.file
        if uploaded_file and hasattr(uploaded_file, 'file') and hasattr(uploaded_file.file, 'content_type'):
            mime = uploaded_file.file.content_type
            allowed_mime_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            ]
            if mime not in allowed_mime_types:
                raise ValidationError({'file': 'Solo se permiten archivos PDF, DOC, DOCX, XLS y XLSX.'})


class FileVencible(File):
    """
    Subclase de File que añade fecha de vencimiento.
    """
    expiration_date = models.DateField()

    class Meta:
        verbose_name = "Archivo con vencimiento"
        verbose_name_plural = "Archivos con vencimiento"
    
    @property
    def is_expired(self):
        """
        Devuelve True si el documento ya expiró.
        """
        return self.expiration_date < timezone.now().date()

    def days_until_expiration(self):
        """
        Devuelve la cantidad de días que faltan para que el documento expire.
        Si ya expiró, retorna 0.
        """
        days = (self.expiration_date - timezone.now().date()).days
        return max(days, 0)
