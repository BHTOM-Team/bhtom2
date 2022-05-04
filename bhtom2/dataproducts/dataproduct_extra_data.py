from typing import Dict, List, Optional, Any
import json

from bhtom_base.tom_dataproducts.models import DataProduct

from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[Dataproduct Extra Data Serializer]')

# Extra Data fields
OBSERVER_KEY: str = 'observer'

EXTRA_FIELD_KEYS: List[str] = [OBSERVER_KEY]


def decode_extra_data(data_product: DataProduct) -> Dict[str, str]:
    if not data_product.extra_data:
        return {}

    try:
        return json.loads(data_product.extra_data)
    except Exception as e:
        logger.error(f'Exception when decoding {data_product.extra_data} for {data_product.target}: {e}')
        return {}


def encode_extra_data(observer: Optional[str] = None) -> str:
    result: Dict[str, Any] = {}

    if observer:
        result[OBSERVER_KEY] = observer

    return json.dumps(result)
