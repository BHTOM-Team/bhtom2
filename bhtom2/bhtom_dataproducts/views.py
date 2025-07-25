import base64
import os

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic import DeleteView
from django.views.generic.edit import FormView, CreateView
from django_filters.views import FilterView
from django_guid import get_guid
from guardian.shortcuts import get_objects_for_user
from django.http import FileResponse, HttpResponseRedirect, Http404
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.conf import settings
from bhtom_base.bhtom_dataproducts.filters import DataProductFilter
from bhtom_base.bhtom_dataproducts.models import DataProduct, DataProductGroup, DataProductGroup_user, CCDPhotJob
from bhtom_base.bhtom_targets.models import Target
from .forms import DataProductUploadForm
from ..bhtom_calibration.models import Calibration_data
from ..bhtom_observatory.models import ObservatoryMatrix, Camera
from bhtom2.bhtom_observatory.models import Observatory
from bhtom2.external_service.connectWSDB import WSDBConnection
from rest_framework.views import APIView
from django.contrib.auth.models import User

from django.urls import reverse

import requests

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.mixins import LoginRequiredMixin
from bhtom2.bhtom_dataproducts.utils import map_data_from_cpcs

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_dataproducts.views')


class DataProductUploadView(LoginRequiredMixin, FormView):
    """
    View that handles manual upload of DataProducts. Requires authentication.
    """
    form_class = DataProductUploadForm
    template_name = 'bhtom_dataproducts/partials/upload_dataproduct.html'
    MAX_FILES: int = 5

    def get(self, request, *args, **kwargs):
        # Check if the request is a GET request without any form data
        if not request.GET:
            messages.error(self.request, 'Please provide a valid form')
            return HttpResponseRedirect(reverse('bhtom_targets:list'))

        # If the request contains form data, proceed with the regular GET handler
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def get_form_kwargs(self):
        kwargs = super(DataProductUploadView, self).get_form_kwargs()
        users = User.objects.filter(is_active=True).order_by('first_name')
        kwargs['initial'] = {'user': self.request.user, 'users': users }
        return kwargs

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        return form

    def form_valid(self, form):
        target = form.cleaned_data['target']
        if not target:
            observation_record = form.cleaned_data['observation_record']
            target = observation_record.target
        else:
            observation_record = None
        dp_type = form.cleaned_data['data_product_type']
        observatory = form.cleaned_data['observatory']
        camera = form.cleaned_data['camera']
        observation_filter = form.cleaned_data['filter']
        mjd = form.cleaned_data['mjd']
        match_dist = -2
        dry_run = form.cleaned_data['dryRun']
        comment = form.cleaned_data['comment']
        observers = form.cleaned_data['observer']
        obs_usernames = [user.username for user in observers]
        # group = form.cleaned_data['group']
        group = None
        prefix = None
        user = self.request.user
        files = self.request.FILES.getlist('files')
        data_product_files = {}

        if dp_type == 'spectroscopy' or dp_type == 'photometry_csv':
            observatory_input = form.cleaned_data['observatory_input']
            observatory = observatory_input

        for index, file_obj in enumerate(files):
            # Add each file to the dictionary with a unique key
            data_product_files[f'file_{index}'] = (file_obj.name, file_obj)
        if dp_type == 'photometry':
            if len(data_product_files) > 1:
                logger.error('upload max for photometry: %s %s' % (1, str(target)))
                messages.error(self.request, f'You can upload max. 1 file at once for photometry type')
                return redirect(form.cleaned_data.get('referrer', '/'))

        if len(data_product_files) > self.MAX_FILES:
            logger.error('upload max: %s %s' % (str(self.MAX_FILES), str(target)))
            messages.error(self.request, f'You can upload max. {self.MAX_FILES} files at once')
            return redirect(form.cleaned_data.get('referrer', '/'))
        if dp_type == 'photometry' or dp_type == 'fits_file':
            try:
                camera = Camera.objects.get(id=camera.id)
                observatory = Observatory.objects.get(id=observatory.id)
                prefix = camera.prefix
            except Camera.DoesNotExist:
                messages.error(self.request, f"Camera doesn't exist")
                return redirect(form.cleaned_data.get('referrer', '/'))
            except Observatory.DoesNotExist:
                messages.error(self.request, f"Observatory doesn't exist")
                return redirect(form.cleaned_data.get('referrer', '/'))
        elif dp_type in ('spectroscopy', 'photometry_csv'):
            prefix = observatory

        if dp_type == 'fits_file' and observatory.calibration_flg is True:
            messages.error(self.request, 'Observatory can calibration only')
            return redirect(form.cleaned_data.get('referrer', '/'))

        if group is not None:
            group = group.group.name

        post_data = {
            'filter': observation_filter,
            'target': target.name,
            'data_product_type': dp_type,
            'match_dist': match_dist,
            'comment': comment,
            'dry_run': dry_run,
            'no_plot': False,
            'observatory': prefix,
            'mjd': mjd,
            'group': group,
            'observers': obs_usernames,
        }
        token = Token.objects.get(user_id=user.id).key

        headers = {
            'Authorization': 'Token ' + token,
            'Correlation-ID': get_guid()
        }
        # Make a POST request to upload-service with the extracted data
        try:
            response = requests.post(settings.UPLOAD_SERVICE_URL + '/upload/', data=post_data, files=data_product_files,
                                     headers=headers)
        except Exception as e:
            logger.error("Error in connect to upload service: " + str(e))
            messages.error(self.request, 'Service is unavailable, please retry again later.')
            return redirect(form.cleaned_data.get('referrer', '/'))

        if response.status_code == 201:
            messages.success(self.request, 'Successfully uploaded')
        else:
            messages.error(self.request, f'There was a problem uploading your file: '
                                         f'{response.json().get("detail")}')
        return redirect(form.cleaned_data.get('referrer', '/'))

    def form_invalid(self, form):
        """
        Adds errors to Django messaging framework in the case of an invalid form and redirects to the previous page.
        """
        if not form.is_bound:
            messages.error(self.request, 'Please provide a valid form: {}'.format(form.errors.as_json()))
            return redirect(form.cleaned_data.get('referrer', '/'))

        # TODO: Format error messages in a more human-readable way
        messages.error(self.request, 'There was a problem uploading your file: {}'.format(form.errors.as_json()))
        return redirect(form.cleaned_data.get('referrer', '/'))


