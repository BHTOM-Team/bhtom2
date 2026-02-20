import csv
from datetime import datetime
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404

import os
from django.http import FileResponse

from bhtom2.bhtom_targets.forms import NonSiderealTargetCreateForm, SiderealTargetCreateForm, TargetLatexDescriptionForm
from bhtom2.bhtom_targets.hooks import update_force_reducedDatum
from bhtom2.bhtom_targets.utils import import_targets
from bhtom2.external_service.data_source_information import get_pretty_survey_name
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.openai_utils import latex_target_title_prompt, latex_text_target_prompt, \
    get_response
from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats_latex
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_common.mixins import Raise403PermissionRequiredMixin
from bhtom_base.bhtom_targets.forms import TargetNamesFormset
from bhtom_base.bhtom_targets.models import TargetName, DownloadedTarget, TargetList
from bhtom2.bhtom_targets.utils import check_duplicate_source_names, check_for_existing_alias, \
    check_for_existing_coords, get_nonempty_names_from_queryset, coords_to_degrees, get_client_ip
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms

from django.views.generic import TemplateView, RedirectView
from django.urls import reverse
from django.shortcuts import render
from abc import ABC, abstractmethod
from django.utils.html import format_html
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import View
from settings import settings
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.views.generic.detail import DetailView
from guardian.mixins import PermissionListMixin
from bhtom2.bhtom_targets.filters import TargetFilter

from bhtom2.utils.reduced_data_utils import save_high_energy_data_for_target_to_csv_file, save_photometry_data_for_target_to_csv_file, \
    save_radio_data_for_target_to_csv_file

from bhtom_base.bhtom_targets.models import Target, TargetList
from bhtom_base.bhtom_dataproducts.models import ReducedDatum, BrokerCadence

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.views')


class TargetCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a Target. Requires authentication.
    """
    model = Target
    fields = '__all__'
    template_name = 'bhtom_targets/target_form.html'

    def get_default_target_type(self):
        """
        Returns the user-configured target type specified in ``settings.py``, if it exists, otherwise returns sidereal

        :returns: User-configured target type or global default
        :rtype: str
        """
        try:
            return settings.TARGET_TYPE
        except AttributeError:
            return Target.SIDEREAL

    def get_target_type(self):
        """
        Gets the type of the target to be created from the query parameters. If none exists, use the default target
        type specified in ``settings.py``.

        :returns: target type
        :rtype: str
        """
        obj = self.request.GET or self.request.POST
        target_type = Target.SIDEREAL
        # If None or some invalid value, use default target type
        if target_type not in (Target.SIDEREAL, Target.NON_SIDEREAL):
            target_type = self.get_default_target_type()
        return target_type

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.

        :returns: Dictionary with the following keys:

                  `type`: ``str``: Type of the target to be created

                  `groups`: ``QuerySet<Group>`` Groups available to the current user

        :rtype: dict
        """
        return {
            'type': self.get_target_type(),
            'groups': self.request.user.groups.all(),
            **dict(self.request.GET.items())
        }

    def get_context_data(self, **kwargs):
        """
        Inserts certain form data into the context dict.

        :returns: Dictionary with the following keys:

                  `type_choices`: ``tuple``: Tuple of 2-tuples of strings containing available target types in the TOM

                  `extra_form`: ``FormSet``: Django formset with fields for arbitrary key/value pairs
        :rtype: dict
        """
        context = super(TargetCreateView, self).get_context_data(**kwargs)
        context['type_choices'] = Target.TARGET_TYPES
        context['names_form'] = TargetNamesFormset()
        return context

    def get_form_class(self):
        """
        Return the form class to use in this view.

        :returns: form class for target creation
        :rtype: subclass of TargetCreateForm
        """
        target_type = self.get_target_type()
        self.initial['type'] = target_type
        return SiderealTargetCreateForm
        # if target_type == Target.SIDEREAL:
        #
        # else:
        #     return NonSiderealTargetCreateForm

    def form_valid(self, form):
        """
        Runs after form validation. Checks for existence of the target, also under different alias name

        Creates the ``Target``, and creates any ``TargetName`` or ``TargetExtra`` objects,
        then runs the ``target_post_save`` hook and redirects to the success URL.

        :param form: Form data for target creation
        :type form: subclass of TargetCreateForm
        """

        names = TargetNamesFormset(self.request.POST)
        target_names = get_nonempty_names_from_queryset(names.data)
        duplicate_names = check_duplicate_source_names(target_names)
        existing_names = check_for_existing_alias(target_names)

        cleaned_data = form.cleaned_data
        stored = Target.objects.all()
        target_type = self.get_target_type()

        if target_type == Target.SIDEREAL:
            try:
                ra = coords_to_degrees(cleaned_data['ra'], 'ra')
                dec = coords_to_degrees(cleaned_data['dec'], 'dec')
            except Exception as e:
                logger.error("Invalid format of the coordinates: %s " % str(e))
                form.add_error(None, "Invalid format of the coordinates")
                return super().form_invalid(form)
        # raise ValidationError(f'Invalid format of the coordinates')

            if ra < 0 or ra > 360 or dec < -90 or dec > 90:
                logger.error("Coordinates beyond range")
                form.add_error(None, "Coordinates beyond range")
                return super().form_invalid(form)
        # raise ValidationError(f'Coordinates beyond range error')
            coords_names = check_for_existing_coords(ra, dec, 3. / 3600., stored)
            if len(coords_names) != 0:
                existing_targets = Target.objects.filter(name__in=coords_names)
                if len(existing_targets) != 0:
                    links = [
                        format_html('<a href="{}">{}</a>', reverse('bhtom_targets:detail', args=[t.id]), t.name)
                        for t in existing_targets
                    ]
                    link_list = format_html(', '.join(links))
                    form.add_error(None, format_html("Source found already at these coordinates (rad 3 arcsec): {}", link_list))
                    return super().form_invalid(form)

        # Check if the form, extras and names are all valid:
        if names.is_valid() and (not duplicate_names) and (not existing_names):
            super().form_valid(form)

        else:
            if duplicate_names:
                form.add_error(None, 'Duplicate source names for aliases.')
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())

            return super().form_invalid(form)

        # storing all the names
        for source_name, name, url in target_names:
            # clearing CPCS names from prefixes if provided:

            to_add, _ = TargetName.objects.update_or_create(target=self.object, source_name=source_name, url=url)
            to_add.name = name
            to_add.save()

        messages.success(self.request, 'Target created, grabbing all the data for it. Please wait and refresh in about a minute...')

        logger.info('Target post save hook: %s created: %s' % (self.object, True))

        if target_type == Target.SIDEREAL:
            run_hook('target_post_save', target=self.object, created=True, user=self.request.user)
        return redirect(self.get_success_url())

    def get_form(self, *args, **kwargs):
        """
        Gets an instance of the ``TargetCreateForm`` and populates it with the groups available to the current user.

        :returns: instance of creation form
        :rtype: subclass of TargetCreateForm
        """
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form


