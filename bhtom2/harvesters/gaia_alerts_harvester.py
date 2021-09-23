import json
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Optional, Dict, Any

import os
import os.path
from django.conf import settings

import pandas as pd
from astropy import units as u
from astropy.coordinates import get_sun, SkyCoord
from astropy.time import Time, TimezoneInfo
from django.core.exceptions import ObjectDoesNotExist
from tom_catalogs.harvester import AbstractHarvester
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.alert_services import AlertSource, alert_target_name, alert_source_name
from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.harvesters.utils.external_service_request import query_external_service
from bhtom2.models.reduced_datum_extra import ReducedDatumExtraData, refresh_reduced_data_view
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.observation_data_extra_data_utils import ObservationDatapointExtraData

ALERT_SOURCE: AlertSource = AlertSource.GAIA
GAIA_ALERTS_CACHE_PATH: str = os.path.join(settings.BASE_DIR, "cache/gaia_alerts.csv")

logger: BHTOMLogger = BHTOMLogger(__name__, '[Gaia Alerts Harvester]')

base_url = 'http://gsaweb.ast.cam.ac.uk/alerts'


# Fetch CSV containing all alerts and save it to file (so that it doesn't have to be fetched every single request)
def fetch_alerts_csv() -> str:
    gaia_alerts_response: str = query_external_service(f'{base_url}/alerts.csv', 'Gaia alerts')
    # Update Gaia alerts cache file
    with open(GAIA_ALERTS_CACHE_PATH, 'w') as f:
        f.write(gaia_alerts_response)

    return gaia_alerts_response


def search_term_in_gaia_data(term: str) -> pd.DataFrame:
    from io import StringIO

    # Check if the cache file exists
    if os.path.exists(GAIA_ALERTS_CACHE_PATH):
        gaia_data: pd.DataFrame = pd.read_csv(str(GAIA_ALERTS_CACHE_PATH))

        try:
            term_data: pd.DataFrame = gaia_data.loc[gaia_data['#Name'].str.lower() == term.lower()]
        except KeyError:
            os.remove(GAIA_ALERTS_CACHE_PATH)
            raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

        if len(term_data.index) > 0:
            target_data: pd.DataFrame = term_data.iloc[0]
            return target_data

    # Term is not found or the CSV file doesn't exist, so CSV needs to be updated
    new_gaia_data = pd.read_csv(StringIO(fetch_alerts_csv()))

    try:
        term_data: pd.DataFrame = new_gaia_data.loc[new_gaia_data['#Name'].str.lower() == term.lower()]
    except KeyError:
        os.remove(GAIA_ALERTS_CACHE_PATH)
        raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

    if len(term_data.index) > 0:
        target_data: pd.DataFrame = term_data.iloc[0]
        return target_data
    else:
        raise NoResultException(f'No result for {term_data} in Gaia Alerts!')


# Queries alerts.csv and searches for the name
# then also loads the light curve
def get(term: str):
    term_data: pd.DataFrame = search_term_in_gaia_data(term)

    # Gaia Alerts data have the columns in format:
    # #Name, RaDeg, DecDeg, ...
    # so the spaces are mandatory in column names if not preprocessed before
    catalog_data: Dict[str, Any] = {
        alert_target_name[AlertSource.GAIA]: term_data["#Name"],
        "ra": Decimal(term_data[" RaDeg"]),
        "dec": Decimal(term_data[" DecDeg"]),
        "disc": term_data[" Date"],
        "classif": term_data[" Class"]
    }

    # TODO: add other things?

    return catalog_data


class GaiaAlertsHarvester(AbstractHarvester):
    name = 'Gaia Alerts'

    def query(self, term):
        self.catalog_data = get(term)

    def to_target(self) -> Optional[Target]:
        # catalog_data contains now all fields needed to create a target
        target = super().to_target()

        gaia_name: str = self.catalog_data[alert_target_name[AlertSource.GAIA]]
        ra: str = self.catalog_data["ra"]
        dec: str = self.catalog_data["dec"]
        disc: str = self.catalog_data["disc"]
        classif: str = self.catalog_data["classif"]

        # Checking if the object already exists in our DB
        try:
            t0: Target = Target.objects.get(name=gaia_name)

            # TODO: add update?

            return t0
        except ObjectDoesNotExist:
            logger.error(f'Target {gaia_name} not found in the database.')
            pass

        try:
            # Creating a target object
            target.type = 'SIDEREAL'
            target.name = gaia_name
            target.ra = ra
            target.dec = dec
            target.epoch = 2000

            target.gaia_alert_name = gaia_name
            target.jdlastobs = 0.
            target.priority = 0.
            target.classification = classif
            target.discovery_date = disc
            target.ztf_alert_name = ''
            target.calib_server_name = ''
            target.cadence = 1.

            # TODO: extra fields?

            logger.info(f'Successfully created target {gaia_name}')

        except Exception as e:
            logger.error(f'Exception while creating object {gaia_name}: {e}')

        return target


# Reads light curve from Gaia Alerts - used in updatereduceddata_gaia
# this also updates the SUN separation
# if update_me == false, only the SUN position gets updated, not the LC

def update_gaia_lc(target: Target):
    from .utils.last_jd import update_last_jd

    # Updating sun separation
    sun_pos = get_sun(Time(datetime.utcnow()))
    obj_pos = SkyCoord(target.ra, target.dec, unit=u.deg)

    sun_sep = sun_pos.separation(obj_pos).deg
    target.save(extras={'Sun_separation': sun_sep})
    logger.debug(f'New Sun separation for target {target.name}: {sun_sep}')

    # Deciding whether to update the light curves or not
    try:
        dont_update_me: Optional[bool] = target.extra_fields.get('dont_update_me')
    except Exception as e:
        dont_update_me: Optional[bool] = None
        logger.error(f'Exception occured when accessing dont_update_me field for {target}: {e}')

    if dont_update_me:
        logger.debug(f'Target {target.name} not updated because of dont_update_me = true')
        return

    # Updating the LC - target has to have the gaia_name value
    try:
        gaia_name: Optional[str] = target.gaia_alert_name
    except Exception as e:
        logger.error(f'Error while accessing gaia name for {target.name}: {e}')
        return None

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

        jdmax: float = 0.0
        maglast: float = 0.0

        for _, row in lc_df.iterrows():
            try:
                jd: float = row['JD(TCB)']
                mag: float = float(row['averagemag'])

                # Update last magnitude
                if jd > jdmax:
                    jdmax = jd
                    maglast = mag

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
                    data_type='photometry',
                    target=target)

                rd.save()
                rd_extra_data, _ = ReducedDatumExtraData.objects.update_or_create(
                    reduced_datum=rd,
                    defaults={'extra_data': ObservationDatapointExtraData(
                        facility_name="Gaia",
                        owner="Gaia"
                    ).to_json_str()}
                )
                rd_extra_data.save()

            except Exception as e:
                logger.error(f'Error while updating LC for target {target.name}: {e}')

        refresh_reduced_data_view()

        # Updating/storing the last JD
        update_last_jd(target=target,
                       mag=maglast,
                       jd=jdmax)

        logger.info(f'Finished updating Gaia LC for {gaia_name}, target: {target.name}')
