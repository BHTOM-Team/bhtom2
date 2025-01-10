import os
from datetime import timedelta, datetime
from django.db import transaction
import requests
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.utils import timezone
from django_guid import get_guid
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, FormView
from django_comments.models import Comment
from settings import settings
from bhtom_base.bhtom_targets.models import Target
from bhtom2.bhtom_calibration.models import Calibration_data
from bhtom2.bhtom_common.forms import UpdateFitsForm
from bhtom2.kafka.producer.calibEvent import CalibCreateEventProducer
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.api_pagination import StandardResultsSetPagination
from django_tables2.views import SingleTableMixin
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, CCDPhotJob
from django.contrib import messages
import json
from rest_framework import status
from rest_framework import views
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from bhtom2.bhtom_common.serializers import DataProductSerializer,CommentSerializer,ReducedDataSerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.exceptions import PermissionDenied


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

        context['fits_file'] = CCDPhotJob.objects \
            .exclude(status='F') \
            .exclude(status='D') \
            .exclude(dataProduct__status='S') \
            .exclude(dataProduct__fits_data__isnull=True) \
            .exclude(dataProduct__fits_data='') \
            .order_by('-job_id')

        context['photometry_data'] = []
        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)

        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        context['delay_fits'] = settings.DELETE_FITS_FILE_DAY
        
        ccdphot = CCDPhotJob.objects.filter((Q(status='F') | Q(status='D')) &
                                            ~Q(dataProduct__fits_data__isnull=True) &
                                            ~Q(dataProduct__fits_data='') &
                                            Q(dataProduct__created__gte=days_delay_error)).order_by('-job_id')

        for data in ccdphot:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data.dataProduct)
            except Calibration_data.DoesNotExist:
                data = {
                    'dataProduct': data.dataProduct,
                    'calibData': None
                }
                context['photometry_data'].append(data)
                continue

            if calib_data.status == 'S':
                continue

            try:
                data = {
                    'dataProduct': data.dataProduct,
                    'calibData': calib_data
                }
                context['photometry_data'].append(data)
            except Exception as e:
                logger.error("Error in Calibration_data: " + str(e))
                continue

        return context
    


class DataListInCalibView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-in-calibration.html'
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

        context['photometry_data'] = []
        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)

        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        context['delay_fits'] = settings.DELETE_FITS_FILE_DAY
        
        ccdphot = CCDPhotJob.objects.filter((Q(status='F') | Q(status='D')) & Q(dataProduct__status='R')&
                                            ~Q(dataProduct__fits_data__isnull=True) &
                                            ~Q(dataProduct__fits_data='') &
                                            Q(dataProduct__created__gte=days_delay_error)).order_by('-job_id')

        for data in ccdphot:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data.dataProduct)
            except Calibration_data.DoesNotExist:
                continue

            if calib_data.status == 'P' or calib_data.status == 'C':
                try:
                    data = {
                        'dataProduct': data.dataProduct,
                        'calibData': calib_data
                    }
                    context['photometry_data'].append(data)
                except Exception as e:
                    logger.error("Error in Calibration_data: " + str(e))
                    continue

        return context


class DataListCPCSErrorView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-cpcs-error.html'
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

        context['photometry_data'] = []
        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)

        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        context['delay_fits'] = settings.DELETE_FITS_FILE_DAY
        
        ccdphot = CCDPhotJob.objects.filter((Q(status='F') | Q(status='D')) &
                                            ~Q(dataProduct__fits_data__isnull=True) &
                                            ~Q(dataProduct__fits_data='') &
                                            Q(dataProduct__created__gte=days_delay_error)).order_by('-job_id')

        for data in ccdphot:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data.dataProduct)
            except Calibration_data.DoesNotExist:
                continue

            if calib_data.status == 'E':
                try:
                    data = {
                        'dataProduct': data.dataProduct,
                        'calibData': calib_data
                    }
                    context['photometry_data'].append(data)
                except Exception as e:
                    logger.error("Error in Calibration_data: " + str(e))
                    continue

        return context

