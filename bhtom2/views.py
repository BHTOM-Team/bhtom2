from abc import ABC, abstractmethod
from django.views.generic import View
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.reduced_data_utils import save_photometry_data_for_target_to_csv_file, save_radio_data_for_target_to_csv_file
from django_filters.views import FilterView
from django.contrib.auth.mixins import PermissionRequiredMixin
from bhtom_base.bhtom_alerts.alerts import get_service_classes
from bhtom_base.bhtom_alerts.models import BrokerQuery
from bhtom_base.bhtom_alerts.views import BrokerQueryFilter


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
