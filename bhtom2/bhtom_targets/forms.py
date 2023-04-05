from django import forms
from astropy.coordinates import Angle
from astropy import units as u
from django.forms import ValidationError, inlineformset_factory, HiddenInput
from django.conf import settings
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_groups_with_perms, remove_perm
from datetime import datetime, timezone

from bhtom_base.bhtom_targets.utils import check_for_existing_coords, coords_to_degrees
from astropy.coordinates import Angle
from astropy import units as u
from django.forms import ValidationError

from bhtom_base.bhtom_targets.models import (
    Target, TargetExtra, TargetName, SIDEREAL_FIELDS, NON_SIDEREAL_FIELDS, REQUIRED_SIDEREAL_FIELDS,
    REQUIRED_NON_SIDEREAL_FIELDS, REQUIRED_NON_SIDEREAL_FIELDS_PER_SCHEME
)


def extra_field_to_form_field(field_type):
    if field_type == 'number':
        return forms.FloatField(required=False)
    elif field_type == 'boolean':
        return forms.BooleanField(required=False)
    elif field_type == 'datetime':
        return forms.DateTimeField(required=False)
    elif field_type == 'string':
        return forms.CharField(required=False, widget=forms.Textarea)
    else:
        raise ValueError(
            'Invalid field type {}. Field type must be one of: number, boolean, datetime string'.format(field_type)
        )


def name_field_to_form_field(source_name):
    return forms.CharField(required=False, widget=forms.TextInput, label=f'{source_name} name')


class CoordinateField(forms.CharField):
    def __init__(self, *args, **kwargs):
        c_type = kwargs.pop('c_type')
        self.c_type = c_type
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            a = float(value)
            return a
        except ValueError:
            try:
                if self.c_type == 'ra':
                    a = Angle(value, unit=u.hourangle)
                else:
                    a = Angle(value, unit=u.degree)
                return a.to(u.degree).value
            except Exception:
                raise ValidationError('Invalid format. Please use sexigesimal or degrees')


class TargetForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(Group.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # for field in self.fields.keys():
        #     if (field in settings.CREATE_TARGET_HIDDEN_FIELDS): 
        #         self.fields[field].widget = forms.HiddenInput()

        self.fields['epoch'].initial = 2000.0
        
        self.extra_fields = {}
        for extra_field in settings.EXTRA_FIELDS:
            # Add extra fields to the form
            field_name = extra_field['name']
            if (field_name in settings.CREATE_TARGET_HIDDEN_EXTRA_FIELDS): continue
            self.extra_fields[field_name] = extra_field_to_form_field(extra_field['type'])
            # Populate them with initial values if this is an update
            # or with default values if the first create
            if (field_name=='importance'): self.extra_fields[field_name].initial = 9.99
            if (field_name=='cadence'): self.extra_fields[field_name].initial = 1.0
            if (field_name=='creation_date'): self.extra_fields[field_name].initial = datetime.now(timezone.utc).isoformat()
            if (field_name=='dont_update_me'): self.extra_fields[field_name].initial = False

            #the values are going to be overwritten if the update
            if kwargs['instance']:
                te = TargetExtra.objects.filter(target=kwargs['instance'], key=field_name)
                if te.exists():
                    self.extra_fields[field_name].initial = te.first().typed_value(extra_field['type'])

            self.fields.update(self.extra_fields)

        self.name_fields = {}

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            for field in settings.EXTRA_FIELDS:
                if self.cleaned_data.get(field['name']) is not None:
                    TargetExtra.objects.update_or_create(
                            target=instance,
                            key=field['name'],
                            defaults={'value': self.cleaned_data[field['name']]}
                    )

#             # #writing the creation date:
#             if (not self.cleaned_data.get('creation_date')):
#                 now = datetime.now(timezone.utc).isoformat()
# #                print("Saving now as the creation date for target ",now,instance.name)
#                 TargetExtra.objects.update_or_create(target=instance,
#                 key='creation_date',
#                 defaults={'value': now})

            #In hooks the light curves should be downloaded and priority computed                

            # Save groups for this target
            for group in self.cleaned_data['groups']:
                assign_perm('bhtom_targets.view_target', group, instance)
                assign_perm('bhtom_targets.change_target', group, instance)
                assign_perm('bhtom_targets.delete_target', group, instance)
            for group in get_groups_with_perms(instance):
                if group not in self.cleaned_data['groups']:
                    remove_perm('bhtom_targets.view_target', group, instance)
                    remove_perm('bhtom_targets.change_target', group, instance)
                    remove_perm('bhtom_targets.delete_target', group, instance)

        return instance

    class Meta:
        abstract = True
        model = Target
        fields = '__all__'
        widgets = {'type': forms.HiddenInput()}


class SiderealTargetCreateForm(TargetForm):
    ra = CoordinateField(required=True, label='Right Ascension', c_type='ra',
                         help_text='Right Ascension, in decimal degrees or sexagesimal hours. See '
                                   'https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                   'supported sexagesimal inputs.')
    dec = CoordinateField(required=True, label='Declination', c_type='dec',
                          help_text='Declination, in decimal or sexagesimal degrees. See '
                                    ' https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                    'supported sexagesimal inputs.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in REQUIRED_SIDEREAL_FIELDS:
            self.fields[field].required = True

        self.extra_fields['classification'].required = True
        self.extra_fields['classification'].help_text = 'Classification of the object (e.g. variable star, microlensing event)'
        self.extra_fields['classification'].label = 'Classification*'
        self.extra_fields['classification'].widget.attrs['rows'] = 1

        self.extra_fields['discovery_date'].required = False
        self.extra_fields['discovery_date'].help_text = 'Date of the discovery, YYYY-MM-DDTHH-MM-SS, or leave blank'
        self.extra_fields['importance'].required = True
        self.extra_fields['importance'].help_text = 'Target importance as an integer 0-10 (10 is the highest)'
        self.extra_fields['importance'].label = 'Importance*'
        self.extra_fields['cadence'].required = True
        self.extra_fields['cadence'].help_text = 'Requested cadence (0-100 days)'
        self.extra_fields['cadence'].label = 'Cadence*'

        # # self.fields['gaia_alert_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['calib_server_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['ztf_alert_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['aavso_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['gaiadr2_id'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['TNS_ID'].widget = TextInput(attrs={'maxlength': 100})
        # self.fields['classification'].widget = TextInput(attrs={'maxlength': 250})

        # self.fields['tweet'].widget = HiddenInput()
        # self.fields['jdlastobs'].widget = HiddenInput()
        # self.fields['maglast'].widget = HiddenInput()
        # self.fields['dicovery_date'].widget = HiddenInput()
        # self.fields['Sun_separation'].widget = HiddenInput()
        # self.fields['dont_update_me'].widget = HiddenInput()

    # def clean(self):
    #     cleaned_data = super().clean()
    #     stored = Target.objects.all()
    #     try:
    #         ra = coords_to_degrees(cleaned_data.get('ra'), 'ra')
    #         dec = coords_to_degrees(cleaned_data.get('dec'), 'dec')
    #     except:
    #         raise ValidationError(f'Invalid format of the coordinates')

    #     if (ra<0 or ra>360 or dec<-90 or dec>90):
    #         raise ValidationError(f'Coordinates beyond range error')

        # if this is an update, do not check if target exists at these coordinates:
#        target = self.data['target']
        # target = self.data.get('target',None)
        # print(target)
        # cd = cleaned_data.get('creation_date',None)
        # print(cd)
#        te = TargetExtra.objects.filter(target=target, key="creation_date")
#        if not te.exists():
        # if (cd is None):
        #     coords_names = check_for_existing_coords(ra, dec, 3./3600., stored)
        #     if (len(coords_names)!=0):
        #         ccnames = ' '.join(coords_names)
        #         raise ValidationError(f'Source found already at these coordinates: {ccnames}')


    class Meta(TargetForm.Meta):
        # fields = ('name', 'type', 'ra', 'dec', 'epoch', 'parallax',
        #           'pm_ra', 'pm_dec', 'galactic_lng', 'galactic_lat',
        #           'distance', 'distance_err')
        fields = ('name', 'type', 'ra', 'dec', 'epoch')
    # class Meta(TargetForm.Meta):
    #     fields = SIDEREAL_FIELDS


class NonSiderealTargetCreateForm(TargetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in REQUIRED_NON_SIDEREAL_FIELDS:
            self.fields[field].required = True

    def clean(self):
        """
        Look at the 'scheme' field and check the fields required for the
        specified field have been given
        """
        cleaned_data = super().clean()
        scheme = cleaned_data['scheme']  # scheme is a required field, so this should be safe
        required_fields = REQUIRED_NON_SIDEREAL_FIELDS_PER_SCHEME[scheme]

        for field in required_fields:
            if not cleaned_data.get(field):
                # Get verbose names of required fields
                field_names = [
                    "'" + Target._meta.get_field(f).verbose_name + "'"
                    for f in required_fields
                ]
                scheme_name = dict(Target.TARGET_SCHEMES)[scheme]
                raise ValidationError(
                    "Scheme '{}' requires fields {}".format(scheme_name, ', '.join(field_names))
                )

    class Meta(TargetForm.Meta):
        fields = NON_SIDEREAL_FIELDS


class TargetVisibilityForm(forms.Form):
    start_time = forms.DateTimeField(required=True, label='Start Time', widget=forms.TextInput(attrs={'type': 'date'}))
    end_time = forms.DateTimeField(required=True, label='End Time', widget=forms.TextInput(attrs={'type': 'date'}))
    airmass = forms.DecimalField(required=False, label='Maximum Airmass')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        target = self.data['target']
        if end_time < start_time:
            raise forms.ValidationError('Start time must be before end time')
        if target.type == 'NON_SIDEREAL':
            raise forms.ValidationError('Airmass plotting is only supported for sidereal targets')


TargetExtraFormset = inlineformset_factory(Target, TargetExtra, fields=('key', 'value'),
                                           widgets={'value': forms.TextInput()}, extra=0)

TargetNamesFormset = inlineformset_factory(Target, TargetName, fields=('source_name', 'name',), validate_min=False,
                                           can_delete=False, extra=1, max_num=100,
                                           widgets={'name': forms.TextInput()},)

class TargetLatexDescriptionForm(TargetForm):
    ra = CoordinateField(required=True, label='Right Ascension', c_type='ra',
                         help_text='Right Ascension, in decimal degrees or sexagesimal hours. See '
                                   'https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                   'supported sexagesimal inputs.')
    dec = CoordinateField(required=True, label='Declination', c_type='dec',
                          help_text='Declination, in decimal or sexagesimal degrees. See '
                                    ' https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                    'supported sexagesimal inputs.')
    latex = forms.CharField(label = 'latex', required = False, 
                            widget=forms.Textarea(attrs={'rows':6, 'cols':80}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # for field in REQUIRED_SIDEREAL_FIELDS:
        #     self.fields[field].required = True

#        self.fields['galactic_lat'].widget = forms.TextInput()
        self.fields['parallax'].label = 'Gaia DR3 parallax'

        self.extra_fields['classification'].required = False
        self.extra_fields['classification'].help_text = 'Classification of the object (e.g. variable star, microlensing event)'
        self.extra_fields['classification'].label = 'Classification'
        self.extra_fields['classification'].widget.attrs['rows'] = 1

        self.extra_fields['discovery_date'].required = False
        self.extra_fields['discovery_date'].help_text = 'Date of the discovery, YYYY-MM-DDTHH-MM-SS, or leave blank'

        # # self.fields['gaia_alert_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['calib_server_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['ztf_alert_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['aavso_name'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['gaiadr2_id'].widget = TextInput(attrs={'maxlength': 100})
        # # self.fields['TNS_ID'].widget = TextInput(attrs={'maxlength': 100})
        # self.fields['classification'].widget = TextInput(attrs={'maxlength': 250})

        #hidding irrelevant fields
        self.fields['importance'].widget = HiddenInput()
        self.fields['cadence'].widget = HiddenInput()

        # self.fields['jdlastobs'].widget = HiddenInput()
        # self.fields['maglast'].widget = HiddenInput()
        # self.fields['dicovery_date'].widget = HiddenInput()
        # self.fields['Sun_separation'].widget = HiddenInput()
        # self.fields['dont_update_me'].widget = HiddenInput()

    class Meta:
        # fields = ('name', 'type', 'ra', 'dec', 'epoch', 'parallax',
        #           'pm_ra', 'pm_dec', 'galactic_lng', 'galactic_lat',
        #           'distance', 'distance_err')
        model = Target
        fields = ('latex','name', 'ra', 'dec', 'galactic_lng', 'galactic_lat',
                  'epoch', 'parallax',
                  'pm_ra', 'pm_dec',
        )
#        fields = ('name', 'type', 'ra', 'dec', 'epoch')