class DataListCPCSLimitView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-cpcs-limit.html'
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

        context['photometry_data'] = []
        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)

        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        context['delay_fits'] = settings.DELETE_FITS_FILE_DAY
        
        ccdphot = CCDPhotJob.objects.filter((Q(status='F') | Q(status='D')) &
                                            ~Q(dataProduct__fits_data__isnull=True) &
                                            ~Q(dataProduct__fits_data='') &
                                            Q(dataProduct__created__gte=days_delay_error)).order_by('-job_id')

        for data in ccdphot:
            try:
                calib_data = Calibration_data.objects.get(dataproduct=data.dataProduct)
            except Calibration_data.DoesNotExist:
                continue

            if calib_data.status == 'S' and (calib_data.mag_error == 1 or calib_data.mag_error == -1):
                try:
                    data = {
                        'dataProduct': data.dataProduct,
                        'calibData': calib_data
                    }
                    context['photometry_data'].append(data)
                except Exception as e:
                    logger.error("Error in Calibration_data: " + str(e))
                    continue

        return context

class DataListCCDPHOTErrorView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-ccdphot-error.html'
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

        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)
        context['fits_file'] = CCDPhotJob.objects \
            .exclude(status='F') \
            .exclude(status='D') \
            .exclude(dataProduct__status='S') \
            .exclude(dataProduct__fits_data__isnull=True) \
            .exclude(dataProduct__fits_data='') \
            .filter(dataProduct__created__gte=days_delay_error, dataProduct__status='E') \
            .order_by('-job_id')


        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        return context


class DataListInProgressView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-in-progress.html'
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
        days_delay_error = timezone.now() - timedelta(days=settings.DELETE_FITS_ERROR_FILE_DAY)

        context['fits_file'] = CCDPhotJob.objects.filter(Q(dataProduct__status='P') 
                                                        & Q(dataProduct__created__gte=days_delay_error)
                                                        & ~Q(dataProduct__fits_data__isnull=True)
                                                        & ~Q(dataProduct__fits_data='')).order_by('-job_id')

        context['delay_fits_error'] = settings.DELETE_FITS_ERROR_FILE_DAY
        return context




class DataListCompletedView(SingleTableMixin, LoginRequiredMixin, ListView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_common/data_product_management-completed.html'
    model = DataProduct
    # table_class = TargetTable

    permission_required = 'bhtom_targets.view_target'
    table_pagination = False
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        logger.debug("Prepare DataListCompletedView for Admin")

        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        days_delay = timezone.now() - timedelta(days=settings.DELETE_FITS_FILE_DAY)

        context['fits_s_file'] = DataProduct.objects.filter(Q(created__gte=days_delay) &
                                                            Q(data_product_type='fits_file') &
                                                            Q(fits_data__isnull=False) &
                                                            Q(status='S'))

        return context

class ReloadFits(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        data_ids_str = request.POST.get('selected-fits-ids', '')
        next_url = request.GET.get('next', reverse('bhtom_common:list_ccdphot_error'))  # Fallback to default URL
        if data_ids_str != '':
            data_ids = data_ids_str.split(',')
        else:
            messages.error(self.request, 'Data is empty!')
            return redirect(next_url)

        user = request.user
        logger.debug("Start ReloadFits, data: %s, user: %s" % (str(data_ids), str(request.user)))

        if not request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))


        if 'update' in request.POST:
            return HttpResponseRedirect(reverse('bhtom_common:update_fits') + f'?data={",".join(data_ids)}&url={next_url}')

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'Correlation-ID': get_guid()
            }
        except Token.DoesNotExist:
            logger.error("Token does not exist")
            messages.error(self.request, "Token does not exist")
            return redirect(next_url)

        for data_id in data_ids:
            post_data = {
                'dataId': data_id
            }
            try:
                if 'test_reload' in request.POST:
                    response = requests.post(settings.UPLOAD_SERVICE_URL + '/testReloadFits/', data=post_data, headers=headers)
                else:
                    response = requests.post(settings.UPLOAD_SERVICE_URL + '/reloadFits/', data=post_data, headers=headers)
                if response.status_code != 201:
                    messages.error(self.request, 'Error while sending file to the ccdphot')
                    return redirect(next_url)

            except Exception as e:
                logger.error("Error in connect to upload service: " + str(e))
                messages.error(self.request, 'Error in connect to upload service.')
                return redirect(next_url)

        messages.success(self.request, 'Send file to ccdphot')
        return redirect(next_url)



