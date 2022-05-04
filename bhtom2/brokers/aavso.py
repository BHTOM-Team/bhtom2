from datetime import datetime
from io import StringIO
from typing import Optional, Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from astropy.time import TimezoneInfo, Time
from django.conf import settings
from django.db import transaction

from bhtom_dataproducts.models import ReducedDatum, DatumValue
from bhtom_targets.models import Target

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.data_source_information import DataSource, AAVSO_ACCEPTED_FLAGS, FILTERS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[AAVSO data fetch]')

DATA_SOURCE: DataSource = DataSource.AAVSO

timezone_info: TimezoneInfo = TimezoneInfo()


class AAVSOBroker(BHTOMBroker):

    name = DataSource.AAVSO.name
    form = None

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

    def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:
        aavso_name: Optional[str] = self.get_target_name(target)

        if not aavso_name:
            self.logger.debug(f'No AAVSO name for {target.name}')
            return return_for_no_new_points()

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

        new_points: int = 0
        data: List[Tuple[datetime, DatumValue]] = []

        for entry in result_df.iterrows():

            try:
                # Pandas row is a tuple: (row index, row)
                _, row = entry

                mag: np.float64 = np.float64(row['mag'])

                jd: np.float64 = np.float64(row["JD"])
                datum_jd = Time(jd, format="jd", scale="utc")

                filter: str = self.filter_name(row["band"])

                data.append((datum_jd.to_datetime(timezone=TimezoneInfo()),
                             DatumValue(mjd=datum_jd.mjd,
                                        value=mag,
                                        filter=filter,
                                        error=row["uncert"],
                                        observer=row["obsName"],
                                        facility=row["obsAffil"])))

                self.update_last_jd_and_mag(jd, mag)

            except Exception as e:
                self.logger.error(f'Error while processing reduced datapoint for {target.name} '
                                  f'with AAVSO name {aavso_name}: {e}')

        try:
            data = list(set(data))
            reduced_datums = [ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=datum[0],
                                           mjd=datum[1].mjd,
                                           value=datum[1].value,
                                           source_name=self.data_source.name,
                                           source_location=self.__base_url,
                                           error=datum[1].error,
                                           filter=datum[1].filter,
                                           observer=datum[1].observer,
                                           facility=datum[1].facility) for datum in data]
            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums))

        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name} '
                              f'with AAVSO name {aavso_name}: {e}')

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.last_jd,
                                      last_mag=self.last_mag)
