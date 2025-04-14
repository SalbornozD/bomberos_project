from datetime import date, timedelta
from django.db import models
from django.utils.timezone import now
from firebrigade.models import Entity
from django.contrib.auth.models import User

# -----------------------
# Tipos y catálogos
# -----------------------

class VehicleType(models.Model):
    """
    Define los tipos de vehículos disponibles, como carros bomba, unidades de rescate, ambulancias, etc.

    Atributos:
        name (str): Nombre del tipo de vehículo.

    Métodos:
        __str__() -> str: Devuelve el nombre como representación legible del tipo.
    """
    name = models.CharField(max_length=100, verbose_name="Tipo de vehículo")

    class Meta:
        verbose_name = "Tipo de vehículo"
        verbose_name_plural = "Tipos de vehículos"

    def __str__(self):
        return self.name


class FuelType(models.IntegerChoices):
    """
    Enumeración de los tipos de combustible que puede utilizar una unidad.

    Atributos/Opciones:
        GASOLINE_93 (int): Bencina - 93 octanos
        GASOLINE_95 (int): Bencina - 95 octanos
        GASOLINE_97 (int): Bencina - 97 octanos
        DIESEL (int): Diésel
        ELECTRIC (int): Eléctrico
    """
    GASOLINE_93 = 1, "Bencina - 93 octanos"
    GASOLINE_95 = 2, "Bencina - 95 octanos"
    GASOLINE_97 = 3, "Bencina - 97 octanos"
    DIESEL = 4, "Diésel"
    ELECTRIC = 5, "Eléctrico"

# -----------------------
# Material Mayor
# -----------------------

