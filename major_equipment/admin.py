from django.contrib import admin
from .models import *

admin.site.register(Unit)
admin.site.register(UnitImage)
admin.site.register(Report)
admin.site.register(ReportItemOption)
admin.site.register(ReportTemplateItem)
admin.site.register(MaintenanceLog)
admin.site.register(FuelLog)
admin.site.register(Quotation)
admin.site.register(MeetingWorkshop)

