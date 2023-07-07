from django import forms
from crispy_forms.layout import Column, Div, HTML, Layout, Row, MultiWidgetField, Fieldset

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm
from bhtom_base.bhtom_observations.widgets import FilterField
from bhtom_base.bhtom_observations.cadence import CadenceForm

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES

valid_instruments = ['ROS2']
valid_filters = [['griz+J','griz+J'],['griz+H','griz+H'],['griz+Ks','griz+Ks']] #griz are always used in REM + infrared filter


class REMPhotometricSequenceForm(BaseManualObservationForm):
    name = forms.CharField()
    start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    observation_id = forms.CharField(required=False)
    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))

    exposure_time = forms.IntegerField()
    exposure_count = forms.IntegerField()
    cadence_in_days = forms.IntegerField() #in days

    filters = forms.ChoiceField(required=True, label='Filters', choices=valid_filters)

    def layout(self):
        return Div(
            Div('name', 'observation_id'),
            Div(
                Div('start', css_class='col'),
                Div('end', css_class='col'),
                css_class='form-row'
            ),
            Div('filters'),
            Div('exposure_time'),
            Div('exposure_count'),
            Div('cadence_in_days'),
            Div('observation_params')
        )
    


class REM(BaseManualObservationFacility):
    name = 'REM'
    SITES = {
        'REM': {
            'sitecode': 'REM',
            'latitude': -29.26,
            'longitude': -70.73,
            'elevation': 2400
        }
    }
    observation_forms = {
        'PHOTOMETRIC_SEQUENCE': REMPhotometricSequenceForm,
    }

    def get_form(self, observation_type):
        return self.observation_forms['PHOTOMETRIC_SEQUENCE']

    def submit_observation(self, observation_payload):
        # TODO: send mail
        return []

    def validate_observation(self, observation_payload):
        # TODO: ?
        return []

    def get_terminal_observing_states(self):
        return TERMINAL_OBSERVING_STATES

    def get_observing_sites(self):
        return self.SITES

    def cancel_observation(self, observation_id):
        return []

    def get_observation_url(self, observation_id):
        return ''

    def all_data_products(self, observation_record):
        return []


# # generate text of the email
#     def generate_email_text(params...):


#     #TODO: add S/N parameter (default = 100?)
    def exposure_time_calculator(self, mag, filter, instrument):
        if instrument not in valid_instruments:
            return -1
        if filter in [item for sublist in valid_filters for item in sublist]:
            pass
        else:
            return -1

        base_exposure_time = 100
        adjusted_exposure_time = base_exposure_time * (10**((mag-14)/2.5))
        return adjusted_exposure_time

    def return_valid_filters():
        return valid_filters
    
    def return_valid_instruments():
        return valid_instruments
    
    def compute_for_all(self):
        text_outputs = []
        ff=valid_filters
        
        mag=15
        instrument='ROS2'
        for filter_pair in ff:
            f = filter_pair[0] # use only the first filter in each pair
            exposure_time = self.exposure_time_calculator(mag, f, instrument)
            text_output = f"{f}: {exposure_time} seconds"
            text_outputs.append(text_output)

        print(text_outputs)