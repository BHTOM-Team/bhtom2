from typing import Optional

import requests
from bhtom2.exceptions.external_service import InvalidExternalServiceResponseException, InvalidExternalServiceStatusException


def query_external_service(url: str,
                           service_name: str = 'External Service',
                           value_to_get: str = 'text',
                           **kwargs) -> str:

    response: requests.Response = requests.get(url, **kwargs)
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

