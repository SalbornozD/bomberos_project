from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from .unit import Unit
from firebrigade.models import Entity
from docs.models import File

User = get_user_model()

class FuelLevel(models.IntegerChoices):
    """ENUM de posibles niveles de combustible."""
    EMPTY = 0, "Vacío"
    ONE_QUARTER = 1, "Un cuarto de tanque"
    HALF = 2, "Medio tanque"
    THREE_QUARTERS = 3, "Tres cuartos de tanque"
    FULL = 4, "Tanque lleno"

class MaintenanceLog(models.Model):
    """Solicitud de mantención de una unidad."""
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name="Unidad", related_name="maintenance_logs")
    description = models.TextField(verbose_name="Descripción")
    responsible_for_payment = models.ForeignKey(Entity, on_delete=models.PROTECT, verbose_name="Responsable de pago", related_name="maintenance_logs")
    author = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Autor", related_name="maintenance_logs")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")

    # Aprobaciones Comandancia.
    approved_by_command = models.BooleanField(default=False, verbose_name="Aprobado por Comandancia")
    command_observations = models.TextField(blank=True, null=True, verbose_name="Observaciones de Comandancia")
    reviewed_by_command = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, verbose_name="Revisado por Comandancia", related_name="maintenance_logs_command")
    command_reviewed_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación por comandancia")
    
    # Aprobaciones Administración.
    approved_by_admin = models.BooleanField(default=False, verbose_name="Aprobado por Administración")
    admin_observations = models.TextField(blank=True, null=True, verbose_name="Observaciones de Administración")
    reviewed_by_admin = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, verbose_name="Revisado por Administración", related_name="maintenance_logs_admin")
    admin_reviewed_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación por administración")

    # Auditoria
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        verbose_name = "Solicitud de mantención"
        verbose_name_plural = "Solicitudes de mantenciones"
        permissions = [
            ("view_own_maintenancerequests",    "Puede ver sus propias solicitudes"),
            ("view_company_maintenancerequests","Puede ver solicitudes de su compañía"),
            ("change_own_maintenancerequests",  "Puede editar sus propias solicitudes"),
            ("change_company_maintenancerequests","Puede editar solicitudes de su compañía"),
            ("delete_own_maintenancerequests",  "Puede eliminar sus propias solicitudes"),
            ("delete_company_maintenancerequests","Puede eliminar solicitudes de su compañía"),
            ("approve_maintenance_as_command",   "Puede aprobar solicitudes como Comandancia"),
            ("approve_maintenance_as_admin",     "Puede aprobar solicitudes como Administración"),
        ]

    def __str__(self):
        return f"{self.unit} • {self.requested_at:%d/%m/%Y}"

class Quotation(models.Model):
    """Registro de cotizaciones."""
    log = models.ForeignKey(MaintenanceLog, on_delete=models.PROTECT, verbose_name="Solicitud de mantención")
    file = models.ForeignKey(File, on_delete=models.PROTECT, verbose_name="Archivo")
    cost = models.PositiveIntegerField(verbose_name="Costo")
    expiration_date = models.DateTimeField(verbose_name="Fecha de expiración", help_text="Fecha hasta la cual la cotización es válida")
    comment = models.TextField(blank=True, null=True, verbose_name="Comentarios")
    workshop_name = models.CharField(max_length=255, verbose_name="Taller")
    author = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Autor")
    is_favorite = models.BooleanField(default=False, verbose_name="Favorita")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")
    

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"

    def __str__(self):
        return f"Cotización para {self.log.unit.unit_number} · {self.workshop_name}"

class MeetingWorkshop(models.Model):
    """Cita con el taller."""
    log = models.ForeignKey(MaintenanceLog, on_delete=models.PROTECT, verbose_name="Solicitud de mantención", related_name="meetings")
    dispatch_date = models.DateField(verbose_name="Fecha de despacho")
    estimated_return_date = models.DateField(verbose_name="Fecha estimada de retorno")
    comments = models.TextField(blank=True, null=True, verbose_name="Comentarios")
    author = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Autor")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        verbose_name = "Cita con el taller"
        verbose_name_plural = "Citas con el taller"
    
    def __str__(self):
        return f"Cita para {self.log.unit.unit_number} · {self.dispatch_date:%d/%m/%Y}"

class UnitShipment(models.Model):
    """Envío de una unidad al taller."""
    meeting_workshop = models.ForeignKey(MeetingWorkshop, on_delete=models.PROTECT, verbose_name="Cita con el taller")
    fuel_level = models.IntegerField(choices=FuelLevel.choices, default=FuelLevel.EMPTY, verbose_name="Nivel de combustible")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    author = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Autor")
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")
    hourmeter = models.PositiveIntegerField(verbose_name="Horómetro")
    mileage = models.PositiveIntegerField(verbose_name="Kilometraje")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Envío de unidad al taller"
        verbose_name_plural = "Envíos de unidades al taller"
    
    def __str__(self):
        return f"Envío de {self.meeting_workshop.log.unit.unit_number} · {self.creation_date:%d/%m/%Y}"

class UnitReception(models.Model):
    """Recepción de una unidad del taller."""
    unit_shipment = models.ForeignKey(UnitShipment, on_delete=models.PROTECT, verbose_name="Envío de unidad al taller")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    author = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Autor")
    hourmeter = models.PositiveIntegerField(verbose_name="Horómetro")
    mileage = models.PositiveIntegerField(verbose_name="Kilometraje")
    fuel_level = models.IntegerField(choices=FuelLevel.choices, default=FuelLevel.EMPTY, verbose_name="Nivel de combustible")
    reception_ok = models.BooleanField(default=True, verbose_name="Recepción OK")
    invoice = models.ForeignKey(File, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Factura")
    comments = models.TextField(blank=True, null=True, verbose_name="Comentarios")
    cost = models.PositiveIntegerField(verbose_name="Costo")
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        verbose_name = "Recepción de unidad del taller"
        verbose_name_plural = "Recepciones de unidades del taller"
        