import os
import os.path
from decimal import Decimal, getcontext
from numpy import around, sqrt
from typing import Optional, Dict, Any
import requests

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

ALERT_SOURCE: DataSource = DataSource.OGLE_EWS
OGLE_EWS_CACHE_FILE: str = os.path.join(settings.BASE_DIR, "bhtom2/cache/ogle_lenses.txt")

logger: BHTOMLogger = BHTOMLogger(__name__, '[OGLE EWS Harvester]')


# Fetch CSV containing all alerts and save it to file (so that it doesn't have to be fetched every single request)
def fetch_alerts_csv():
    # Update OGLE EWS cache file
    try:
        download_all_ews(OGLE_EWS_CACHE_FILE)
    except Exception as e:
        logger.error(f'Error downloading OGLE EWS data from web! {e}')



def search_term_in_ogleews_data(term: str) -> pd.DataFrame:
    from io import StringIO

    # Check if the cache file exists
    if os.path.exists(OGLE_EWS_CACHE_FILE):
        try:
            ogle_data: pd.DataFrame = pd.read_csv(str(OGLE_EWS_CACHE_FILE), header=None, names=['name','field','starno','ra', 'dec'])
            term_data: pd.DataFrame = ogle_data.loc[ogle_data['name'].str.lower() == term.lower()]
            if len(term_data.index) > 0:
                target_data: pd.DataFrame = term_data.iloc[0]
                return target_data
        except :
#            raise InvalidExternalServiceResponseException(f'OGLE EWS didn\'t return a valid csv file!')
            logger.error(f'OGLE EWS target not found, downloading again.')


    # Term is not found or the CSV file doesn't exist, so CSV needs to be updated
    fetch_alerts_csv()
    new_ogle_data: pd.DataFrame = pd.read_csv(str(OGLE_EWS_CACHE_FILE), header=None, names=['name','field','starno','ra', 'dec'])

    try:
        term_data: pd.DataFrame = ogle_data.loc[ogle_data['name'].str.lower() == term.lower()]
        if len(term_data.index) > 0:
            target_data: pd.DataFrame = term_data.iloc[0]
            return target_data
        else:
            raise MissingDataException(f'No result for {term} in OGLE EWS!')
    except :
#        raise InvalidExternalServiceResponseException(f'OGLE EWS didn\'t return a valid csv file!')
        logger.error(f'OGLE EWS didn\'t return a valid csv file!')
        raise MissingDataException(f'No result in OGLE EWS!')




'''
Downloads all lenses.par files from OGLE EWS into one file. Should be done only if the file is missing (new system) 
or the event users asked for was not present in the list. 
'''
def download_all_ews(output_file):
    import csv

    urls=[
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2011/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2012/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2013/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2014/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2015/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2016/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2017/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2018/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2019/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2020/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2021/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2022/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle4/ews/2023/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2002/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2003/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2004/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2005/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2006/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2007/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2008/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle3/ews/2009/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle2/ews/1998/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle2/ews/1999/lenses.par',
    'http://www.astrouw.edu.pl/ogle/ogle2/ews/2000/lenses.par',]
    
    # Open the output file in write mode
    with open(output_file, 'w') as outfile:
        writer = csv.writer(outfile)
        # Loop through each URL
        for url in urls:
            print("downloading ",url)
            # Read the contents of the URL
            response = requests.get(url)
            content = response.text
            
            # Split the content into lines and skip the first two lines
            lines = content.split('\n')[2:]
            
            # Process each line
            for line in lines:
                # Check if the line is empty
                if line.strip():
                    # Split the line into columns using spaces as the separator
                    columns = line.split()
                    
                    # Write columns 0 to 4 to the output file
                    writer.writerow(columns[:5])

class OGLEEWSHarvester(AbstractHarvester):
    name = 'OGLE EWS'

    def query(self, term):
        self.catalog_data = get(term)
        return self.catalog_data

    def to_target(self) -> Optional[Target]:
        # catalog_data contains now all fields needed to create a target
        target = super().to_target()

        ogle_name: str = self.catalog_data[TARGET_NAME_KEYS[DataSource.OGLE_EWS]]
        ra: str = self.catalog_data['ra']
        dec: str = self.catalog_data['dec']
        # disc: str = self.catalog_data["disc"]
        # classif: str = self.catalog_data["classif"]

        # Checking if the object already exists in our DB
        try:
            t0: Target = Target.objects.get(name=ogle_name)

            # TODO: add update?

            return t0
        except ObjectDoesNotExist:
