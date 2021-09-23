from enum import auto, Enum
from typing import Dict


class AlertSource(Enum):
    GAIA = auto()
    CPCS = auto()
    ZTF = auto()
    AAVSO = auto()


alert_target_name: Dict[AlertSource, str] = {
    AlertSource.GAIA: 'gaia_name',
    AlertSource.CPCS: 'cpcs_name',
    AlertSource.ZTF: 'ztf_name',
    AlertSource.AAVSO: 'aavso_name'
}


alert_source_name: Dict[AlertSource, str] = {
    AlertSource.GAIA: 'GaiaAlerts'
}