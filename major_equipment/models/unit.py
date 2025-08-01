from django.db import models
from docs.models import File, FileVencible
from firebrigade.models import Entity 
from major_equipment.utils.validators import validate_chilean_plate

# ENUMs para tipos de vehículos y combustible

class VehicleType(models.IntegerChoices):
    """
    ENUM de tipos de vehículos.
    """
    CAR = 1, "Automóvil"
    SUV = 2, "Todoterreno"
    TRUCK = 3, "Camión"
    VAN = 4, "Furgoneta"
    BUS = 5, "Bus"
    MOTORCYCLE = 6, "Motocicleta"
    AMBULANCE = 7, "Ambulancia"
    OTHER = 8, "Otro"

class FuelType(models.IntegerChoices):
    """
    ENUM de tipos de combustible.
    """
    GASOLINE = 1, "Bencina"
    DIESEL = 2, "Diésel"
    ELECTRIC = 3, "Eléctrico"

class State(models.IntegerChoices):
    """
    ENUM de estados.
    """
    IN_OPERATION = 1, "Operativo"
    IN_MAINTENANCE = 2, "En mantención"

# Clase para representar una unidad de material mayor (vehículo) del Cuerpo de Bomberos e imagenes asociadas.

class Unit(models.Model):
    """
    Representa una unidad de material mayor (vehículo) del Cuerpo de Bomberos.

    Contiene datos de identificación, especificaciones técnicas, neumáticos y frenos,
    documentos asociados y estado de la unidad.
    """
    # Identificación
    unit_number = models.CharField(max_length=10, unique=True, verbose_name="Número de unidad")
    description = models.CharField(max_length=100, verbose_name="Descripción")
    plate_number = models.CharField(max_length=10, unique=True, verbose_name="Placa patente", validators=[validate_chilean_plate])
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT, verbose_name="Entidad asignada", related_name="units")

    # Especificaciones técnicas
    brand = models.CharField(max_length=100, verbose_name="Marca", blank=True, null=True)
    model = models.CharField(max_length=100, verbose_name="Modelo", blank=True, null=True)
    year = models.PositiveIntegerField(verbose_name="Año", blank=True, null=True)
    vehicle_type = models.IntegerField(choices=VehicleType.choices, verbose_name="Tipo de vehículo", blank=True, null=True)
    fuel_type = models.IntegerField(choices=FuelType.choices, verbose_name="Tipo de combustible", blank=True, null=True)
    fuel_tank_capacity = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Capacidad estanque de combustible (L)", blank=True, null=True)
    engine_number = models.CharField(max_length=100, verbose_name="N° de motor", blank=True, null=True)
    chassis_number = models.CharField(max_length=100, verbose_name="N° de chasis", blank=True, null=True)

    # Neumáticos y frenos
    tire_size = models.CharField(max_length=100, verbose_name="Tamaño neumático", blank=True, null=True)
    tire_pressure = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Presión neumático (psi)", blank=True, null=True)

    padron = models.ForeignKey(File, on_delete=models.PROTECT, verbose_name="Padrón", blank=True, null=True, related_name="unit_padron")
    soap = models.ForeignKey(FileVencible, on_delete=models.PROTECT, verbose_name="SOAP", blank=True, null=True, related_name="unit_soap")
    technical_inspection = models.ForeignKey(FileVencible, on_delete=models.PROTECT, verbose_name="Revisión técnica", blank=True, null=True, related_name="unit_technical_inspection")
    vehicle_permit = models.ForeignKey(FileVencible, on_delete=models.PROTECT, verbose_name="Permiso de circulación", blank=True, null=True, related_name="unit_vehicle_permit")

    # Estado del objeto
    state = models.IntegerField(choices=State.choices, default=State.IN_OPERATION, verbose_name="Estado")
    editable = models.BooleanField(default=True, verbose_name="Editable")
    deleted = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"
        permissions = [
            ("view_company_majorequipment"   , "Puede ver unidades de su compañía"),
            ("change_company_majorequipment" , "Puede modificar unidades de su compañía"),
        ]

    def __str__(self):
        """Representación textual de la unidad."""
        return f"{self.unit_number} - {self.description}"

class UnitImage(models.Model):
    """
    Imagen asociada a una unidad, con una descripción opcional.
    """
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="images", verbose_name="Unidad")
    image = models.ImageField(upload_to="unit_images/", verbose_name="Imagen")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Imagen de unidad"
        verbose_name_plural = "Imágenes de unidades"

    def __str__(self):
        return f"Imagen de {self.unit}"