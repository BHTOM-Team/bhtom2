import json
import requests
from typing import Optional, Dict, Any

from astropy import units as u
from astropy.coordinates import SkyCoord
from collections import OrderedDict
from django.conf import settings

from bhtom_base.bhtom_catalogs.harvester import AbstractHarvester, MissingDataException
from bhtom_base.bhtom_common.exceptions import ImproperCredentialsException
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import Target

logger: BHTOMLogger = BHTOMLogger(__name__, '[Transient Name Server Harvester]')

TNS_URL = 'https://www.wis-tns.org'

try:
    TNS_CREDENTIALS = settings.HARVESTERS['TNS']
except (AttributeError, KeyError):
    TNS_CREDENTIALS = {
        'api_key': '',
        'user_agent': ''
    }


#removes AT or SN from the term
def remove_initial_substring(string):
    if string.startswith("AT"):
        return string[2:]
    elif string.startswith("SN"):
        return string[2:]
    elif string.startswith("AT "):
        return string[3:]
    elif string.startswith("SN "):
        return string[3:]
    else:
        return string
    
def get(term):
    get_url = TNS_URL + '/api/get/object'

    #term should be just YYYYabc, removing AT or SN if preceding
    term = remove_initial_substring(term)

    # change term to json format
    json_list = [("objname", term)]
    json_file = OrderedDict(json_list)

    headers = {
        'User-Agent': TNS_CREDENTIALS['user_agent']
    }

    # construct the list of (key,value) pairs
    get_data = [('api_key', (None, TNS_CREDENTIALS['api_key'])),
                ('data', (None, json.dumps(json_file)))]

    response = requests.post(get_url, files=get_data, headers=headers)

    if 400 <= response.status_code <= 403:
        raise ImproperCredentialsException('TNS: improper credentials')

    response_data = json.loads(response.text)

    if 'name' in response_data['data']['reply']:
        if '110' in response_data['data']['reply']['name']: #not found message is 110
            raise MissingDataException(f'No result for {term} in TNS!')

    return response_data['data']['reply']


class TNSHarvester(AbstractHarvester):
    """
    The ``TNSBroker`` is the interface to the Transient Name Server. For information regarding the TNS, please see
    https://www.wis-tns.org/.
    """

    name = 'TNS'

    def query(self, term):
        self.catalog_data = get(term)

    def to_target(self) -> Optional[Target]:
        target = super().to_target()
        try:
            target.type = 'SIDEREAL'
            target.name = (self.catalog_data['name_prefix'] + self.catalog_data['objname'])
            c = SkyCoord('{0} {1}'.format(self.catalog_data['ra'], self.catalog_data['dec']), unit=(u.hourangle, u.deg))
            target.ra, target.dec = c.ra.deg, c.dec.deg
            target.epoch=2000.0
            logger.info(f'Successfully found TNS target {target.name}')

        except Exception as e:
            logger.error(f'Exception while looking for TNS object {e}')
        
        return target

    def to_extras(self) -> Dict[str,str]:

        disc: str = self.catalog_data["discoverydate"]
        classif: str = self.catalog_data["object_type"]["name"]

        extras : Dict[str] = {}
        extras["classification"] = classif
        extras["importance"] = str(9.99)
        extras["discovery_date"] = disc
        extras["cadence"] = str(1.0)

        return extras
