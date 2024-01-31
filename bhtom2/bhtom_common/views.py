import os
from datetime import timedelta, datetime
from django.db import transaction
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils import timezone
from django_guid import get_guid
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, FormView

from bhtom2 import settings
from bhtom2.bhtom_calibration.models import Calibration_data
from bhtom2.bhtom_common.forms import UpdateFitsForm
from bhtom2.kafka.producer.calibEvent import CalibCreateEventProducer
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django_tables2.views import SingleTableMixin
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, CCDPhotJob
from django.contrib import messages

from rest_framework import views
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from bhtom2.bhtom_observatory.rest.serializers import DataProductSerializer


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
            .exclude(status='S')\
            .exclude(fits_data__isnull=True) \
            .exclude(fits_data='') \
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

        if 'update' in request.POST:
            return HttpResponseRedirect(reverse('bhtom_common:update_fits') + f'?data={",".join(data_ids)}')

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'Correlation-ID': get_guid()
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
                requests.post(settings.UPLOAD_SERVICE_URL + '/reloadFits/', data=post_data, headers=headers)
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
        calibration_copy, reducedDatum_copy= None, None
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
                'Correlation-ID': get_guid()
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
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not Exist, data: " + str(data_id))
                messages.error(self.request, 'DataProduct not Exist.')
                continue

            try:
                calib_deleted = False
                reducedDatum_deleted = False
                with transaction.atomic():
                    try:
                        calib = Calibration_data.objects.get(dataproduct=dataProduct)
                        calib.delete()
                        calib_deleted = True
                    except Calibration_data.DoesNotExist:
                        calib_deleted = True  
                    except Exception as e:
                        logger.error("Error in delete Calibration_data: " + str(e))
                        messages.error(self.request, 'Error in delete Calibration_data.')

                    try:
                        reducedDatum = ReducedDatum.objects.get(data_product=dataProduct)
                        reducedDatum.delete()
                        reducedDatum_deleted = True
                    except ReducedDatum.DoesNotExist:
                        reducedDatum_deleted = True 
                    except Exception as e:
                        logger.error("Error in delete ReducedDatum: " + str(e))
                        messages.error(self.request, 'Error in delete ReducedDatum.')

                    if not calib_deleted or not reducedDatum_deleted:
                        raise Exception("Rollback")

            except Exception as rollback_exception:
                logger.error("Rollback: " + str(rollback_exception))
                messages.error(self.request, 'Rollback: Unable to delete data.')

            if calib_deleted and reducedDatum_deleted:
                try:
                    logger.info("DeletePointAndRestartProcess for dataProduct_id: " + str(data_id))
                    dataProduct.save()
                    requests.post(settings.UPLOAD_SERVICE_URL + '/reloadFits/', data=post_data, headers=headers)
                    success = True
                    
                except Exception as e:
                    logger.error("Error in connect to upload service: " + str(e))
                    messages.error(self.request, 'Error in connect to upload service.')
                    return redirect(reverse('bhtom_common:list'))
                
        if success:
            messages.success(self.request, 'Send file to ccdphot')
            
        return redirect(reverse('bhtom_common:list'))


class UpdateFits(LoginRequiredMixin, FormView):
    model = DataProduct
    form_class = UpdateFitsForm
    template_name = 'bhtom_common/fits_update.html'
    success_url = reverse_lazy('bhtom_common:list')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        fitsId = self.request.GET.get('data', '')
        context['fitsId'] = fitsId
        fits = DataProduct.objects.filter(id__in=fitsId.split(','))
        context['fitsName'] = [fit.get_file_name() for fit in fits]
        return context

    def form_valid(self, form):
        logger.info("Start update Fits by Admin")

        fitsId = self.request.GET.get('data', '').split(',')
        delete_fits = form.cleaned_data['delete_fits']
        status = form.cleaned_data['status']
        status_message = form.cleaned_data['status_message']

        dataProducts = DataProduct.objects.filter(id__in=fitsId)

        for data in dataProducts:
            if delete_fits:
                try:
                    base_path = settings.DATA_FILE_PATH
                    url_result = base_path + str(data.fits_data)
                    os.remove(url_result)
                    data.fits_data = ''
                    logger.info("Delete fits from disk: " + str(data.data))
                except Exception as e:
                    logger.error("Error in delete fits: " + str(e))
                    continue
            if status_message:
                ccdphot = CCDPhotJob.objects.get(dataProduct=data)
                ccdphot.status = status
                ccdphot.status_message = status_message
                logger.info("Set status message: " + str(data.data))
                ccdphot.save()

            data.status = status
            data.save()

        messages.success(self.request,
                         'successfully created, observatory requires administrator approval')
        return redirect(self.get_success_url())


class GetDataProductApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = DataProductSerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data_product_type': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_STRING),
                'fits_data': openapi.Schema(type=openapi.TYPE_STRING),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            },
            required=[]
        ),
        manual_parameters=[
            openapi.Parameter(
            name='Authorization',
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            required=True,
            description='Token <Your Token>'
        ),
    ],
    )
    def post(self, request):
        query = Q()

        data_product_type = self.request.data.get('data_product_type', None)
        status = self.request.data.get('status', None)
        fits_data = self.request.data.get('fits_data', None)
        created_start = self.request.data.get('created_start', None)
        created_end = self.request.data.get('created_end', None)

        if data_product_type is not None:
            query &= Q(data_product_type=data_product_type)
        if status is not None:
            query &= Q(status=status)
        if fits_data is not None:
            query &= Q(fits_data=fits_data)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = DataProduct.objects.filter(query).order_by('created')
        serialized_queryset = self.serializer_class(queryset,many=True).data
        return Response(serialized_queryset, status=200)
