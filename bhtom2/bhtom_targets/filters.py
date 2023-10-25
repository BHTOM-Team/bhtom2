from django.conf import settings
from django.db.models import Q
import django_filters

from bhtom_base.bhtom_targets.models import Target, TargetList
from bhtom_base.bhtom_targets.utils import cone_search_filter

CLASSIFICATION_TYPES = settings.CLASSIFICATION_TYPES

def filter_for_field(field):
    if field['type'] == 'number':
        return django_filters.RangeFilter(field_name=field['name'], method=filter_number)
    elif field['type'] == 'boolean':
        return django_filters.BooleanFilter(field_name=field['name'], method=filter_boolean)
    elif field['type'] == 'datetime':
        return django_filters.DateTimeFromToRangeFilter(field_name=field['name'], method=filter_datetime)
    elif field['type'] == 'string':
        return django_filters.CharFilter(field_name=field['name'], method=filter_text)
    else:
        raise ValueError(
            'Invalid field type {}. Field type must be one of: number, boolean, datetime string'.format(field['type'])
        )


def filter_number(queryset, name, value):
    if value.start and value.stop:
        return queryset.filter(
            targetextra__key=name, targetextra__float_value__gte=value.start, targetextra__float_value__lte=value.stop
        )
    elif value.start:
        return queryset.filter(
            targetextra__key=name, targetextra__float_value__gte=value.start
        )
    elif value.stop:
        return queryset.filter(
            targetextra__key=name, targetextra__float_value__lte=value.stop
        )


def filter_datetime(queryset, name, value):
    if value.start and value.stop:
        return queryset.filter(
            targetextra__key=name, targetextra__time_value__gte=value.start, targetextra__time_value__lte=value.stop
        )
    elif value.start:
        return queryset.filter(
            targetextra__key=name, targetextra__time_value__gte=value.start
        )
    elif value.stop:
        return queryset.filter(
            targetextra__key=name, targetextra__time_value__lte=value.stop
        )

def filter_boolean(queryset, name, value):
    return queryset.filter(targetextra__key=name, targetextra__bool_value=value)


def filter_text(queryset, name, value):
    return queryset.filter(targetextra__key=name, targetextra__value__icontains=value)


class TargetFilter(django_filters.FilterSet):

    def filter_name(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(aliases__name__icontains=value)).distinct()
   
    def filter_description(self, queryset, description, value):
        return queryset.filter(Q(description__icontains=value)).distinct()

    def filter_ra(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(ra__gte=value.start) & Q(ra__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(ra__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(ra__lte=value.stop))

    def filter_dec(self, queryset, name, value):
        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(dec__gte=value.start) & Q(dec__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(dec__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(dec__lte=value.stop))

    def filter_priority(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(cadence_priority__gte=value.start) & Q(cadence_priority__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(cadence_priority__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(cadence_priority__lte=value.stop))

    def filter_gall(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(galactic_lng__gte=value.start) & Q(galactic_lng__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(galactic_lng__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(galactic_lng__lte=value.stop))

    def filter_galb(self, queryset, name, value):
        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(galactic_lat__gte=value.start) & Q(galactic_lat__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(galactic_lat__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(galactic_lat__lte=value.stop))

    def filter_importance(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(importance__gte=value.start) & Q(importance__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(importance__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(importance__lte=value.stop))

    def filter_sunDistance(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(sun_separation__gte=value.start) & Q(sun_separation__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(sun_separation__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(sun_separation__lte=value.stop))

    def filter_magLast(self, queryset, name, value):

        if value.start is not None and value.stop is not None:
            return queryset.filter(Q(mag_last__gte=value.start) & Q(mag_last__lte=value.stop))
        elif value.start is not None:
            return queryset.filter(Q(mag_last__gte=value.start))
        elif value.stop is not None:
            return queryset.filter(Q(mag_last__lte=value.stop))

    def filter_cone_search(self, queryset, name, value):
        """
        Perform a cone search filter on this filter's queryset,
        using the cone search utlity method and either specified RA, DEC
        or the RA/DEC from the named target.
        """
        if name == 'cone_search':
            ra, dec, radius = value.split(',')
        elif name == 'target_cone_search':
            target_name, radius = value.split(',')
            targets = Target.objects.filter(
                Q(name__icontains=target_name) | Q(aliases__name__icontains=target_name)
            ).distinct()
            if len(targets) == 1:
                ra = targets[0].ra
                dec = targets[0].dec
            else:
                return queryset.filter(name=None)
        else:
            return queryset

        ra = float(ra)
        dec = float(dec)

        return cone_search_filter(queryset, ra, dec, radius)

    # hide target grouping list if user not logged in
    def get_target_list_queryset(request):
        if request.user.is_authenticated:
            return TargetList.objects.all()
        else:
            return TargetList.objects.none()

    name = django_filters.CharFilter(method='filter_name', label='Name')

    cone_search = django_filters.CharFilter(method='filter_cone_search', label='Cone Search',
                                            help_text='RA, Dec, Search Radius (degrees)')

    target_cone_search = django_filters.CharFilter(method='filter_cone_search', label='Cone Search (Target)',
                                                   help_text='Target Name, Search Radius (degrees)')

    ra: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_ra', label='RA')
    dec: django_filters.RangeFilter = django_filters.NumericRangeFilter(method='filter_dec', label='Dec')
    gall: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_gall', label='Galactic Longitude (0,360)')
    galb: django_filters.RangeFilter = django_filters.NumericRangeFilter(method='filter_galb', label='Galactic Latitude (-90,90)')

    importance: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_importance', label='Importance (0,10)')
    priority: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_priority', label='Priority')
    sun: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_sunDistance', label='Sun separation')
    mag: django_filters.RangeFilter = django_filters.RangeFilter(method='filter_magLast', label='Last magnitude')

    targetlist__name = django_filters.ModelChoiceFilter(queryset=get_target_list_queryset, label="Target Grouping")

    description = django_filters.CharFilter(method='filter_description', label='Description')

    order = django_filters.OrderingFilter(
        fields=['name', 'created', 'modified'],
        field_labels={
            'name': 'Name',
            'created': 'Creation Date',
            'modified': 'Last Update'
        }
    )

    class Meta:
        model = Target
        fields = ['type', 'name', 'classification', 'description', 'cone_search', 'targetlist__name']
