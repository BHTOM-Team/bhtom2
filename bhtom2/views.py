from abc import ABC, abstractmethod
from datetime import datetime
from astropy.time import Time
from django.views.generic import View
from bhtom2.dataproducts import last_jd
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.reduced_data_utils import save_photometry_data_for_target_to_csv_file, save_radio_data_for_target_to_csv_file
from django_filters.views import FilterView
from django.contrib.auth.mixins import PermissionRequiredMixin
from bhtom_base.bhtom_alerts.alerts import get_service_classes
from bhtom_base.bhtom_alerts.models import BrokerQuery
from bhtom_base.bhtom_alerts.views import BrokerQueryFilter
from bhtom2.templatetags.dataproduct_extras import photometry_for_target_icon
from django_tables2.views import SingleTableMixin
import django_tables2 as tables
from django_tables2 import Table
from django.utils.html import format_html
from django.urls import reverse_lazy, reverse
from guardian.mixins import PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms, assign_perm
from bhtom_base.bhtom_targets.filters import TargetFilter
from bhtom_base.bhtom_targets.models import Target, TargetExtra, TargetList, TargetName
from astropy import units as u
from astropy.coordinates import get_sun, SkyCoord
from numpy import around
from bhtom2.utils.coordinate_utils import computePriority

logger: BHTOMLogger = BHTOMLogger(__name__, '[BHTOM2 views]')

class BrokerQueryListView(FilterView):
    """
    View that displays all saved ``BrokerQuery`` objects.
    """
    model = BrokerQuery
    template_name = 'bhtom_alerts/brokerquery_list.html'
    filterset_class = BrokerQueryFilter

    def get_context_data(self, *args, **kwargs):
        """
        Adds the brokers available to the TOM to the context dictionary.

        :returns: context
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context['installed_brokers'] = {}
        for broker_name, broker in get_service_classes().items():
            if broker.form:
                context['installed_brokers'][broker_name] = broker
        return context


class TargetDownloadDataView(ABC, PermissionRequiredMixin, View):
    permission_required = 'tom_dataproducts.add_dataproduct'

    @abstractmethod
    def generate_data_method(self, target_id):
        pass

    def get(self, request, *args, **kwargs):
        import os
        from django.http import FileResponse

        target_id: int = kwargs.get('pk', None)
        logger.info(f'Generating photometry CSV file for target with id={target_id}...')

        tmp = None
        try:
            tmp, filename = self.generate_data_method(target_id)
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating photometry CSV file for target with id={target_id}: {e}')
        finally:
            if tmp:
                os.remove(tmp.name)


class TargetDownloadPhotometryDataView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        return save_photometry_data_for_target_to_csv_file(target_id)

class TargetDownloadRadioDataView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        return save_radio_data_for_target_to_csv_file(target_id)

# overwriting table production
# class TargetTable(Table):
#     #adding a new column, which does not exist in the model, can not be sorted by
# #    image = tables.Column(empty_values=(),orderable=False)
#     comment = tables.Column(empty_values=(),orderable=False)
#     Gmag = tables.Column(empty_values=(),orderable=False)
#     dt = tables.Column(empty_values=(),orderable=False)


#     #TODO add a new field: classification, with enum, sortable, filterable
#     # so people could just select microlensing candidates or SNe
    
#     class Meta:
#         model = Target
#         template_name = "django_tables2/bootstrap-responsive.html"
#         fields = ("id","name", "ra", "dec", "dt", "Gmag", "importance", "comment")

#     def render_ra(self, record):
#         return format_html('%.6f'%record.ra)

#     def render_dec(self, record):
#         return format_html('%.6f'%record.dec)

#     def render_name(self, record):
#         """
#         This function will render over the default id column.
#         By adding <a href> HTML formatting around the id number a link will be added,
#         thus acting the same as linkify. The record stands for the entire record
#         for the row from the table data.
#         """
#         return format_html('<a href="{}">{}</a>',
#                            reverse('detail',
#                                    kwargs={'pk': record.id}), record.name)