# overwriting the view from bhtom_base
class TargetListView(SingleTableMixin, PermissionListMixin, FilterView):
    """
    View for listing targets in the TOM. Only shows targets that the user is authorized to view. Requires authorization.
    """
    template_name = 'bhtom_targets/target_list.html'
    strict = False
    model = Target
    # table_class = TargetTable
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
    
    #default filter sets importance_min=1
    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)

        if kwargs['data'] is None:
            kwargs['data'] = {'importance_min': '1'}
            kwargs['data'].update({'type': 'SIDEREAL'})
            messages.success(self.request, 'Warning: Default filter applied. Showing targets with Importance>0 only')

        return kwargs

class TargetUpdateView(LoginRequiredMixin, UpdateView):
    """
    View that handles updating a target. Requires authorization.
    """
    permission_required = 'bhtom_targets.change_target'
    model = Target
    fields = '__all__'
    template_name = 'bhtom_targets/target_form.html'

    def get_context_data(self, **kwargs):
        """
        Adds formset for ``TargetName`` and ``TargetExtra`` to the context.

        :returns: context object
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context['names_form'] = TargetNamesFormset(instance=self.object)

        return context

    def form_valid(self, form):
        """
        Runs after form validation. Validates and saves the ``TargetExtra`` and ``TargetName`` formsets, then calls the
        superclass implementation of ``form_valid``, which saves the ``Target``. If any forms are invalid, rolls back
        the changes.

        Saving is done in this order to ensure that new names/extras are available in the ``target_post_save`` hook.

        :param form: Form data for target update
        :type form: subclass of TargetCreateForm
        """
        names = TargetNamesFormset(self.request.POST, instance=self.object)
        target_names = get_nonempty_names_from_queryset(names.data)
        duplicate_names = check_duplicate_source_names(target_names)

        if duplicate_names:
            form.add_error(None, 'Duplicate source names for aliases.')
            return super().form_invalid(form)

        target = Target.objects.get(id=self.object.id)
        cadence = form.cleaned_data['cadence']
        importance = form.cleaned_data['importance']

        if target.importance != importance or target.cadence != cadence:
            try:
                run_hook('update_priority', target=self.object)
            except Exception as e:
                logger.error("Error in update priority: " + str(e))

        super().form_valid(form)

        # Update target names for given source
        for source_name, name, url in target_names:
            # clearing  CPCS names from prefixes if provided:

            # Not clearing ASASSN, as it can have different prefixes

            to_update, created = TargetName.objects.update_or_create(target=self.object, source_name=source_name)
            
            if to_update.name != name or (to_update.url != url and not (to_update.url is None and url == '')):
                to_update.name = name
                to_update.url = url
                to_update.modified = datetime.now()
                to_update.save()
                run_hook('update_alias', target=self.object, broker=source_name)

                messages.add_message(
                    self.request,
                    messages.INFO,
                    f'{"Added" if created else "Updated"} alias {to_update.name} for '
                    f'{get_pretty_survey_name(to_update.source_name)}'
                )
        target_source_names = [s for s, _, u in target_names]

        # Delete target names not in the form (probably deleted by the user)
        for to_delete in TargetName.objects.filter(target=self.object).exclude(source_name__in=target_source_names):
            run_hook('delete_alias', target=self.object, broker=get_pretty_survey_name(to_delete.source_name))
            to_delete.delete()
            messages.add_message(
                self.request,
                messages.INFO,
                f'Deleted alias {to_delete.name} for {get_pretty_survey_name(to_delete.source_name)}'
            )

        return redirect(self.get_success_url())

    def get_queryset(self, *args, **kwargs):
        """
        Returns the queryset that will be used to look up the Target by limiting the result to targets that the user is
        authorized to modify.

        :returns: Set of targets
        :rtype: QuerySet
        """
        return get_objects_for_user(self.request.user, 'bhtom_targets.change_target')

    def get_form_class(self):
        """
        Return the form class to use in this view.

        :returns: form class for target update
        :rtype: subclass of TargetCreateForm
        """
        if self.object.type == Target.SIDEREAL:
            return SiderealTargetCreateForm
        elif self.object.type == Target.NON_SIDEREAL:
            return NonSiderealTargetCreateForm

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view. For the ``TargetUpdateView``, adds the groups that the
        target is a member of.

        :returns:
        :rtype: dict
        """
        initial = super().get_initial()
        initial['groups'] = get_groups_with_perms(self.get_object())
        return initial

    def get_form(self, *args, **kwargs):
        """
        Gets an instance of the ``TargetCreateForm`` and populates it with the groups available to the current user.

        :returns: instance of creation form
        :rtype: subclass of TargetCreateForm
        """
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form


