import base64
import os

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django_filters.views import FilterView
from guardian.shortcuts import get_objects_for_user
from rest_framework.views import APIView
from django.http import HttpResponse, FileResponse, HttpResponseRedirect, Http404
import requests
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.conf import settings

from bhtom_base.bhtom_dataproducts.filters import DataProductFilter
from bhtom_base.bhtom_dataproducts.models import DataProduct, DataProductGroup, DataProductGroup_user
from bhtom_base.bhtom_targets.models import Target
from .forms import DataProductUploadForm
from ..bhtom_calibration.models import calibration_data
from ..bhtom_observatory.models import ObservatoryMatrix, Observatory

logger = BHTOMLogger(__name__, '[BHTOM2 views]')


class DataProductUploadView(LoginRequiredMixin, FormView):
    """
    View that handles manual upload of DataProducts. Requires authentication.
    """
    form_class = DataProductUploadForm

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if not settings.TARGET_PERMISSIONS_ONLY:
            if self.request.user.is_superuser:
                form.fields['groups'].queryset = Group.objects.all()
            else:
                form.fields['groups'].queryset = self.request.user.groups.all()
        return form

    def form_valid(self, form):
        """
        Runs after ``DataProductUploadForm`` is validated. Saves each ``DataProduct`` and calls ``run_data_processor``
        on each saved file. Redirects to the previous page.
        """
        # ... (remaining unchanged)

    def form_invalid(self, form):
        """
        Adds errors to Django messaging framework in the case of an invalid form and redirects to the previous page.
        """
        # ... (remaining unchanged)


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
