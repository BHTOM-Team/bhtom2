from enum import Enum, auto
from typing import Dict, List


class DataSource(Enum):
    Gaia = auto()
    ZTF = auto()
    CPCS = auto()
    AAVSO = auto()
    TNS = auto()
    ASASSN = auto()


TARGET_NAME_KEYS: Dict[DataSource, str] = {
    DataSource.Gaia: "Gaia name",
    DataSource.ZTF: "ZTF name",
    DataSource.CPCS: "CPCS name",
    DataSource.AAVSO: "AAVSO name",
    DataSource.TNS: "TNS name",
    DataSource.ASASSN: "ASASSN name",
}


FILTERS: Dict[DataSource, List[str]] = {
    DataSource.Gaia: ["g"],
    DataSource.ZTF: ["g", "i", "r"],
    DataSource.AAVSO: ["V", "I", "R"],
}


AAVSO_ACCEPTED_FLAGS: List[str] = ["V", "Z"]
# V - fully validated
# Z - passed automatic validation tests


ZTF_FILTERS: Dict[int, str] = {1: 'g', 2: 'r', 3: 'i'}
