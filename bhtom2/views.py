from abc import ABC, abstractmethod
from django.views.generic import View
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
from bhtom_base.bhtom_targets.models import Target, TargetList, TargetName


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

## overwriting table production
class TargetTable(Table):
    #adding a new column, which does not exist in the model, can not be sorted by
#    image = tables.Column(empty_values=(),orderable=False)
    comment = tables.Column(empty_values=(),orderable=True)

    #TODO add a new field: classification, with enum, sortable, filterable
    # so people could just select microlensing candidates or SNe
    
    class Meta:
        model = Target
        template_name = "django_tables2/bootstrap-responsive.html"
        fields = ("id","name", "ra", "dec", "comment")

    def render_ra(self, record):
        return format_html('%.6f'%record.ra)

    def render_dec(self, record):
        return format_html('%.6f'%record.dec)

    def render_name(self, record):
        """
        This function will render over the default id column.
        By adding <a href> HTML formatting around the id number a link will be added,
        thus acting the same as linkify. The record stands for the entire record
        for the row from the table data.
        """
        return format_html('<a href="{}">{}</a>',
                           reverse('detail',
                                   kwargs={'pk': record.id}), record.name)

    def render_comment(self, record):
        return format_html('{}', record.extra_fields.get('classification'))

#overwriting the view from bhtom_base
class TargetListView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list.html'
    strict = False
    model = Target
    table_class = TargetTable
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

#Table list view with light curves only

class TargetListImagesView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list_images.html'
    strict = False
    model = Target
    table_class = TargetTable
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
