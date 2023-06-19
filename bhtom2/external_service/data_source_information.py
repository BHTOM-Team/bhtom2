from enum import Enum, auto
from typing import Dict, List


class DataSource(Enum):
    GAIA_ALERTS = auto()
    GAIA_DR3 = auto()
    GAIA_DR2 = auto()
    ZTF = auto()
    CPCS = auto()
    AAVSO = auto()
    TNS = auto()
    ASASSN = auto()
    ANTARES = auto()
    ZTF_DR8 = auto()
    SDSS_DR14 = auto()
    NEOWISE = auto()
    ALLWISE = auto()
    CRTS = auto()
    LINEAR = auto()
    FIRST = auto()
    PS1 = auto()
    DECAPS = auto()


PRETTY_SURVEY_NAME: Dict[DataSource, str] = {
    DataSource.GAIA_ALERTS: "Gaia Alerts",
#    "GAIA": "Gaia",
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
    DataSource.NEOWISE: "NEOWISE",
    DataSource.ALLWISE: "ALLWISE",
    DataSource.CRTS: "CRTS",
    DataSource.LINEAR: "LINEAR",
    DataSource.FIRST: "FIRST",
    DataSource.PS1: "PS1",
    DataSource.DECAPS: "DECAPS",
}


def get_pretty_survey_name(source_name: DataSource) -> str:
    return PRETTY_SURVEY_NAME.get(source_name, str(source_name))


TARGET_NAME_KEYS: Dict[DataSource, str] = {
    DataSource.GAIA_ALERTS: "Gaia Alerts name",
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
    DataSource.NEOWISE: "NEOWISE name",
    DataSource.ALLWISE: "ALLWISE name",
    DataSource.CRTS: "CRTS name",
    DataSource.LINEAR: "LINEAR name",
    DataSource.FIRST: "FIRST name",
    DataSource.PS1: "PS1 name",
    DataSource.DECAPS: "DECAPS name",
}


FILTERS: Dict[DataSource, List[str]] = {
    DataSource.GAIA_ALERTS: ["G"],
    DataSource.ZTF: ["g", "i", "r"],
    DataSource.AAVSO: ["V", "I", "R"],
    DataSource.ANTARES: ["R", "g"],
    DataSource.ZTF_DR8: ["g", "i", "r"],
    DataSource.GAIA_DR3: ["RP", "G", "BP"],
    DataSource.SDSS_DR14: ["u","g", "r", "i", "z"],
    DataSource.NEOWISE: ["W1", "W2"],
    DataSource.ALLWISE: ["W1", "W2"],
    DataSource.CRTS: ["CL"],
    DataSource.LINEAR: ["CL"],
    DataSource.FIRST: ["Flux 1.4GHz"],
    DataSource.PS1: ["g", "r", "i", "z"],
    DataSource.DECAPS: ["g", "r", "i", "z"],
    DataSource.CPCS: ["g", "r", "i", "z"], ##is it used anywhere?    
}


AAVSO_ACCEPTED_FLAGS: List[str] = ["V", "Z"]
# V - fully validated
# Z - passed automatic validation tests


ZTF_FILTERS: Dict[int, str] = {1: 'g', 2: 'r', 3: 'i'}
ZTF_DR8_FILTERS: Dict[str, str] = {1: 'g', 2: 'r', 3: 'i'}

PHOTOMETRY_BROKER_DATAPRODUCT_TYPE: str = 'broker_photometry'
