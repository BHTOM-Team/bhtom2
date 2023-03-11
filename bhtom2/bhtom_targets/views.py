import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView
from bhtom2.bhtom_targets.forms import NonSiderealTargetCreateForm, SiderealTargetCreateForm
from bhtom2.external_service.data_source_information import get_pretty_survey_name
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_common.mixins import Raise403PermissionRequiredMixin
from bhtom_base.bhtom_targets.forms import TargetExtraFormset, TargetNamesFormset
from bhtom_base.bhtom_targets.models import Target, TargetName
from bhtom_base.bhtom_targets.utils import check_duplicate_source_names, check_for_existing_alias, get_nonempty_names_from_queryset
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms

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
        Runs after form validation. Creates the ``Target``, and creates any ``TargetName`` or ``TargetExtra`` objects,
        then runs the ``target_post_save`` hook and redirects to the success URL.

        :param form: Form data for target creation
        :type form: subclass of TargetCreateForm
        """

        extra = TargetExtraFormset(self.request.POST)
        names = TargetNamesFormset(self.request.POST)

        target_names = get_nonempty_names_from_queryset(names.data)
        duplicate_names = check_duplicate_source_names(target_names)
        existing_names = check_for_existing_alias(target_names)

        # Check if the form, extras and names are all valid:
        if extra.is_valid() and names.is_valid() and (not duplicate_names) and (not existing_names):
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

        for source_name, name in target_names:
            to_add, _ = TargetName.objects.update_or_create(target=self.object, source_name=source_name)
            to_add.name = name
            to_add.save()

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

    @transaction.atomic
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

