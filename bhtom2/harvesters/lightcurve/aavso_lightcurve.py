from io import StringIO
from typing import List, Optional, Tuple

import pandas as pd
import requests as req
from astropy.time import Time, TimezoneInfo
from django.conf import settings
from django.core.cache import cache
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.models.reduced_datum_extra import ReducedDatumExtraData, refresh_reduced_data_view
from bhtom2.utils.observation_data_extra_data_utils import ObservationDatapointExtraData
from bhtom2.utils.bhtom_logger import BHTOMLogger


logger: BHTOMLogger = BHTOMLogger(__name__, '[AAVSO data fetch]')

ACCEPTED_VALID_FLAGS: List[str] = ['V', 'Z']
# V - fully validated
# Z - passed automatic validation tests

FILTERS: List[str] = ['V', 'I', 'R']

SOURCE_NAME: str = 'AAVSO'

timezone_info: TimezoneInfo = TimezoneInfo()


def fetch_aavso_photometry(target: Target,
                           from_time: Optional[Time] = None,
                           to_time: Time = Time.now(),
                           delimiter: str = "~") -> Tuple[Optional[pd.DataFrame], Optional[int]]:
    target_name: str = target.name
    target_id: int = target.pk

    logger.info(f'Fetching AAVSO photometry for {target_name}...')

    params = {
        "view": "api.delim",
        "ident": target_name,
        "tojd": to_time.jd,
        "fromjd": from_time.jd if from_time else 0,
        "delimiter": delimiter
    }
    result = req.get(settings.AAVSO_DATA_FETCH_URL, params=params)
    status_code: Optional[int] = getattr(result, 'status_code', None)

    if status_code and getattr(result, 'text', None):
        buffer: StringIO = StringIO(str(result.text))
        result_df: pd.DataFrame = filter_data(pd.read_csv(buffer,
                                                          sep=delimiter,
                                                          index_col=False,
                                                          error_bad_lines=False))

        logger.info(f'AAVSO returned {len(result_df.index)} rows for {target_name}')

        for i, row in result_df.iterrows():
            save_row_to_db(target_id, row, settings.AAVSO_DATA_FETCH_URL)

        logger.info(f'Saved {len(result_df.index)} rows of AAVSO data for {target_name}')

        cache.set(f'{target_id}_aavso', result_df.JD.max())
        refresh_reduced_data_view()

        return result_df, result.status_code
    elif status_code:
        logger.error(f'AAVSO returned status code {status_code} for {target_name}')
        return None, status_code
    else:
        logger.error(f'AAVSO returned no status code for {target_name}')
        return None, None


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df.obsType == 'CCD']\
        .loc[df.val.isin(ACCEPTED_VALID_FLAGS)]\
        .loc[df.band.isin(FILTERS)]


def save_row_to_db(target_id: int,
                   row: pd.Series,
                   url: str):
    rd, _ = ReducedDatum.objects.get_or_create(
        data_type="photometry",
        source_name=SOURCE_NAME,
        source_location=url,
        timestamp=Time(row["JD"], format="jd", scale="utc").to_datetime(timezone=timezone_info),
        value=to_json_value(row),
        target_id=target_id
    )

    obs_affil: str = row["obsAffil"]
    obs_name: str = row["obsName"]

    if obs_affil or obs_name:
        rd_extra_data, _ = ReducedDatumExtraData.objects.update_or_create(
            reduced_datum=rd,
            defaults={'extra_data': ObservationDatapointExtraData(facility_name=obs_affil,
                                                                  owner=obs_name).to_json_str()}
        )
    return rd


def to_json_value(row: pd.Series):
    import json
    return json.dumps({
        "magnitude": row["mag"],
        "filter": "%s/AAVSO" % row["band"],
        "error": row["uncert"],
        "jd": row["JD"]
    })
