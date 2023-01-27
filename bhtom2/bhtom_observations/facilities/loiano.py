from crispy_forms.layout import Div
from django import forms
from crispy_forms.layout import Column, Div, HTML, Layout, Row, MultiWidgetField, Fieldset

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm
from bhtom_base.bhtom_observations.widgets import FilterField

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES


class LoianoPhotometryObservationForm(BaseManualObservationForm):
    
    name = forms.CharField()
    start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    observation_id = forms.CharField(required=False)
    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))
    cadence_frequency = forms.IntegerField(required=True, help_text='in hours')
    exposure_time = forms.FloatField(required=True, help_text='in seconds')

    valid_filters = [['V', 'V'], ['R', 'R'], ['I', 'I']]
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
            Div('observation_params')
        )


class Loiano(BaseManualObservationFacility):
    name = 'Loiano'
    SITES = {
        'Loiano': {
            'sitecode': 'loiano',
            'latitude': 44.25917,
            'longitude': 11.3338,
            'elevation': 785
        }
    }
    observation_forms = {
        'PHOTOMETRIC_SEQUENCE': LoianoPhotometryObservationForm,
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

    def get_facility_weather_urls(self):
        facility_weather_urls = {
            'code': 'Loiano',
            'sites': [
                {
                    'code': site['sitecode'],
                    'weather_url': 'http://meteo.bo.astro.it/'
                }
                for site in self.SITES.values()]
            }
        return facility_weather_urls


    def get_facility_status(self):
        return {
            'code': 'Loiano',
            'sites': [
                {
                    'code': site['sitecode'],
                    'telescopes': [
                        {
                            'code': 'loiano',
                            'status': 'AVAILABLE'
                        },
                    ],
                    'weather_url': "http://meteo.bo.astro.it/"
                }
                for site in self.SITES.values()]
            }