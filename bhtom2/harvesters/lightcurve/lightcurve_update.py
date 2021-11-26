from typing import Optional

from tom_targets.models import Target

from bhtom2.harvesters.lightcurve.cpcs_lightcurve import update_cpcs_lc
from bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve import update_gaia_lc
from bhtom2.models.view_reduceddatum import refresh_reduced_data_view
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[Lightcurve Update for Target]')


def update_lightcurve_for_target(target: Target):
    """
    Update all lightcurves for the requested target.
    Target must have the names for respective catalogs filled in.

    :param target: target to update the lightcurves for
    :return: void
    """

    from ..utils.last_jd import update_last_jd

    # Deciding whether to update the light curves or not
    try:
        dont_update_me: Optional[bool] = target.extra_fields.get('dont_update_me')
    except Exception as e:
        dont_update_me: Optional[bool] = None
        logger.error(f'Exception occurred when accessing dont_update_me field for {target}: {e}')

    if dont_update_me:
        logger.debug(f'Target {target.name} not updated because of dont_update_me = true')
        return

    last_jd: Optional[float] = 0.0

    # We just note the last magnitude from Gaia - to assure it's always the same filter
    gaia_last_mag: Optional[float] = None

    # Update Gaia lightcurves
    try:
        gaia_last_jd, gaia_last_mag = update_gaia_lc(target)

        if gaia_last_jd and gaia_last_jd > last_jd:
            last_jd = gaia_last_jd

    except Exception as e:
        logger.error(f'Error while updating Gaia LC for target {target.name}: {e}')

    # Update CPCS lightcurves
    try:
        cpcs_last_jd, _ = update_cpcs_lc(target)

        if cpcs_last_jd and cpcs_last_jd > last_jd:
            last_jd = cpcs_last_jd

    except Exception as e:
        logger.error(f'Error while updating CPCS LC for target {target.name}: {e}')

    if last_jd > 0.0:
        update_last_jd(target, jd=last_jd, mag=gaia_last_mag)

    # Update CPCS lightcurves

    refresh_reduced_data_view()
