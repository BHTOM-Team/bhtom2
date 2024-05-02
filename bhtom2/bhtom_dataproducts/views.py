import base64

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
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
from django.urls import reverse

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def get_form_kwargs(self):
        kwargs = super(DataProductUploadView, self).get_form_kwargs()
        kwargs['initial'] = {'user': self.request.user}
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
        match_dist = 0.5
        dry_run = form.cleaned_data['dryRun']
        comment = form.cleaned_data['comment']
        observer = form.cleaned_data['observer']
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
            'observer': observer,
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
            messages.error(self.request, 'There was a problem uploading your file')
        return redirect(form.cleaned_data.get('referrer', '/'))

    def form_invalid(self, form):
        """
        Adds errors to Django messaging framework in the case of an invalid form and redirects to the previous page.
        """
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
            return super().get_queryset().filter(
                target__in=get_objects_for_user(self.request.user, 'bhtom_targets.view_target'),
            ).exclude(
                group__in=dataProductGroup
            ).order_by('created')
        else:
            return get_objects_for_user(self.request.user, 'bhtom_dataproducts.view_dataproduct').order_by('created')

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
            ).order_by('created')
        else:
            return get_objects_for_user(self.request.user, 'bhtom_dataproducts.view_dataproduct').order_by('created')

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
            address = settings.DATA_TARGET_PATH + format(dataProduct.photometry_data)

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

        try:
            try:
                context = {}
                data_product = DataProduct.objects.get(id=kwargs['pk'])
                context['object'] = data_product
                target = Target.objects.get(id=data_product.target.id)
                context['target'] = target
            except DataProduct.DoesNotExist:
                logger.error("DataProduct not found")
                messages.error(self.request, 'Data not found')
                raise
            except Target.DoesNotExist:
                logger.error("Target not found")
                messages.error(self.request, 'Target not found')
                raise

            if data_product.data_product_type == "fits_file":
                try:
                    ccdphot = CCDPhotJob.objects.get(job_id=data_product.id)
                except CCDPhotJob.DoesNotExist:
                    logger.error("CCDPhotJob not found: data" + str(data_product.id))
                    messages.error(self.request, 'Data not found')
                    raise

                context['fits_data'] = data_product.fits_data.split('/')[-1]
                context['ccdphot'] = ccdphot

            if data_product.photometry_data:
                context['photometry_data'] = data_product.photometry_data.split('/')[-1]

                try:
                    observatory_matrix = ObservatoryMatrix.objects.get(id=data_product.observatory.id)
                except (ObservatoryMatrix.DoesNotExist):
                    logger.error("Observatory not found")
                    messages.error(self.request, 'Observatory not found')
                    raise

                context['observatory'] = observatory_matrix.camera.observatory
                context['camera'] = observatory_matrix.camera
                context['owner'] = observatory_matrix.user.first_name + ' ' + observatory_matrix.user.last_name

                try:
                    calibration = Calibration_data.objects.get(dataproduct=data_product)
                    context['calibration'] = calibration

                    if calibration.calibration_plot:
                        try:
                            with open(settings.DATA_PLOT_PATH + calibration.calibration_plot, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read())
                                context['cpcs_plot'] = encoded_string.decode("utf-8")
                        except IOError as e:
                            logger.error('plot error: ' + str(e))
                except Calibration_data.DoesNotExist:
                    logger.debug("Calibration_data not found")
                    context['calibration'] = None

        except Exception as e:
            logger.error(str(e))
            context['error_message'] = "An error occurred while processing the data."
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

    def get_context_data(self):
        context = {}

        logger.debug("Preparing data for your view")

        if not self.request.user.is_staff:
            logger.error("The user is not an admin")
            return redirect('home')

        try:
            wsdb = WSDBConnection()

            try:
                cpcs_alerts = wsdb.run_query("SELECT * FROM cpcs_alerts")
                columns_alert = ['id', 'ivorn', 'ra', 'dec', 'url', 'published', 'comment']
                context["cpcs_alerts"] = map_data_from_cpcs(columns_alert, cpcs_alerts)
            except Exception as e:
                logger.error("Error loading data cpcs_alerts from wsdb: " + str(e))
                context["cpcs_alerts"] = []

            try:
                cpcs_archive_calib = wsdb.run_query("SELECT * FROM cpcs_archive_calibrations")
                columns_calib = ['id', 'ra', 'dec', 'observation_target_name', 'observer', 'facility', 'mjd', 'mag',
                                 'mag_err', 'exp_time',
                                 'zeropoint', 'outlier_fraction', 'scatter', 'npoints', 'created', 'filter', 'survey',
                                 'match_distance', 'processing_time',
                                 'data', 'observatory_lon', 'observatory_lat', 'observatory_filter', 'source']
                context["cpcs_archive_calib"] = map_data_from_cpcs(columns_calib, cpcs_archive_calib)

            except Exception as e:
                logger.error("Error loading data cpcs_archive_calib from wsdb: " + str(e))
                context["cpcs_archive_calib"] = []

            try:
                cpcs_catalogs = wsdb.run_query("SELECT * FROM cpcs_catalogs")
                columns_catalog = ['id', 'name', 'filters']
                context["cpcs_catalogs"] = map_data_from_cpcs(columns_catalog, cpcs_catalogs)
            except Exception as e:
                logger.error("Error loading data cpcs_catalogs from wsdb: " + str(e))
                context["cpcs_catalogs"] = []

            try:
                cpcs_followup = wsdb.run_query("SELECT * FROM cpcs_followup")
                columns_followup = ['id', 'alert_id', 'observatory_id', 'mjd_obs', 'mag', 'mag_err', 'calib_err',
                                    'catalog_id', 'filter_id',
                                    'comment', 'npoints', 'match_dist', 'isfits', 'force_filter', 'exp_time',
                                    'calib_date', 'is_archive']

                context["cpcs_followup"] = map_data_from_cpcs(columns_followup, cpcs_followup)
            except Exception as e:
                logger.error("Error loading data cpcs_followup from wsdb: " + str(e))
                context["cpcs_followup"] = []

            try:
                cpcs_observatories = wsdb.run_query("SELECT * FROM cpcs_observatories")
                columns_obs = ['id', 'name', 'lon', 'lat', 'hashtag', 'filters', 'is_admin', 'allow_upload']

                context["cpcs_observatories"] = map_data_from_cpcs(columns_obs, cpcs_observatories)
            except Exception as e:
                logger.error("Error loading data cpcs_observatories from wsdb: " + str(e))
                context["cpcs_observatories"] = []

        except Exception as e:
            logger.error("Error connecting to wsdb")
        return context
