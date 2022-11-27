import os
import os.path
from decimal import Decimal
from typing import Optional, Dict, Any

import pandas as pd
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from bhtom_base.bhtom_catalogs.harvester import AbstractHarvester
from bhtom_base.bhtom_targets.models import Target

from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger

ALERT_SOURCE: DataSource = DataSource.GAIA
GAIA_ALERTS_CACHE_PATH: str = os.path.join(settings.BASE_DIR, "bhtom2/cache/gaia_alerts.csv")

logger: BHTOMLogger = BHTOMLogger(__name__, '[Gaia Alerts Harvester]')

try:
    base_url = settings.GAIA_ALERTS_PATH
except Exception as e:
    logger.error(f'No GAIA_ALERTS_PATH in settings found!')


# Fetch CSV containing all alerts and save it to file (so that it doesn't have to be fetched every single request)
def fetch_alerts_csv() -> str:
    gaia_alerts_response: str = query_external_service(f'{base_url}/alerts/alerts.csv', 'Gaia alerts')

    # Update Gaia alerts cache file
    try:
        with open(GAIA_ALERTS_CACHE_PATH, 'w+') as f:
            f.write(gaia_alerts_response)
    except FileNotFoundError:
        logger.error(f'File {GAIA_ALERTS_CACHE_PATH} not found! Gaia alerts harvester response wasn\'t saved')

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
        TARGET_NAME_KEYS[DataSource.GAIA]: term_data["#Name"],
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

        gaia_name: str = self.catalog_data[TARGET_NAME_KEYS[DataSource.GAIA]]
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
#            logger.error(f'Target {gaia_name} not found in the database.')
            pass

        try:
            # Creating a target object
            target.type = 'SIDEREAL'
            target.name = gaia_name
            target.ra = ra
            target.dec = dec
            target.epoch = 2000
            target.jdlastobs = 0.
#            target.priority = 0.
            target.targetextra_set['priority'] = 10.

#            target.classification = classif
            target.targetextra_set['classification'] = classif

#            target.discovery_date = disc
            target.targetextra_set['discovery_date'] = disc
            target.cadence = 1.

            # TODO: extra fields?

            logger.info(f'Successfully created target {gaia_name}')

        except Exception as e:
            logger.error(f'Exception while creating object {gaia_name}: {e}')

        return target