# form for generating latex description of the target (under Publication)
# very similar form to update
class TargetGenerateTargetDescriptionLatexView(LoginRequiredMixin, UpdateView):
    permission_required = 'bhtom_targets.change_target'
    template_name = 'bhtom_targets/target_generate_latex_form.html'
    model = Target
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = Target.objects.get(pk=self.kwargs['pk'])
        # Add any additional context data here
        context['target'] = target

        return context

    def get_form_class(self):
        """
        Return the form class to use in this view.
        """
        return TargetLatexDescriptionForm

    def get_initial(self):
        initial = super().get_initial()
        initial['groups'] = get_groups_with_perms(self.get_object())

        target: Target = self.object
        prompt = latex_text_target_prompt(target)
        initial['latex'] = get_response(prompt)
        initial['prompt'] = prompt

        # title:
        prompt_title = latex_target_title_prompt(target)
        initial['title'] = get_response(prompt_title)
        initial['prompt_title'] = prompt_title

        return initial

    def get_queryset(self, *args, **kwargs):
        return get_objects_for_user(self.request.user, 'bhtom_targets.change_target')

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form


class TargetDownloadDataView(ABC, PermissionRequiredMixin, View):
    permission_required = 'bhtom_dataproducts.add_dataproduct'

    @abstractmethod
    def generate_data_method(self, target_id):
        pass

    def get(self, request, *args, **kwargs):

        target_id = None

        if 'pk' in kwargs:
            target_id = kwargs['pk']
        elif 'name' in kwargs:
            target_id = kwargs['name']
        logger.info(f'Generating file for target with id={str(target_id)}...')

        tmp = None
        try:
            tmp, filename = self.generate_data_method(target_id)
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating file for target with id={target_id}: {e}')
        finally:
            if tmp:
                try:
                    os.remove(tmp.name)
                except Exception as e:
                    logger.error("Error in delete tmp: " + str(e))


class TargetDownloadPhotometryStatsLatexTableView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        return get_photometry_stats_latex(target_id)


