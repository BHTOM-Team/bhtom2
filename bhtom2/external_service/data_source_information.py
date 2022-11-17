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
    GAIA_DR3 = auto()
    SDSS_DR14 = auto()
    NEOWISE = auto()


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
    DataSource.ZTF_DR8: "ZTF DR8",
    DataSource.GAIA_DR3: "Gaia DR3",
    DataSource.SDSS_DR14: "SDSS-DR14",
    DataSource.NEOWISE: "NEOWISE"
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
    DataSource.ZTF_DR8: "ZTF DR8 id",
    DataSource.GAIA_DR3: "Gaia DR3 id",
    DataSource.SDSS_DR14: "SDSS-DR14 id",
    DataSource.NEOWISE: "NEOWISE name"
}


FILTERS: Dict[DataSource, List[str]] = {
    DataSource.GAIA: ["g"],
    DataSource.ZTF: ["g", "i", "r"],
    DataSource.AAVSO: ["V", "I", "R"],
    DataSource.ANTARES: ["R", "g"],
    DataSource.ZTF_DR8: ["g", "i", "r"],
    DataSource.GAIA_DR3: ["RP", "G", "BP"],
    DataSource.SDSS_DR14: ["g", "r", "i", "z"],
    DataSource.NEOWISE: ["W1", "W2"]
}


AAVSO_ACCEPTED_FLAGS: List[str] = ["V", "Z"]
# V - fully validated
# Z - passed automatic validation tests


ZTF_FILTERS: Dict[int, str] = {1: 'g', 2: 'r', 3: 'i'}
ZTF_DR8_FILTERS: Dict[str, str] = {1: 'g', 2: 'r', 3: 'i'}

PHOTOMETRY_BROKER_DATAPRODUCT_TYPE: str = 'broker_photometry'