class UpdateFits(LoginRequiredMixin, FormView):
    model = DataProduct
    form_class = UpdateFitsForm
    template_name = 'bhtom_common/fits_update.html'
    success_url = reverse_lazy('bhtom_common:list_ccdphot_error')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        fitsId = self.request.GET.get('data', '')
        next_url = self.request.GET.get('url', reverse('bhtom_common:list_ccdphot_error'))  # Fallback to default URL
        context['fitsId'] = fitsId
        context['next_url'] = next_url
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
                    base_path = settings.DATA_MEDIA_PATH
                    url_result = base_path + str(data.fits_data)
                    os.remove(url_result)
                    data.fits_data = ''
                    logger.info("Delete fits from disk: " + str(data.data))
                except Exception as e:
                    logger.warning("Error in delete fits: " + str(e))
                    messages.warning(self.request, str(e))
                    continue

            if status_message:
                ccdphot = CCDPhotJob.objects.get(dataProduct=data)
                ccdphot.status = status
                ccdphot.status_message = status_message
                logger.info("Set status message: " + str(data.data))
                ccdphot.save()

            data.status = status
            data.save()

        messages.success(self.request,'Files updated successfully')
        next_url = self.request.GET.get('url', reverse('bhtom_common:list_ccdphot_error'))  # Fallback to default URL
        return redirect(next_url)


