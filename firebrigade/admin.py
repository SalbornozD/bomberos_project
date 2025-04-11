from django.contrib import admin
from .models import Entity, Position, Membership, MembershipHistory


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """
    Admin para entidades del cuerpo de bomberos (compañías, comandancia, etc.).

    Muestra:
        - Nombre
        - Tipo de entidad

    Permite:
        - Filtrar por tipo
        - Buscar por nombre
    """
    list_display = ('name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    Admin para cargos disponibles en el sistema.

    Muestra:
        - Nombre
        - Si es exclusivo
        - Cuántos permisos tiene

    Permite:
        - Editar permisos directamente
    """
    list_display = ('name', 'is_unique', 'permissions_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = "Permisos asignados"


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """
    Admin para la asignación activa de un usuario a un cargo.

    Muestra:
        - Nombre de usuario
        - Cargo
        - Entidad

    Permite:
        - Buscar por nombre o cargo
        - Filtrar por entidad y cargo
        - Mostrar campo de autocompletado si hay muchos usuarios
    """
    list_display = ('user', 'position', 'entity')
    list_filter = ('entity', 'position')
    search_fields = ('user__first_name', 'user__last_name', 'position__name')
    autocomplete_fields = ('user',)


@admin.register(MembershipHistory)
class MembershipHistoryAdmin(admin.ModelAdmin):
    """
    Admin para el historial de cargos de usuarios.

    Muestra:
        - Nombre del usuario
        - Cargo
        - Entidad
        - Fechas de inicio y término

    Permite:
        - Filtrar por entidad y cargo
        - Orden cronológico
    """
    list_display = ('full_name', 'position', 'entity', 'start_date', 'end_date')
    list_filter = ('entity', 'position')
    search_fields = ('full_name',)
    ordering = ('-start_date',)


    
