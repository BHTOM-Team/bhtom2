from bhtom_targets.models import Target
import logging
from typing import Optional
from sentry_sdk import capture_exception


logger: logging.Logger = logging.getLogger(__name__)


def update_last_jd(target: Target,
                   jd: Optional[float] = None,
                   mag: Optional[float] = None):
    '''
    Update JD of the last observation for the target if the passed observation has been the latest one
    :param target:
    :param mag: Magnitude of the observation
    :param jd: JD of the observation
    :return:
    '''

    try:
        # Get the latest JD saved in the database
        previous_jd = target.extra_fields.get('last_jd')

        if jd and (previous_jd is None or jd > previous_jd):
            target.save(extras={'last_jd': jd})
            logger.debug(f'Saving new latest JD for {target}: {jd}')

            if mag:
                target.save(extras={'last_mag': mag})
                logger.debug(f'Saving new latest magnitude for {target}: {mag}')
    except Exception as e:
        logger.error(f'Error while updating last JD and magnitude for {target}: {e}')
        capture_exception(e)