# copied from bhtom_base to use my own utils.import_target
class TargetImportView(LoginRequiredMixin, TemplateView):
    """
    View that handles the import of targets from a CSV. Requires authentication.
    """
    template_name = 'bhtom_targets/target_import.html'

    def post(self, request):
        """
        Handles the POST requests to this view. Creates a StringIO object and passes it to ``import_targets``.

        :param request: the request object passed to this view
        :type request: HTTPRequest
        """
        user = request.user 
        csv_file = request.FILES['target_csv']
        csv_stream = StringIO(csv_file.read().decode('utf-8'), newline=None)
        targets_count = StringIO(csv_file.read().decode('utf-8'), newline=None)
        targets_count = len(list(csv.reader(targets_count)))

        logger.info("Import targets, count: %s" % str(targets_count))

        if targets_count > 500:
            messages.error(request, "You can upload max 500 targets")
            return redirect(reverse('bhtom_targets:list'))

        group_name = request.POST.get('group_name', None)
        result = import_targets(csv_stream, group_name, user)
        messages.success(
            request,
            'Targets created: {}'.format(len(result['targets']))
        )
        for error in result['errors']:
            messages.warning(request, error)
        return redirect(reverse('bhtom_targets:list'))


class TargetDownloadDataView(ABC, PermissionRequiredMixin, View):
    permission_required = 'bhtom_dataproducts.add_dataproduct'

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
        ip_address = get_client_ip(self.request)
        DownloadedTarget.objects.create(
                user=self.request.user,
                target_id=target_id,
                download_type='P',
                ip_address=ip_address
            )
        return save_photometry_data_for_target_to_csv_file(target_id)


class TargetDownloadRadioDataView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        ip_address = get_client_ip(self.request)
        DownloadedTarget.objects.create(
                user=self.request.user,
                target_id=target_id,
                download_type='R',
                ip_address=ip_address
            )
        return save_radio_data_for_target_to_csv_file(target_id)

class TargetDownloadHEDataView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        ip_address = get_client_ip(self.request)
        DownloadedTarget.objects.create(
                user=self.request.user,
                target_id=target_id,
                download_type='H',
                ip_address=ip_address
            )
        return save_high_energy_data_for_target_to_csv_file(target_id)


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
                                             ).filter(error__gt=0, active_flg=True)

        allobs = []
        allobs_nowise = []
        for datum in datums:
            ff = str(datum.filter)
            if "LAT" in ff:
                continue

            allobs.append(ff)

            if "WISE" not in ff:
                allobs_nowise.append(ff)

        # counting the number of entires per filter in order to remove the very short ones
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

        # extracting uniq list and sort it alphabetically
        all_filters = sorted(set(allobs))
        # this will move the WISE to the end of the list, if present
        if 'WISE(W1)' in all_filters:
            all_filters.remove('WISE(W1)')
            all_filters.append('WISE(W1)')
        if 'WISE(W2)' in all_filters:
            all_filters.remove('WISE(W2)')
            all_filters.append('WISE(W2)')

        all_filters_nowise = sorted(set(allobs_filtered))  # no wise and no short filters

        # for form values:
        if request.method == 'GET':
            init_t0 = request.GET.get('init_t0', '')
            init_te = request.GET.get('init_te', '')
            init_u0 = request.GET.get('init_u0', '')
            init_piEN = request.GET.get('init_piEN', '')
            init_piEE = request.GET.get('init_piEE', '')
            logu0 = request.GET.get('logu0', '')
            fixblending = request.GET.get('fixblending', 'on')
            auto_init = request.GET.get('auto_init', '')
            selected_filters = request.GET.getlist('selected_filters')
        else:
            selected_filters = all_filters_nowise  # by default, selecting all filters but wise

        if len(selected_filters) == 0:
            selected_filters = all_filters_nowise  # by default, selecting all filters but wise

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
            'init_piEN': init_piEN,
            'init_piEE': init_piEE,
            'logu0': logu0,
            'fixblending': fixblending,
            'auto_init': auto_init,
            'filter_counts': filter_counts
        })
        return self.render_to_response(context)


class UpdateReducedDatum(LoginRequiredMixin, RedirectView):

        """
        View that handles the updating of reduced data tied to a ``DataProduct`` that was automatically ingested from a
        broker. Requires authentication.
        """

        def get(self, request, *args, **kwargs):
            """
            Method that handles the GET requests for this view. Calls the management command to update the reduced data and
            adds a hint using the messages framework about automation.
            """
            target_id = kwargs.get('pk', None)
            target = Target.objects.get(pk=target_id)
            update_force_reducedDatum(target)
            messages.success(
                request,
                'Reduced datum will be updated.')

            return HttpResponseRedirect(reverse('targets:detail', kwargs={'pk': target.id}))