class MajorEquipment(models.Model):
    """
    Representa una unidad de material mayor del Cuerpo de Bomberos.

    Atributos:
        unit_number (str): Número de unidad único.
        short_description (str): Descripción breve de la unidad.
        plate_number (str): Patente única del vehículo.
        entity (Entity): Entidad a la que pertenece la unidad.
        [Categorías técnicas]: Información técnica del vehículo (motor, frenos, bomba, etc.).
        [Documentos]: Archivos adjuntos y fechas de vencimiento.
        next_maintenance_date (date): Fecha de próxima mantención.

    Métodos:
        __str__() -> str
        get_registration_certificate_status() -> str
        get_soap_certificate_status() -> str
        get_technical_inspection_certificate_status() -> str
        get_vehicle_permit_status() -> str
        get_next_maintenance_status() -> str
    """

    # Opciones de elección
    class DiscType(models.IntegerChoices):
        SOLID = 1, "Sólido"
        VENTILATED = 2, "Ventilado"
        PERFORATED = 3, "Perforado"

    class PadType(models.IntegerChoices):
        ORGANIC = 1, "Orgánica"
        SEMI_METALLIC = 2, "Semi-metálica"
        METALLIC = 3, "Metálica"

    # Identificación general
    unit_number = models.CharField(max_length=10, unique=True, verbose_name="Número de unidad")
    short_description = models.CharField(max_length=100, verbose_name="Descripción")
    plate_number = models.CharField(max_length=10, unique=True, verbose_name="Placa patente")
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, verbose_name="Entidad asignada")

    # Información técnica general
    brand = models.CharField(max_length=100, verbose_name="Marca", blank=True, null=True)
    model = models.CharField(max_length=100, verbose_name="Modelo", blank=True, null=True)
    year = models.IntegerField(verbose_name="Año", blank=True, null=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, verbose_name="Tipo de vehículo", null=True, blank=True)
    fuel_type = models.IntegerField(choices=FuelType.choices, verbose_name="Tipo de combustible", blank=True, null=True)
    cylinders = models.CharField(max_length=100, verbose_name="Cilindros", blank=True, null=True)
    displacement = models.CharField(max_length=100, verbose_name="Cilindrada", blank=True, null=True)
    transmission = models.CharField(max_length=100, verbose_name="Transmisión", blank=True, null=True)
    drive_system = models.CharField(max_length=100, verbose_name="Sistema de tracción", blank=True, null=True)
    fuel_tank_capacity = models.CharField(max_length=100, verbose_name="Capacidad del estanque de combustible", blank=True, null=True)

    # Motor y aceite
    engine_number = models.CharField(max_length=100, verbose_name="Número de motor", blank=True, null=True)
    chassis_number = models.CharField(max_length=100, verbose_name="Número de chasis", blank=True, null=True)
    motor_oil_type = models.CharField(max_length=100, verbose_name="Tipo de aceite de motor", blank=True, null=True)
    motor_oil_capacity = models.CharField(max_length=100, verbose_name="Capacidad de aceite de motor", blank=True, null=True)
    gearbox_oil_type = models.CharField(max_length=100, verbose_name="Tipo de aceite de caja de cambios", blank=True, null=True)
    differential_oil_type = models.CharField(max_length=100, verbose_name="Tipo de aceite de diferencial", blank=True, null=True)
    differential_oil_capacity = models.CharField(max_length=100, verbose_name="Capacidad de aceite de diferencial", blank=True, null=True)

    # Filtros
    fuel_filter_quantity = models.CharField(max_length=100, verbose_name="Cantidad de filtros de combustible", blank=True, null=True)
    fuel_part_number = models.CharField(max_length=100, verbose_name="Nomenclatura de filtro de combustible", blank=True, null=True)
    oil_filter_quantity = models.CharField(max_length=100, verbose_name="Cantidad de filtros de aceite", blank=True, null=True)
    oil_part_number = models.CharField(max_length=100, verbose_name="Nomenclatura de filtro de aceite", blank=True, null=True)
    air_filter_part_number = models.CharField(max_length=100, verbose_name="Nomenclatura de filtro de aire", blank=True, null=True)
    air_purifier_part_number = models.CharField(max_length=100, verbose_name="Nomenclatura de purificador de aire", blank=True, null=True)


    # Neumáticos y frenos
    tire_size = models.CharField(max_length=100, verbose_name="Tamaño de neumático", blank=True, null=True)
    tire_brand = models.CharField(max_length=100, verbose_name="Marca de neumático", blank=True, null=True)
    tire_pressure = models.CharField(max_length=100, verbose_name="Presión de neumático", blank=True, null=True)
    brake_system_type = models.CharField(max_length=100, verbose_name="Tipo de sistema de freno", blank=True, null=True)
    parking_brake_type = models.CharField(max_length=100, verbose_name="Tipo de freno de estacionamiento", blank=True, null=True)
    pad_type = models.IntegerField(choices=PadType.choices, verbose_name="Tipo de pastilla", blank=True, null=True)
    disc_type = models.IntegerField(choices=DiscType.choices, verbose_name="Tipo de disco", blank=True, null=True)

    # Bomba y sistema hidráulico
    water_tank_capacity = models.CharField(max_length=100, verbose_name="Capacidad de estanque de agua", blank=True, null=True)
    pump_type = models.CharField(max_length=100, verbose_name="Tipo de bomba", blank=True, null=True)
    pump_capacity = models.CharField(max_length=100, verbose_name="Capacidad de bomba", blank=True, null=True)
    pump_pressure = models.CharField(max_length=100, verbose_name="Presión de bomba", blank=True, null=True)
    pump_model = models.CharField(max_length=100, verbose_name="Modelo de bomba", blank=True, null=True)
    pump_brand = models.CharField(max_length=100, verbose_name="Marca de bomba", blank=True, null=True)
    pump_serial_number = models.CharField(max_length=100, verbose_name="Número de serie de bomba", blank=True, null=True)
    pump_year = models.IntegerField(verbose_name="Año de bomba", blank=True, null=True)
    maximum_flow_rate = models.CharField(max_length=100, verbose_name="Caudal máximo", blank=True, null=True)

    # Documentos y vencimientos
    registration_certificate = models.FileField(upload_to="major_equipment/registration_certificates", verbose_name="Padrón del vehículo", blank=True, null=True)
    soap_certificate = models.FileField(upload_to="major_equipment/soap_certificates", verbose_name="Certificado SOAP", blank=True, null=True)
    soap_certificate_expiration = models.DateField(verbose_name="Vencimiento del SOAP", blank=True, null=True)
    technical_inspection_certificate = models.FileField(upload_to="major_equipment/technical_inspection_certificates", verbose_name="Certificado de revisión técnica", blank=True, null=True)
    technical_inspection_certificate_expiration = models.DateField(verbose_name="Vencimiento de la revisión técnica", blank=True, null=True)
    vehicle_permit = models.FileField(upload_to="major_equipment/vehicle_permits", verbose_name="Permiso de circulación", blank=True, null=True)
    vehicle_permit_expiration = models.DateField(verbose_name="Vencimiento del permiso de circulación", blank=True, null=True)

    # Mantención
    next_maintenance_date = models.DateField(verbose_name="Próxima mantención", blank=True, null=True)

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"
        permissions = [
            ("view_company_majorequipment", "Puede ver unidades de su compañía"),
            ("add_company_majorequipment", "Puede agregar unidades para su compañía"),
            ("change_company_majorequipment", "Puede modificar unidades de su compañía"),
            ("delete_company_majorequipment", "Puede eliminar unidades de su compañía"),
        ]

    def __str__(self) -> str:
        return f"{self.unit_number} - {self.short_description}"

    def get_registration_certificate_status(self) -> str:
        if not self.registration_certificate_expiration:
            return "Sin información"
        elif self.registration_certificate_expiration < date.today():
            return "Vencido"
        elif self.registration_certificate_expiration <= date.today() + timedelta(days=30):
            return "Por vencer"
        return "Vigente"

    def get_soap_certificate_status(self) -> str:
        if not self.soap_certificate_expiration:
            return "Sin información"
        elif self.soap_certificate_expiration < date.today():
            return "Vencido"
        elif self.soap_certificate_expiration <= date.today() + timedelta(days=30):
            return "Por vencer"
        return "Vigente"

    def get_technical_inspection_certificate_status(self) -> str:
        if not self.technical_inspection_certificate_expiration:
            return "Sin información"
        elif self.technical_inspection_certificate_expiration < date.today():
            return "Vencido"
        elif self.technical_inspection_certificate_expiration <= date.today() + timedelta(days=30):
            return "Por vencer"
        return "Vigente"

    def get_vehicle_permit_status(self) -> str:
        if not self.vehicle_permit_expiration:
            return "Sin información"
        elif self.vehicle_permit_expiration < date.today():
            return "Vencido"
        elif self.vehicle_permit_expiration <= date.today() + timedelta(days=30):
            return "Por vencer"
        return "Vigente"

    def get_next_maintenance_status(self) -> str:
        if not self.next_maintenance_date:
            return "Sin información"
        elif self.next_maintenance_date < date.today():
            return "Vencida"
        elif self.next_maintenance_date <= date.today() + timedelta(days=30):
            return "Por vencer"
        return "Vigente"

    def get_state(self) -> str:
        return "Activo"

