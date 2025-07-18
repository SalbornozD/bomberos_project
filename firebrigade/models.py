from django.db import models
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class EntityType(models.TextChoices):
    """
    Enumeración de tipos de entidades dentro del Cuerpo de Bomberos.

    Valores posibles:
        - 'COMPANY': Compañía
        - 'COMMAND': Comandancia
        - 'CENTRAL': Central de Comunicaciones
        - 'ADMIN': Administración General
    """
    COMPANY = 'COMPANY', 'Compañía'
    COMMAND = 'COMMAND', 'Comandancia'
    CENTRAL = 'CENTRAL', 'Central de Comunicaciones'
    ADMIN = 'ADMIN', 'Administración General'


class Entity(models.Model):
    """
    Representa una unidad organizativa dentro del Cuerpo de Bomberos.

    Atributos:
        name (str): Nombre de la entidad.
        type (str): Tipo de entidad (definido en EntityType).
        logo (Image): Logo institucional de la entidad (opcional).

    Métodos:
        __str__() -> str: Representación legible del nombre de la entidad.
    """
    name: str = models.CharField(max_length=100, verbose_name='Nombre')
    type: str = models.CharField(max_length=20, choices=EntityType.choices, verbose_name="Tipo de entidad")
    logo = models.ImageField(upload_to='media/entity_logos/', null=True, blank=True, verbose_name='Logo institucional')

    class Meta:
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'

        permissions = [
            ('view_own_entity', 'Puede ver solo su entidad'),
        ]

    def __str__(self) -> str:
        return self.name


class Position(models.Model):
    """
    Representa un cargo que puede ocupar un usuario dentro de una entidad.

    Atributos:
        name (str): Nombre del cargo.
        is_unique (bool): Indica si solo puede haber una persona ocupando este cargo por entidad.
        permissions (ManyToMany[Permission]): Permisos asignados a este cargo.

    Métodos:
        __str__() -> str: Representación legible del nombre del cargo.
    """
    name: str = models.CharField(max_length=100, verbose_name='Nombre')
    is_unique: bool = models.BooleanField(default=False, verbose_name='Cargo exclusivo')
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name='Permisos')
    
    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    """
    Representa la asignación activa de un usuario a un cargo dentro de una entidad.

    Atributos:
        user (User): Usuario que ocupa el cargo.
        entity (Entity): Entidad donde se desempeña el cargo.
        position (Position): Cargo que ocupa el usuario.

    Métodos:
        clean() -> None: Valida unicidad si el cargo es exclusivo.
        get_permissions() -> QuerySet[Permission]: Obtiene permisos del cargo.
        has_permission(codename: str) -> bool: Verifica si el cargo tiene cierto permiso.
        __str__() -> str: Representación legible de la asignación.
    """
    user: User = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuario')
    entity: Entity = models.ForeignKey(Entity, on_delete=models.CASCADE, verbose_name='Entidad')
    position: Position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name='Cargo')

    class Meta:
        verbose_name = 'Asignación de cargo'
        verbose_name_plural = 'Asignaciones de cargo'

    def clean(self) -> None:
        if self.position.is_unique:
            exists = Membership.objects.filter(
                entity=self.entity,
                position=self.position
            ).exclude(pk=self.pk).exists()
            if exists:
                raise ValidationError(
                    _(f"El cargo '{self.position}' ya está asignado en {self.entity}.")
                )

    def get_permissions(self) -> models.QuerySet:
        return self.position.permissions.all()

    def has_permission(self, codename: str) -> bool:
        return self.position.permissions.filter(codename=codename).exists()

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} – {self.position} en {self.entity}"


class MembershipHistory(models.Model):
    """
    Almacena el historial de cargos ocupados por un usuario en distintas entidades.

    Atributos:
        full_name (str): Nombre .
        entity (Entity): Entidad en la que desempeñó el cargo.
        position (Position): Cargo desempeñado.
        start_date (date): Fecha de inicio del cargo.
        end_date (date): Fecha de término del cargo (opcional).

    Métodos:
        __str__() -> str: Representación legible del historial de cargo.
    """
    full_name = models.CharField(max_length=100, verbose_name='Nombre completo', editable=False)
    entity: Entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, verbose_name='Entidad')
    position: Position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name='Cargo')
    start_date: models.DateField = models.DateField(verbose_name='Fecha de inicio')
    end_date: models.DateField = models.DateField(null=True, blank=True, verbose_name='Fecha de término')

    class Meta:
        verbose_name = 'Historial de cargo'
        verbose_name_plural = 'Historial de cargo'

    def __str__(self) -> str:
        return f"{self.full_name} fue {self.position} en {self.entity}"

