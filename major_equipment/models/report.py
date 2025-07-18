from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .unit import Unit
from django.contrib.auth import get_user_model

User = get_user_model()

class QuestionType(models.IntegerChoices):
    YES_NO = 1, 'Sí o No'
    MULTIPLE_CHOICE = 2, 'Opciones predefinidas'
    TEXT = 3, 'Descriptivo'

class ItemCategory(models.Model):
    label = models.CharField(max_length=255, verbose_name="Etiqueta")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.label

class ReportTemplateItem(models.Model):
    """
    Plantilla dinámica de preguntas para los reportes.
    """
    label = models.CharField(max_length=255, verbose_name="Etiqueta")
    question_type = models.IntegerField(
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
        verbose_name="Tipo de pregunta"
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        verbose_name="Categoría"
    )

    class Meta:
        verbose_name = "Ítem de plantilla"
        verbose_name_plural = "Ítems de plantilla"
        
    def __str__(self):
        return self.label

class ReportItemOption(models.Model):
    """
    Opciones disponibles para preguntas de opción múltiple.
    """
    question = models.ForeignKey(
        ReportTemplateItem,
        on_delete=models.CASCADE,
        related_name="options",
        limit_choices_to={'question_type': QuestionType.MULTIPLE_CHOICE},
        verbose_name="Pregunta"
    )
    value = models.CharField(max_length=255, verbose_name="Opción")

    class Meta:
        verbose_name = "Opción de plantilla"
        verbose_name_plural = "Opciones de plantilla"

    def __str__(self):
        return self.value

class Report(models.Model):
    """
    Reporte diario para una unidad.
    """
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        verbose_name="Unidad",
        related_name="checklist_reports"
    )
    date = models.DateField(
        default=timezone.localdate,
        verbose_name="Fecha del reporte"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Autor",
        related_name="checklist_reports"
    )
    coment = models.TextField(verbose_name="Comentario", blank=True, null=True)
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        unique_together = ('unit', 'date')
        ordering = ['-date']
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

    def __str__(self):
        return f"Reporte {self.unit} - {self.date}"

class ReportEntry(models.Model):
    report   = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Reporte"
    )
    question = models.ForeignKey(
        ReportTemplateItem,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Pregunta"
    )
    answer   = models.CharField(max_length=255, verbose_name="Respuesta")
    comment  = models.CharField(max_length=255, blank=True, verbose_name="Comentario adicional")

    class Meta:
        unique_together = ('report', 'question')
        verbose_name = "Entrada de checklist"
        verbose_name_plural = "Entradas de checklist"

    def clean(self):
        super().clean()
        qt = self.question.question_type
        val = (self.answer or "").strip()

        if qt == QuestionType.YES_NO:
            if val not in ['Bueno', 'Malo', 'No aplica']:
                raise ValidationError("Para preguntas Bueno/Malo la respuesta debe ser “Bueno”, “Malo” o 'No aplica'.")
        elif qt == QuestionType.MULTIPLE_CHOICE:
            opciones = [opt.value for opt in self.question.options.all()]
            if val not in opciones:
                raise ValidationError(
                    f"Respuesta inválida. Debe ser una de: {', '.join(opciones)}"
                )
        elif qt == QuestionType.TEXT:
            if not val:
                raise ValidationError("La respuesta descriptiva no puede estar vacía.")
        else:
            raise ValidationError("Tipo de pregunta desconocido.")

    def __str__(self):
        return f"{self.report} - {self.question.label}: {self.answer}"
