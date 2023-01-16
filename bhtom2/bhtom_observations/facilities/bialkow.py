from crispy_forms.layout import Div
from django import forms

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES


class BialkowPhotometryObservationForm(BaseManualObservationForm):
    name = forms.CharField()
    start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    observation_id = forms.CharField(required=False)
    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))

    def layout(self):
        return Div(
            Div('name', 'observation_id'),
            Div(
                Div('start', css_class='col'),
                Div('end', css_class='col'),
                css_class='form-row'
            ),
            Div('observation_params')
        )

class Bialkow(BaseManualObservationFacility):
    name = 'Bialkow'
    SITES = {
        'Bialkow': {
            'sitecode': 'bialkow',
            'latitude': 16.658407910831198,
            'longitude': 51.47435543316016,
            'elevation': 150
        }
    }
    observation_forms = {
        'PHOTOMETRIC_SEQUENCE': BialkowPhotometryObservationForm,
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
