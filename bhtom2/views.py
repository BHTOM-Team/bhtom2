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
from bhtom_base.bhtom_dataproducts.models import  ReducedDatum


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
        return context


class TargetMicrolensingView(PermissionRequiredMixin, DetailView):
    template_name = 'bhtom_targets/target_microlensing.html'
    model = Target
    permission_required = 'bhtom_targets.view_target'

    def get(self, request, *args, **kwargs):
        target_id: int = kwargs.get('pk', None)
        target: Target = Target.objects.get(pk=target_id)

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

        #TODO: check if len data!=0

        #extracting uniq list and sort it alphabetically
        all_filters = sorted(set(allobs))
        all_filters.remove('WISE(W1)')
        all_filters.remove('WISE(W2)')
        all_filters.append('WISE(W1)') #this trick will move WISE to the end of the list
        all_filters.append('WISE(W2)') #this trick will move WISE to the end of the list

        all_filters_nowise = sorted(set(allobs_nowise))

        #for form values:
        if request.method == 'GET':
            clevel = request.GET.get('clevel', '')
            slevel = request.GET.get('slevel', '')
            selected_filters = request.GET.getlist('selected_filters')
        else:
            #for default first render:??
            clevel = str(0.05)
            slevel = str(0.05)
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
        context['clevel'] = clevel
        context['slevel'] = slevel
        context['selected_filters'] = selected_filters
        context['sel'] = sel
#        print(context)  
#        print("VIEW", sel)

        return self.render_to_response(context)

#     def filter_form(self, request, *args, **kwargs):
#         target_id: int = kwargs.get('pk', None)
#         target: Target = Target.objects.get(pk=target_id)

#         datums = ReducedDatum.objects.filter(target=target,
#                                              data_type=settings.DATA_PRODUCT_TYPES['photometry'][0]
#                                              )

#         allfilters = []
#         for datum in datums:
#             if str(datum.facility) == "NEOWISE" or str(datum.facility) == "ALLWISE":
#                 continue
#             else:
#                 allfilters.append(str(datum.facility))

#         #extracting uniq list and sort it alphabetically
#         filters = sorted(set(allfilters))

#         if request.method == 'POST':
#             selected_filters = request.POST.getlist('filters')
#             slevel = float(request.POST['slevel'])
#             clevel = float(request.POST['clevel'])
#             context = self.get_context_data(object=self.object)
#             # Call microlensing_for_target() with selected filters and other parameters
# #            result = microlensing_for_target(context, target, slevel, clevel, selected_filters)
#             # Render result template with context data
#             context['clevel'] = clevel
#             context['slevel'] = slevel
#             context['filters'] = filters
#             print("POST", filters)
#             return self.render_to_response(context)
#         else:
#             pass
#             # filters = get_all_filters()
#             # return render(request, 'filter_form.html', {'filters': filters})
