import math
from typing import Dict, Optional, Any

from alerce.core import Alerce
from alerce.exceptions import APIError, ObjectNotFoundError
from astropy.time import Time, TimezoneInfo
from tom_alerts.alerts import GenericQueryForm
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, ZTF_FILTERS, FILTERS
from bhtom2.models.reduced_datum_value import reduced_datum_value, reduced_datum_non_detection_value

import json
import re
from typing import Optional, List, Any, Dict

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimezoneInfo
from bs4 import BeautifulSoup
from dateutil.parser import parse
from django import forms
from tom_alerts.alerts import GenericAlert
from tom_alerts.alerts import GenericQueryForm
from tom_dataproducts.models import ReducedDatum

from bhtom2 import settings
from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource, FILTERS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.external_service.filter_name import filter_name
from bhtom2.models.reduced_datum_value import reduced_datum_value


class ZTFQueryForm(GenericQueryForm):

    target_name = forms.CharField(required=False)

    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in arcsecs'
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


class ZTFBroker(BHTOMBroker):

    name = DataSource.ZTF.name

    def __init__(self):
        super().__init__(DataSource.ZTF)

        self.__alerce: Alerce = Alerce()

        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"

    def fetch_alerts(self, parameters):

        response: List[Any] = []

        if parameters['cone'] is not None and len(parameters['cone']) > 0:
            cone_params = parameters['cone'].split(',')
            if len(cone_params) > 3:
                parameters['cone_ra'] = float(cone_params[0])
                parameters['cone_dec'] = float(cone_params[1])
                parameters['cone_radius'] = float(cone_params[2])

                query: Dict[str, Any] = self.__alerce.query_objects(ra=parameters['cone_ra'],
                                                                    dec=parameters['cone_dec'],
                                                                    radius=parameters['cone_radius'])
                response.extend(query.get('items', []))

        if parameters['target_name']:
            query: Dict[str, Any] = self.__alerce.query_objects(name=parameters['target_name'])
            response.extend(query.get('items', []))

        return response

    def fetch_alert(self, target_name):

        alert_list = list(self.fetch_alerts({'target_name': target_name, 'cone': None}))

        if len(alert_list) == 1:
            return alert_list[0]
        else:
            return {}


    def to_generic_alert(self, alert):
        return GenericAlert(
            timestamp=Time(alert.get('firstmjd', 0.0), format='mjd', scale='utc').to_datetime(timezone=TimezoneInfo()),
            id=alert.get('oid', ''),
            name=alert.get('oid', ''),
            ra=alert.get('meanra', 0.0),
            dec=alert.get('meandec', 0.0)
        )

    def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:

        ztf_name: Optional[str] = self.get_target_name(target)

        if not ztf_name:
            self.logger.debug(f'No ZTF name for {target.name}')
            return return_for_no_new_points()

        self.logger.debug(f'Updating ZTF Alerts Lightcurve for {target.name} with ZTF name {ztf_name}')

        try:
            query: Dict[str, Any] = self.__alerce.query_lightcurve(ztf_name)
        # No such object on ZTF
        except ObjectNotFoundError as e:
            raise NoResultException(f'No ZTF data found for {target.name} with ZTF name {ztf_name}')
        except APIError as e:
            raise InvalidExternalServiceResponseException(f'Invalid ALeRCE response for {target.name}: {e}')

        new_points: int = 0

        for entry in query['detections']:

            try:
                mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
                mag: float = float(entry['magpsf_corr'])

                if (mag is not None) and (not math.isnan(mag)):
                    self.logger.debug(f'None magnitude for target {target.name}')

                    magerr: float = float(entry['sigmapsf_corr'])
                    filter: str = ZTF_FILTERS[int(entry['fid'])]

                    if filter not in FILTERS[self.data_source]:
                        self.logger.warning(f'Invalid ZTF filter for {target.name}: {filter}')

                    # Non detections have an error of 100.
                    if magerr > 1.:
                        continue

                    else:
                        value: Dict[str, Any] = reduced_datum_value(mag=mag, filter=self.filter_name(filter),
                                                                    error=magerr, jd=mjd.jd,
                                                                    observer=self.__OBSERVER_NAME,
                                                                    facility=self.__FACILITY_NAME)

                    rd, _ = ReducedDatum.objects.get_or_create(
                        timestamp=mjd.to_datetime(timezone=TimezoneInfo()),
                        value=value,
                        source_name='ALeRCE',
                        source_location='ALeRCE',
                        data_type='photometry',
                        target=target)

                    rd.save()
                    new_points += 1

                    self.update_last_jd_and_mag(mjd.jd, mag)
            except Exception as e:
                self.logger.error(f'Error while processing reduced datapoint for {target.name} with '
                                  f'ZTF name {ztf_name}: {e}')
                continue

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.last_jd,
                                      last_mag=self.last_mag)
