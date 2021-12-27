import json
from io import StringIO
from typing import Optional, Tuple, Any, Iterable

import numpy as np
import pandas as pd
from astropy.time import Time, TimezoneInfo
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2 import settings
from bhtom2.external_service.data_source_information import DataSource, FILTERS
from bhtom2.harvesters.lightcurve.lightcurve_update import LightcurveUpdate
from bhtom2.harvesters.utils.external_service_request import query_external_service
from bhtom2.harvesters.utils.filter_name import filter_name


class GaiaLightcurveUpdate(LightcurveUpdate):
    def __init__(self):
        super().__init__(DataSource.Gaia)

        try:
            self.__base_url: str = settings.GAIA_ALERTS_PATH
        except Exception as e:
            self.logger.error(f'No GAIA_ALERTS_PATH in settings found!')

        self.__GAIA_FILTER_NAME: str = FILTERS[DataSource.Gaia][0]
        self.__filter: str = filter_name(self.__GAIA_FILTER_NAME, self.data_source.name)
        self.__FACILITY_NAME: str = "Gaia"
        self.__OBSERVER_NAME: str = "Gaia"

    def fetch_data_from_data_source(self, target: Target) -> Iterable:
        gaia_name: Optional[str] = self.get_target_name(target)

        if not gaia_name:
            self.logger.debug(f'No Gaia name for {target.name}')
            return [{}]

        lightcurve_url: str = f'{self.__base_url}/alert/{gaia_name}/lightcurve.csv'

        # Replace the first line so that the columns are properly parsed.
        # The separator must be the same as in the rest of the file!
        response: str = query_external_service(lightcurve_url, 'Gaia alerts').replace('#Date JD(TCB) averagemag',
                                                                                      'Date,JD(TCB),averagemag')

        # The data contains object name at the top- remove that since this would create a multi-index pandas dataframe
        lc_df: pd.DataFrame = pd.read_csv(StringIO(response.replace(gaia_name, '')))

        self.logger.debug(f'Updating Gaia Alerts lightcurve for {gaia_name}, target: {target.name}')

        # Remove non-numeric (e.g. NaN, untrusted) averagemags:
        lc_df = lc_df[pd.to_numeric(lc_df['averagemag'], errors='coerce').notnull()]

        return lc_df.iterrows()

    def process_row_to_reduced_datum(self, target: Target, internal_target_name: str, datum: Any) -> Tuple[
        Optional[ReducedDatum],
        bool,
        Optional[np.float64],
        Optional[np.float64]]:
        # Pandas row is a tuple: (row index, row)
        _, row = datum

        jd: np.float64 = row['JD(TCB)']
        mag: np.float64 = np.float64(row['averagemag'])

        datum_jd = Time(jd, format='jd', scale='utc')
        value = {
            'magnitude': mag,
            'filter': self.__filter,
            'error': 0,  # for now
            'jd': datum_jd.jd
        }

        rd, created = ReducedDatum.objects.get_or_create(
            timestamp=datum_jd.to_datetime(timezone=TimezoneInfo()),
            value=json.dumps(value),
            source_name='GaiaAlerts',
            source_location=f'{self.__base_url}/alert/{internal_target_name}/lightcurve.csv',
            data_product=self.get_dataproduct(target, self.__filter,
                                              self.__FACILITY_NAME,
                                              self.__OBSERVER_NAME),
            data_type='photometry',
            target=target)

        return rd, created, datum_jd.value, mag
