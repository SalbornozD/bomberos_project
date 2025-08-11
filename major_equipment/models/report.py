from django.db                  import models
from django.core.exceptions     import ValidationError
from django.utils               import timezone
from django.contrib.auth        import get_user_model
from .unit                      import Unit

# Incorporación del modelo User.
User = get_user_model()


class QuestionType(models.IntegerChoices):
    """
    ENUM de tipos de preguntas.
    """
    GOOD_BAD = 1, 'Bueno/Malo'
    MULTIPLE_CHOICE = 2, 'Opciones predefinidas'
    NUMERIC = 3, 'Numérico'
    
class ItemCategory(models.Model):
    """
    Categorías de preguntas.
    """
    label = models.CharField(
        max_length=255, 
        verbose_name="Etiqueta",
        unique = True
    )
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.label

class ReportTemplateItem(models.Model):
    """
    Plantilla dinámica de preguntas para los reportes.
    """
    label = models.CharField(
        max_length=255,
        verbose_name="Etiqueta"
    )

    question_type = models.IntegerField(
        choices=QuestionType.choices,
        default=QuestionType.GOOD_BAD,
        verbose_name="Tipo de pregunta"
    )

    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        verbose_name="Categoría"
    )
    
    units = models.ManyToManyField(
        Unit, 
        blank=True,
        related_name="report_template_items",
        verbose_name="Unidades asignadas",
        help_text="Selecciona las unidades en las que esta pregunta debe aparecer. Si no seleccionas ninguna, la pregunta no se usará."
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

    value = models.CharField(
        max_length=255,
        verbose_name="Opción"
    )

    triggers_alert = models.BooleanField(
        default=False,
        verbose_name="Activar alerta"
    )

    class Meta:
        verbose_name = "Opción de plantilla"
        verbose_name_plural = "Opciones de plantilla"

    def __str__(self):
        return self.value

class NumericAlertRule(models.Model):
    """
    Reglas de alerta para respuestas numéricas.
    """
    question = models.ForeignKey(
        ReportTemplateItem,
        on_delete=models.CASCADE,
        related_name="numeric_alert_rules",
        limit_choices_to={'question_type': QuestionType.NUMERIC},
        verbose_name="Pregunta numérica"
    )

    min_value = models.IntegerField(
        verbose_name="Valor mínimo (opcional)",
        blank=True,
        null=True
    )

    max_value = models.IntegerField(
        verbose_name="Valor máximo (opcional)",
        blank=True,
        null=True
    )

    description = models.CharField(
        max_length=255,
        verbose_name="Descripción de la alerta",
        blank=True
    )

    class Meta:
        verbose_name = "Regla para alerta numérica"
        verbose_name_plural = "Reglas para alerta numéricas"
    
    def is_triggered(self, value):
        """
        Devuelve True si el valor viola alguna condición
        """
        try:
            val = int(value)
        except (TypeError, ValueError):
            return False
        
        if self.min_value is not None and val < self.min_value:
            return True
        if self.max_value is not None and val > self.max_value:
            return True
        if self.min_value is not None and self.max_value is not None:
            return self.min_value <= val <= self.max_value
        return False

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

    coment = models.TextField(
        verbose_name="Comentario",
        blank=True,
        null=True
    )
    
    editable = models.BooleanField(
        default=True,
        verbose_name="Editable"
    )

    deleted = models.BooleanField(
        default=False,
        verbose_name="Eliminado"
    )

    class Meta:
        unique_together = ('unit', 'date')
        ordering = ['-date']
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

    def __str__(self):
        return f"Reporte {self.unit} - {self.date}"

class ReportEntry(models.Model):
    report = models.ForeignKey(
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

    answer = models.CharField(
        max_length=255,
        verbose_name="Respuesta"
    )
    
    comment = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Comentario adicional"
        )

    class Meta:
        unique_together = ('report', 'question')
        verbose_name = "Entrada de checklist"
        verbose_name_plural = "Entradas de checklist"

    def clean(self):
        super().clean()
        qt = self.question.question_type
        val = (self.answer or "").strip()

        if qt == QuestionType.GOOD_BAD:
            if val not in ['Bueno', 'Malo']:
                raise ValidationError('Para preguntas Bueno/Malo la respuesta debe ser “Bueno” o “Malo”.')
        
        elif qt == QuestionType.MULTIPLE_CHOICE:
            opciones = [opt.value for opt in self.question.options.all()]
            if val not in opciones:
                raise ValidationError(f"Respuesta inválida. Debe ser una de: {', '.join(opciones)}")
        
        elif qt == QuestionType.NUMERIC:
            try:
                float(val)
            except ValueError:
                raise ValidationError('Para preguntas numéricas la respuesta debe ser un número.')
        else:
            raise ValidationError('Tipo de pregunta no soportado.')

    def should_trigger_alert(self):
        """
        Determina si esta entrada debe generar alerta según el tipo de pregunta.
        """
        val = (self.answer or "").strip()
        qt = self.question.question_type

        if qt == QuestionType.GOOD_BAD:
            # Alerta en "Malo"
            return val == "Malo"
        
        elif qt == QuestionType.MULTIPLE_CHOICE:
            # Usa el flag de cada opción
            return self.question.options.filter(value=val, triggers_alert=True).exists()
        
        elif qt == QuestionType.NUMERIC:
            # Consulta cada regla numerica
            for rule in self.question.numeric_alert_rules.all():
                if rule.is_triggered(val):
                    return True
        
        return False
        
    def __str__(self):
        return f"{self.report} - {self.question.label}: {self.answer}"
