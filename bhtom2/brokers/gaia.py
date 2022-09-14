from typing import Optional

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord, ICRS
from astropy.time import Time
from astroquery.gaia import Gaia
from django import forms
from django.db import transaction

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom_base.bhtom_alerts.alerts import GenericQueryForm
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import TargetName


def gaia_time_to_bjd(tcb_time: float) -> float:
    return tcb_time + 55197


def mag_error(flux_over_error: float) -> float:
    return 1 / (flux_over_error * 2.5 / np.log(10))


def rescale_mag_error(mag: float, mag_error: float, passband: str = 'G') -> float:
    if passband == 'G':
        if mag < 13.5:
            mag = 13.5
        new_mag_error: float = np.sqrt(30) * np.power(10, 0.17 * mag - 5.1)
        return np.sqrt(mag_error ** 2 + new_mag_error ** 2)
    else:
        return 10 * mag_error


class GaiaQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class GaiaBroker(BHTOMBroker):
    name = DataSource.GAIA_DR3.name
    form = GaiaQueryForm

    def __init__(self):
        super().__init__(DataSource.GAIA_DR3)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "Gaia"
        self.__OBSERVER_NAME: str = "Gaia"

        self.__target_name_key: str = TARGET_NAME_KEYS[self.data_source]

        self.__update_cadence = None
        self.__cross_match_max_separation = 0.5 * u.arcsec

    def download_dr3_lightcurve(self, source_id: str) -> pd.DataFrame:
        data_structure = 'INDIVIDUAL'  # Options are: 'INDIVIDUAL', 'COMBINED', 'RAW'
        data_release = 'Gaia DR3'  # Options are: 'Gaia DR3' (default), 'Gaia DR2'

        self.logger.debug(f'Fetching DR3 lightcurve for target with DR3 source {source_id}')

        datalink = Gaia.load_data(ids=[str(source_id)],
                                  data_release=data_release,
                                  retrieval_type='EPOCH_PHOTOMETRY',
                                  data_structure=data_structure,
                                  verbose=False, output_file=None)
        dl_keys = [inp for inp in datalink.keys()]
        dl_keys.sort()

        self.logger.debug(f'len{dl_keys} lightcurves found.')
        if len(dl_keys) == 0:
            return pd.DataFrame()

        return datalink[dl_keys[0]][0].to_table().to_pandas()

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:
        dr3_id: Optional[str] = self.get_target_name(target)

        self.logger.debug(f'Searching for DR3 lightcurve for DR3 id {dr3_id} (target {target.name})...')

        if not dr3_id:

            coord = SkyCoord(ra=target.ra * u.degree,
                             dec=target.dec * u.degree,
                             frame=ICRS)

            try:
                result = Gaia.query_object_async(coordinate=coord,
                                                 width=self.cross_match_max_separation,
                                                 height=self.cross_match_max_separation).to_pandas().sort_values(
                    by=['dist'])['source_id']
                if len(result) > 0:
                    dr3_id = result[0]
                    TargetName.objects.create(target=target, source_name=DataSource.GAIA_DR3.name, name=dr3_id)
            except Exception as e:
                self.logger.error(f'Error when querying Gaia DR3 for {target.name}: {e}')
                return return_for_no_new_points()

        lightcurve: pd.DataFrame = self.download_dr3_lightcurve(dr3_id)

        if len(lightcurve) == 0:
            self.logger.info(f'No lightcurves downloaded for Gaia DR3 for target {target.name}')
            return return_for_no_new_points()

        lightcurve['time_bjd'] = gaia_time_to_bjd(lightcurve['time'])
        lightcurve['mag_err'] = mag_error(lightcurve['flux_over_error'])

        try:
            reduced_datums = [ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=Time(datum['time_bjd'], format='mjd').to_datetime(),
                                           mjd=datum['time_bjd'],
                                           value=datum['mag'],
                                           source_name=self.name,
                                           source_location='Gaia TAP+',
                                           error=datum['mag_err'],
                                           filter=self.filter_name(datum['band']),
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME)
                              for _, datum in lightcurve.iterrows()]  # Inline loop
            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()

        return LightcurveUpdateReport(new_points=new_points)
