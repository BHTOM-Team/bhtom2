from typing import Optional

import requests
from bhtom2.exceptions.external_service import InvalidExternalServiceResponseException, InvalidExternalServiceStatusException


def query_external_service(url: str,
                           service_name: str = 'External Service',
                           value_to_get: str = 'text',
                           **kwargs) -> str:

    response: requests.Response = requests.get(url, timeout=10, **kwargs)
    response.raise_for_status()

    status: int = response.status_code

    if status != 200:
        raise InvalidExternalServiceStatusException(f'{service_name} returned status code {status} '
                                                    f'after querying url {url}!')

    response_text: Optional[str] = response.__getattribute__(value_to_get)

    if not response_text:
        raise InvalidExternalServiceResponseException(f'{service_name} didn\'t return a response with body '
                                                      f'after querying url {url}!')

    return response_text


"""
    except requests.exceptions.ConnectionError:
        logger.error(f'{LOG_PREFIX} Connection error while requesting TNS')
        raise TNSConnectionError(f'Connection error while requesting TNS. Please try again later.')
    except requests.exceptions.Timeout:
        logger.error(f'{LOG_PREFIX} Timeout while requesting TNS')
        raise TNSConnectionError(f'Timeout while requesting TNS. Please try again later.')
    except requests.exceptions.RequestException:
        logger.error(f'{LOG_PREFIX} Request exception while requesting TNS: {e}')
        raise TNSConnectionError(f'Unexpected network error occurred while requesting TNS.')

    if not response:
        logger.error(f'{LOG_PREFIX} No respose returned for {target_url}')
        raise TNSConnectionError(f'No response from TNS. Please try again later.')
"""