class FitsUploadAPIView(APIView):
    def post(self, request):
        # Extract the POST data from the original request
        post_data = request.POST
        # Extract the authorization header from the original request
        authorization_header = request.headers.get('Authorization')
        files = request.FILES.getlist('files')
        files_data = {}
        for index, file_obj in enumerate(files):
            # Add each file to the dictionary with a unique key
            files_data[f'file_{index}'] = (file_obj.name, file_obj)

        # Set headers for the POST request to upload-service
        headers = {
            'Authorization': authorization_header,
            'Correlation-ID': get_guid(),
        }

        # Make a POST request to upload-service with the extracted data
        try:
            response = requests.post(settings.UPLOAD_SERVICE_URL + '/upload/', data=post_data, files=files_data,
                                     headers=headers)
        except Exception as e:
            logger.error("Error in connect to upload service: " + str(e))
            return HttpResponse("Internal error", status=500)

        return HttpResponse(response.content, status=response.status_code)


class DataProductListAllView(LoginRequiredMixin, FilterView):
    """
    View that handles the list of ``DataProduct`` objects.
    """

    model = DataProduct
    template_name = 'bhtom_dataproducts/partials/dataproduct_all_table.html'
    paginate_by = 25
    filterset_class = DataProductFilter
    strict = False

    def get_queryset(self):
        """
        Gets the set of ``DataProduct`` objects that the user has permission to view.

        :returns: Set of ``DataProduct`` objects
        :rtype: QuerySet
        """
        dataProductGroup = DataProductGroup.objects.filter(private=True)

        if settings.TARGET_PERMISSIONS_ONLY:
            queryset = super().get_queryset().filter(
                target__in=get_objects_for_user(self.request.user, 'bhtom_targets.view_target'),
            ).exclude(
                group__in=dataProductGroup
            )
        else:
            queryset = get_objects_for_user(self.request.user, 'bhtom_dataproducts.view_dataproduct')

        # Order by 'created' descending to show the newest first
        return queryset.order_by('-created')

    def get_context_data(self, *args, **kwargs):
        """
        Adds the set of ``DataProductGroup`` objects to the context dictionary.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context['product_groups'] = DataProductGroup.objects.all()
        objects = context['object_list']
        return context


class DataProductListUserView(LoginRequiredMixin, FilterView):
    """
    View that handles the list of ``DataProduct`` objects.
    """

    model = DataProduct
    template_name = 'bhtom_dataproducts/partials/dataproduct_user_table.html'
    paginate_by = 25
    filterset_class = DataProductFilter
    strict = False

    def get_queryset(self):
        """
        Gets the set of ``DataProduct`` objects that the user has permission to view.

        :returns: Set of ``DataProduct`` objects
        :rtype: QuerySet
        """

        dataProductGroup = DataProductGroup.objects.filter(private=True)

        if settings.TARGET_PERMISSIONS_ONLY:

            return super().get_queryset().filter(
                target__in=get_objects_for_user(self.request.user, 'bhtom_targets.view_target'),
                user=self.request.user
            ).exclude(
                group__in=dataProductGroup
            ).order_by('-created')
        else:
            return get_objects_for_user(self.request.user, 'bhtom_dataproducts.view_dataproduct').order_by('-created')

    def get_context_data(self, *args, **kwargs):
        """
        Adds the set of ``DataProductGroup`` objects to the context dictionary.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context['product_groups'] = DataProductGroup.objects.all()
        objects = context['object_list']
        user_list = []

        for row in objects:
            try:
                row.photometry_data = row.photometry_data.split('/')[-1]
            except:
                continue

        context['user_list'] = objects
        return context


