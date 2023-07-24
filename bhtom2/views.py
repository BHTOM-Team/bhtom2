from abc import ABC, abstractmethod
from datetime import datetime

from astropy import units as u
from astropy.coordinates import get_sun, SkyCoord
from astropy.time import Time
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import View
from bhtom2 import settings
from bhtom2.utils.openai_utils import latex_text_target
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.views.generic.detail import DetailView
from guardian.mixins import PermissionListMixin
from numpy import around
from bhtom2.bhtom_targets.filters import TargetFilter
from bhtom2.dataproducts import last_jd
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import computePriority
from bhtom2.utils.reduced_data_utils import save_photometry_data_for_target_to_csv_file, \
    save_radio_data_for_target_to_csv_file
from bhtom_base.bhtom_alerts.alerts import get_service_classes
from bhtom_base.bhtom_alerts.models import BrokerQuery
from bhtom_base.bhtom_alerts.views import BrokerQueryFilter
from bhtom_base.bhtom_targets.models import Target, TargetExtra, TargetList
from bhtom_base.bhtom_dataproducts.models import  ReducedDatum, DataProduct
from bhtom_base.bhtom_dataproducts.exceptions import  InvalidFileFormatException
from bhtom2.bhtom_observatory.models import Observatory
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
import requests
import os
from rest_framework import  status
from rest_framework.response import Response
from django.http import HttpResponse
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_dataproducts.data_processor import DataProcessor, run_data_processor
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.authtoken.models import Token
from bhtom2.forms import DataProductUploadForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.views.generic.edit import FormView
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

        if 'pk' in kwargs:
            target_id = kwargs['pk']
        elif 'name' in kwargs:
            target_id = kwargs['name']
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


# overwriting the view from bhtom_base
class TargetListView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list.html'
    strict = False
    model = Target
    #    table_class = TargetTable
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

        context['target_count'] = context['object_list'].count

        mjd_now = Time(datetime.utcnow()).mjd

        prioritylist = []
        # SUN's position now:
        sun_pos = get_sun(Time(datetime.utcnow()))

        for target in context['object_list']:
            # read dynamically from the current light curve:
            mag_last, mjd_last, filter_last = last_jd.get_last(target)

            # everytime the list is rendered, the last mag and last mjd are updated per target
            TargetExtra.objects.update_or_create(target=target,
                                                 key='mag_last',
                                                 defaults={'value': mag_last})

            TargetExtra.objects.update_or_create(target=target,
                                                 key='mjd_last',
                                                 defaults={'value': mjd_last})

            # updating sun separation
            try:
                obj_pos = SkyCoord(target.ra, target.dec, unit=u.deg)
                Sun_sep = around(sun_pos.separation(obj_pos).deg, 0)
            except:
                logger.error("Coordinates outside the range in {target} for Sun position calculation!")
                obj_pos = SkyCoord(0, 0, unit=u.deg)
                Sun_sep = "error"  # around(sun_pos.separation(obj_pos).deg,0)

            TargetExtra.objects.update_or_create(target=target,
                                                 key='sun_separation',
                                                 defaults={'value': Sun_sep})

            target.sun = Sun_sep

            out_filter = ""
            if (mjd_last > 0):
                out_filter = filter_last
            else:
                out_filter = "null"

            target.last_mag = mag_last
            target.last_filter = out_filter

            try:
                target.dt = (mjd_now - mjd_last)
                dt = (mjd_now - mjd_last)
            except:
                dt = 10
                target.dt = -1.

            try:
                imp = float(target.extra_field.get('importance'))
                cadence = float(target.extra_field.get('cadence'))
            except:
                imp = 1
                cadence = 1

            target.cadencepriority = computePriority(dt, imp, cadence)
            prioritylist.append(target.cadencepriority)

        return context


# Table list view with light curves only
class TargetListImagesView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list_images.html'
    strict = False
    model = Target
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

        context['target_count'] = context['object_list'].count

        return context


class TargetMicrolensingView(PermissionRequiredMixin, DetailView):
    model = Target
    permission_required = 'bhtom_targets.view_target'

    def get(self, request, *args, **kwargs):
        target_id = kwargs.get('pk', None)
        if isinstance(target_id, int):
            target: Target = Target.objects.get(pk=target_id)
        else:
            target: Target = Target.objects.get(name=target_id)


        datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0]
                                             )

        allobs = []
        allobs_nowise = []
        for datum in datums:
            if str(datum.filter) == "WISE(W1)" or str(datum.filter) == "WISE(W2)":
