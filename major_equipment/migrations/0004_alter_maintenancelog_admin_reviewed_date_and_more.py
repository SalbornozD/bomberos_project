# Generated by Django 5.2.4 on 2025-07-24 16:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firebrigade', '0001_initial'),
        ('major_equipment', '0003_fuellog_author_fuellog_deleted_fuellog_editable'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='maintenancelog',
            name='admin_reviewed_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de aprobación por Administración'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='approved_by_admin',
            field=models.BooleanField(blank=True, default=None, null=True, verbose_name='Aprobado por Administración'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='approved_by_command',
            field=models.BooleanField(blank=True, default=None, null=True, verbose_name='Aprobado por Comandancia'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_logs_author', to=settings.AUTH_USER_MODEL, verbose_name='Autor'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='command_reviewed_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de aprobación por Comandancia'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='responsible_for_payment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_logs_responsible', to='firebrigade.entity', verbose_name='Responsable de pago'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='reviewed_by_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_logs_reviewed_admin', to=settings.AUTH_USER_MODEL, verbose_name='Revisado por Administración'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='reviewed_by_command',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_logs_reviewed_command', to=settings.AUTH_USER_MODEL, verbose_name='Revisado por Comandancia'),
        ),
        migrations.AlterField(
            model_name='maintenancelog',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_logs_unit', to='major_equipment.unit', verbose_name='Unidad'),
        ),
    ]