class ReloadPhotometry(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_ids_str = request.POST.get('selected-photometry-ids', '')
        next_url = request.GET.get('next', reverse('bhtom_common:list_ccdphot_error'))  # Fallback to default URL
        if data_ids_str != '':
            data_ids = data_ids_str.split(',')
        else:
            messages.error(self.request, 'Data is empty!')
            return redirect(next_url)


        success = False

        logger.debug("Start ReloadPhotometry, data: %s, user: %s" % (str(data_ids), str(request.user)))

        if not request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        if len(data_ids) == 0:
            messages.error(self.request, 'Data is empty!')
            return redirect(next_url)

        if 'update-photometry' in request.POST:
            action = 'update-photometry'
        elif 'test-reload-photometry' in request.POST:
            action = 'test-reload-photometry'
        else:
            action = None


        if action:
            return HttpResponseRedirect(reverse('bhtom_common:reload_photometry_fits') + f'?action={action}&url={next_url}&data={",".join(data_ids)}')

        for data_id in data_ids:
            try:
                dataProduct = DataProduct.objects.get(id=data_id)
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not Exist, data: " + str(data_id))
                messages.error(self.request, 'DataProduct not Exist')
                continue
            try:
                reduced_datum = ReducedDatum.objects.get(data_product=dataProduct)
                reduced_datum.delete()
            except ReducedDatum.DoesNotExist:
                logger.info(f"ReducedDatum does not exist for data_product: {dataProduct}")
            
            try:
                calib = Calibration_data.objects.get(dataproduct=dataProduct)
                calib.status = "C"
                calib.status_message = "Send to calibration"
                calib.save()
            except Calibration_data.DoesNotExist:
                logger.error("Calibration_data not exist, data: %s, type: %s"
                             % (str(data_id), str(dataProduct.data_product_type)))

                if dataProduct.data_product_type == 'fits_file':
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
        return redirect(next_url)


class ReloadPhotometryWithFits(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        fitsId = self.request.GET.get('data', '').split(',')

        user = request.user
        next_url = self.request.GET.get('url', reverse('bhtom_common:list_ccdphot_error'))  # Fallback to default URL
        logger.debug("Start ReloadFits, data: %s, user: %s" % (str(fitsId), str(request.user)))
        if not request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'Correlation-ID': get_guid()
            }
        except Token.DoesNotExist:
            logger.error("Token does not exist")
            messages.error(self.request, "Token does not exist")
            return redirect(next_url)

        try:
            dataProducts = DataProduct.objects.filter(id__in=fitsId)
        except DataProduct.DoesNotExist:
            logger.error("DataProduct not Exist")
            messages.error(self.request, 'DataProduct not Exist')
            return redirect(next_url)

        for data in dataProducts:

            post_data = {
                'dataId': data.id
            }

            try:
                action = self.request.GET.get('action', '')
                if action == 'test-reload-photometry':
                    response = requests.post(settings.UPLOAD_SERVICE_URL + '/testReloadFits/', data=post_data, headers=headers)
                else:
                    response = requests.post(settings.UPLOAD_SERVICE_URL + '/reloadFits/', data=post_data, headers=headers)
                if response.status_code != 201:
                    messages.error(self.request, 'Error while sending file to the ccdphot, id:' + str(data.id))
                else:
                    messages.success(self.request, 'Send file to ccdphot')
            except Exception as e:
                logger.error("Error in connect to upload service: " + str(e))
                messages.error(self.request, 'Error in connect to upload service.')
                return redirect(next_url)

        return redirect(next_url)
    
    


class DeletePointAndRestartProcess(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        data_ids_str = request.POST.get('selected-s-fits-ids', '')
        if data_ids_str != '':
            data_ids = data_ids_str.split(',')
        else:
            messages.error(self.request, 'Data is empty!')
            return redirect(reverse('bhtom_common:list_ccdphot_error'))

        user = request.user
        success = False

        logger.debug("Start DeletePointAndRestartProcess, data: %s, user: %s" % (str(data_ids), str(user)))

        if not user.is_staff:
            logger.error("The user is not an admin")
            return redirect(reverse('home'))

        if len(data_ids) == 0:
            messages.error(self.request, 'Data is empty!')
            return redirect(reverse('bhtom_common:list_ccdphot_error'))

        try:
            token = Token.objects.get(user=user)
            headers = {
                'Authorization': 'Token ' + token.key,
                'Correlation-ID': get_guid()
            }
        except Token.DoesNotExist:
            logger.error("Token not exist")
            messages.error(self.request, "Token not exist")
            return redirect(reverse('bhtom_common:list_ccdphot_error'))

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

            calib_deleted = True
            reducedDatum_deleted = True

            try:
                with transaction.atomic():
                    try:
                        calib = Calibration_data.objects.get(dataproduct=dataProduct)
                        calib.delete()
                        calib_deleted = True
                    except Calibration_data.DoesNotExist:
                        pass
                    except Exception as e:
                        calib_deleted = False
                        logger.error("Error in delete Calibration_data: " + str(e))
                        messages.error(self.request, 'Error in delete Calibration_data.')

                    try:
                        reducedDatum = ReducedDatum.objects.get(data_product=dataProduct)
                        reducedDatum.delete()
                    except ReducedDatum.DoesNotExist:
                        pass
                    except Exception as e:
                        reducedDatum_deleted = False
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
                    return redirect(reverse('bhtom_common:list_ccdphot_error'))

        if success:
            messages.success(self.request, 'Send file to ccdphot')

        return redirect(reverse('bhtom_common:list_ccdphot_error'))

class GetDataProductApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = DataProductSerializer
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'data_product_type': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_STRING),
                'fits_data': openapi.Schema(type=openapi.TYPE_STRING),
                'photometry_data': openapi.Schema(type=openapi.TYPE_STRING),
                'camera': openapi.Schema(type=openapi.TYPE_STRING),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'mjd': openapi.Schema(type=openapi.TYPE_STRING),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER),
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
            openapi.Parameter(
                name='page',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Page number for pagination'
            ),
        ],
    )
    def post(self, request):
        query = Q()
        id = request.data.get('id', None)
        data_product_type = request.data.get('data_product_type', None)
        dp_status = request.data.get('status', None)
        fits_data = request.data.get('fits_data', None)
        photometry_data = request.data.get('photometry_data', None)
        camera = request.data.get('camera', None)
        created_start = request.data.get('created_start', None)
        created_end = request.data.get('created_end', None)
        mjd = request.data.get('mjd', None)
        page = request.data.get('page', 1)

        if id is not None:
            query &= Q(id=id)
        if photometry_data is not None:
            query &= Q(data__contains=photometry_data)
        if data_product_type is not None:
            query &= Q(data_product_type=data_product_type)
        if dp_status is not None:
            query &= Q(status=dp_status)
        if camera is not None:
            query &= Q(observatory__camera__prefix=camera)
        if fits_data is not None:
            query &= Q(fits_data__contains=fits_data)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)
        if mjd is not None:
            query &= (Q(spectroscopydatum__mjd=mjd) | Q(calibration_data__mjd=mjd))

        queryset = DataProduct.objects.filter(query).distinct().order_by('-created')

        page_size = 500 if not request.user.is_staff else 1000
        paginator = Paginator(queryset, page_size)

        try:
            data_products = paginator.page(page)
        except PageNotAnInteger:
            data_products = paginator.page(1)
        except EmptyPage:
            data_products = paginator.page(paginator.num_pages)

        # Serialize the data
        serialized_queryset = self.serializer_class(data_products, many=True).data

        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': data_products.number,
            'data': serialized_queryset
        }, status= status.HTTP_200_OK)




class GetReducedDataApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReducedDataSerializer
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'target_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'target_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=[]  # Optional fields
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
            openapi.Parameter(
                name='page',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Page number for pagination'
            ),
        ],
    )
    def post(self, request):
        target_id = request.data.get('target_id')
        target_name = request.data.get('target_name')
        page_number = request.data.get('page', 1)

        if bool(target_id) == bool(target_name): 
            return Response(
                {"error": "Provide either 'target_id' or 'target_name', but not both."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if target_name:
            try:
                target_id = Target.objects.get(name=target_name).id
            except Target.DoesNotExist:
                return Response({"error": "Target does not exist."}, status=status.HTTP_404_NOT_FOUND)

        queryset = ReducedDatum.objects.filter(target_id=target_id).distinct()

        page_size = 1000 if request.user.is_staff else 500
        paginator = Paginator(queryset, page_size)

        try:
            paginated_data = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            return Response({"error": "Invalid page number."}, status=status.HTTP_400_BAD_REQUEST)

        serialized_data = self.serializer_class(paginated_data, many=True).data

        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_data.number,
            'data': serialized_data
        }, status=status.HTTP_200_OK)


class NewsletterView(LoginRequiredMixin, TemplateView):
    template_name = 'bhtom_common/newsletter.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            file_path = settings.DATA_CACHE_PATH + '/newsletter/newsletter_data.json'
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['start_date'] = datetime.fromisoformat(data['start_date'])
                data['end_date'] = datetime.fromisoformat(data['end_date'])
        except FileNotFoundError:
            logger.error("Newsletter file not found")
            data = {}
        except Exception as e:
            logger.error("Error with newsletter " + str(e))
            data = {}

        context['data'] = data 
        return context