#                allobs.append(str("WISE"))
                allobs.append(str(datum.filter))
                continue
            else:
                allobs_nowise.append(str(datum.filter))
                allobs.append(str(datum.filter))

        #counting the number of entires per filter in order to remove the very short ones
        filter_counts = {}
        for obs in allobs:
            if obs in filter_counts:
                filter_counts[obs] += 1
            else:
                filter_counts[obs] = 1

        # Create a new list that only includes filters with at least three occurrences
        allobs_filtered = []
        for obs in allobs_nowise:
            if filter_counts[obs] > 2:
                allobs_filtered.append(obs)
                
        #extracting uniq list and sort it alphabetically
        all_filters = sorted(set(allobs))
        #this will move the WISE to the end of the list, if present
        if 'WISE(W1)' in all_filters:
            all_filters.remove('WISE(W1)')
            all_filters.append('WISE(W1)')
        if 'WISE(W2)' in all_filters:
            all_filters.remove('WISE(W2)')
            all_filters.append('WISE(W2)')

        all_filters_nowise = sorted(set(allobs_filtered)) #no wise and no short filters

        #for form values:
        if request.method == 'GET':
            init_t0 = request.GET.get('init_t0', '')
            init_te = request.GET.get('init_te', '')
            init_u0 = request.GET.get('init_u0', '')
            logu0 = request.GET.get('logu0', '')
            fixblending = request.GET.get('fixblending', 'on')
            auto_init = request.GET.get('auto_init', '')
            selected_filters = request.GET.getlist('selected_filters')
        else:
            selected_filters = all_filters_nowise #by default, selecting all filters but wise


        if len(selected_filters) == 0:
            selected_filters = all_filters_nowise #by default, selecting all filters but wise

        sel = {}
        for f in all_filters:
            if f in selected_filters:
                sel[f] = True
            else:
                sel[f] = False

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['selected_filters'] = selected_filters
        context['sel'] = sel
        context.update({
        'init_t0': init_t0,
        'init_te': init_te,
        'init_u0': init_u0,
        'logu0': logu0,
        'fixblending': fixblending,
        'auto_init': auto_init,
        'filter_counts': filter_counts
        })
        return self.render_to_response(context)



class DataProductUploadView(LoginRequiredMixin,FormView):
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
        MJD = form.cleaned_data['MJD']
        ExpTime = form.cleaned_data['ExpTime']
        matchDist = form.cleaned_data['matchDist']
        dryRun = form.cleaned_data['dryRun']
        comment = form.cleaned_data['comment']
        facility = form.cleaned_data['facility']
        observer = form.cleaned_data['observer']
        user = self.request.user

        if dp_type == 'fits_file' and observatory.cpcsOnly == True:
            logger.error('observatory without ObsInfo: %s %s' % (str(f[0].name), str(target)))
            messages.error(self.request, 'Used Observatory without ObsInfo')
            return redirect(form.cleaned_data.get('referrer', '/'))

        post_data = {
            'filter': observation_filter,
            'target': target,
            'data_product_type': dp_type,
            'matchDist': matchDist,
            'comment': comment,
            'dryRun': dryRun,
            'observatory': observatory,
            'MJD':MJD,
            'ExpTime': ExpTime
        }
        token = Token.objects.get(user_id=user.id).key

        headers = {
            'Authorization': 'Token ' + token
        }

        # Make a POST request to upload-service with the extracted data
        response = requests.post(settings.UPLOAD_SERVICE_URL + 'upload/', data=post_data, files=data_product_files, headers=headers)

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

        # Set headers for the POST request to upload-service
        headers = {
            'Authorization': authorization_header,
        }

        # Make a POST request to upload-service with the extracted data
        response = requests.post(settings.UPLOAD_SERVICE_URL + 'upload/', data=post_data, files=request.FILES, headers=headers)

        return HttpResponse(response.content, status=response.status_code)

def deleteFits(dp):
    try:
        logger.info('try remove fits' + str(dp.data))
        BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        url_base = BASE + '/data/'
        url_result = os.path.join(url_base, str(dp.data))
        os.remove(url_result)
    except Exception as e:
        logger.info(e)


class ProceedUploadDPAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dp, target_id, observatory_name, observation_filter, MJD, expTime, comment, user, plot = None, None, None, None, None, None, None, None, None
        fits_quantity = None

        try:
            dp_id = request.data.get('dp')
            dp = DataProduct.objects.get(id=dp_id)

            target_id = request.data.get('target_id')
            observatory_name = request.data.get('observatory')
            observation_filter = request.data.get('observation_filter')
            MJD = request.data.get('MJD')
            expTime = request.data.get('expTime')
            dry_run = request.data.get('dryRun')
            matchDist = request.data.get('matchDist')
            comment = request.data.get('comment')
            user = request.data.get('user')
            fits_quantity = request.data.get('fits_quantity')
            plot = request.data.get('plot')

            run_hook(
                'data_product_post_upload',
                dp, target_id, observatory_name,
                observation_filter, MJD, expTime,
                dry_run, matchDist, comment,
                user, fits_quantity, plot
            )
            run_data_processor(dp)

        except InvalidFileFormatException as iffe:
            #deleteFits(dp)
            # capture_exception(iffe)
            print(str(iffe))
            ReducedDatum.objects.filter(data_product=dp).delete()
            dp.delete()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(str(e))
            #deleteFits(dp)
            # capture_exception(e)
            ReducedDatum.objects.filter(data_product=dp).delete()
            dp.delete()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)