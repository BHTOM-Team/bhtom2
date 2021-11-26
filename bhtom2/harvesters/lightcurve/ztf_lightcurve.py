import json
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import requests
from ztfquery import query
from astropy.time import Time, TimezoneInfo
from tom_dataproducts.models import ReducedDatum

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.observation_data_extra_data_utils import ObservationDatapointExtraData

logger: BHTOMLogger = BHTOMLogger(__name__, '[ZTF Alerts Harvester]')


MARS_URL: str = 'https://mars.lco.global/'
ZTF_OBSERVATORY_NAME: str = 'Palomar'

filters: Dict[int, str] = {1: 'g_ZTF', 2: 'r_ZTF', 3: 'i_ZTF'}


def update_ztf_lc(target, requesting_user_id) -> Tuple[Optional[float],
                                                       Optional[float]]:
    """
    Read light curve from ZTF

    :param target: target to update the ZTF lightcurve for
    :return last_jd, last_mag: (JD of the last observation, mag of the last observation), (None, None) if no new lightcurve points
    """

    # Probably you don't need ZTF name!
    try:
        ztf_name: Optional[str] = target.extra_fields.get('ztf_alert_name')
    except Exception as e:
        logger.error(f'Error while accessing ztf_alert_name for {target}: {e}')
        return None, None

    if ztf_name:
        zquery = query.ZTFQuery()

        starttime = Time("2018-05-14").jd
        # Do the Query to see what exists

        zquery.load_metadata(radec=[target.ra, target.dec], size=0.1)
        zquery.metatable
        #
        # jdarr: List[float] = []
        #
        # for alert in alerts:
        #     if all([key in alert['candidate'] for key in ['jd', 'magpsf', 'fid', 'sigmapsf', 'magnr', 'sigmagnr']]):
        #         jd = Time(alert['candidate']['jd'], format='jd', scale='utc')
        #         jdarr.append(jd.jd)
        #         jd.to_datetime(timezone=TimezoneInfo())
        #
        #         # adding reference flux to the difference psf flux
        #         zp = 30.0
        #         m = alert['candidate']['magpsf']
        #         r = alert['candidate']['magnr']
        #         f = 10 ** (-0.4 * (m - zp)) + 10 ** (-0.4 * (r - zp))
        #         mag = zp - 2.5 * np.log10(f)
        #
        #         er = alert['candidate']['sigmagnr']
        #         em = alert['candidate']['sigmapsf']
        #         emag = np.sqrt(er ** 2 + em ** 2)
        #
        #         value = {
        #             'magnitude': mag,
        #             'filter': filters[alert['candidate']['fid']],
        #             'error': emag,
        #             'jd': jd.jd
        #         }
        #         rd, created = ReducedDatum.objects.get_or_create(
        #             timestamp=jd.to_datetime(timezone=TimezoneInfo()),
        #             value=json.dumps(value),
        #             source_name='ZTF',
        #             source_location=alert['lco_id'],
        #             data_type='photometry',
        #             target=target)
        #         rd.save()
        #         rd_extra_data, _ = ReducedDatumExtraData.objects.update_or_create(
        #             reduced_datum=rd,
        #             defaults={'extra_data': ObservationDatapointExtraData(facility_name=ZTF_OBSERVATORY_NAME,
        #                                                                   owner='ZTF').to_json_str()
        #                       }
        #         )
        #
        # refresh_reduced_data_view()
        #
        # if jdarr:
        #     jdlast = np.array(jdarr).max()
        #
        #     # modifying jd of last obs
        #
        #     previousjd = 0
        #
        #     try:
        #         previousjd = float(target.targetextra_set.get(key='jdlastobs').value)
        #         logger.debug("DEBUG-ZTF prev= ", previousjd, " this= ", jdlast)
        #     except Exception as e:
        #         logger.error(f'Error while updating last JD for {target}: {e}')
        #     if (jdlast > previousjd):
        #         target.save(extras={'jdlastobs': jdlast})
        #         logger.debug("DEBUG saving new jdlast from ZTF: ", jdlast)
