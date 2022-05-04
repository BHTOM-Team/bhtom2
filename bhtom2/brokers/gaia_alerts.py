import json
import re
from datetime import datetime
from typing import Optional, List, Tuple

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimezoneInfo
from bs4 import BeautifulSoup
from dateutil.parser import parse
from django import forms
from django.db import transaction

from bhtom_base.bhtom_alerts.alerts import GenericAlert
from bhtom_base.bhtom_alerts.alerts import GenericQueryForm
from bhtom_base.bhtom_dataproducts.models import ReducedDatum

from bhtom2 import settings
from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.data_source_information import DataSource, FILTERS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.external_service.filter_name import filter_name
from bhtom_base.bhtom_dataproducts.models import DatumValue


def g_gaia_error(mag: float) -> float:
    a1 = 0.2
    b1 = -5.2
    a2 = 0.26
    b2 = -6.26

    error = 0.0

    if mag < 13.5:
        error: float = a1 * 13.5 + b1
    elif 13.5 < mag < 17:
        error: float = a1 * mag + b1
    elif mag > 17:
        error: float = a2 * mag + b2

    return 10 ** error


class GaiaQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)
    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in degrees'
    )

    def clean_cone(self):
        cone = self.cleaned_data['cone']
        if cone:
            cone_params = cone.split(',')
            if len(cone_params) != 3:
                raise forms.ValidationError('Cone search parameters must be in the format \'RA,Dec,Radius\'.')
        return cone

    def clean(self):
        super().clean()
        if not (self.cleaned_data.get('target_name') or self.cleaned_data.get('cone')):
            raise forms.ValidationError('Please enter either a target name or cone search parameters.')
        elif self.cleaned_data.get('target_name') and self.cleaned_data.get('cone'):
            raise forms.ValidationError('Please only enter one of target name or cone search parameters.')


class GaiaAlertsBroker(BHTOMBroker):
    name = DataSource.Gaia.name
    form = GaiaQueryForm

    def __init__(self):
        super().__init__(DataSource.Gaia)

        try:
            self.__base_url: str = settings.GAIA_ALERTS_PATH
        except Exception as e:
            self.logger.error(f'No GAIA_ALERTS_PATH in settings found!')
            self.__base_url = 'http://gsaweb.ast.cam.ac.uk'

        self.__GAIA_FILTER_NAME: str = FILTERS[DataSource.Gaia][0]
        self.__filter: str = filter_name(self.__GAIA_FILTER_NAME, self.data_source.name)
        self.__FACILITY_NAME: str = "Gaia"
        self.__OBSERVER_NAME: str = "Gaia"

    def fetch_alerts(self, parameters):
        """Must return an iterator"""
        response = query_external_service(f'{self.__base_url}/alerts/alertsindex', self.name, 'content')

        soup = BeautifulSoup(response, 'html.parser')
        script_tags = soup.find_all('script')
        alerts = None

        alerts_pattern = re.compile(r'var alerts = \[(.*?)];')
        for script in script_tags:
            m = alerts_pattern.match(str(script.string).strip())
            if m is not None:
                alerts = '[' + m.group(1) + ']'
                break

        alert_list = json.loads(alerts)

        if parameters['cone'] is not None and len(parameters['cone']) > 0:
            cone_params = parameters['cone'].split(',')
            if len(cone_params) > 3:
                parameters['cone_ra'] = float(cone_params[0])
                parameters['cone_dec'] = float(cone_params[1])
                parameters['cone_radius'] = float(cone_params[2]) * u.deg
                parameters['cone_centre'] = SkyCoord(float(cone_params[0]),
                                                     float(cone_params[1]),
                                                     frame="icrs", unit="deg")

        filtered_alerts = []
        if parameters.get('target_name'):
            for alert in alert_list:
                if parameters['target_name'] in alert['name']:
                    filtered_alerts.append(alert)

        elif 'cone_radius' in parameters.keys():
            for alert in alert_list:
                c = SkyCoord(float(alert['ra']), float(alert['dec']),
                             frame="icrs", unit="deg")
                if parameters['cone_centre'].separation(c) <= parameters['cone_radius']:
                    filtered_alerts.append(alert)

        else:
            filtered_alerts = alert_list

        return iter(filtered_alerts)

    def fetch_alert(self, target_name):

        alert_list = list(self.fetch_alerts({'target_name': target_name, 'cone': None}))

        if len(alert_list) == 1:
            return alert_list[0]
        else:
            return {}

    def to_generic_alert(self, alert):
        timestamp = parse(alert['obstime'])
        alert_link = alert.get('per_alert', {})['link']
        url = f'{self.__base_url}/{alert_link}'

        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=alert['name'],
            name=alert['name'],
            ra=alert['ra'],
            dec=alert['dec'],
            mag=alert['alertMag'],
            score=1.0
        )

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:

        gaia_name: Optional[str] = self.get_target_name(target)

        if not gaia_name:
            self.logger.debug(f'No Gaia name for {target.name}')
            return return_for_no_new_points()

        self.logger.debug(f'Updating Gaia Alerts lightcurve for {gaia_name}, target: {target.name}')

        if alert is not None:
            alert_name = alert['name']
            alert_link = alert.get('per_alert', {})['link']
            lc_url = f'{self.__base_url}/alerts/alert/{alert_name}/lightcurve.csv'
            alert_url = f'{self.__base_url}/{alert_link}'
        elif target:
            alert_url = f'{self.__base_url}/alerts/alert/{gaia_name}/'
            lc_url = f'{alert_url}/lightcurve.csv'
        else:
            return

        response: str = query_external_service(lc_url, 'Gaia alerts')
        html_data: List[str] = response.split('\n')
        new_points: int = 0

        data: List[Tuple[datetime, DatumValue]] = []

        # The data contains alert name at the top: we wish to skip the first 3 lines
        for entry in html_data[2:]:
            phot_data = entry.split(',')

            if len(phot_data) == 3:
                # Photometry data is of format:
                # (date, JD, photometry mag)

                data_jd: str = phot_data[1]
                data_mag: str = phot_data[2]

                try:
                    if 'untrusted' not in data_mag and 'null' not in data_mag and 'NaN' not in data_mag:
                        mag: float = float(data_mag)

                        jd = Time(float(data_jd), format='jd', scale='utc')

                        data.append((
                            jd.to_datetime(timezone=TimezoneInfo()),
                            DatumValue(
                                value=mag,
                                error=g_gaia_error(mag),
                                filter=self.__filter,
                                mjd=jd.mjd)))

                        self.update_last_jd_and_mag(jd.value, mag)
                except Exception as e:
                    self.logger.error(f'Error while processing reduced datapoint for {target.name}: {e}')
                    continue

        try:
            data = list(set(data))
            reduced_datums = [ReducedDatum(target=target, data_type='photometry',
                                           timestamp=datum[0], mjd=datum[1].mjd, value=datum[1].value,
                                           source_name=self.name,
                                           source_location=alert_url,
                                           error=datum[1].error,
                                           filter=datum[1].filter, observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME) for datum in data]
            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.last_jd,
                                      last_mag=self.last_mag)
