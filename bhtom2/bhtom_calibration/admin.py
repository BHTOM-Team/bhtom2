from django.contrib import admin
from bhtom2.bhtom_calibration.models import Calibration_data
from django.db.models import Q


class CalibrationDataAdmin(admin.ModelAdmin):
    model = Calibration_data
    list_display = ['id', 'status_message', 'created', 'dataproduct_id']
    list_filter = ['status_message', 'created']
    search_fields = ['status_message']  

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        try:
            search_id = int(search_term)
            queryset |= self.model.objects.filter(Q(id=search_id) | Q(dataproduct_id=search_id))
        except ValueError:
            pass
        return queryset, use_distinct

admin.site.register(Calibration_data, CalibrationDataAdmin)
