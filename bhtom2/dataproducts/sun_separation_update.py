from datetime import datetime
from typing import Optional, Any

from astropy import units as u
from astropy.coordinates import get_sun, SkyCoord
from astropy.time import Time
from bhtom_base.bhtom_targets.models import Target

from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[Sun Separation Update for Target]')


def update_sun_separation(target: Target) -> Optional[float]:
    """
    Update sun separation for the requested target.

    :param target: target to update the sun separation for
    :return sun_separation: new sun_separation, None if unsuccessful
    """
    # Updating sun separation

    sun_pos: Any = get_sun(Time(datetime.utcnow()))
    obj_pos: SkyCoord = SkyCoord(target.ra, target.dec, unit=u.deg)

    sun_sep = sun_pos.separation(obj_pos).deg

    try:
        target.save(extras={'sun_separation': sun_sep})
    except Exception as e:
        logger.error(f'Error when saving new sun separation {sun_sep} for target {target.name}: {e}')
        return None

    logger.debug(f'New Sun separation for target {target.name}: {sun_sep}')
    return sun_sep
