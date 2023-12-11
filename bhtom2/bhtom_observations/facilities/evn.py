from bhtom_base.bhtom_observations.facility import BaseRoboticObservationFacility, \
    BaseRoboticObservationForm

from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from bhtom_base.bhtom_targets.models import Target
from crispy_forms.layout import Div, Layout, Submit

import requests
import json
from datetime import datetime, time, timedelta, timezone
from time import time as time_t

def make_request(*args, **kwargs):
    response = requests.request(*args, **kwargs)
    response.raise_for_status()
    return response

band_choices = (
    ('92cm', '92 cm or 0.33 GHz'),
    ('49cm', '49 cm or 0.6 GHz'),
    ('30cm', '30 cm or  1 GHz'),
    ('21cm', '21 cm or 1.4 GHz'),
    ('18cm', '18 cm or 1.7 GHz'),
    ('13cm', '13 cm or 2.3 GHz'),
    ('6cm', '6 cm or 5 GHz'),
    ('5cm', '5 cm or 6 GHz'),
    ('3.6cm', '3.6 cm or 8.3 GHz'),
    ('2.5cm', '2.5 cm or 12 GHz'),
    ('2cm', '2 cm or 15 GHz'),
    ('1.3cm', '1.3 cm or 23 GHz'),
    ('0.7cm', '0.7 cm or 43 GHz'),
    ('0.3cm', '0.3 cm or 100 GHz'),
    ('0.1cm', '0.1 cm or 300 GHz'))
API_URL = "https://tom-backend.jive.eu/api/1.0.0"

class StationsCache:
    refresh_time = 0
    refresh_cycle = 10 * 60 # 10 minutes
    json_stations = None

    @classmethod
    def _get(cls):
        now = time_t()
        if now - cls.refresh_time > cls.refresh_cycle:
            response = make_request('GET', API_URL + '/stations/')
            cls.json_stations = response.json()['stations']
            cls.refresh_time = now
        return cls.json_stations
    
    @classmethod
    def station_choices(cls):
        return cls._get()

    @classmethod
    def station_initial(cls):
        return [abbreviation for abbreviation, _ in cls._get()]

class EvnObservationFacilityForm(BaseRoboticObservationForm):

    stations = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                         choices=StationsCache.station_choices,
                                         initial=StationsCache.station_initial)
    
    band = forms.ChoiceField(choices=band_choices, initial='21cm')
                             
    def tomorrow_noon():
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        noon = time(hour=12, tzinfo=timezone.utc)
        return datetime.combine(tomorrow, noon)

    def tomorrow_fourpm():
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        fourpm = time(hour=16, tzinfo=timezone.utc)
        return datetime.combine(tomorrow, fourpm)

    # using DateTimeField gives an error where django tries to json serialize
    # a datetime object
    start_time = forms.CharField(initial=tomorrow_noon,
                                 widget=forms.DateTimeInput(
                                     attrs={'type': 'datetime-local'}))
    end_time = forms.CharField(initial=tomorrow_fourpm,
                               widget=forms.DateTimeInput(
                                   attrs={'type': 'datetime-local'}))

    def layout(self):
        check_submit = Submit(
            "check-availability", "Check station availability",
            formaction="https://tom-backend.jive.eu/availability/overview/",
            formtarget="_blank",
            formmethod="GET")
        link_account_submit = Submit(
            "link-account", "Link EVN account",
            formaction="/connect_evn_account/login_redirect/",
            formtarget="_blank",
            formmethod="POST")
        return Div('band', 'stations', 'start_time', 'end_time',
                   check_submit, link_account_submit)


class EvnObservationFacility(BaseRoboticObservationFacility):
    name = 'EVN'
    observation_forms = {'IMAGING': EvnObservationFacilityForm}

    def data_products(self, observation_id, product_id=None):
        if product_id is not None:
            return []
        response = make_request('GET',
                                API_URL + f'/data_products/{observation_id}')
        if response.status_code != 200:
            return []
        return response.json()['result']
    
    def get_form(self, observation_type):
        return self.observation_forms.get(observation_type, 
                                          EvnObservationFacilityForm)

    def get_observation_status(self, observation_id):
        response = make_request('GET', API_URL + f'/status/{observation_id}')
        print('status', response.json())
        return response.json()

    def get_observation_url(self, observation_id):
        return ''

    def get_observing_sites(self):
        return {}

    def get_terminal_observing_states(self):
        return ['COMPLETED', 'FAILED']

    def submit_observation(self, observation_payload):
        """
        Required observation_payload['params'] keywords:
        start_time: datetime
        end_time: datetime
        stations: list of 2 letter station codes
        band: a string from the first element of the band_choices
        """
        print('submitted', observation_payload)

        # UGLY hack, just here so testing with oauth can continue,
        # the request or user has to be available in this class' methods
        # to be able to use oauth
        from inspect import currentframe
        request = currentframe().f_back.f_locals['self'].request
        print(request.session['access_token'])
        
        target = Target.objects.get(id=observation_payload['target_id'])
        params = observation_payload['params']
        observation_request = {k: params[k]
                               for k in ('start_time', 'end_time', 'stations',
                                         'band')}
        # FIX ignoring epoch for now
        observation_request['target_ra'] = target.ra
        observation_request['target_dec'] = target.dec

        header = {'Authorization': 'token {}'.format(
            request.session['access_token'])}
        
        response = make_request('POST',
                                API_URL + '/submit/',
                                headers=header,
                                json=observation_request)

        print('response', response.json())
        return [response.json()['id']]

    def validate_observation(self, observation_payload):
        pass
