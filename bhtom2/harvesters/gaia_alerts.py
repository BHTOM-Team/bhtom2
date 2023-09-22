import os
import os.path
from decimal import Decimal, getcontext
from numpy import around, sqrt
from typing import Optional, Dict, Any

import pandas as pd
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from bhtom_base.bhtom_catalogs.harvester import AbstractHarvester, MissingDataException
from bhtom_base.bhtom_targets.models import Target, TargetExtra

from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger

from astropy.coordinates import Angle, SkyCoord

ALERT_SOURCE: DataSource = DataSource.GAIA_ALERTS
GAIA_ALERTS_CACHE_PATH: str = os.path.join(settings.BASE_DIR, "bhtom2/cache/gaia_alerts.csv")

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: Gaia Alerts Harvester')

try:
    base_url = settings.GAIA_ALERTS_PATH
except Exception as e:
    logger.error(f'No GAIA_ALERTS_PATH in settings found!')


# Fetch CSV containing all alerts and save it to file (so that it doesn't have to be fetched every single request)
def fetch_alerts_csv() -> str:
    gaia_alerts_response: str = query_external_service(f'{base_url}/alerts/alerts.csv', 'Gaia alerts')

    # Update Gaia alerts cache file
    try:
        with open(GAIA_ALERTS_CACHE_PATH, 'w+', encoding='utf-8') as f:
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

    try:
        new_gaia_data = pd.read_csv(StringIO(fetch_alerts_csv()))
        term_data: pd.DataFrame = new_gaia_data.loc[new_gaia_data['#Name'].str.lower() == term.lower()]
    except KeyError:
#        os.remove(GAIA_ALERTS_CACHE_PATH)
        raise InvalidExternalServiceResponseException(f'Nothing found in Gaia Alerts.')


    if len(term_data.index) > 0:
        target_data: pd.DataFrame = term_data.iloc[0]
        return target_data
    else:
        raise MissingDataException(f'No result for {term} in Gaia Alerts!')

#performs a cone search on Gaia CSV file - TODO: is there an API for Gaia Alerts to do that?
#returns the name of the target if present
def cone_search(coordinates:SkyCoord, radius:Angle):
    from io import StringIO
    import astropy.units as u

    # Check if the cache file exists
    if os.path.exists(GAIA_ALERTS_CACHE_PATH):
        logger.debug("Using cashed Gaia Alerts csv file in cone_search for Gaia Alert name")
        gaia_data: pd.DataFrame = pd.read_csv(str(GAIA_ALERTS_CACHE_PATH))
        gaia_data["diff"] = ((sqrt((gaia_data[" RaDeg"]-coordinates.ra)**2)+((gaia_data[" DecDeg"]-coordinates.dec)**2))<radius.degree)

        try:
            term_data: pd.DataFrame = gaia_data.loc[gaia_data['diff'] == True]
        except KeyError:
            os.remove(GAIA_ALERTS_CACHE_PATH)
            raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

        if len(term_data.index) > 0:
            target_data: pd.DataFrame = term_data.iloc[0]
            return target_data

    # Term is not found or the CSV file doesn't exist, so CSV needs to be updated
    new_gaia_data = pd.read_csv(StringIO(fetch_alerts_csv()))

    #simple cone search, computing the difference in coordinates column
    new_gaia_data["diff"] = ((sqrt((new_gaia_data[" RaDeg"]-coordinates.ra)**2)+((new_gaia_data[" DecDeg"]-coordinates.dec)**2))<radius.degree)
#    new_gaia_data.sort_values(by=['diff'], inplace=True)

    try:
        term_data: pd.DataFrame = new_gaia_data.loc[new_gaia_data['diff'] == True]
    except KeyError:
        os.remove(GAIA_ALERTS_CACHE_PATH)
        raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

    if len(term_data.index) > 0:
        target_data: pd.DataFrame = term_data.iloc[0]
        return target_data
    else:
        logger.info('Cone Search returned no results in Gaia Alerts!')
        return pd.DataFrame() #empty data frame returned

# Queries alerts.csv and searches for the name
# then also loads the light curve
def get(term: str):
    term_data: pd.DataFrame = search_term_in_gaia_data(term)

    # Gaia Alerts data have the columns in format:
    # #Name, RaDeg, DecDeg, ...
    # so the spaces are mandatory in column names if not preprocessed before
#    getcontext().prec = 12

    catalog_data: Dict[str, Any] = {
        TARGET_NAME_KEYS[DataSource.GAIA_ALERTS]: term_data["#Name"],
        "ra": (term_data[" RaDeg"]), #dropping Decimal (LW), returning string
        "dec": (term_data[" DecDeg"]), #dropping Decimal (LW), returning string
        "disc": term_data[" Date"],
        "classif": term_data[" Class"]
    }

    return catalog_data


class GaiaAlertsHarvester(AbstractHarvester):
    name = 'Gaia Alerts'

    def query(self, term):
        self.catalog_data = get(term)
        return self.catalog_data

    def to_target(self) -> Optional[Target]:
        # catalog_data contains now all fields needed to create a target
        target = super().to_target()

        gaia_name: str = self.catalog_data[TARGET_NAME_KEYS[DataSource.GAIA_ALERTS]]
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

#             te, _ = TargetExtra.objects.update_or_create(target=target,
#                 key='importance',
#                 defaults={'value': 10})
# #            te.save() #LW: this will never work, as the target is not written into db yet.
#                         # so we either pass these params elsewhere or change the model
#                         # for target to include those fields and not in extras.
#             target.targetextra_set['importance'] = 9.99

# #            target.classification = classif
# #            target.targetextra_set['classification'] = classif
#             te, _ = TargetExtra.objects.update_or_create(target=target,
#                 key='classification',
#                 defaults={'value': classif})
# #            te.save()

# #            target.discovery_date = disc
# #            target.targetextra_set['discovery_date'] = disc
#             te, _ = TargetExtra.objects.update_or_create(target=target,
#                 key='discovery_date',
#                 defaults={'value': disc})
# #            te.save()

#             te, _ = TargetExtra.objects.update_or_create(target=target,
#                 key='cadence',
#                 defaults={'value': 1})
# #            te.save()


            # the name passing is done in hooks in the coords search
            # but that one is again a search in csv, so we do it twice!
            # te, _ = TargetExtra.objects.update_or_create(target=target,
            #     key=TARGET_NAME_KEYS[DataSource.GAIA],
            #     defaults={'value': gaia_name})
 #           te.save()

            #TNSId is also in the csv! use it

            logger.info(f'Successfully created target {gaia_name}')

        except Exception as e:
            logger.error(f'Exception while creating object {gaia_name}: {e}')

        return target

    def to_extras(self) -> Dict[str,str]:

        gaia_name: str = self.catalog_data[TARGET_NAME_KEYS[DataSource.GAIA_ALERTS]]
        ra: str = self.catalog_data["ra"]
        dec: str = self.catalog_data["dec"]
        disc: str = self.catalog_data["disc"]
        classif: str = self.catalog_data["classif"]

        extras : Dict[str] = {}
        extras["classification"] = classif
        extras["importance"] = str(9.99)
        extras["discovery_date"] = disc
        extras["cadence"] = str(1.0)

        return extras
