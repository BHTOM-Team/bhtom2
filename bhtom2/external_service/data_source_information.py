from enum import Enum, auto
from typing import Dict, List


class DataSource(Enum):
    GAIA = auto()
    ZTF = auto()
    CPCS = auto()
    AAVSO = auto()
    TNS = auto()
    ASASSN = auto()
    ANTARES = auto()
    GAIA_DR2 = auto()
    ZTF_DR8 = auto()


PRETTY_SURVEY_NAME: Dict[DataSource, str] = {
    DataSource.GAIA: "Gaia",
    "GAIA": "Gaia",
    DataSource.ZTF: "ZTF",
    DataSource.CPCS: "CPCS",
    DataSource.AAVSO: "AAVSO",
    DataSource.TNS: "TNS",
    DataSource.ASASSN: "ASAS-SN",
    DataSource.ANTARES: "ANTARES",
    DataSource.GAIA_DR2: "Gaia DR2",
    DataSource.ZTF_DR8: "ZTF DR8"
}


def get_pretty_survey_name(source_name: DataSource) -> str:
    return PRETTY_SURVEY_NAME.get(source_name, str(source_name))


TARGET_NAME_KEYS: Dict[DataSource, str] = {
    DataSource.GAIA: "Gaia name",
    DataSource.ZTF: "ZTF name",
    DataSource.CPCS: "CPCS name",
    DataSource.AAVSO: "AAVSO name",
    DataSource.TNS: "TNS name",
    DataSource.ASASSN: "ASASSN name",
    DataSource.ANTARES: "ANTARES name",
    DataSource.GAIA_DR2: "Gaia DR2 id",
    DataSource.ZTF_DR8: "ZTF DR8 id"
}


FILTERS: Dict[DataSource, List[str]] = {
    DataSource.GAIA: ["g"],
    DataSource.ZTF: ["g", "i", "r"],
    DataSource.AAVSO: ["V", "I", "R"],
    DataSource.ANTARES: ["R", "g"],
    DataSource.ZTF_DR8: ["g", "i", "r"]
}


AAVSO_ACCEPTED_FLAGS: List[str] = ["V", "Z"]
# V - fully validated
# Z - passed automatic validation tests


ZTF_FILTERS: Dict[int, str] = {1: 'g', 2: 'r', 3: 'i'}
ZTF_DR8_FILTERS: Dict[str, str] = {1: 'g', 2: 'r', 3: 'i'}

PHOTOMETRY_BROKER_DATAPRODUCT_TYPE: str = 'broker_photometry'
