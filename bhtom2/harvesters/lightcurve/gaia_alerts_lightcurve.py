import json
from io import StringIO
from typing import Optional, Tuple

from django.contrib.auth.models import User
from django.core.cache import cache

import pandas as pd
from astropy.time import Time, TimezoneInfo
from tom_dataproducts.models import ReducedDatum, DataProductGroup, DataProduct
from tom_observations.models import ObservationGroup, ObservationRecord
from tom_targets.models import Target

from bhtom2 import settings
from bhtom2.alert_services import AlertSource, alert_source_name
from bhtom2.harvesters.utils.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.observation_data_extra_data_utils import ObservationDatapointExtraData

logger: BHTOMLogger = BHTOMLogger(__name__, '[Gaia Alerts Lightcurve Update]')

try:
    base_url = settings.GAIA_ALERTS_PATH
except Exception as e:
    logger.error(f'No GAIA_ALERTS_PATH in settings found!')


def get_gaia_dataproduct_group() -> DataProductGroup:
    data_product_group, created = DataProductGroup.objects.get_or_create(name="Gaia")

    if created:
        data_product_group.save()

    return data_product_group


def get_gaia_observation_group(observation_record: ObservationRecord) -> ObservationGroup:
    observation_group, created = ObservationGroup.objects.get_or_create(name="Gaia",
                                                                        observation_records=observation_record)

    if created:
        observation_group.save()

    return observation_group


def get_gaia_observation_record(target: Target) -> ObservationRecord:
    observation_record, created = ObservationRecord.objects.get_or_create(name="Gaia", user=None, target=Target)

    if created:
        observation_record.save()
        get_gaia_observation_group(observation_record)

    return observation_record


def get_gaia_dataproduct(target: Target) -> DataProduct:
    from bhtom2.dataproducts.dataproduct_extra_data import encode_extra_data

    data_product, created = DataProduct.objects.get_or_create(target=Target,
                                                              group=get_gaia_dataproduct_group(),
                                                              observation_record=get_gaia_observation_record(target),
                                                              extra_data=encode_extra_data(observer="Gaia"),
                                                              data_product_type="photometry")

    if created:
        data_product.save()

    return data_product


# Reads light curve from Gaia Alerts - used in updatereduceddata_gaia
# this also updates the SUN separation
# if update_me == false, only the SUN position gets updated, not the LC

def update_gaia_lc(target: Target) -> Tuple[Optional[float],
                                            Optional[float]]:
    """
    Read light curve from Gaia Alerts

    :param target: target to update the Gaia Alerts lightcurve for
    :return last_jd, last_mag: (JD of the last observation, mag of the last observation), (None, None) if no new lightcurve points
    """

    # Updating the LC - target has to have the gaia_name value
    try:
        gaia_name: Optional[str] = target.gaia_alert_name
    except Exception as e:
        logger.error(f'Error while accessing gaia name for {target.name}: {e}')
        return None, None

    if gaia_name:

        lightcurve_url: str = f'{base_url}/alert/{gaia_name}/lightcurve.csv'

        # Replace the first line so that the columns are properly parsed.
        # The separator must be the same as in the rest of the file!
        response: str = query_external_service(lightcurve_url, 'Gaia alerts').replace('#Date JD(TCB) averagemag',
                                                                                      'Date,JD(TCB),averagemag')

        # The data contains object name at the top- remove that since this would create a multi-index pandas dataframe
        lc_df = pd.read_csv(StringIO(response.replace(gaia_name, '')))

        logger.debug(f'Updating Gaia Alerts lightcurve for {gaia_name}, target: {target.name}')

        # Remove non-numeric (e.g. NaN, untrusted) averagemags:
        lc_df = lc_df[pd.to_numeric(lc_df['averagemag'], errors='coerce').notnull()]

        last_jd: float = 0.0
        last_mag: Optional[float] = None

        gaia_data_product: DataProduct = get_gaia_dataproduct(target)

        for _, row in lc_df.iterrows():
            try:
                jd: float = row['JD(TCB)']
                mag: float = float(row['averagemag'])

                datum_jd = Time(jd, format='jd', scale='utc')
                value = {
                    'magnitude': mag,
                    'filter': 'G_Gaia',
                    'error': 0,  # for now
                    'jd': datum_jd.jd
                }

                rd, created = ReducedDatum.objects.get_or_create(
                    timestamp=datum_jd.to_datetime(timezone=TimezoneInfo()),
                    value=json.dumps(value),
                    source_name=alert_source_name[AlertSource.GAIA],
                    source_location=lightcurve_url,
                    data_product=gaia_data_product,
                    data_type='photometry',
                    target=target)

                rd.save()

                # Update last magnitude and JD
                if jd > last_jd:
                    last_jd = jd
                    last_mag = mag

            except Exception as e:
                logger.error(f'Error while updating LC for target {target.name}: {e}')
                continue

        logger.info(f'Finished updating Gaia LC for {gaia_name}, target: {target.name}')

        last_jd = last_jd if last_jd > 0.0 else None
        return last_jd, last_mag

    return None, None
