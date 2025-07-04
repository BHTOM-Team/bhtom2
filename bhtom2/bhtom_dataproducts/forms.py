from django import forms
from django.conf import settings

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera
from bhtom2.bhtom_calibration.models import Catalogs
from bhtom_base.bhtom_dataproducts.models import DataProductGroup_user
from django_select2.forms import ModelSelect2MultipleWidget
from django.contrib.auth import get_user_model
logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_dataproducts.forms')


class ObservatoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        if obj.calibration_flg:
            return '{name} (Only Instrumental photometry file)'.format(name=obj.name)
        else:
            return '{name}'.format(name=obj.name)

class CameraChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
            return obj.camera_name
      


class GroupChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.group.name
    

class UserSelect2MultipleWidget(ModelSelect2MultipleWidget):
    model = get_user_model()
    search_fields = ['username__icontains', 'first_name__icontains', 'last_name__icontains']

    def get_queryset(self):
        return get_user_model().objects.filter(is_active=True).exclude(username='AnonymousUser')

    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.username})"

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
        self.user = kwargs['initial']['user']
        users = kwargs['initial']['users']
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
            label="MJD OBS *"
        )

        self.fields['observer'] = forms.ModelMultipleChoiceField(
            queryset=users,
            widget=UserSelect2MultipleWidget,
            required=False,
            label='Observers *',
            initial=[self.user]
        )
        user_cameras = ObservatoryMatrix.objects.filter(user=self.user).values_list('camera__id', flat=True)
        user_active_cameras = Camera.objects.filter(id__in=user_cameras, active_flg=True)
        users_obs_id = Camera.objects.filter(id__in=user_cameras, active_flg=True).values_list('observatory_id', flat=True)


        user_observatories = Observatory.objects.filter(id__in=users_obs_id).order_by('name')
        self.fields['observatory'] = ObservatoryChoiceField(
            queryset=user_observatories,
            widget=forms.Select(),
            required=False,
            label='Observatory*'
        )
        
        self.fields['observatory_input'] =forms.CharField(
            required=False,
            label='Observatory*'
        )


        self.fields['camera'] = CameraChoiceField(
            queryset=user_active_cameras,
            widget=forms.Select(),
            required=False,
            label='Camera*'
            
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