import re

import bleach
from django import forms
from django.forms import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.forms.widgets import CheckboxInput

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_observatory-forms')


def validate_data(value):
    cleaned_name = bleach.clean(value, tags=[], attributes={}, protocols=[], strip=True)

    if value != cleaned_name:
        logger.error("----------Error in validate data, detect html code------------")
        raise ValidationError("Invalid data format.")

    pattern = r'^[a-zA-Z0-9\-_+. :?\'"&apos;&#39;()@!]*$'
    match = re.match(pattern, value)
    if not match:
        invalid_chars = re.findall(r'[^a-zA-Z0-9\-_+. :?\'"&apos;&#39;()@!]', value)
        invalid_chars_str = ', '.join(invalid_chars)
        raise ValidationError("Illegal sign: " + str(invalid_chars_str))


class CustomCheckboxInput(CheckboxInput):
    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer)
    
class ObservatoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        if obj.calibration_flg:
            return '{name} (Only Instrumental photometry file)'.format(name=obj.name,)
        else:
            return '{name} '.format(name=obj.name)


class CameraChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
            return obj.camera_name


class CameraCreationForm(forms.ModelForm):
    id = forms.CharField(widget=forms.HiddenInput)
    example_file = forms.FileField(
        label='Sample fits*',
        help_text='Provide one sample fits per filter, clearly labelled.',
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'custom-label'}),
    )
    camera_name = forms.CharField(
        initial="Default",
        label='Camera Name',
        widget=forms.TextInput()
    )

    class Meta:
        model = Camera
        fields = ('id','camera_name', 'example_file', 'binning', 'gain', 'readout_noise',
                  'saturation_level', 'pixel_scale', 'pixel_size', 'readout_speed')

    def __init__(self, *args, **kwargs):
        super(CameraCreationForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = True 
        self.fields['example_file'].required = False 

    def clean_camera_name(self):
        cleaned_data = self.clean()
        camera_name = cleaned_data.get('camera_name', '')
        if camera_name is not None:
            validate_data(camera_name)
        return camera_name


class NoDeleteInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(NoDeleteInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    def should_delete(self, form):
        return False

CamerasFormSet = inlineformset_factory(
        Observatory,
        Camera,
        form=CameraCreationForm,
        extra=1,
        formset=NoDeleteInlineFormSet, 
    )
CamerasUpdateFormSet = inlineformset_factory(
        Observatory,
        Camera,
        form=CameraCreationForm,
        extra=0,
    )


class ObservatoryCreationForm(forms.ModelForm):
    calibration_flg = forms.BooleanField(
        label='Only instrumental photometry file',
        required=False,
        initial=False,
        widget=CustomCheckboxInput(),
    )
   
    approx_lim_mag = forms.FloatField(
        initial=None,
        label='Approx. limit magnitude in V band* [mag]',
        widget=forms.NumberInput(attrs={'placeholder': '18.0'})
    )
    altitude = forms.FloatField(
        initial=None,
        label='Altitude [m]*',
        widget=forms.NumberInput(attrs={'placeholder': '0.0'})
    )
    filters = forms.CharField(
        initial=None,
        label='Filters*',
        widget=forms.TextInput(attrs={'placeholder': 'V,R,I'})
    )

    def __init__(self, *args, **kwargs):
        super(ObservatoryCreationForm, self).__init__(*args, **kwargs)
        calibration_flag = self.fields['calibration_flg']
        for field_name in self.fields:
            if field_name != 'calibration_flg':
                self.fields[field_name].required = not calibration_flag
        self.fields['name'].required = True
        self.fields['lon'].required = True
        self.fields['lat'].required = True
        self.fields['comment'].required = False
        self.fields['aperture'].required = False
        self.fields['focal_length'].required = False
        self.fields['telescope'].required = False
    
    class Meta:
        model = Observatory
        fields = ('name', 'lon', 'lat',
                  'approx_lim_mag', 'filters', 'altitude','aperture','focal_length',
                  'telescope', 'comment','calibration_flg')

    def clean_name(self):
        cleaned_data = self.clean()
        name = cleaned_data.get('name', '')
        if name is not None:
            validate_data(str(name))
        return name

    def clean_telescope(self):
        cleaned_data = self.clean()
        telescope = cleaned_data.get('telescope', '')
        if telescope is not None:
            validate_data(str(telescope))
        return telescope

    def clean_comment(self):
        cleaned_data = self.clean()
        comment = cleaned_data.get('comment', '')
        if comment is not None:
            validate_data(str(comment))
        return comment


class ObservatoryUpdateForm(forms.ModelForm):
    calibration_flg = forms.BooleanField(
        label='Only instrumental photometry file',
        required=False,
        initial=False,
        widget=CustomCheckboxInput(),
    )

    approx_lim_mag = forms.FloatField(
                                      initial=None,
                                      label='Approx. limit magnitude in V band* [mag]',
                                      widget=forms.NumberInput(attrs={'placeholder': '18.0'}))

    altitude = forms.FloatField(
                                initial=None,
                                label='Altitude [m]*',
                                widget=forms.NumberInput(attrs={'placeholder': '0.0'}))
    filters = forms.CharField(
                              initial=None,
                              label='Filters*',
                              widget=forms.TextInput(attrs={'placeholder': 'V,R,I'}))
    
    def __init__(self, *args, **kwargs):
        super(ObservatoryUpdateForm, self).__init__(*args, **kwargs)
        # Set the 'required' attribute of fields based on calibration_flg
        calibration_flag = self.fields['calibration_flg']
        for field_name in self.fields:
            if field_name != 'calibration_flag':
                self.fields[field_name].required = not calibration_flag
        self.fields['name'].required = True
        self.fields['lon'].required = True
        self.fields['lat'].required = True
        self.fields['comment'].required = False
        self.fields['aperture'].required = False
        self.fields['focal_length'].required = False
        self.fields['telescope'].required = False

    class Meta:
        model = Observatory
        fields = ('name', 'lon', 'lat',
                  'approx_lim_mag', 'filters', 'altitude','aperture','focal_length',
                  'telescope', 'comment','calibration_flg')


class ObservatoryUserUpdateForm(forms.ModelForm):
    class Meta:
        model = ObservatoryMatrix
        fields = ('comment',)


class ObservatoryUserCreationForm(forms.Form):
    observatory = forms.ChoiceField(widget=forms.Select(attrs={'id': 'observatory-select'}))
    camera = forms.ChoiceField(widget=forms.Select(attrs={'id': 'camera-select'}))
    comment = forms.CharField(
        widget=forms.Textarea,
        label="Comment",
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        observatory_id = kwargs.pop('observatory_id', None)
        super(ObservatoryUserCreationForm, self).__init__(*args, **kwargs)

        active_observatory_ids = set(Camera.objects.filter(active_flg=True).values_list('observatory_id', flat=True))
        active_observatories = Observatory.objects.filter(id__in=active_observatory_ids).order_by('name')
        
        self.fields['observatory'] = ObservatoryChoiceField(
            queryset=active_observatories,
            widget=forms.Select(),
            required=True
        )

        self.fields['camera'] = CameraChoiceField(
                queryset= Camera.objects.all(),
                widget=forms.Select(),
                required=True
            )
        self.fields['camera'].widget.attrs['data-observatory'] = observatory_id
