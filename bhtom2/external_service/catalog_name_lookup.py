from typing import Any, Dict, List, Optional

import antares_client.search as antares
from alerce.core import Alerce
from astropy.coordinates import Angle, SkyCoord
from astroquery.simbad import Simbad
import astropy.units as u
from astropy.coordinates import ICRS, SkyCoord
from astropy.time import Time
from astroquery.gaia import Gaia
from bhtom2.brokers.gaia import GaiaBroker


from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.harvesters import ogleews, tns, gaia_alerts
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import Target

logger: BHTOMLogger = BHTOMLogger(__name__, '[Catalog name lookup]')
alerce: Alerce = Alerce()

TNS_SEARCH_URL_SLUG: str = "search"
TNS_OBJECT_URL_SLUG: str = "object"


# def request_tns(target_url: str, payload: Dict[str, str]) -> Dict[str, Any]:
#     logger.info(f'Requesting {target_url}...')
#     api_key: str = settings.TNS_API_KEY
#     user_agent: str = settings.TNS_USER_AGENT
#
#     headers = {
#         'User-Agent': user_agent
#     }
#
#     search_data = [('api_key', (None, api_key)),
#                    ('data', (None, json.dumps(OrderedDict(payload))))]
#
#     response: requests.Response = requests.post(target_url, files=search_data, headers=headers)
#
#     response_payload: Dict[Any, Any] = json.loads(response.content.decode("utf-8"))
#     response_code: int = response.status_code
#
#     if response_code == 200:
#         if 'data' not in response_payload.keys() or 'reply' not in response_payload['data'].keys():
#             logger.error(f'{LOG_PREFIX} TNS returned an invalid response: {response_payload}')
#             raise TNSConnectionError(f'TNS has returned an invalid response. Please try again later.')
#         return response_payload['data']['reply']
#     else:
#         logger.error(f'{LOG_PREFIX} TNS returned {response_code}.')
#         raise TNSConnectionError(f'TNS returned with status code {response_code}. Please try again later.')
#
#
# def get_tns_id(target: Target) -> Optional[str]:
#     """
#     Queries the TNS server and returns a dictionary with
#     ztf_alert_name and gaia_alert_name, if found
#     """
#
#     logger.info(f'[Name fetch for {target.name}] Attempting to query TNS...')
#     target_url: str = f'{settings.TNS_URL}/{TNS_SEARCH_URL_SLUG}'
#     logger.info(f'[Name fetch for {target.name}] Requesting {target_url}...')
#
#     search_json = {
#         "ra": str(target.ra),
#         "dec": str(target.dec),
#         "objname": "",
#         "objname_exact_match": 0,
#         "internal_name": str(target.name),
#         "internal_name_exact_match ": 0,
#     }
#
#     # data: Dict[str, str] = response_data['data']['reply'][0]
#
#     response: Dict[str, Any] = request_tns(target_url,
#                                            search_json)
#
#     if len(response) < 1:
#         logger.error(f'{LOG_PREFIX} No TNS ID found in response {data}')
#         raise TNSReplyError(f'No TNS ID found in TNS response.')
#     else:
#         data: Dict[str, str] = response[0]
#         prefix: Optional[str] = data.get("prefix")
#         object_name: Optional[str] = data.get("objname")
#
#         if prefix and object_name:
#             logger.info(f'{LOG_PREFIX} '
#                         f'Read names as {prefix}{object_name}')
#             return f'{prefix}{object_name}'
#         else:
#             logger.error(f'{LOG_PREFIX} No prefix and/or object name in TNS reply: {data}')
#             raise TNSConnectionError(f'No TNS ID in expected format found in TNS response. Please try again later.')
#
#
# def get_tns_internal(tns_id: str) -> Dict[str, str]:
#     """
#     Queries the TNS server and returns a dictionary with
#     ztf_alert_name and gaia_alert_name, if found
#     """
#
#     logger.info(f'[Name fetch for {tns_id}] Attempting to query TNS...')
#     target_url: str = f'{settings.TNS_URL}/{TNS_OBJECT_URL_SLUG}'
#     logger.info(f'[Name fetch for {tns_id}] Requesting {target_url}...')
#
#     search_json = {
#         "objname": tns_id_to_url_slug(tns_id),
#         "objname_exact_match": 1,
#         "photometry": "0",
#         "spectra": "0"
#     }
#
#     response: Dict[str, Any] = request_tns(target_url, search_json)
#
#     if response.get("internal_names"):
#         internal_names: List[str] = [n.strip() for n in response.get("internal_names").split(',')]
#         logger.info(f'{LOG_PREFIX} Read internal names as {internal_names}')
#
#         result_dict: Dict[str, str] = {}
#
#         for internal_name in internal_names:
#             matched_group: List[str] = assign_group_to_internal_name(internal_name)
#             logger.info(f'{LOG_PREFIX} Attempting to read internal name for {matched_group}...')
#
#             if len(matched_group) > 0:
#                 try:
#                     result_dict[matched_group[0][0]] = internal_name
#                     logger.info(
#                         f'{LOG_PREFIX} Read internal name for {matched_group[0][0]}: {internal_name}')
#                 except:
#                     continue
#
#         return result_dict
#     else:
#         logger.error(f'{LOG_PREFIX} No TNS internal names found in response {response}')
#         raise TNSReplyError(f'No TNS internal names in response.')


