import base64

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView
from django_filters.views import FilterView
from guardian.shortcuts import get_objects_for_user
from django.http import FileResponse, HttpResponseRedirect, Http404
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.conf import settings

from bhtom_base.bhtom_dataproducts.filters import DataProductFilter
from bhtom_base.bhtom_dataproducts.models import DataProduct, DataProductGroup, DataProductGroup_user
from bhtom_base.bhtom_targets.models import Target
from .forms import DataProductUploadForm
from ..bhtom_calibration.models import calibration_data
from ..bhtom_observatory.models import ObservatoryMatrix
from bhtom2.bhtom_observatory.models import Observatory
from rest_framework.views import APIView

import requests
import os
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.authtoken.models import Token
from django.contrib.auth.mixins import LoginRequiredMixin

logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_dataproducts: views]')


class DataProductUploadView(LoginRequiredMixin, FormView):
    """
    View that handles manual upload of DataProducts. Requires authentication.
    """
    form_class = DataProductUploadForm

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
        data_product_files = self.request.FILES
        observatory = form.cleaned_data['observatory']
        observation_filter = form.cleaned_data['filter']
        mjd = form.cleaned_data['MJD']
        exp_time = form.cleaned_data['ExpTime']
        match_dist = form.cleaned_data['matchDist']
        dry_run = form.cleaned_data['dryRun']
        comment = form.cleaned_data['comment']
        facility = form.cleaned_data['facility']
        observer = form.cleaned_data['observer']
        group = form.cleaned_data['group']
        user = self.request.user

        if dp_type == 'fits_file' and observatory.calibration_flg is True:
            messages.error(self.request, 'Used Observatory without ObsInfo')
            return redirect(form.cleaned_data.get('referrer', '/'))

        post_data = {
            'filter': observation_filter,
            'target': target.name,
            'data_product_type': dp_type,
            'match_dist': match_dist,
            'comment': comment,
            'dry_tun': dry_run,
            'observatory': observatory,
            'mjd': mjd,
            'exp_time': exp_time,
            'group': group.group.name,
            'observer': observer,
            'facility': facility
        }
        token = Token.objects.get(user_id=user.id).key

        headers = {
            'Authorization': 'Token ' + token
        }

        # Make a POST request to upload-service with the extracted data
        response = requests.post(settings.UPLOAD_SERVICE_URL + 'upload/', data=post_data, files=data_product_files,
                                 headers=headers)

        if response.status_code == 201:
            messages.success(self.request, 'Successfully uploaded:' + str(response.content))
        else:
            messages.error(self.request, 'There was a problem uploading your file:' + str(response.content))
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

        # Set headers for the POST request to upload-service
        headers = {
            'Authorization': authorization_header,
        }

        # Make a POST request to upload-service with the extracted data
        response = requests.post(settings.UPLOAD_SERVICE_URL + 'upload/', data=post_data, files=request.FILES,
                                 headers=headers)

        return HttpResponse(response.content, status=response.status_code)


class DataProductListView(FilterView):
    """
    View that handles the list of ``DataProduct`` objects.
    """

    model = DataProduct
    template_name = 'bhtom_dataproducts/dataproduct_list.html'
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

        return context


class DataProductGroupListView(ListView):
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


class DataProductGroupDetailView(FilterView):
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
            file = self.kwargs['data']
            logger.info('Download Photometry file: %s, user: %s' % (str(file), str(self.request.user)))
            dataProduct = DataProduct.objects.get(data=file)
            assert dataProduct.photometry_file is None
        except (DataProduct.DoesNotExist, AssertionError):
            logger.error('Download Photometry error, file not exist')

            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

        try:
            address = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data/' + format(
                dataProduct.photometry_data)

            logger.debug('Photometry download address: ' + address)
            open(address, 'r')

            return FileResponse(open(address, 'rb'), as_attachment=True)

        except IOError:
            logger.error('Download Photometry error, file not exist')
            if self.request.META.get('HTTP_REFERER') is None:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class DataDetailsView(LoginRequiredMixin, DetailView):
    template_name = 'bhtom_dataproducts/dataproduct_details.html'
    model = DataProduct
    slug_field = 'data'
    slug_url_kwarg = 'data'

    def get_context_data(self, *args, **kwargs):

        try:
            context = super().get_context_data(**kwargs)
            dataProduct = context['object']
            target = Target.objects.get(id=dataProduct.target.id)
        except Exception as e:
            raise Http404

        if dataProduct.fits_data is not None or dataProduct.photometry_data is not None:
            try:
                observatoryMatrix = ObservatoryMatrix.objects.get(id=dataProduct.observatory.id)
                observatory = Observatory.objects.get(id=observatoryMatrix.observatory.id)

                context['observatory'] = observatory
                context['owner'] = observatoryMatrix.user
            except Exception as e:
                raise Http404

            try:
                calibration = calibration_data.objects.get(dataproduct=dataProduct)
                context['calibration'] = calibration

                if calibration.calibration_plot is not None:
                    try:
                        encoded_string = base64.b64encode(calibration.calibration_plot.read())
                        context['calibration_plot'] = str(encoded_string, "utf-8")
                    except IOError as e:
                        logger.error('plot error')
            except calibration_data.DoesNotExist:
                context['calibration'] = None

        context['target'] = target

        return context
