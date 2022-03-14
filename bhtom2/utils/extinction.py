from typing import Optional

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.ogle import Ogle
from tom_targets.models import Target

from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[Extinction calculator]')


def ogle_extinction(target: Target) -> Optional[float]:

    if (target.galactic_lng is None) or (target.galactic_lat is None):
        return None

    coordinates: SkyCoord = SkyCoord(target.galactic_lng * u.deg,
                                     target.galactic_lat * u.deg,
                                     frame='galactic')
    query_result = Ogle.query_region(coord=coordinates)

    try:
        extinction: float = query_result['E(V-I)'][0]
        if extinction == -9.999:
            return None
        return extinction
    except Exception as e:
        logger.error(f'Error while querying extinction for target {target.name}: {e}')
        return None
