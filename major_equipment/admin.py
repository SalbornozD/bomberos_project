from django.contrib import admin
from .models.unit import *
from .models.report import *
from .models.fuel_log import *
from .models.maintenance_log import *
from django.utils.html import format_html
from .utils.permission import get_units, can_view_unit, can_edit_unit
from firebrigade.utils import get_user_entity


class UnitImageInline(admin.TabularInline):
    """
    Inline admin descriptor para UnitImage.
    Permite gestionar imágenes directamente desde la edición de una Unidad.
    """
    model = UnitImage
    extra = 1  # Formularios extra para nuevas imágenes

    readonly_fields = ("preview",)
    fields = ('image', 'preview', 'description',)

    verbose_name = "Imagen de unidad"
    verbose_name_plural = "Imágenes de unidades"

    def preview(self, obj):
        """
        Devuelve una etiqueta <img> con una miniatura de la imagen.
        """
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:150px; object-fit:contain;"/>',
                obj.image.url
            )
        return "-"
    preview.short_description = "Vista previa"

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Unit.
    Organiza los campos en secciones, habilita búsqueda, filtros,
    y gestiona imágenes asociadas mediante un inline.
    También aplica controles de permiso personalizados.
    """
    inlines = [UnitImageInline]

    # Columnas mostradas en la lista principal
    list_display = (
        "unit_number",
        "description",
        "plate_number",
        "entity",
        "fuel_type",
    )

    # Campos que pueden buscarse mediante la barra de búsqueda
    search_fields = ("unit_number", "description", "plate_number",)

    # Filtros en la barra lateral
    list_filter = ("entity", "vehicle_type",)

    # Estructura del formulario de edición en pestañas o secciones
    fieldsets = (
        ("Identificación", {
            "fields": ("unit_number", "description", "plate_number", "entity")
        }),
        ("Especificaciones técnicas", {
            "fields": (
                "brand", "model", "year",
                "vehicle_type", "fuel_type", "fuel_tank_capacity",
                "engine_number", "chassis_number"
            )
        }),
        ("Neumáticos y frenos", {
            "fields": ("tire_size", "tire_pressure",)
        }),
        ("Documentos asociados", {
            "fields": ("padron", "soap", "technical_inspection", "vehicle_permit")
        }),
        ("Estado del registro", {
            "fields": ("editable", "deleted")
        }),
    )

    def get_queryset(self, request):
        """
        Restringe el queryset de unidades según los permisos del usuario,
        usando la función get_units.
        """
        qs = super().get_queryset(request)
        return get_units(request.user).filter(pk__in=qs.values_list('pk', flat=True))

    def has_view_permission(self, request, obj=None):
        user = request.user

        if obj is None:
            # permisos global o de compañía permiten ver la lista
            return (
                user.is_superuser
                or user.has_perm('major_equipment.view_majorequipment')
                or user.has_perm('major_equipment.view_company_majorequipment')
            )

        # delegamos en can_view_unit para comprobar entidad, superuser, etc
        return can_view_unit(user, obj)


    def has_add_permission(self, request):
        """
        Permite agregar unidades solo a usuarios con el permiso "add_company_majorequipment".
        """
        return request.user.has_perm('major_equipment.add_company_majorequipment')

    def has_change_permission(self, request, obj=None):
        """
        Permite modificar unidades solo a usuarios con el permiso "change_company_majorequipment".
        """
        return request.user.has_perm('major_equipment.change_company_majorequipment')

    def has_delete_permission(self, request, obj=None):
        """
        Permite eliminar unidades solo a usuarios con el permiso "delete_company_majorequipment".
        """
        return request.user.has_perm('major_equipment.delete_company_majorequipment')

admin.site.register(ReportTemplateItem)
admin.site.register(ItemCategory)
admin.site.register(ReportItemOption)
admin.site.register(Report)
admin.site.register(ReportEntry)
admin.site.register(FuelLog)
admin.site.register(Station)
admin.site.register(MaintenanceLog)