def query_all_services(target: Target) -> Dict[DataSource, str]:
    tns_result: Dict[DataSource, str] = query_tns_for_names(target)
    alerce_result: Dict[DataSource, str] = query_antares_for_names(target)
    simbad_result: Dict[DataSource, str] = query_simbad_for_names(target)
    gaia_alerts_result: Dict[DataSource, str] = query_gaia_alerts_for_name(target)
    gaiadr3_result: Dict[DataSource, str] = query_gaia_dr3_for_name(target)
    ogle_ews_result: Dict[DataSource, str] = query_ogle_ews_for_name(target)
    return {**alerce_result, **simbad_result, **gaia_alerts_result, **gaiadr3_result, **tns_result, **ogle_ews_result}

def query_antares_for_names(target: Target) -> Dict[DataSource, str]:
    try:
        coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
        radius: Angle = Angle(1, unit="arcsec")
   
        target: Optional[Any] = None
        result_dict: Dict[str] = {}

        for locus in antares.cone_search(coordinates, radius):
            target = locus
            break

        if target:
            result_dict[DataSource.ANTARES] = target.locus_id
            result_dict[DataSource.ZTF]= target.properties.get('ztf_object_id', '')
            return result_dict
            # return {
            #     TARGET_NAME_KEYS[DataSource.ANTARES]: target.locus_id,
            #     TARGET_NAME_KEYS[DataSource.ZTF]: target.properties.get('ztf_object_id', '')
            # }

        return {}
    except Exception as e:
        logger.error(f'Exception when querying antares for target {target.name}: {e}')
        return {}

#TODO: use coords instaed of name; Add SDSS name
def query_simbad_for_names(target: Target) -> Dict[str, str]:
    from astropy.table import Table
    import re

    try:
        logger.info(f'Querying Simbad using target`s name {target.name}...')

        result_table: Optional[Table] = Simbad.query_objectids(object_name=target.name)
        result_dict: Dict[str] = {}

        if result_table:
            logger.info(f'[Name fetch for {target.name}] Returned Simbad query table...')

            for row in result_table['ID']:
                if 'AAVSO' in row:
                    logger.info(f'Found AAVSO name...')
                    result_dict[DataSource.AAVSO] = re.sub(r'^AAVSO( )*', '', row)
        ##LW: GAIA DR2 off, as we get an error if DR3 id is the same (key violation)
                # elif 'Gaia DR2' in row:
                #     logger.info(f'Found Gaia DR2 name...')
                #     result_dict[DataSource.GAIA_DR2] = re.sub(r'^Gaia( )*DR2( )*', '', row)
                # elif 'Gaia DR3' in row:
                #     logger.info(f'Found Gaia DR3 name...')
                #     result_dict[DataSource.GAIA_DR3] = re.sub(r'^Gaia( )*DR3( )*', '', row)

        return result_dict
    except Exception as e:
        logger.error(f'Error while querying Simbad for target {target.name}: {e}')
        return {}