#     def render_comment(self, record):
#         return format_html('{}', record.extra_fields.get('classification'))

#     def render_dt(self, record):
#         mag_last, mjd_last, filter_last, approxsign = last_jd.get_last(record)
#         mjd_now = Time(datetime.utcnow()).mjd

#         if (mjd_last >0):
#             return format_html('%.3f'%(mjd_now-mjd_last))
#         else:
#             return format_html('--')

#     def render_Gmag(self, record):
#         mag_last, mjd_last, filter_last,approxsign = last_jd.get_last(record)

#         if (mjd_last >0 ):
#             if (approxsign!="x"):
#                 return format_html('%.1f%s'%(mag_last, approxsign))
#             else:
#                 return format_html('%.1f (%s)'%(mag_last,filter_last))
#         else:
#             return format_html('--')

#     def render_importance(self, record):
#         return record.extra_fields.get('importance')


#overwriting the view from bhtom_base
class TargetListView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list.html'
    strict = False
    model = Target
#    table_class = TargetTable
    filterset_class = TargetFilter
    permission_required = 'bhtom_targets.view_target'
    table_pagination = False

    def get_context_data(self, *args, **kwargs):
        """
        Adds the number of targets visible, the available ``TargetList`` objects if the user is authenticated, and
        the query string to the context object.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        # hide target grouping list if user not logged in
        context['groupings'] = (TargetList.objects.all()
                                if self.request.user.is_authenticated
                                else TargetList.objects.none())
        context['query_string'] = self.request.META['QUERY_STRING']

        mjd_now = Time(datetime.utcnow()).mjd

        prioritylist = []
         #SUN's position now:
        sun_pos = get_sun(Time(datetime.utcnow()))
        
        for target in context['object_list']:
            #read dynamically from the current light curve:
            mag_last, mjd_last, filter_last = last_jd.get_last(target)

            #everytime the list is rendered, the last mag and last mjd are updated per target
            TargetExtra.objects.update_or_create(target=target,
            key='mag_last',
            defaults={'value': mag_last})

            TargetExtra.objects.update_or_create(target=target,
            key='mjd_last',
            defaults={'value': mjd_last})

            #updating sun separation
            try:
                obj_pos = SkyCoord(target.ra, target.dec, unit=u.deg)
                Sun_sep = around(sun_pos.separation(obj_pos).deg,0)
            except:
                logger.error("Coordinates outside the range in {target} for Sun position calculation!")
                obj_pos = SkyCoord(0,0,unit=u.deg)
                Sun_sep = "error"#around(sun_pos.separation(obj_pos).deg,0)

            TargetExtra.objects.update_or_create(target=target,
            key='sun_separation',
            defaults={'value': Sun_sep})

            target.sun = Sun_sep

            out_filter = ""
            if (mjd_last >0 ):
                    out_filter= filter_last
            else:
                out_filter= "null"


            target.last_mag = mag_last
            target.last_filter = out_filter

            try:
                target.dt = (mjd_now - mjd_last)
                dt = (mjd_now - mjd_last)
            except:
                dt = 10
                target.dt = -1.

            try:
                imp = float(target.extra_field.get('importance'))
                cadence = float(target.extra_field.get('cadence'))
            except:
                imp = 1
                cadence = 1

            target.cadencepriority = computePriority(dt, imp, cadence)
            prioritylist.append(target.cadencepriority)

        return context

#Table list view with light curves only
class TargetListImagesView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list_images.html'
    strict = False
    model = Target
#    table_class = TargetTable
    filterset_class = TargetFilter
    permission_required = 'bhtom_targets.view_target'
    table_pagination = False

    def get_context_data(self, *args, **kwargs):
        """
        Adds the number of targets visible, the available ``TargetList`` objects if the user is authenticated, and
        the query string to the context object.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        # hide target grouping list if user not logged in
        context['groupings'] = (TargetList.objects.all()
                                if self.request.user.is_authenticated
                                else TargetList.objects.none())
        context['query_string'] = self.request.META['QUERY_STRING']
        return context