class DataProductGroupListView(LoginRequiredMixin, ListView):
    """
    View that handles the display of all ``DataProductGroup`` objects.
    """
    model = DataProductGroup
    ordering = ['-created']

    def get_context_data(self, *args, **kwargs):
        """
        Adds the set of ``DataProductGroup`` objects to the context dictionary.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)

        user_groups = DataProductGroup_user.objects.filter(user=self.request.user, active_flg=True).order_by('created')
        context['user_group'] = [group.group for group in user_groups]
        return context


class DataProductGroupCreateView(LoginRequiredMixin, CreateView):
    """
    View that handles the creation of a new ``DataProductGroup``.
    """
    model = DataProductGroup
    success_url = reverse_lazy('bhtom_dataproducts:group-list')
    fields = ['name', 'private']

    def get_context_data(self, *args, **kwargs):
        """
        Adds the set of ``DataProductGroup`` objects to the context dictionary.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)

        user_group = DataProductGroup_user.objects.filter(user_id=self.request.user, active_flg=True)

        context['product_groups'] = DataProductGroup.objects.all()
        context['user_group'] = DataProductGroup.objects.filter(id__in=user_group)
        return context

    def form_valid(self, form):
        user = self.request.user
        name = form.cleaned_data['name']
        private = form.cleaned_data['private']
        dataGroup = DataProductGroup.objects.create(name=name, private=private)
        dataGroup.save()
        dataGroupUser = DataProductGroup_user.objects.create(owner=True, active_flg=True, user_id=user.id,
                                                             group_id=dataGroup.id)
        dataGroupUser.save()


