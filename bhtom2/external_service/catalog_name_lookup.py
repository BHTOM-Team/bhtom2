from typing import Any, Dict, List, Optional

import antares_client.search as antares
from alerce.core import Alerce
from astropy.coordinates import Angle, SkyCoord
from astroquery.simbad import Simbad

from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.harvesters.gaia_alerts import cone_search
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


def query_all_services(target: Target) -> Dict[str, str]:
    alerce_result: Dict[str, str] = query_antares_for_names(target)
    simbad_result: Dict[str, str] = query_simbad_for_names(target)
    gaia_alerts_result: Dict[str, str] = query_gaia_alerts_for_name(target)
    return {**alerce_result, **simbad_result, **gaia_alerts_result}
#    return {**alerce_result, **simbad_result}


def query_antares_for_names(target: Target) -> Dict[str, str]:
    try:
        coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
        radius: Angle = Angle(1, unit="arcsec")

        target: Optional[Any] = None

        for locus in antares.cone_search(coordinates, radius):
            target = locus
            break

        if target:
            return {
                TARGET_NAME_KEYS[DataSource.ANTARES]: target.locus_id,
                TARGET_NAME_KEYS[DataSource.ZTF]: target.properties.get('ztf_object_id', '')
            }

        return {}
    except Exception as e:
        logger.error(f'Exception when querying antares for target {target.name}: {e}')
        return {}


def query_simbad_for_names(target: Target) -> Dict[str, str]:
    from astropy.table import Table
    import re

    try:
        logger.info(f'Querying Simbad for target {target.name}...')

        result_table: Optional[Table] = Simbad.query_objectids(object_name=target.name)
        result_dict: Dict[str] = {}

        if result_table:
            logger.info(f'[Name fetch for {target.name}] Returned Simbad query table...')

            for row in result_table['ID']:
                if 'AAVSO' in row:
                    logger.info(f'Found AAVSO name...')
                    result_dict[TARGET_NAME_KEYS[DataSource.AAVSO]] = re.sub(r'^AAVSO( )*', '', row)
                elif 'Gaia DR2' in row:
                    logger.info(f'Found Gaia DR2 name...')
                    result_dict[TARGET_NAME_KEYS[DataSource.GAIA_DR2]] = re.sub(r'^Gaia( )*DR2( )*', '', row)
                elif 'Gaia DR3' in row:
                    logger.info(f'Found Gaia DR3 name...')
                    result_dict[TARGET_NAME_KEYS[DataSource.GAIA_DR3]] = re.sub(r'^Gaia( )*DR3( )*', '', row)

        return result_dict
    except Exception as e:
        logger.error(f'Error while querying Simbad for target {target.name}: {e}')
        return {}

#searches Gaia Alerts for names of this target
def query_gaia_alerts_for_name(target: Target) -> Dict[str,str]:
    coordinates: SkyCoord = SkyCoord(ra=target.ra, dec=target.dec, unit="deg")
    radius: Angle = Angle(1, unit="arcsec")
    try:

#        target: Optional[Any] = None

        #returns pd.DataFrame
        result = cone_search(coordinates, radius)
        name=''
#        if (result is not None):
        if ( result.empty==False ):
            name = result["#Name"]
            logger.info(f'Found Gaia Alerts name...{name}')
            return {
                    TARGET_NAME_KEYS[DataSource.GAIA]: name,
                }
        return {} #if nothing found, returns empty dictionary
    except Exception as e:
        logger.error(f'Exception when querying Gaia Alerts for target {target.name}: {e}')
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
