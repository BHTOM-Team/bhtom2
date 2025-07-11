import django_filters
from django.db.models import Q
from bhtom_base.bhtom_dataproducts.models import DataProduct

class FitsFilter(django_filters.FilterSet):
    target_name = django_filters.CharFilter(label='Target Name', method='filter_target_name')
    observatory = django_filters.CharFilter(label='Observatory', method='filter_observatory_name')
    user = django_filters.CharFilter(label='Owner', method='filter_owner_name')
    mjd = django_filters.NumberFilter(label='MJD', method='filter_mjd')

    created = django_filters.DateFromToRangeFilter(label='Date Range (yyyy-mm-dd)', 
        help_text='Select a date range for the creation date.')

    class Meta:
        model = DataProduct
        fields = [
            'target_name', 'observatory',
            'user','created'
        ]

    def filter_target_name(self, queryset, name, value):
        return queryset.filter(Q(target__name__icontains=value))
    
    def filter_owner_name(self, queryset, name, value):
        return queryset.filter(Q(user__first_name__icontains=value))
    
    def filter_observatory_name(self, queryset, name, value):
        return queryset.filter(Q(observatory__camera__observatory__name__icontains=value))
    
    def filter_mjd(self, queryset, name, value):
           return queryset.filter(
            Q(spectroscopydatum__mjd=value) | 
            Q(calibration_data__mjd=value)
        )