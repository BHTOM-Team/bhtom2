import django_filters
from django.db.models import Q
from bhtom_base.bhtom_dataproducts.models import CCDPhotJob, DataProduct

class CCDPhotJobFilter(django_filters.FilterSet):
    filename = django_filters.CharFilter(label='Filename', method='filter_filename')
    target_name = django_filters.CharFilter(label='Target Name', method='filter_target_name')
    observatory = django_filters.CharFilter(label='Observatory', method='filter_observatory_name')
    user = django_filters.CharFilter(label='Owner', method='filter_owner_name')
    mjd = django_filters.NumberFilter(label='MJD', method='filter_mjd')

    created = django_filters.DateFromToRangeFilter(
        label='Date Range (yyyy-mm-dd)',
        method='filter_created_range',
        help_text='Select a date range for the creation date.'
    )

    class Meta:
        model = CCDPhotJob
        fields = []
    
    def filter_filename(self, queryset, name, value):
        return queryset.filter(Q(dataProduct__data__icontains=value))
    def filter_target_name(self, queryset, name, value):
        return queryset.filter(Q(dataProduct__target__name__icontains=value))

    def filter_owner_name(self, queryset, name, value):
        return queryset.filter(Q(dataProduct__user__first_name__icontains=value))

    def filter_observatory_name(self, queryset, name, value):
        return queryset.filter(Q(dataProduct__observatory__camera__observatory__name__icontains=value))

    def filter_mjd(self, queryset, name, value):
        return queryset.filter(
            Q(dataProduct__spectroscopydatum__mjd=value) |
            Q(dataProduct__calibration_data__mjd=value)
        )

    def filter_created_range(self, queryset, name, value):
        if value.start and value.stop:
            return queryset.filter(dataProduct__created__range=(value.start, value.stop))
        elif value.start:
            return queryset.filter(dataProduct__created__gte=value.start)
        elif value.stop:
            return queryset.filter(dataProduct__created__lte=value.stop)
        return queryset
    




class DataproductFilter(django_filters.FilterSet):
    filename = django_filters.CharFilter(label='Filename', method='filter_filename')
    target_name = django_filters.CharFilter(label='Target Name', method='filter_target_name')
    observatory = django_filters.CharFilter(label='Observatory', method='filter_observatory_name')
    user = django_filters.CharFilter(label='Owner', method='filter_owner_name')
    mjd = django_filters.NumberFilter(label='MJD', method='filter_mjd')

    created = django_filters.DateFromToRangeFilter(
        label='Date Range (yyyy-mm-dd)',
        method='filter_created_range',
        help_text='Select a date range for the creation date.'
    )

    class Meta:
        model = DataProduct
        fields = []

    def filter_filename(self, queryset, name, value):
        return queryset.filter(Q(data__icontains=value))

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

    def filter_created_range(self, queryset, name, value):
        if value.start and value.stop:
            return queryset.filter(created__range=(value.start, value.stop))
        elif value.start:
            return queryset.filter(created__gte=value.start)
        elif value.stop:
            return queryset.filter(created__lte=value.stop)
        return queryset