#            logger.error(f'Target {gaia_name} not found in the database.')
            pass

        try:
            # Creating a target object
            target.type = 'SIDEREAL'
            target.name = ogle_name
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

            logger.info(f'Successfully created target {ogle_name}')

        except Exception as e:
            logger.error(f'Exception while creating object {ogle_name}: {e}')

        return target

    def to_extras(self) -> Dict[str,str]:

        # ogle_name: str = self.catalog_data[TARGET_NAME_KEYS[DataSource.OGLE_EWS]]
        # ra: str = self.catalog_data[3]
        # dec: str = self.catalog_data[4]
        # disc: str = self.catalog_data["disc"]
        # classif: str = self.catalog_data["classif"]

        extras : Dict[str] = {}
        extras["classification"] = "ulens candidate"
        # extras["importance"] = str(9.99)
        # extras["discovery_date"] = disc
        # extras["cadence"] = str(1.0)

        return extras


# Queries alerts.csv and searches for the name
# then also loads the light curve
def get(term: str):
    term_data: pd.DataFrame = search_term_in_ogleews_data(term)

    # OGLE data have the columns in format:
    # id field star ra dec .... (but no header!)

    catalog_data: Dict[str, Any] = {
        TARGET_NAME_KEYS[DataSource.OGLE_EWS]: term_data['name'],
        "ra": (term_data['ra']), #dropping Decimal (LW), returning string
        "dec": (term_data['dec']), #dropping Decimal (LW), returning string
    }

    return catalog_data


# #performs a cone search on Gaia CSV file - TODO: is there an API for Gaia Alerts to do that?
# #returns the name of the target if present
# def cone_search(coordinates:SkyCoord, radius:Angle):
#     from io import StringIO
#     import astropy.units as u

#     # Check if the cache file exists
#     if os.path.exists(GAIA_ALERTS_CACHE_PATH):
#         logger.debug("Using cashed Gaia Alerts csv file in cone_search for Gaia Alert name")
#         gaia_data: pd.DataFrame = pd.read_csv(str(GAIA_ALERTS_CACHE_PATH))
#         gaia_data["diff"] = ((sqrt((gaia_data[" RaDeg"]-coordinates.ra)**2)+((gaia_data[" DecDeg"]-coordinates.dec)**2))<radius.degree)

#         try:
#             term_data: pd.DataFrame = gaia_data.loc[gaia_data['diff'] == True]
#         except KeyError:
#             os.remove(GAIA_ALERTS_CACHE_PATH)
#             raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

#         if len(term_data.index) > 0:
#             target_data: pd.DataFrame = term_data.iloc[0]
#             return target_data

#     # Term is not found or the CSV file doesn't exist, so CSV needs to be updated
#     new_gaia_data = pd.read_csv(StringIO(fetch_alerts_csv()))

#     #simple cone search, computing the difference in coordinates column
#     new_gaia_data["diff"] = ((sqrt((new_gaia_data[" RaDeg"]-coordinates.ra)**2)+((new_gaia_data[" DecDeg"]-coordinates.dec)**2))<radius.degree)
# #    new_gaia_data.sort_values(by=['diff'], inplace=True)

#     try:
#         term_data: pd.DataFrame = new_gaia_data.loc[new_gaia_data['diff'] == True]
#     except KeyError:
#         os.remove(GAIA_ALERTS_CACHE_PATH)
#         raise InvalidExternalServiceResponseException(f'Gaia Alerts didn\'t return a valid csv file!')

#     if len(term_data.index) > 0:
#         target_data: pd.DataFrame = term_data.iloc[0]
#         return target_data
#     else:
#         logger.info('Cone Search returned no results in Gaia Alerts!')
#         return pd.DataFrame() #empty data frame returned
