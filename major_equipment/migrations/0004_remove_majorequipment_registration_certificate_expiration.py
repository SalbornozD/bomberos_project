# Generated by Django 5.2 on 2025-04-11 20:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('major_equipment', '0003_maintenancereport'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='majorequipment',
            name='registration_certificate_expiration',
        ),
    ]
