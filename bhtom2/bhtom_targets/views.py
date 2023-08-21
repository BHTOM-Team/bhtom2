from io import StringIO
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView
from bhtom2.bhtom_targets.forms import NonSiderealTargetCreateForm, SiderealTargetCreateForm, TargetLatexDescriptionForm
from bhtom2.bhtom_targets.utils import import_targets
from bhtom2.external_service.data_source_information import get_pretty_survey_name
from bhtom2.utils.openai_utils import latex_target_title_prompt, latex_text_target, latex_text_target_prompt, get_response
from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats_latex
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_common.mixins import Raise403PermissionRequiredMixin
from bhtom_base.bhtom_targets.forms import TargetExtraFormset, TargetNamesFormset
from bhtom_base.bhtom_targets.models import Target, TargetExtra, TargetName
from bhtom_base.bhtom_targets.templatetags.targets_extras import deg_to_sexigesimal
from bhtom_base.bhtom_targets.utils import check_duplicate_source_names, check_for_existing_alias, check_for_existing_coords, get_nonempty_names_from_queryset, coords_to_degrees
from bhtom2.utils.coordinate_utils import computeDtAndPriority
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms
from django.forms import inlineformset_factory
from astropy.coordinates import Angle
from astropy import units as u
from django.views.generic import View

from astropy import units as u
from astropy.coordinates import get_sun, SkyCoord
from astropy.time import Time
from numpy import around
from datetime import datetime
from django.core.management import call_command
from bhtom2.dataproducts import last_jd

from abc import ABC, abstractmethod
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.views.generic import  TemplateView, View
from django.urls import reverse_lazy, reverse

logger = logging.getLogger(__name__)

class TargetCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a Target. Requires authentication.
    """
    model = Target
    fields = '__all__'

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
        target_type = obj.get('type')
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
        context['extra_form'] = TargetExtraFormset()
        return context

    def get_form_class(self):
        """
        Return the form class to use in this view.

        :returns: form class for target creation
        :rtype: subclass of TargetCreateForm
        """
        target_type = self.get_target_type()
        self.initial['type'] = target_type
        if target_type == Target.SIDEREAL:
            return SiderealTargetCreateForm
        else:
            return NonSiderealTargetCreateForm

    def form_valid(self, form):
        """
        Runs after form validation. Checks for existence of the target, also under different alias name
        
        Creates the ``Target``, and creates any ``TargetName`` or ``TargetExtra`` objects,
        then runs the ``target_post_save`` hook and redirects to the success URL.

        :param form: Form data for target creation
        :type form: subclass of TargetCreateForm
        """

        extra = TargetExtraFormset(self.request.POST)
        names = TargetNamesFormset(self.request.POST)

        target_names = get_nonempty_names_from_queryset(names.data)
        duplicate_names = check_duplicate_source_names(target_names)
        existing_names = check_for_existing_alias(target_names)

        cleaned_data = form.cleaned_data
        stored = Target.objects.all()
        try:
            ra = coords_to_degrees(cleaned_data['ra'], 'ra')
            dec = coords_to_degrees(cleaned_data['dec'], 'dec')
        except:
            form.add_error(None, "Invalid format of the coordinates")
            return super().form_invalid(form)
#            raise ValidationError(f'Invalid format of the coordinates')

        if (ra<0 or ra>360 or dec<-90 or dec>90):
            form.add_error(None, "Coordinates beyond range")
            return super().form_invalid(form)
#            raise ValidationError(f'Coordinates beyond range error')
        
        coords_names = check_for_existing_coords(ra, dec, 3./3600., stored)
        if (len(coords_names)!=0):
            ccnames = ' '.join(coords_names)
            form.add_error(None, f"There is a source found already at these coordinates (rad 3 arcsec): {ccnames}")
            return super().form_invalid(form)
#            raise ValidationError(f'Source found already at these coordinates: {ccnames}')

        # Check if the form, extras and names are all valid:
        if extra.is_valid() and names.is_valid() and (not duplicate_names) and (not existing_names):
#            messages.success(self.request, 'Target Create success, now grabbing all the data for it. Wait.')
            
            super().form_valid(form)

            extra.instance = self.object
            extra.save()
        else:
            if duplicate_names:
                form.add_error(None, 'Duplicate source names for aliases.')
            form.add_error(None, extra.errors)
            form.add_error(None, extra.non_form_errors())
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())

            return super().form_invalid(form)

        #storing all the names
        for source_name, name in target_names:
            #clearing CPCS names from prefixes if provided:

            if "CPCS" in source_name:
                if name.startswith("ivo://"):
                    name= name.replace("ivo://", "")

            to_add, _ = TargetName.objects.update_or_create(target=self.object, source_name=source_name)
            to_add.name = name
            to_add.save()


#        form.add_error(None,'Creating target, please wait...')
        # messages.add_message(self.request,
        #         messages.INFO,
        #         f'Creating target, please wait...')

        #TODO: there should be a message here on success and a warning to wait: Gathering archival data for target
        #TODO: the hook here should be run in the background         

        logger.info('Target post save hook: %s created: %s', self.object, True)
        run_hook('target_post_save', target=self.object, created=True)

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


class TargetUpdateView(Raise403PermissionRequiredMixin, UpdateView):
    """
    View that handles updating a target. Requires authorization.
    """
    permission_required = 'bhtom_targets.change_target'
    model = Target
    fields = '__all__'

    def get_context_data(self, **kwargs):
        """
        Adds formset for ``TargetName`` and ``TargetExtra`` to the context.

        :returns: context object
        :rtype: dict
        """
        extra_field_names = [extra['name'] for extra in settings.EXTRA_FIELDS]
        context = super().get_context_data(**kwargs)
        context['names_form'] = TargetNamesFormset(instance=self.object)
        context['extra_form'] = TargetExtraFormset(
            instance=self.object,
            queryset=self.object.targetextra_set.exclude(key__in=extra_field_names)
        )
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
        extra = TargetExtraFormset(self.request.POST, instance=self.object)
        names = TargetNamesFormset(self.request.POST, instance=self.object)

        target_names = get_nonempty_names_from_queryset(names.data)
        duplicate_names = check_duplicate_source_names(target_names)

        # Check if the form, extras and names are all valid:
        if extra.is_valid() and not duplicate_names:
            extra.instance = self.object
            extra.save()
        else:
            if duplicate_names:
                form.add_error(None, 'Duplicate source names for aliases.')
            form.add_error(None, extra.errors)
            form.add_error(None, extra.non_form_errors())
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())
            return super().form_invalid(form)

        super().form_valid(form)

        # Update target names for given source
        for source_name, name in target_names:
            #clearing  CPCS names from prefixes if provided:

            #Not clearing ASASSN, as it can have different prefixes

            if "CPCS" in source_name:
                if name.startswith("ivo://"):
                    name= name.replace("ivo://", "")

            to_update, created = TargetName.objects.update_or_create(target=self.object, source_name=source_name)
            to_update.name = name
            to_update.save(update_fields=['name'])
            messages.add_message(
                self.request,
                messages.INFO,
                f'{"Added" if created else "Updated"} alias {to_update.name} for '
                f'{get_pretty_survey_name(to_update.source_name)}'
            )

        target_source_names = [s for s, _ in target_names]

        # Delete target names not in the form (probably deleted by the user)
        for to_delete in TargetName.objects.filter(target=self.object).exclude(source_name__in=target_source_names):
            to_delete.delete()
            messages.add_message(
                self.request,
                messages.INFO,
                f'Deleted alias {to_delete.name} for {get_pretty_survey_name(to_delete.source_name)}'
            )

        #the hook is run even if not called?
        #hook fails in Update giving me errors on openned transactions, atomic and stuff. Not running hook, but taking care of importance/cadence changes only
        # logger.info('Target post save hook: %s created: %s', self.object, False)
        # run_hook('target_post_save', target=self.object, created=False)
        
        # to_update = TargetExtra.objects.update_or_create(target=self.object, key='importance')
        # to_update.save(update_fields=['name'])

        try:
            call_command('updatereduceddata', target_id=self.object.id, stdout=StringIO())
            mag_last, mjd_last, filter_last = last_jd.get_last(self.object)

            #everytime the list is rendered, the last mag and last mjd are updated per target
            te, _ = TargetExtra.objects.update_or_create(target=self.object,
            key='mag_last',
            defaults={'value': mag_last})
            te.save()

            te, _ = TargetExtra.objects.update_or_create(target=self.object,
            key='mjd_last',
            defaults={'value': mjd_last})
            te.save()

            messages.add_message(
            self.request,
            messages.INFO,
            f'Checked for new data in {self.object}. MJD_last = {mjd_last}')
        except Exception as e:
            logger.error("Error checking for new data after Update for {self.object}!")

        #updating priority:
        oldpriority =  float(TargetExtra.objects.get(target=self.object, key='priority').value)

        try:
            imp = float(extra.data['importance'])
            cadence = float(extra.data['cadence'])
        except:
            #what if not provided?
            pass

        #mjd_last = extra.data['mjd_last']
        mjd_last = float(TargetExtra.objects.get(target=self.object, key='mjd_last').value)
        priority = computeDtAndPriority(mjd_last, imp, cadence)
        te, _ = TargetExtra.objects.update_or_create(target=self.object,
        key='priority',
        defaults={'value': priority})
        te.save()

        if (oldpriority!=priority):
            messages.add_message(
                self.request,
                messages.INFO,
                f'Observing priority changed to {priority}'
            )

        # updating sun separation
        sun_pos = get_sun(Time(datetime.utcnow()))

        try:
            obj_pos = SkyCoord(extra.data['ra'], extra.data['dec'], unit=u.deg)
            Sun_sep = around(sun_pos.separation(obj_pos).deg, 0)
        except:
            logger.error("Coordinates outside the range in {target} for Sun position calculation!")
            obj_pos = SkyCoord(0, 0, unit=u.deg)
            Sun_sep = "error"  # around(sun_pos.separation(obj_pos).deg,0)

        TargetExtra.objects.update_or_create(target=self.object,
                                                key='sun_separation',
                                                defaults={'value': Sun_sep})
        print("NEW SUN SEP: ",Sun_sep)

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



#form for generating latex description of the target (under Publication)
#very similar form to update
class TargetGenerateTargetDescriptionLatexView(UpdateView):
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

        #title:
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
        logger.info(f'Generating file for target with id={target_id}...')

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
                os.remove(tmp.name)

class TargetDownloadPhotometryStatsLatexTableView(TargetDownloadDataView):
    def generate_data_method(self, target_id):
        return get_photometry_stats_latex(target_id)

#copied from bhtom_base to use my own utils.import_target
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
        csv_file = request.FILES['target_csv']
        csv_stream = StringIO(csv_file.read().decode('utf-8'), newline=None)
        result = import_targets(csv_stream)
        messages.success(
            request,
            'Targets created: {}'.format(len(result['targets']))
        )
        for error in result['errors']:
            messages.warning(request, error)
        return redirect(reverse('bhtom2.bhtom_targets:list'))
