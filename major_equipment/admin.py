from django.contrib import admin
from django.utils.html import format_html
from .models import MajorEquipment, UnitImage, MaintenanceReport, VehicleType
from firebrigade.models import Membership
from django.contrib.auth import get_user_model
from django.http import HttpRequest


User = get_user_model()

def get_user_entity(user):
    """
    Devuelve la entidad del usuario según su Membership.
    Si no tiene, retorna None.
    """
    membership = Membership.objects.filter(user=user).first()
    return membership.entity if membership else None


class UnitImageInline(admin.TabularInline):
    """
    Permite gestionar las imágenes directamente desde el admin del vehículo.
    """
    model = UnitImage
    extra = 1
    fields = ("image", "description", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "-"
    preview.short_description = "Vista previa"

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]

    def get_model_perms(self, request):
        """
        Oculta el modelo del menú lateral del admin.
        """
        return {}


@admin.register(MajorEquipment)
class MajorEquipmentAdmin(admin.ModelAdmin):
    """
    Configura el panel de administración para unidades de material mayor,
    filtrando por entidad si el permiso es de tipo *_company_*.
    """

    list_display = (
        "unit_number", "short_description", "plate_number",
        "entity", "vehicle_type", "year"
    )
    list_filter = (
        "entity", "vehicle_type", "year", "fuel_type"
    )
    search_fields = (
        "unit_number", "plate_number", "short_description",
        "model", "engine_number", "chassis_number"
    )
    readonly_fields = (
        "get_registration_certificate_status",
        "get_soap_certificate_status",
        "get_technical_inspection_certificate_status",
        "get_vehicle_permit_status",
        "get_next_maintenance_status",
    )
    fieldsets = (
        ("Identificación general", {
            "fields": ("unit_number", "short_description", "plate_number", "entity")
        }),
        ("Motor y transmisión", {
            "fields": ("brand", "model", "year", "vehicle_type", "fuel_type", "cylinders", "displacement",
                       "transmission", "drive_system", "fuel_tank_capacity")
        }),
        ("Sistema de aceites", {
            "fields": ("engine_number", "chassis_number", "motor_oil_type", "motor_oil_capacity",
                       "gearbox_oil_type", "differential_oil_type", "differential_oil_capacity")
        }),
        ("Filtros", {
            "fields": ("fuel_filter_quantity", "fuel_part_number", "oil_filter_quantity", "oil_part_number",
                       "air_filter_part_number", "air_purifier_part_number")
        }),
        ("Neumáticos y frenos", {
            "fields": ("tire_size", "tire_brand", "tire_pressure", "brake_system_type",
                       "parking_brake_type", "pad_type", "disc_type")
        }),
        ("Sistema hidráulico / bomba", {
            "fields": ("water_tank_capacity", "pump_type", "pump_capacity", "pump_pressure",
                       "pump_model", "pump_brand", "pump_serial_number", "pump_year", "maximum_flow_rate")
        }),
        ("Documentación", {
            "fields": ("registration_certificate", "get_registration_certificate_status",
                       "soap_certificate", "soap_certificate_expiration", "get_soap_certificate_status",
                       "technical_inspection_certificate", "technical_inspection_certificate_expiration", "get_technical_inspection_certificate_status",
                       "vehicle_permit", "vehicle_permit_expiration", "get_vehicle_permit_status")
        }),
        ("Mantención", {
            "fields": ("next_maintenance_date", "get_next_maintenance_status")
        }),
    )
    inlines = [UnitImageInline]
    autocomplete_fields = ["vehicle_type"]

    def get_queryset(self, request):
        """
        Filtra los vehículos mostrados en el admin según los permisos del usuario.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm("major_equipment.view_majorequipment"):
            return qs
        elif request.user.has_perm("major_equipment.view_company_majorequipment"):
            entity = get_user_entity(request.user)
            return qs.filter(entity=entity)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.has_perm("major_equipment.view_majorequipment"):
            return True
        if obj and request.user.has_perm("major_equipment.view_company_majorequipment"):
            return obj.entity == get_user_entity(request.user)
        return request.user.has_perm("major_equipment.view_company_majorequipment")

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.has_perm("major_equipment.change_majorequipment"):
            return True
        if obj and request.user.has_perm("major_equipment.change_company_majorequipment"):
            return obj.entity == get_user_entity(request.user)
        return request.user.has_perm("major_equipment.change_company_majorequipment")

    def has_add_permission(self, request):
        return (
            request.user.is_superuser or
            request.user.has_perm("major_equipment.add_majorequipment") or
            request.user.has_perm("major_equipment.add_company_majorequipment")
        )

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.has_perm("major_equipment.delete_majorequipment"):
            return True
        if obj and request.user.has_perm("major_equipment.delete_company_majorequipment"):
            return obj.entity == get_user_entity(request.user)
        return request.user.has_perm("major_equipment.delete_company_majorequipment")

@admin.register(MaintenanceReport)
class MaintenanceReportAdmin(admin.ModelAdmin):
    """
    Administración personalizada de reportes de desperfecto (fallas) en unidades.

    Permite controlar el acceso en base a niveles de permisos:
        - Permisos por sistema (total)
        - Permisos por compañía
        - Permisos por reportes propios
    """

    list_display = ("id", "unit", "reported_by", "created_at", "editable")
    list_filter = ("created_at", "editable")
    search_fields = ("description", "unit__unit_number", "reported_by__username")

    # -------------------------------
    # VISIBILIDAD EN LISTADO
    # -------------------------------
    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser or user.has_perm("major_equipment.view_maintenancereport"):
            return qs

        if user.has_perm("major_equipment.view_company_maintenancereports"):
            entities = Membership.objects.filter(user=user).values_list("entity_id", flat=True)
            return qs.filter(unit__entity_id__in=entities)

        if user.has_perm("major_equipment.view_own_maintenancereports"):
            return qs.filter(reported_by=user)

        return MaintenanceReport.objects.none()

    # -------------------------------
    # PERMISOS VIEW / CHANGE / DELETE
    # -------------------------------
    def has_view_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser or user.has_perm("major_equipment.view_maintenancereport"):
            return True
        if obj:
            if user.has_perm("major_equipment.view_company_maintenancereports") and \
                    obj.unit.entity in Membership.objects.filter(user=user).values_list("entity", flat=True):
                return True
            if user.has_perm("major_equipment.view_own_maintenancereports") and obj.reported_by == user:
                return True
            return False
        return user.has_perm("major_equipment.view_company_maintenancereports") or user.has_perm("major_equipment.view_own_maintenancereports")

    def has_change_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser or user.has_perm("major_equipment.change_maintenancereport"):
            return True
        if obj:
            if user.has_perm("major_equipment.change_company_maintenancereports") and \
                    obj.unit.entity in Membership.objects.filter(user=user).values_list("entity", flat=True):
                return True
            if user.has_perm("major_equipment.change_own_maintenancereports") and obj.reported_by == user:
                return True
        return False

    def has_delete_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser or user.has_perm("major_equipment.delete_maintenancereport"):
            return True
        if obj:
            if user.has_perm("major_equipment.delete_company_maintenancereports") and \
                    obj.unit.entity in Membership.objects.filter(user=user).values_list("entity", flat=True):
                return True
            if user.has_perm("major_equipment.delete_own_maintenancereports") and obj.reported_by == user:
                return True
        return False

    def has_add_permission(self, request):
        user = request.user
        return (
            user.is_superuser or
            user.has_perm("major_equipment.add_maintenancereport") or
            user.has_perm("major_equipment.create_company_maintenancereports") or
            user.has_perm("major_equipment.create_own_maintenancereports")
        )

    # -------------------------------
    # FORMULARIOS - FILTROS FK
    # -------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = request.user

        if db_field.name == "unit":
            if user.is_superuser or user.has_perm("major_equipment.view_majorequipment"):
                kwargs["queryset"] = MajorEquipment.objects.all()
            elif user.has_perm("major_equipment.view_company_majorequipment"):
                entities = Membership.objects.filter(user=user).values_list("entity_id", flat=True)
                kwargs["queryset"] = MajorEquipment.objects.filter(entity_id__in=entities)
            else:
                kwargs["queryset"] = MajorEquipment.objects.none()

        if db_field.name == "reported_by":
            if user.is_superuser:
                kwargs["queryset"] = User.objects.all()
            elif user.has_perm("major_equipment.view_company_maintenancereports"):
                entities = Membership.objects.filter(user=user).values_list("entity_id", flat=True)
                user_ids = Membership.objects.filter(entity_id__in=entities).values_list("user_id", flat=True)
                kwargs["queryset"] = User.objects.filter(id__in=user_ids)
            else:
                kwargs["queryset"] = User.objects.filter(id=user.id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)