class CommentAPIView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'target': openapi.Schema(type=openapi.TYPE_STRING, description='Target name'),
                'targetid': openapi.Schema(type=openapi.TYPE_INTEGER, description='Target ID'),
                'user': openapi.Schema(type=openapi.TYPE_STRING, description='Username who made the comment'),
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Text to search in comments'),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Start date for comment creation (YYYY-MM-DD)'),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='End date for comment creation (YYYY-MM-DD)'),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number for pagination'),
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
        # Extract filters from the request body
        target_name = request.data.get('target', None)
        target_id = request.data.get('targetid', None)
        user = request.data.get('user', None)
        text = request.data.get('text', None)
        created_start = request.data.get('created_start', None)
        created_end = request.data.get('created_end', None)
        page = request.data.get('page', 1)

        # Initialize the query
        query = Q()

        # Apply filters
        if target_name:
            try:
                target = Target.objects.get(name=target_name)
                query &= Q(object_pk=target.id)
            except Target.DoesNotExist:
                return Response({"error": "Target not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if target_id:
            query &= Q(object_pk=target_id)
        
        if user:
            query &= Q(user_name=user)
        
        if text:
            query &= Q(comment__icontains=text)
        
        # Apply date filtering if provided
        try:
            if created_start:
                created_start = datetime.strptime(created_start, '%Y-%m-%d').date()
                query &= Q(submit_date__date__gte=created_start)

            if created_end:
                created_end = datetime.strptime(created_end, '%Y-%m-%d').date()
                query &= Q(submit_date__date__lte=created_end)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Query filtered comments
        comments = Comment.objects.filter(query).order_by('submit_date')

        # Pagination
        paginator = Paginator(comments, self.pagination_class.max_page_size)
        try:
            paginated_comments = paginator.page(page)
        except PageNotAnInteger:
            paginated_comments = paginator.page(1)
        except EmptyPage:
            paginated_comments = paginator.page(paginator.num_pages)

        # Serialize the paginated comments
        serializer = CommentSerializer(paginated_comments, many=True)
        
        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_comments.number,
            'data': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
class DeleteReduceDatumApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'target_name': openapi.Schema(type=openapi.TYPE_STRING, description='Target name.'),
                'target_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Target ID.'),
                'mjd': openapi.Schema(type=openapi.TYPE_NUMBER, description='Modified Julian Date (precision up to 1e-6).', ),
                'mag': openapi.Schema(type=openapi.TYPE_NUMBER, description='Magnitude (precision up to 1e-3).'),
                'magerr': openapi.Schema(type=openapi.TYPE_NUMBER, description='Magnitude error (precision up to 1e-3).'),
                'filter': openapi.Schema(type=openapi.TYPE_STRING, description='Filter used (e.g., V, R, I).'),
                'observer': openapi.Schema(type=openapi.TYPE_STRING, description='Observer name.'),
                'delete_associated_data_product': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Flag to delete associated data product (default: False).')
           
            },
            required= ['mjd','mag','magerr','filter','observer',]
        ),
    )
    def delete(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")

        # Get parameters from request body
        target_name = request.data.get('target_name')
        target_id = request.data.get('target_id')
        mjd = request.data.get('mjd')
        mag = request.data.get('mag')
        magerr = request.data.get('magerr')
        filter_ = request.data.get('filter')
        observer = request.data.get('observer')
        delete_associated_data_product = request.data.get('delete_associated_data_product', False)

        if not (mjd and mag and magerr and filter_ and observer):
            return Response({"Error": "Missing required parameters."}, status=400)

        try:
            query = Q(mjd__range=(float(mjd) - 1e-6, float(mjd) + 1e-6)) & \
                    Q(value__range=(float(mag) - 1e-3, float(mag) + 1e-3)) & \
                    Q(error__range=(float(magerr) - 1e-3, float(magerr) + 1e-3)) & \
                    Q(filter=filter_) & Q(observer=observer)

            if target_name:
                query &= Q(target_id__name=target_name)
            if target_id:
                query &= Q(target_id=target_id)

            reducedatum = ReducedDatum.objects.filter(query).first()

            if not reducedatum:
                return Response({"Error": "Reduced datum not found."}, status=404)

            if delete_associated_data_product and reducedatum.data_product_id:
                dp = DataProduct.objects.get(id=reducedatum.data_product_id)
                dp.delete()

            reducedatum.delete()

            return Response({"Success": "Reduced datum deleted successfully."}, status=200)

        except Exception as e:
            return Response({"Error": f"An error occurred: {str(e)}"}, status=500)


class DeactivateReduceDatumApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='Target name.'),
                'target_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Target ID.'),
                'mjd': openapi.Schema(type=openapi.TYPE_NUMBER, description='Modified Julian Date (precision up to 1e-6).', ),
                'mag': openapi.Schema(type=openapi.TYPE_NUMBER, description='Magnitude (precision up to 1e-3).'),
                'magerr': openapi.Schema(type=openapi.TYPE_NUMBER, description='Magnitude error (precision up to 1e-3).'),
                'filter': openapi.Schema(type=openapi.TYPE_STRING, description='Filter used (e.g., V, R, I).'),
                'observer': openapi.Schema(type=openapi.TYPE_STRING, description='Observer name.'),
             
            },
            required= ['mjd','mag','magerr','filter','observer',]
        ),
    )
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")

        # Get parameters from request body
        target_name = request.data.get('target_name')
        target_id = request.data.get('target_id')
        mjd = request.data.get('mjd')
        mag = request.data.get('mag')
        magerr = request.data.get('magerr')
        filter_ = request.data.get('filter')
        observer = request.data.get('observer')

        if not (mjd and mag and magerr and filter_ and observer):
            return Response({"Error": "Missing required parameters."}, status=400)

        try:
            query = Q(mjd__range=(float(mjd) - 1e-6, float(mjd) + 1e-6)) & \
                    Q(value__range=(float(mag) - 1e-3, float(mag) + 1e-3)) & \
                    Q(error__range=(float(magerr) - 1e-3, float(magerr) + 1e-3)) & \
                    Q(filter=filter_) & Q(observer=observer)

            if target_name:
                query &= Q(target_id__name=target_name)
            if target_id:
                query &= Q(target_id=target_id)

            reducedatum = ReducedDatum.objects.filter(query).first()
            reducedatum.active_flg = False
            reducedatum.save()
            return Response({"Success": "Reduced datum deactivated successfully."}, status=200)

        except Exception as e:
            return Response({"Error": f"An error occurred: {str(e)}"}, status=500)



class DeleteDataProductApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, description='Target name.'),
            },
            required= ['id']
        ),
    )
    def delete(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")
        
        id = request.data.get('id')

        if not id:
            return Response ( {"Error": "Missing required parameter 'id'."}, status=400)

        try:
            dp = DataProduct.objects.get(id= id)
            dp.delete()
            return Response({"Success": "DataProduct deleted successfully."}, status=200)

        except Exception as e:
            return Response({"Error": f"An error occurred: {str(e)}"}, status=500)

