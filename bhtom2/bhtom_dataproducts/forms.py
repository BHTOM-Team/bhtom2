from django import forms
from django.conf import settings

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom2.bhtom_calibration.models import Catalogs
from bhtom_base.bhtom_dataproducts.models import DataProductGroup_user

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_dataproducts.forms')


class ObservatoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        if obj.observatory.calibration_flg:
            return '{name} ({prefix}) (Only Instrumental photometry file)'.format(name=obj.observatory.name,
                                                                                  prefix=obj.observatory.prefix)
        else:
            return '{name} ({prefix})'.format(name=obj.observatory.name, prefix=obj.observatory.prefix)


class GroupChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.group.name


class DataProductUploadForm(forms.Form):
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
        label="Choose a Files",
        widget=forms.ClearableFileInput(
            attrs={'multiple': True,'class': 'custom-label'}
        ),
    )
    data_product_type = forms.ChoiceField(
        choices=[v for k, v in settings.DATA_PRODUCT_TYPES.items()],
        initial='photometry',
        widget=forms.RadioSelect(attrs={'onclick': "dataProductSelect();"}),
    )

    dryRun = forms.BooleanField(
        label='Dry Run (no data will be stored in the database)',
        required=False,
    )

    referrer = forms.CharField(
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs['initial']['user']
        filter = {}
        filter['no'] = 'Auto'
        catalogs = Catalogs.objects.filter(isActive=True)
        for curval in catalogs:
            curname = curval.survey
            filters = curval.filters
            filter[curname + '/' + filters] = curname + '/' + filters

        super(DataProductUploadForm, self).__init__(*args, **kwargs)

        self.fields['mjd'] = forms.FloatField(
            widget=forms.NumberInput(attrs={'id': 'mjd'}),
            required=False,
            label="MJD OBS *",
        )

        self.fields['observer'] = forms.CharField(
            initial=user.first_name + " " + user.last_name,
            required=False,
            label='Observer\'s Name *',
        )

        self.fields['observatory'] = ObservatoryChoiceField(
            queryset=ObservatoryMatrix.objects.filter(user=user, active_flg=True).order_by('observatory__name'),
            widget=forms.Select(),
            required=False,
            
        )
        self.fields['filter'] = forms.ChoiceField(
            choices=[v for v in filter.items()],
            initial="GaiaSP/any",
            widget=forms.Select(),
            required=False,
            label='Force filter'
        )

        self.fields['comment'] = forms.CharField(
            widget=forms.Textarea,
            required=False,
            label='Comment',
        )
        # self.fields['group'] = GroupChoiceField(
        #     queryset=DataProductGroup_user.objects.filter(user_id=user.id, active_flg=True).order_by('created'),
        #     widget=forms.Select(),
        #     required=False,
        #     label="Group",
        # )
