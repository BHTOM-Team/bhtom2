import json
from typing import Optional, Dict, Any

import numpy as np

from tom_dataproducts.models import ReducedDatum

from tom_targets.models import Target
from astropy.time import Time, TimezoneInfo

from .utils.filter_name import filter_name
from .utils.last_jd import update_last_jd
from .utils.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger

from bhtom2.models.reduced_datum_extra import ReducedDatumExtraData, refresh_reduced_data_view
from ..utils.observation_data_extra_data_utils import ObservationDatapointExtraData
from django.conf import settings

CPCS_BASE_URL: str = settings.CPCS_BASE_URL
CPCS_DATA_ACCESS_HASHTAG: Optional[str] = settings.CPCS_DATA_ACCESS_HASHTAG

logger: BHTOMLogger = BHTOMLogger(__name__, '[CPCS data fetch]')


def mag_error_with_calib_error(magerr: float, caliberr: float) -> float:
    return np.sqrt(magerr * magerr + caliberr * caliberr)


def update_cpcs_lc(target: Target):
    try:
        cpcs_name: Optional[str] = target.calib_server_name
    except Exception as e:
        cpcs_name: Optional[str] = None
        logger.error(f'Error while accessing calib_server_name for {target}: {e}')
    if cpcs_name:

        response: str = query_external_service(f'{CPCS_BASE_URL}/get_alert_lc_data?alert_name={cpcs_name}',
                                               'CPCS', cookies={'hashtag': CPCS_DATA_ACCESS_HASHTAG})
        lc_data: Dict[str, Any] = json.loads(response)

        print(lc_data)

        for mjd, magerr, observatory, caliberr, mag, catalog, filter, id in zip(
                lc_data['mjd'], lc_data['magerr'], lc_data['observatory'], lc_data['caliberr'], lc_data['mag'],
                lc_data['catalog'], lc_data['filter'], lc_data['id']
        ):
            try:
                # Errors are marked with magerr==-1 in CPCS
                if float(magerr) == -1:
                    continue

                jd: float = float(mjd) + 2400000.5
                timestamp: Time = Time(jd, format='jd', scale='utc')

                # Adding calibration error in quad
                magerr_with_caliberr: float = mag_error_with_calib_error(float(magerr),
                                                                         float(caliberr))

                value: str = json.dumps({
                    'magnitude': float(mag),
                    'filter': filter_name(filter, catalog),
                    'error': magerr_with_caliberr,
                    'jd': timestamp.jd
                })

                rd, created = ReducedDatum.objects.get_or_create(
                    timestamp=timestamp.to_datetime(timezone=TimezoneInfo()),
                    value=value,
                    source_name='CPCS',
                    source_location=f'{CPCS_BASE_URL}/get_alert_lc_data?alert_name={cpcs_name}&{id}',
                    data_type='photometry',
                    target=target
                )

                rd.save()

                rd_extra_data, _ = ReducedDatumExtraData.objects.update_or_create(
                    reduced_datum=rd,
                    defaults={'extra_data': ObservationDatapointExtraData(
                        facility_name=observatory,
                        owner=observatory
                    ).to_json_str()}
                )

                rd_extra_data.save()

                # Updating the last observation JD
                latest_jd: float = np.max(np.array(lc_data['mjd']).astype(np.float)) + 2400000.5

                # Don't update the last mag, since we only want Gaia mag as the last mag
                update_last_jd(target, jd=latest_jd)
            except Exception as e:
                logger.error(f'Exception while saving datapoint for target {cpcs_name}: {e}')
                continue

        try:
            refresh_reduced_data_view()
        except Exception as e:
            logger.error(f'Exception while refreshing reduced data views for {cpcs_name}: {e}')

