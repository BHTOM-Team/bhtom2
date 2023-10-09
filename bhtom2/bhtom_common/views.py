import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django_guid import get_guid
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from bhtom2 import settings
from bhtom2.bhtom_calibration.models import Calibration_data
from bhtom2.kafka.producer.calibEvent import CalibCreateEventProducer
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django_tables2.views import SingleTableMixin
from bhtom_base.bhtom_dataproducts.models import DataProduct
from django.contrib import messages

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_common.views')


class DataListView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/dataProductManagement.html'
    model = DataProduct
    # table_class = TargetTable

    permission_required = 'bhtom_targets.view_target'
    table_pagination = False
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['fits_file'] = DataProduct.objects.filter(data_product_type='fits_file').order_by('-created')
        context['fits_count'] = context['fits_file'].count
        dataProduct = DataProduct.objects.filter(photometry_data__isnull=False).order_by('-created')
        context['photometry_count'] = dataProduct.count
        context['photometry_data'] = []

        for data in dataProduct:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data)
                data = {
                    'dataProduct': data,
                    'calibData': calib_data
                }
                context['photometry_data'].append(data)
            except Exception as e:
                logger.error("Error is " + str(e))
                continue

        return context


class ReloadFits(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_ids = request.POST.getlist('selected-fits')
        user = request.user
        token = Token.objects.get(user=user)
        headers = {
            'Authorization': 'Token ' + token.key,
            'correlation_id': get_guid()
        }

        for data_id in data_ids:
            post_data = {
                'dataId': data_id
            }

            try:
                requests.post(settings.UPLOAD_SERVICE_URL + 'reloadFits/', data=post_data, headers=headers)
            except Exception as e:
                logger.error("Error in connect to upload service: " + str(e))
                messages.error(self.request, 'Upload service is unavailable.')
                return redirect(reverse('bhtom_common:list'))

        messages.success(self.request, 'Send file to ccdphot')
        return redirect(reverse('bhtom_common:list'))


class ReloadPhotometry(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_ids = request.POST.getlist('selected-photometry')

        for data_id in data_ids:
            dataProduct = DataProduct.objects.get(id=data_id)
            calib = Calibration_data.objects.get(dataproduct=dataProduct)
            calib.status = "C"
            calib.status_message = ""
            calib.save()

            CalibCreateEventProducer().send_message(data_id, dataProduct.target.name, dataProduct.data.name)

        return redirect(reverse('bhtom_common:list'))
