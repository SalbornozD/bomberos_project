from django.contrib import admin
from .models import *

admin.site.register(Unit)
admin.site.register(UnitImage)
admin.site.register(MaintenanceLog)
admin.site.register(FuelLog)
admin.site.register(Quotation)
admin.site.register(MeetingWorkshop)


# ── Inlines para ReportTemplateItem ────────────────────────────────────────

class ReportItemOptionInline(admin.TabularInline):
    model = ReportItemOption
    extra = 1
    fields = ('value', 'triggers_alert')
    verbose_name = "Opción"
    verbose_name_plural = "Opciones (predefinidas)"

class NumericAlertRuleInline(admin.TabularInline):
    model = NumericAlertRule
    extra = 1
    fields = ('min_value', 'max_value', 'description')
    verbose_name = "Regla de alerta"
    verbose_name_plural = "Reglas de alerta numéricas"

# ── Admin para Plantillas de Preguntas ────────────────────────────────────

@admin.register(ReportTemplateItem)
class ReportTemplateItemAdmin(admin.ModelAdmin):
    list_display      = ('label', 'question_type', 'category')
    list_filter       = ('question_type', 'category')
    search_fields     = ('label',)
    filter_horizontal = ('units',)
    fieldsets = (
        (None, {
            'fields': ('label', 'question_type', 'category', 'units'),
            'description': "Define la pregunta, su tipo y las unidades en las que aplica."
        }),
    )
    # Declaramos las dos posibles inlines, pero los mostraremos condicionalmente
    inlines = [ReportItemOptionInline, NumericAlertRuleInline]

    def get_inline_instances(self, request, obj=None):
        """
        Sólo retorna el inline de opciones si es MULTIPLE_CHOICE,
        sólo retorna el inline de reglas numéricas si es NUMERIC.
        Para obj=None (creación), no muestra ninguno.
        """
        inline_instances = []
        if obj is None:
            return inline_instances

        for inline_class in self.inlines:
            if inline_class == ReportItemOptionInline and obj.question_type == QuestionType.MULTIPLE_CHOICE:
                inline_instances.append(inline_class(self.model, self.admin_site))
            if inline_class == NumericAlertRuleInline and obj.question_type == QuestionType.NUMERIC:
                inline_instances.append(inline_class(self.model, self.admin_site))

        return inline_instances

# ── Inline para Entradas de Reporte ───────────────────────────────────────

class ReportEntryInline(admin.TabularInline):
    model = ReportEntry
    extra = 0
    fields = ('question', 'answer', 'comment', 'should_trigger_alert')
    readonly_fields = ('should_trigger_alert',)
    verbose_name = "Entrada"
    verbose_name_plural = "Entradas"

    def should_trigger_alert(self, obj):
        return obj.should_trigger_alert()
    should_trigger_alert.boolean = True
    should_trigger_alert.short_description = "Alerta?"

# ── Admin para Reportes ────────────────────────────────────────────────────

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display    = ('unit', 'date', 'author', 'editable')
    list_filter     = ('date', 'unit', 'author', 'editable')
    search_fields   = ('unit__unit_number', 'author__username')
    raw_id_fields   = ('unit', 'author')
    inlines         = [ReportEntryInline]
