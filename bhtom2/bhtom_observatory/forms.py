from django import forms

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.forms.widgets import CheckboxInput

logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_observatory: forms]')


class CustomCheckboxInput(CheckboxInput):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['onclick'] = 'CheckCalibrationFlag();'  # Add an onclick event
        return super().render(name, value, attrs, renderer)
    
class ObservatoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        if obj.calibration_flg:
            return '{name} ({prefix}) (Only Instrumental photometry file)'.format(name=obj.name,
                                                                                  prefix=obj.prefix)
        else:
            return '{name} ({prefix})'.format(name=obj.name, prefix=obj.prefix)


class ObservatoryCreationForm(forms.ModelForm):
    calibration_flg = forms.BooleanField(
        label='Only instrumental photometry file',
        required=False,
        initial=False,
        widget=CustomCheckboxInput(),
    )
    example_file = forms.FileField(label='Sample fits*',
                                   help_text='Provide one sample fits per filter, clearly labelled.',
                                   widget=forms.ClearableFileInput(
                                       attrs={'multiple': True}
                                   ))

    gain = forms.FloatField(
                            initial=None,
                            label='Gain* [electrons/ADU]',
                            widget=forms.NumberInput(attrs={'placeholder': '2.0'}))
    readout_noise = forms.FloatField(
                                     initial=None,
                                     label='Readout noise* [electrons]',
                                     widget=forms.NumberInput(attrs={'placeholder': '2'}))
    binning = forms.FloatField(
                               initial=None,
                               label='Binning*',
                               widget=forms.NumberInput(attrs={'placeholder': '1'}))
    saturation_level = forms.FloatField(initial=None,
                                        label='Saturation level* [ADU]',
                                        widget=forms.NumberInput(attrs={'placeholder': '63000'}))
    pixel_scale = forms.FloatField(
                                   initial='',
                                   label='Pixel scale* [arcsec/pixel]',
                                   widget=forms.NumberInput(attrs={'placeholder': '0.8'}))
    readout_speed = forms.FloatField(
                                     initial=None,
                                     label='Readout speed [ms/pixel] (if not known, pass 9999)*',
                                     widget=forms.NumberInput(attrs={'placeholder': '3'}))
    pixel_size = forms.FloatField(
                                  initial=None,
                                  label='Pixel size [um]',
                                  widget=forms.NumberInput(attrs={'placeholder': '13.5'}))
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
        super(ObservatoryCreationForm, self).__init__(*args, **kwargs)
        # Set the 'required' attribute of fields based on calibration_flg
        calibration_flag = self.fields['calibration_flg']
        for field_name in self.fields:
            if field_name != 'calibration_flag':
                self.fields[field_name].required = not calibration_flag
        self.fields['name'].required = True
        self.fields['lon'].required = True
        self.fields['lat'].required = True
        self.fields['comment'].required = False

    class Meta:
        model = Observatory
        fields = ('name', 'lon', 'lat',
                  'calibration_flg', 'example_file',
                  'gain', 'readout_noise', 'binning', 'saturation_level',
                  'pixel_scale', 'readout_speed', 'pixel_size',
                  'approx_lim_mag', 'filters', 'altitude',
                  'comment')


class ObservatoryUpdateForm(forms.ModelForm):
    calibration_flg = forms.BooleanField(
        label='Only instrumental photometry file',
        required=False,
        initial=False,
        widget=CustomCheckboxInput(),
    )
    example_file = forms.FileField(label='Sample fits*',
                                   help_text='Provide one sample fits per filter, clearly labelled.',
                                   widget=forms.ClearableFileInput(
                                       attrs={'multiple': True}
                                   ))

    gain = forms.FloatField(
                            initial=None,
                            label='Gain* [electrons/ADU]',
                            widget=forms.NumberInput(attrs={'placeholder': '2.0'}))
    readout_noise = forms.FloatField(
                                     initial=None,
                                     label='Readout noise* [electrons]',
                                     widget=forms.NumberInput(attrs={'placeholder': '2'}))
    binning = forms.FloatField(
                               initial=None,
                               label='Binning*',
                               widget=forms.NumberInput(attrs={'placeholder': '1'}))
    saturation_level = forms.FloatField(initial=None,
                                        label='Saturation level* [ADU]',
                                        widget=forms.NumberInput(attrs={'placeholder': '63000'}))
    pixel_scale = forms.FloatField(
                                   initial='',
                                   label='Pixel scale* [arcsec/pixel]',
                                   widget=forms.NumberInput(attrs={'placeholder': '0.8'}))
    readout_speed = forms.FloatField(
                                     initial=None,
                                     label='Readout speed [ms/pixel] (if not known, pass 9999)*',
                                     widget=forms.NumberInput(attrs={'placeholder': '3'}))
    pixel_size = forms.FloatField(
                                  initial=None,
                                  label='Pixel size [um]',
                                  widget=forms.NumberInput(attrs={'placeholder': '13.5'}))
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

    class Meta:
        model = Observatory
        fields = ('name', 'lon', 'lat',
                  'calibration_flg', 'example_file',
                  'gain', 'readout_noise', 'binning', 'saturation_level',
                  'pixel_scale', 'readout_speed', 'pixel_size',
                  'approx_lim_mag', 'filters', 'altitude',
                  'comment')


class ObservatoryUserUpdateForm(forms.ModelForm):
    class Meta:
        model = ObservatoryMatrix
        fields = ('comment',)


class ObservatoryUserCreationForm(forms.Form):
    observatory = forms.ChoiceField()

    comment = forms.CharField(
        widget=forms.Textarea,
        label="Comment",
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ObservatoryUserCreationForm, self).__init__(*args, **kwargs)

        observatory = ObservatoryMatrix.objects.filter(user=user)
        insTab = []
        for ins in observatory:
            insTab.append(ins.observatory.id)

        self.fields['observatory'] = ObservatoryChoiceField(

            queryset=Observatory.objects.exclude(id__in=insTab).filter(active_flg=True).order_by('name'),
            widget=forms.Select(),
            required=True
        )