#searches Gaia DR3 for name using coordinates TODO: should we move this to GaiaBroker? Same for other searches?
def query_gaia_dr3_for_name(target: Target) -> Dict[DataSource, str]:

    coord = SkyCoord(ra=target.ra,
                        dec=target.dec, unit=u.deg,
                        frame=ICRS)

    try:
        rad: Angle = Angle(1, unit="arcsec")
        result = Gaia.query_object_async(coordinate=coord,
                                            radius=rad
                                            ).to_pandas().sort_values(
            by=['dist'])['source_id']
        if (not result.empty):
            dr3_id = result[0]
            logger.debug(f"Gaia DR3 id found for {target.name}: {dr3_id}")
            return {DataSource.GAIA_DR3:dr3_id,}
        else:
            logger.debug(f"No Gaia DR3 id found for {target.name}")
            return {}
    except Exception as e:
        logger.error(f'Error when querying Gaia DR3 for {target.name}: {e}')
        return {}

#searches Gaia Alerts for names of this target
def query_gaia_alerts_for_name(target: Target) -> Dict[DataSource,str]:
    coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
    radius: Angle = Angle(1, unit="arcsec")
    try:

#        target: Optional[Any] = None

        #returns pd.DataFrame
        result = gaia_alerts.cone_search(coordinates, radius)
        name=''
#        if (result is not None):
        if ( result.empty==False ):
            name = result["#Name"]
            logger.info(f'Found Gaia Alerts name...{name}')
            return {
                    DataSource.GAIA_ALERTS: name,
                }
        return {} #if nothing found, returns empty dictionary
    except Exception as e:
        logger.error(f'Exception when querying Gaia Alerts for target {target.name}: {e}')
        return {}

def query_tns_for_names(target: Target) -> Dict[DataSource,str]:
    coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
    radius: Angle = Angle(3, unit="arcsec")
    
    try:
#        target: Optional[Any] = None

        #returns pd.DataFrame
        result = tns.cone_search(coordinates, radius)
        name=''
        if ( len(result) != 0 ):
            name = result
            logger.info(f'Found TNS name...{name}')
            return {
                    DataSource.TNS: name,
                }
        return {} #if nothing found, returns empty dictionary
    except Exception as e:
        logger.error(f'Exception when querying TNSfor target {target.name}: {e}')
        return {}
    

def tns_id_to_url_slug(tns_id: str) -> str:
    import re

    return re.sub(r'^([A-Z])+( )*', '', tns_id)


def assign_group_to_internal_name(name: str) -> List[str]:
    import re

    name_regex = re.compile('(^([A-Z]|[a-z])+)')
    return name_regex.findall(name)


def tns_internal_name_xpath(group_name: str) -> str:
    return f'//tr[td[@class="cell-groups" and text()="{group_name}"]]/td[@class="cell-internal_name"]/text()'

#searches OGLE EWS for names of this target
def query_ogle_ews_for_name(target: Target) -> Dict[DataSource,str]:
    coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
    radius: Angle = Angle(1.5, unit="arcsec")
    try:

        #returns pd.DataFrame
        result = ogleews.cone_search(coordinates, radius)
        name=''
#        if (result is not None):
        if ( result.empty==False ):
            name = result["name"].values[0]
            logger.info(f'Found OGLE EWS name...{name}')
            return {
                    DataSource.OGLE_EWS: name,
                }
        return {} #if nothing found, returns empty dictionary
    except Exception as e:
        logger.error(f'Exception when querying OGLE EWS for target {target.name}: {e}')
        return {}