# -----------------------
# Imágenes de unidad
# -----------------------

class UnitImage(models.Model):
    """
    Representa una imagen asociada a una unidad de material mayor.

    Atributos:
        unit (MajorEquipment): Unidad a la que pertenece la imagen.
        image (ImageField): Archivo de imagen subido.
        description (str): Descripción breve de la imagen (opcional).

    Métodos:
        __str__() -> str: Retorna una representación legible indicando a qué unidad pertenece la imagen.
    """

    unit = models.ForeignKey(
        MajorEquipment,
        on_delete=models.CASCADE,
        verbose_name="Unidad",
        related_name="images"
    )
    image = models.ImageField(
        upload_to="media/unit_images",
        verbose_name="Imagen"
    )
    description = models.CharField(
        max_length=100,
        verbose_name="Descripción",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Imagen de unidad"
        verbose_name_plural = "Imágenes de unidades"

    def __str__(self) -> str:
        return f"Imagen de {self.unit}"

# -----------------------
# Reporte de desperfecto
# -----------------------

class MaintenanceReport(models.Model):
    """
    Reporte inicial de un desperfecto o falla detectada en una unidad de Material Mayor.

    Generalmente es informado por los cuarteleros u operarios, permitiendo llevar un registro formal
    de los problemas encontrados en los vehículos.

    Atributos:
        unit (MajorEquipment): Unidad afectada por el desperfecto.
        reported_by (User): Usuario que realizó el reporte.
        description (str): Descripción detallada del problema.
        created_at (datetime): Fecha y hora en que se creó el reporte.
        editable (bool): Indica si el reporte puede seguir siendo modificado (controlado por la lógica de negocio).

    Métodos:
        __str__() -> str:
            Devuelve una representación legible del reporte.
    """

    unit = models.ForeignKey(MajorEquipment, on_delete=models.CASCADE, verbose_name="Unidad")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Reportado por")
    description = models.TextField(verbose_name="Descripción del desperfecto")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de reporte", editable=True)
    editable = models.BooleanField(default=True, verbose_name="Editable")

    class Meta:
        verbose_name = "Reporte de desperfecto"
        verbose_name_plural = "Reportes de desperfectos"

        # Permisos adicionales personalizados
        permissions = (
            # Permiso de creación propio
            ("create_own_maintenancereport", "Puede crear reportes en su propio nombre"),

            # Permisos de lectura
            ("view_own_maintenancereports", "Puede ver sus propios reportes"),
            ("view_company_maintenancereport", "Puede ver reportes de su compañía"),

            # Permisos de edición
            ("change_own_maintenancereport", "Puede editar sus propios reportes"),
            ("change_company_maintenancereport", "Puede editar reportes de su compañía"),
            ("change_body_maintenancereport", "Puede editar reportes de todo el cuerpo"),

            # Permisos de eliminación
            ("delete_own_maintenancereport", "Puede eliminar sus propios reportes"),
            ("delete_company_maintenancereport", "Puede eliminar reportes de su compañía"),
        )

    def __str__(self) -> str:
        return f"Reporte {self.id} - {self.unit}"