class DataProductGroupDetailView(LoginRequiredMixin, FilterView):
    """
    View that handles the viewing of a specific ``DataProductGroup``.
    """
    model = DataProductGroup
    filterset_class = DataProductFilter
    table_pagination = False
    template_name = 'bhtom_dataproducts/dataproductgroup_detail.html'

    def get_context_data(self, *args, **kwargs):
        """
        Adds the set of ``DataProductGroup`` objects to the context dictionary.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)

        user_group = DataProductGroup_user.objects.filter(user_id=self.request.user, active_flg=True)

        context['product_groups'] = DataProductGroup.objects.all()
        context['user_group'] = DataProductGroup.objects.filter(id__in=user_group)
        return context


class photometry_download(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            file = self.kwargs['id']
            logger.info('Download Photometry file: %s, user: %s' % (str(file), str(self.request.user)))
            dataProduct = DataProduct.objects.get(id=file)
            assert dataProduct.photometry_data is not None

        except (DataProduct.DoesNotExist, AssertionError):
            logger.error('Download Photometry error, file not exist')
            messages.error(self.request, 'File not found')
            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

        try:
            address = settings.DATA_MEDIA_PATH + format(dataProduct.photometry_data)

            logger.debug('Photometry download address: ' + address)
            open(address, 'r')

            return FileResponse(open(address, 'rb'), as_attachment=True)

        except IOError:
            logger.error('Download Photometry error, file not exist')
            messages.error(self.request, 'File not found')
            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class DataDetailsView(DetailView):
    template_name = 'bhtom_dataproducts/dataproduct_details.html'
    model = DataProduct

    def get_context_data(self, **kwargs):
        logger.debug("Start preparation data details")
        error_message = "An error occurred while processing the data."
        try:
            try:
                context = {}
                data_product = DataProduct.objects.get(id=kwargs['pk'])
                context['object'] = data_product
                target = Target.objects.get(id=data_product.target.id)
                context['target'] = target
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not found")
                error_message = 'Data not found'
                raise
            except Target.DoesNotExist:
                logger.error("Target not found")
                error_message = 'Target not found'
                raise

            if data_product.data_product_type == "fits_file":
                try:
                    ccdphot = CCDPhotJob.objects.get(job_id=data_product.id)

                except CCDPhotJob.DoesNotExist:
                    logger.error("CCDPhotJob not found: data" + str(data_product.id))
                    error_message = 'Data not found'
                    raise

                if data_product.data_product_type == 'fits_file':
                    context['fits_data'] = data_product.data.name.split('/')[-1]

                context['ccdphot'] = ccdphot
                context['fits_webp_url'] = data_product.fits_webp.url if data_product.fits_webp else None
            
            observers = data_product.observers
            observers_users = User.objects.filter(id__in=observers)
            observers_names = [f"{user.first_name} {user.last_name}" for user in observers_users]
            observers_string = ', '.join(observers_names)
            context['observers'] =   observers_string
            
            if data_product.photometry_data:
                context['photometry_data'] = data_product.photometry_data.split('/')[-1]

                try:
                    observatory_matrix = ObservatoryMatrix.objects.get(id=data_product.observatory.id)
                except ObservatoryMatrix.DoesNotExist:
                    logger.error("Observatory not found")
                    error_message = 'Observatory not found'
                    raise

                context['observatory'] = observatory_matrix.camera.observatory
                context['camera'] = observatory_matrix.camera
                context['owner'] = observatory_matrix.user.first_name + ' ' + observatory_matrix.user.last_name

                try:
                    calibration = Calibration_data.objects.get(dataproduct=data_product)
                    context['calibration'] = calibration
                    if calibration.calibration_log is not None and calibration.calibration_log != '':
                        context['cpcs_log'] = calibration.calibration_log.split('/')[-1]
                    else:
                        context['cpcs_log'] = None

                    if calibration.calibration_plot:
                        try:
                            with open(settings.DATA_PLOTS_PATH + calibration.calibration_plot, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read())
                                context['cpcs_plot'] = encoded_string.decode("utf-8")
                        except IOError as e:
                            logger.error('plot error: ' + str(e))

                except Calibration_data.DoesNotExist:
                    logger.debug("Calibration_data not found")
                    context['calibration'] = None

        except Exception as e:
            logger.error(str(e))
            context['error_message'] = error_message
            return context

        return context

    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
            if 'error_message' in context:
                messages.error(request, context['error_message'])
                return HttpResponseRedirect(reverse('bhtom_dataproducts:list_all'))
        except Exception as e:
            logger.error("Error in DataDetailsView: " + str(e))
            return HttpResponseRedirect(reverse('bhtom_dataproducts:list_all'))

        return self.render_to_response(context)


class CpcsArchiveData(LoginRequiredMixin, View):
    template_name = 'bhtom_dataproducts/cpcs_archiwum_data.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect('home')

        # Handle separate filters for each table
        cpcs_alerts_filters = {
            'ivorn': request.POST.get('ivorn', ''),
            'ra': request.POST.get('ra', ''),
            'dec': request.POST.get('dec', ''),
            'radius': request.POST.get('radius', ''),
        }

        cpcs_followup_filters = {
            'alert': request.POST.get('alert', ''),
            'observatory': request.POST.get('observatory', ''),
            'catalog': request.POST.get('catalog', ''),
            'filter': request.POST.get('filter', ''),
            'data_from': request.POST.get('data_from', ''),
            'data_to': request.POST.get('data_to', ''),
        }

        cpcs_observatories_filters = {
            'observatory': request.POST.get('name', ''),
            'lon': request.POST.get('lon', ''),
            'lat': request.POST.get('lat', ''),
        }

        context = self.get_context_data(
            cpcs_alerts_filters=cpcs_alerts_filters,
            cpcs_followup_filters=cpcs_followup_filters,
            cpcs_observatories_filters=cpcs_observatories_filters,
        )
        return render(request, self.template_name, context)

    def get_context_data(self, cpcs_alerts_filters=None, cpcs_followup_filters=None, cpcs_observatories_filters=None):
        context = {}

        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return context

        # Define API endpoints with filter parameters if provided
        endpoints = {
            "cpcs_alerts": (settings.CPCS_URL + '/archive/getAlerts/', cpcs_alerts_filters),
            "cpcs_followup": (settings.CPCS_URL + '/archive/getFollowup/', cpcs_followup_filters),
            "cpcs_observatories": (settings.CPCS_URL + '/archive/getObservatories/', cpcs_observatories_filters),
        }

        try:
            # Fetch data from each endpoint
            for key, (url, params) in endpoints.items():
                try:
                    response = requests.post(url, data=params)
                    response.raise_for_status()  # Raise HTTPError for bad responses
                    context[key] = response.json()
                except requests.RequestException as e:
                    logger.error(f"Error loading data from {url}: {e}")
                    context[key] = []

        except Exception as e:
            logger.error("Error during data retrieval")
            logger.error(str(e))

        # Add filters to context with default empty string if not provided
        context['cpcs_alerts_filters'] = cpcs_alerts_filters or {
            'ivorn': '',
            'ra': '',
            'dec': '',
            'radius': '',
        }
        context['cpcs_followup_filters'] = cpcs_followup_filters or {
            'alert': '',
            'observatory': '',
            'catalog': '',
            'filter': '',
            'data_from': '',
            'data_to': '',
        }
        context['cpcs_observatories_filters'] = cpcs_observatories_filters or {
            'name': '',
            'lon': '',
            'lat': '',
        }

        return context
    
class download_archive_photometry(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            followup_id = self.kwargs['id']
            base_path = settings.DATA_ARCHIVE_PATH
            file_path =  os.path.join(base_path, 'export', 'data', '%08d.dat' % followup_id)

            logger.info('Download Photometry Archive file: %s, user: %s' % (str(file_path), str(self.request.user)))
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
        except Exception as e:
            logger.info('Error while downloading file: %s, error: %s' % (str(file_path), str(e)))
            messages.error(self.request, 'File not found')
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class CalibrationLogDownload(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            data_id = self.kwargs['id']
            logger.info('Download Calibration log: %s, user: %s' % (str(data_id), str(self.request.user)))
            calibration = Calibration_data.objects.get(dataproduct_id=data_id)
            assert calibration.calibration_log is not None

        except (Calibration_data.DoesNotExist, AssertionError):
            logger.error('Download Calibration log - file not exist')
            messages.error(self.request, 'File not found')
            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

        try:
            address = settings.DATA_TARGETS_PATH + format(calibration.calibration_log)
            logger.debug('Calibration log download address: ' + address)
            open(address, 'r')

            return FileResponse(open(address, 'rb'), as_attachment=True)

        except IOError:
            logger.error('Download Calibration log, file not exist')
            messages.error(self.request, 'File not found')
            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class DataProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DataProduct
    template_name = 'bhtom_dataproducts/partials/dataproduct_confirm_delete.html'
    context_object_name = 'data_product'
    success_url = reverse_lazy('bhtom_dataproducts:list_user')

    def test_func(self):
        data_product = self.get_object()
        return self.request.user == data_product.user or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        data_product = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Data product deleted successfully.')
        logger.error(f'DataProduct {data_product.id} deleted by {request.user}')
        return response


    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to delete this data product.')
        return redirect('bhtom_dataproducts:list_user')
    


class CpcsCatalogData(LoginRequiredMixin, View):
    template_name = 'bhtom_dataproducts/cpcs_catalog_data.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect('home')

        cpcs_catalogs_filter = {
            'ra': request.POST.get('ra', ''),
            'dec': request.POST.get('dec', ''),
            'radius': request.POST.get('radius', ''),
            'target': request.POST.get('target', ''),
            'facility': request.POST.get('facility', ''),
            'mjd_min': request.POST.get('mjd_min', ''),
            'mjd_max': request.POST.get('mjd_max', ''),
        }

        context = self.get_context_data(
            cpcs_catalogs_filter=cpcs_catalogs_filter,
        )

        return render(request, self.template_name, context)

    def get_context_data(self, cpcs_catalogs_filter=None):
        context = {}

        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return context

        try:
            url = settings.CPCS_URL + '/catalogs/getDataFromCatalog/'
            response = requests.post(url, data=cpcs_catalogs_filter)
            response.raise_for_status()
            context['cpcs_catalogs'] = response.json()
            
        except requests.RequestException as e:
                    logger.error(f"Error loading data from {url}: {e}")
                    context['cpcs_catalogs'] = []

        except Exception as e:
            context['cpcs_catalogs'] = []
            logger.error("Error during data retrieval")
            logger.error(str(e))

        # Add filters to context with default empty string if not provided
        context['cpcs_catalogs_filter'] = cpcs_catalogs_filter or {
            'ra': '',
            'dec': '',
            'radius': '',
            'target': '',
            'facility': '',
            'mjd_min': '',
            'mjd_max': '',
        }

        return context
    