class TargetNotFoundView(View):
    template_name = 'bhtom_targets/target_not_exist_error.html'
    
    def get(self, request, *args, **kwargs):
        # Get the target_name from the query parameters
        target_name = request.GET.get('target_name', 'Unknown Target')
        try:
            alias = TargetName.objects.get(name=target_name)
            context = {'target_name': target_name, 'alias': alias.name, 'target_alias': alias.target}
        except Exception as e:
            alias = None
            context = {'target_name': target_name, 'alias': None, 'target_alias': None}
        return render(request, self.template_name, context)
    


class TargetAddNewGroupingView(LoginRequiredMixin, View):
    """
    View that handles the creation of new groups and addition of targets to target groups. Requires authentication.
    """

    def post(self, request, *args, **kwargs):
 
        query_string = request.POST.get('query_string', '')
        grouping_name = request.POST.get('grouping')  
        selected_target_id = request.POST.get('selected-target')

        try:
            if not grouping_name:
                messages.error(request, 'Group name is required.')
                return redirect(reverse('bhtom_base.bhtom_targets:list') + '?' + query_string)
            
            if TargetList.objects.filter(name=grouping_name).exists():
                messages.warning(
                    request,
                    f'A group with the name "{grouping_name}" already exists. Please provide a new group name.'
                )
                return redirect(reverse('bhtom_base.bhtom_targets:list') + '?' + query_string)

            grouping_object = TargetList.objects.create(name=grouping_name)
            messages.success(request, f'Group "{grouping_name}" created successfully.')
            

            if selected_target_id:
                target = Target.objects.get(pk=selected_target_id)
                grouping_object.targets.add(target)
                messages.success(request, f'Target "{target.name}" added to group "{grouping_name}".')
            else:
                messages.warning(request, 'No target selected to add to the group.')

        except Target.DoesNotExist:
            messages.error(request, f'Target with ID "{selected_target_id}" does not exist.')
        except Exception as e:
            messages.error(request, f'Error creating group or adding target: {e}')
        
        return redirect(reverse('bhtom_base.bhtom_targets:list') + '?' + query_string)





class TargetPublicDetailView(DetailView):
    """
    View that handles the display of the target details. Allows fetching via ID or name.
    """
    model = Target
    template_name = "bhtom_targets/target_public_detail.html"
    context_object_name = "target"

    def get_object(self):
        identifier = self.kwargs.get("identifier")
        if identifier is None:
            identifier = str(self.kwargs.get("pk"))

        try:
            if identifier.isdigit():
                return Target.objects.get(id=int(identifier))
            return Target.objects.get(name=identifier)
        except:
            raise Http404

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect(reverse('bhtom_targets:target_not_found') + f'?target_name={self.kwargs.get("identifier")}')
        
        return super().get(request, *args, **kwargs)
    

# replacing targetdetailview and adding ads
from bhtom_base.bhtom_targets.views import TargetDetailView as BaseTargetDetailView
from bhtom_base.bhtom_targets.models import TargetName
from bhtom2.bhtom_targets.utils import fetch_ads_text_block 

#not using these aliases in the ADS query
import re
BLOCKED_SOURCES = {"CRTS", "NEOWISE", "2MASS", "ATLAS", "PS1", "DECAPS", "twomass"}
BLOCKED_NAME_PREFIX = re.compile(r'^(?:CRTS|NEOWISE|2MASS|ATLAS|PS1|DECAPS|twomass)\b', re.IGNORECASE)

class TargetDetailView(BaseTargetDetailView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        target = self.object

        # Prefill with target.name + aliases, excluding CRTS/NEOWISE/2MASS
        alias_qs = (
            TargetName.objects
            .filter(target=target)
            .exclude(source_name__in=BLOCKED_SOURCES)
            .values_list('name', 'source_name')
        )
        aliases = [n for (n, src) in alias_qs if n and not BLOCKED_NAME_PREFIX.match(n)]
        names_list = [target.name] + aliases

        default_names = "; ".join(sorted({n.strip() for n in names_list if n and n.strip()}))

        raw = self.request.GET.get('ads_names', default_names)
        context['ads_names'] = raw
        context['ads_default_names'] = default_names

        context['ads_results_text'] = ""
        if 'ads_names' in self.request.GET:
            context['ads_results_text'] = fetch_ads_text_block(raw)  # see util changes below

        return context
