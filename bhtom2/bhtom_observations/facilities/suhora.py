from crispy_forms.layout import Div
from django import forms
from crispy_forms.layout import Column, Div, HTML, Layout, Row, MultiWidgetField, Fieldset

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm
from bhtom_base.bhtom_observations.widgets import FilterField

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES


class SuhoraPhotometryObservationForm(BaseManualObservationForm):
    
    name = forms.CharField()
    start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    observation_id = forms.CharField(required=False)
    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))
    cadence_frequency = forms.IntegerField(required=True, help_text='in hours')
    exposure_time = forms.FloatField(required=True, help_text='in seconds')

    valid_filters = [['U', 'U'],['B', 'B'],['V', 'V'], ['R', 'R'], ['I', 'I'],['g_prime', 'G_PRIME'],['r_prime', 'R_PRIME'],['su','SU'],['sv','SV'],['sy','SY'],['i_prime', 'I_PRIME'],['G2', 'GD'],['BG40','BG40'],['ND', 'ND']]
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


class Suhora(BaseManualObservationFacility):
    name = 'Suhora'
    SITES = {
        'Suhora': {
            'sitecode': 'suhora',
            'latitude': 49.569167,
            'longitude': 20.0675,
            'elevation': 1000
        }
    }
    observation_forms = {
        'PHOTOMETRIC_SEQUENCE': SuhoraPhotometryObservationForm,
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
            'code': 'Suhora',
            'sites': [
                {
                    'code': site['sitecode'],
                    'weather_url': 'https://www.as.up.krakow.pl/main/index.php?lang=en'
                }
                for site in self.SITES.values()]
            }
        return facility_weather_urls


    def get_facility_status(self):
        return {
            'code': 'Suhora',
            'sites': [
                {
                    'code': site['sitecode'],
                    'telescopes': [
                        {
                            'code': 'suhora',
                            'status': 'AVAILABLE'
                        },
                    ],
                    'weather_url': "https://www.as.up.krakow.pl/main/index.php?lang=en"
                }
                for site in self.SITES.values()]
            }