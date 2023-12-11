from django.contrib import admin
from bhtom2.bhtom_calibration.models import Calibration_data
# Register your models here.

class CalibrationDataAdmin(admin.ModelAdmin):
    model = Calibration_data
    list_display = ['id', 'status_message', 'created', ]
    list_filter = ['id', 'status_message', 'created']
    search_fields = ['id', 'status_message','created']


admin.site.register(Calibration_data, CalibrationDataAdmin)
