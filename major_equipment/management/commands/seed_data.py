import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import IntegrityError

from firebrigade.models import Entity
from major_equipment.models import (
    MajorEquipment,
    MaintenanceReport,
    MaintenanceRequest,
    VehicleType,
    FuelType,
)

class Command(BaseCommand):
    help = "Seed the DB with test units, reports, and requests"

    def handle(self, *args, **options):
        # ——————————————————————————————
        # Limpieza inicial (borrar todo para evitar duplicados)
        MaintenanceRequest.objects.all().delete()
        MaintenanceReport.objects.all().delete()
        MajorEquipment.objects.all().delete()
        self.stdout.write("🗑️  Cleared existing units, reports and requests")

        """# 1) Usuarios de prueba
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("admin", "admin@example.com", "adminpass")
            self.stdout.write("✅ Created superuser 'admin'")
        users = []
        for i in range(1, 4):
            u, _ = User.objects.get_or_create(
                username=f"user{i}",
                defaults={"email": f"user{i}@example.com", "password": "password"}
            )
            users.append(u)
        self.stdout.write(f"✅ Ensured {len(users)} regular users")

        # 2) Entidades existentes
        ents = list(Entity.objects.filter(name__in=["Cuerpo de Bomberos", "Primera compañia de bomberos"]))
        if len(ents) < 2:
            self.stdout.write(self.style.ERROR("Faltan las dos entidades requeridas"))
            return

        # 3) Tipos de vehículo
        if VehicleType.objects.count() == 0:
            for name in ["Carro Bomba", "Ambulancia", "Camión Cisterna"]:
                VehicleType.objects.create(name=name)
        vtypes = list(VehicleType.objects.all())
        fuels = [c[0] for c in FuelType.choices]

        # 4) Crear 10 unidades (5 por entidad)
        units = []
        for ent in ents:
            for n in range(5):
                plate = None
                # Generar placa única
                while True:
                    plate = f"PB{random.randint(100,999)}"
                    if not MajorEquipment.objects.filter(plate_number=plate).exists():
                        break
                unit_no = f"U{ent.id}{n+1:02}"
                try:
                    unit = MajorEquipment.objects.create(
                        unit_number=unit_no,
                        short_description=random.choice(["Rescate","Transporte","Soporte"]),
                        plate_number=plate,
                        entity=ent,
                        brand=random.choice(["Ford","Chevrolet","Mercedes"]),
                        model=random.choice(["X1","Z3","Alpha"]),
                        year=random.randint(2000, timezone.now().year),
                        vehicle_type=random.choice(vtypes),
                        fuel_type=random.choice(fuels),
                    )
                except IntegrityError:
                    continue
                units.append(unit)
        self.stdout.write(f"✅ Created {len(units)} units")

        # 5) Crear 10–20 reportes por unidad
        report_texts = ["Batería descompuesta", "Cambio de aceite", "Fallo en luces",
                        "Revisión de frenos", "Filtro de aire sucio"]
        reports = []
        for unit in units:
            for _ in range(random.randint(10,20)):
                rpt = MaintenanceReport.objects.create(
                    unit=unit,
                    reported_by=random.choice(users),
                    description=random.choice(report_texts),
                    created_at=timezone.now() - timedelta(days=random.randint(1,365))
                )
                reports.append(rpt)
        self.stdout.write(f"✅ Created {len(reports)} maintenance reports")

        # 6) Crear 5–10 solicitudes por unidad usando cada reporte solo una vez
        available_reports = reports.copy()
        requests = []
        for unit in units:
            for _ in range(random.randint(5,10)):
                if available_reports:
                    rpt = available_reports.pop(random.randrange(len(available_reports)))
                else:
                    rpt = None

                req = MaintenanceRequest.objects.create(
                    unit=unit,
                    report=rpt,
                    requested_by=random.choice(users),
                    requested_at=timezone.now() - timedelta(days=random.randint(0,180)),
                    description=random.choice(report_texts),
                    responsible_for_payment=random.choice(ents),
                )
                requests.append(req)
        self.stdout.write(f"✅ Created {len(requests)} maintenance requests")"""
