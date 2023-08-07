from django import forms
from django.contrib.auth.models import Group
from django.conf import settings

from bhtom_base.bhtom_dataproducts.models import DataProductGroup, DataProduct
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target
from bhtom2.bhtom_observatory.models import Observatory
from django.contrib.auth.models import User
from bhtom2.bhtom_calibration.models import catalogs as Catalogs


class ObservatoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        if obj.cpcsOnly:
            return '{name} ({prefix}) (Only Instrumental photometry file)'.format(name=obj.name,
                                                                                     prefix=obj.prefix)
        else:
            return '{name} ({prefix})'.format(name=obj.name, prefix=obj.prefix)


class DataProductUploadForm(forms.Form):
    MATCHING_RADIUS = [
        ('0.5', '0.5 arcsec'),
    ]

    observation_record = forms.ModelChoiceField(
        ObservationRecord.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )
    target = forms.ModelChoiceField(
        Target.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )

    files = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True}
        ),
    )

    data_product_type = forms.ChoiceField(
        choices=[v for k, v in settings.DATA_PRODUCT_TYPES.items()],
        initial='photometry_cpcs',
        widget=forms.RadioSelect(attrs={'onclick': "dataProductSelect();"}),
        required=True
    )

    MJD = forms.DecimalField(
        label="MJD OBS",
        widget=forms.NumberInput(attrs={'id': 'mjd', 'disable': 'none'}),
        required=False
    )

    ExpTime = forms.IntegerField(
        label='Exposure time (sec)',
        widget=forms.NumberInput(attrs={'id': 'ExpTime'}),
        required=False
    )

    matchDist = forms.ChoiceField(
        choices=MATCHING_RADIUS,
        widget=forms.Select(),
        label='Matching radius',
        initial='0.5',
        required=False
    )

    dryRun = forms.BooleanField(
        label='Dry Run (no data will be stored in the database)',
        required=False
    )

    referrer = forms.CharField(
        widget=forms.HiddenInput()
    )

    observer = forms.CharField(
        label='Observer\'s Name',
        required=False
    )

    facility = forms.CharField(
        label='Facility Name',
        required=False
    )

    def __init__(self, *args, **kwargs):
        filter = {}
        filter['no'] = 'Auto'
        catalogs = Catalogs.objects.all().values_list('filters')
        for curval in catalogs:
            curname, filters = curval
            for i, f in enumerate(filters):
                filter[curname + '/' + f] = curname + '/' + f
            filter['%s/any' % (curname)] = '%s/any' % (curname)

        for f in ['U', 'B', 'V', 'R', 'I', 'u', 'g', 'r', 'i', 'z']:
            filter['any/%s' % f] = 'any/%s' % f

        if not settings.TARGET_PERMISSIONS_ONLY:
            self.fields['groups'] = forms.ModelMultipleChoiceField(Group.objects.none(),
                                                                   required=False,
                                                                   widget=forms.CheckboxSelectMultiple)
            
        super(DataProductUploadForm, self).__init__(*args, **kwargs)    
        self.fields['observatory'] = ObservatoryChoiceField(
            queryset= Observatory.objects.filter(isActive=True).order_by('name'),
            widget=forms.Select(),
            required=False
        )

        self.fields['filter'] = forms.ChoiceField(
            choices=[v for v in filter.items()],
            widget=forms.Select(),
            required=False,
            label='Force filter'
        )

        self.fields['comment'] = forms.CharField(
            widget=forms.Textarea,
            required=False,
            label='Comment',
        )