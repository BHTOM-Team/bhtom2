import json
from io import StringIO
from typing import Optional, Tuple, Iterable, Any

import numpy as np
import pandas as pd
from astropy.time import TimezoneInfo, Time
from django.conf import settings
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.external_service.data_source_information import DataSource, AAVSO_ACCEPTED_FLAGS, FILTERS
from bhtom2.brokers.lightcurve_update import LightcurveUpdate
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.external_service.filter_name import filter_name
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[AAVSO data fetch]')

DATA_SOURCE: DataSource = DataSource.AAVSO

timezone_info: TimezoneInfo = TimezoneInfo()


class AAVSOLightcurveUpdate(LightcurveUpdate):
    def __init__(self):
        super().__init__(DataSource.AAVSO)

        try:
            self.__base_url: str = settings.AAVSO_API_PATH
        except Exception as e:
            self.logger.error(f'No AAVSO_API_PATH in settings found!')

        self.__QUERY_FOV: int = 60
        self.__MAG_LIMIT: float = 25.

    def filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.loc[df.obsType == 'CCD'] \
            .loc[df.val.isin(AAVSO_ACCEPTED_FLAGS)] \
            .loc[df.band.isin(FILTERS[self.data_source])]

    def fetch_data_from_data_source(self, target: Target) -> Iterable:
        aavso_name: Optional[str] = self.get_target_name(target)

        if not aavso_name:
            self.logger.debug(f'No AAVSO name for {target.name}')
            return [{}]

        params = {
            "view": "api.delim",
            "ident": aavso_name,
            "tojd": Time.now().jd,
            "fromjd": 0,
            "delimiter": "~"
        }

        response = query_external_service(self.__base_url, params=params)

        buffer: StringIO = StringIO(str(response))
        result_df: pd.DataFrame = self.filter_data(pd.read_csv(buffer,
                                                               sep="~",
                                                               index_col=False,
                                                               error_bad_lines=False))

        return result_df.iterrows()

    def process_row_to_reduced_datum(self, target: Target, internal_target_name: str, datum: Any) -> Tuple[
        Optional[ReducedDatum],
        bool,
        Optional[np.float64],
        Optional[np.float64]]:

        # Pandas row is a tuple: (row index, row)
        _, row = datum

        mag: np.float64 = np.float64(row['mag'])

        jd: np.float64 = np.float64(row["JD"])
        datum_jd = Time(jd, format="jd", scale="utc")

        filter: str = filter_name(row["band"], self.data_source.name)

        value = {
            "magnitude": mag,
            "filter": filter,
            "error": row["uncert"],
            "jd": jd
        }

        facility: str = row["obsAffil"]
        observer: str = row["obsName"]

        rd, created = ReducedDatum.objects.get_or_create(
            timestamp=datum_jd.to_datetime(timezone=TimezoneInfo()),
            value=json.dumps(value),
            source_name=self.data_source.name,
            source_location=f'{self.__base_url}',
            data_product=self.get_dataproduct(target,
                                              filter,
                                              facility,
                                              observer),
            data_type='photometry',
            target=target)

        return rd, created, jd, mag
