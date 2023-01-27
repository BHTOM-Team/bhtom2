from django import forms
from crispy_forms.layout import Column, Div, HTML, Layout, Row, MultiWidgetField, Fieldset

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm
from bhtom_base.bhtom_observations.widgets import FilterField
from bhtom_base.bhtom_observations.cadence import CadenceForm

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES


class REMPhotometricSequenceForm(BaseManualObservationForm):
    name = forms.CharField()
    start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    observation_id = forms.CharField(required=False)
    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))

    exposure_time = forms.IntegerField()
    exposure_count = forms.IntegerField()
    cadence_in_days = forms.IntegerField() #in days

    valid_instruments = ['ROS2']
    valid_filters = [['griz+J','griz+J'],['griz+H','griz+H'],['griz+Ks','griz+Ks']] #griz are always used in REM + infrared filter
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
