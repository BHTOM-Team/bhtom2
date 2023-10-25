from datetime import timedelta, datetime

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
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
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, CCDPhotJob
from django.contrib import messages

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_common.views')


class DataListView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management.html'
    model = DataProduct
    # table_class = TargetTable

    permission_required = 'bhtom_targets.view_target'
    table_pagination = False
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        logger.debug("Prepare DataListView for Admin")

        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        context['fits_file'] = DataProduct.objects.filter(data_product_type='fits_file') \
            .exclude(status='S') \
            .order_by('-created')

        days_delay = timezone.now() - timedelta(days=7)

        dataProduct = DataProduct.objects.filter(Q(photometry_data__isnull=False) & Q(created__gte=days_delay)) \
            .exclude(status='S') \
            .order_by('-created')

        context['fits_s_file'] = DataProduct.objects.filter(Q(created__gte=days_delay) &
                                                            Q(data_product_type='fits_file') &
                                                            Q(fits_data__isnull=False) &
                                                            Q(status='S'))

        context['photometry_data'] = []

        for data in dataProduct:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data)
            except Calibration_data.DoesNotExist:
                data = {
                    'dataProduct': data,
                    'calibData': None
                }
                context['photometry_data'].append(data)
                continue

            if calib_data.status == 'S':
                continue

            try:
                data = {
                    'dataProduct': data,
                    'calibData': calib_data
                }
                context['photometry_data'].append(data)
            except Exception as e:
                logger.error("Error in Calibration_data: " + str(e))
                continue

        return context


class ReloadFits(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_ids = request.POST.getlist('selected-fits')
        user = request.user
        logger.debug("Start ReloadFits, data: %s, user: %s" % (str(data_ids), str(request.user)))

        if not request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'correlation_id': get_guid()
            }
        except Token.DoesNotExist:
            logger.error("Token not exist")
            messages.error(self.request, "Token not exist")
            return redirect(reverse('bhtom_common:list'))

        for data_id in data_ids:
            post_data = {
                'dataId': data_id
            }

            try:
                requests.post(settings.UPLOAD_SERVICE_URL + 'reloadFits/', data=post_data, headers=headers)
            except Exception as e:
                logger.error("Error in connect to upload service: " + str(e))
                messages.error(self.request, 'Error in connect to upload service.')
                return redirect(reverse('bhtom_common:list'))

        messages.success(self.request, 'Send file to ccdphot')
        return redirect(reverse('bhtom_common:list'))


class ReloadPhotometry(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_ids = request.POST.getlist('selected-photometry')
        success = False

        logger.debug("Start ReloadPhotometry, data: %s, user: %s" % (str(data_ids), str(request.user)))

        if not request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        for data_id in data_ids:
            try:
                dataProduct = DataProduct.objects.get(id=data_id)
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not Exist, data: " + str(data_id))
                messages.error(self.request, 'DataProduct not Exist')
                continue

            try:
                calib = Calibration_data.objects.get(dataproduct=dataProduct)
                calib.status = "C"
                calib.status_message = "Send to calibration"
                calib.save()
            except Calibration_data.DoesNotExist:
                logger.error("Calibration_data not exist, data: %s, type: %s"
                             % (str(data_id), str(dataProduct.data_product_type)))

                if dataProduct.data_product_type is 'fits_file':
                    try:
                        ccdphotJob = CCDPhotJob.objects.get(dataProduct=dataProduct)

                        Calibration_data.objects.create(
                            dataproduct=dataProduct,
                            status='C',
                            status_message='Sent to Calibration',
                            created=datetime.now(),
                            mjd=ccdphotJob.fits_mjd,
                            exp_time=ccdphotJob.fits_exp,
                            ra=dataProduct.target.ra,
                            dec=dataProduct.target.dec,
                            no_plot=False
                        )
                    except CCDPhotJob.DoesNotExist:
                        logger.error("CCDPhotJob not exist")
                        messages.error(self.request, 'CCDPhotJob not exist, file:' + str(dataProduct.photometry_data))
                        continue
                else:
                    messages.error(self.request, 'Calibration data not exist, file:' + str(dataProduct.photometry_data))
                    continue

            except Exception as e:
                messages.error(self.request, 'Error in update Calibration_date')
                logger.error("Error in update Calibration_date, data: %s, error: %s" % (str(data_id), str(e)))

            try:
                CalibCreateEventProducer().send_message(data_id, dataProduct.target.name, dataProduct.data.name)
                success = True
            except Exception as e:
                logger.error("Error in send Calibration Event: " + str(e))
                messages.error(self.request, 'Error in send Calibration Event')

        if success:
            messages.success(self.request, 'Send file to calibration')
        return redirect(reverse('bhtom_common:list'))


class DeletePointAndRestartProcess(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):

        data_ids = request.POST.getlist('selected-s-fits')
        user = request.user
        success = False

        logger.debug("Start DeletePointAndRestartProcess, data: %s, user: %s" % (str(data_ids), str(user)))

        if not user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'correlation_id': get_guid()
            }
        except Token.DoesNotExist:
            logger.error("Token not exist")
            messages.error(self.request, "Token not exist")
            return redirect(reverse('bhtom_common:list'))

        for data_id in data_ids:
            post_data = {
                'dataId': data_id
            }

            try:
                dataProduct = DataProduct.objects.get(id=data_id)
                dataProduct.status = 'P'
                dataProduct.save()
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not Exist, data: " + str(data_id))
                messages.error(self.request, 'DataProduct not Exist.')
                continue

            try:
                calib = Calibration_data.objects.get(dataproduct=dataProduct)
                calib.delete()
            except Exception as e:
                logger.error("Error in delete Calibration_data: " + str(e))
                messages.error(self.request, 'Error in delete Calibration_data.')
            try:
                reducedDatum = ReducedDatum.objects.get(data_product=dataProduct)
                reducedDatum.delete()
            except Exception as e:
                logger.error("Error in delete ReducedDatum: " + str(e))
                messages.error(self.request, 'Error in delete ReducedDatum.')

            try:
                logger.info("DeletePointAndRestartProcess for dataProduct_id: " + str(data_id))
                requests.post(settings.UPLOAD_SERVICE_URL + 'reloadFits/', data=post_data, headers=headers)
                success = True
            except Exception as e:
                logger.error("Error in connect to upload service: " + str(e))
                messages.error(self.request, 'Error in connect to upload service.')
                return redirect(reverse('bhtom_common:list'))

        if success:
            messages.success(self.request, 'Send file to ccdphot')

        return redirect(reverse('bhtom_common:list'))
