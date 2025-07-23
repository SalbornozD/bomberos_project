from django.db import models
from django.utils import timezone
from .unit import Unit
from django.contrib.auth.models import User

class Station(models.Model):
    """Representa una estación de servicio."""
    label   = models.CharField(max_length=300, verbose_name="Nombre de la estación")
    address = models.CharField(max_length=1000, verbose_name="Dirección")

    def __str__(self):
        return self.label


class FuelLog(models.Model):
    """Registro de cada vez que una unidad carga combustible."""
    guide_number  = models.PositiveIntegerField(verbose_name="Número de guía")
    station       = models.ForeignKey(Station, on_delete=models.PROTECT, related_name="fuel_logs", verbose_name="Estación de servicio")
    unit          = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="fuel_logs", verbose_name="Unidad")
    date          = models.DateTimeField(default=timezone.now, verbose_name="Fecha de carga")
    quantity      = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad (L)")
    cost          = models.IntegerField(verbose_name="Costo (CLP)")
    notes         = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    ticket        = models.ImageField(upload_to="fuel_tickets/", blank=True, null=True, verbose_name="Boleta de combustible")
    cargo_mileage = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Kilometraje al cargar")
    author        = models.ForeignKey(User, on_delete=models.PROTECT, related_name="fuel_logs", verbose_name="Autor")
    editable      = models.BooleanField(default=True, verbose_name="Editable")
    deleted       = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        verbose_name        = "Registro de combustible"
        verbose_name_plural = "Registros de combustible"
        ordering            = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "guide_number"],
                name="unique_guide_per_station"
            )
        ]

    def __str__(self):
        return f"{self.station.label} #{self.guide_number} — {self.date:%d/%m/%Y %H:%M}"

    @property
    def ticket_url(self):
        return self.ticket.url if self.ticket else None
