from django.db import models
from django.utils import timezone
from .unit import Unit

class FuelLog(models.Model):
    """Registro de cada vez que una unidad carga combustible."""
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="fuel_logs", verbose_name="Unidad")
    date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de carga")
    quantity = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad (L)")
    cost = models.IntegerField(verbose_name="Costo")
    station = models.CharField(max_length=150, blank=True, null=True, verbose_name="Estación de servicio")
    notes = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    ticket = models.ImageField(upload_to="fuel_tickets", blank=True, null=True, verbose_name="Boleta de combustible")

    class Meta:
        verbose_name = "Registro de combustible"
        verbose_name_plural = "Registros de combustible"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.unit.unit_number} • {self.date:%d/%m/%Y %H:%M} • {self.quantity} L"
    
    @property
    def ticket_url(self):
        if self.ticket:
            return self.ticket.url
        return None
