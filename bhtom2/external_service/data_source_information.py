from enum import Enum, auto
from typing import Dict, List


class DataSource(Enum):
    GAIA_ALERTS = auto()
    CPCS = auto()
    ASASSN = auto()
    OGLE_EWS = auto()
    ZTF = auto()
    ATLAS = auto()
    AAVSO = auto()
    TNS = auto()
    ANTARES = auto()
    ZTF_DR8 = auto()
    SDSS = auto()
    NEOWISE = auto()
    ALLWISE = auto()
    CRTS = auto()
    LINEAR = auto()
    FIRST = auto()
    PS1 = auto()
    DECAPS = auto()
    GAIA_DR3 = auto()
    GAIA_DR2 = auto()
    KMT_NET = auto()
    LOFAR = auto()
    twomass = auto()
    PTF = auto()
    OGLE_OCVS = auto()
    ASTRO_COLIBRI = auto()
    GALEX = auto()
    SWIFT_UVOT = auto()
    FAVA = auto()

PRETTY_SURVEY_NAME: Dict[DataSource, str] = {
    DataSource.GAIA_ALERTS: "Gaia Alerts",
    #    "GAIA": "Gaia",
    DataSource.ZTF: "ZTF",
    DataSource.CPCS: "CPCS",
    DataSource.AAVSO: "AAVSO",
    DataSource.TNS: "TNS",
    DataSource.ASASSN: "ASASSN",
    DataSource.ANTARES: "ANTARES",
    DataSource.GAIA_DR2: "Gaia DR2",
    DataSource.ZTF_DR8: "ZTF DR8",
    DataSource.GAIA_DR3: "Gaia DR3",
    DataSource.SDSS: "SDSS",
    DataSource.NEOWISE: "NEOWISE",
    DataSource.ALLWISE: "ALLWISE",
    DataSource.CRTS: "CRTS",
    DataSource.LINEAR: "LINEAR",
    DataSource.FIRST: "FIRST",
    DataSource.PS1: "PS1",
    DataSource.DECAPS: "DECAPS",
    DataSource.OGLE_EWS: "OGLE-EWS",
    DataSource.ATLAS: "ATLAS",
    DataSource.KMT_NET: "KMT-NET",
    DataSource.LOFAR: "LOFAR2m",
    DataSource.twomass: "2MASS",
    DataSource.PTF: "PTF",
    DataSource.OGLE_OCVS: "OGLE OCVS ",
    DataSource.ASTRO_COLIBRI: "Astro COLIBRI",
    DataSource.GALEX: "GALEX",
    DataSource.SWIFT_UVOT: "SwiftUVOT",
    DataSource.FAVA: "FAVA",

}

def get_pretty_survey_name(source_name: DataSource) -> str:
    return PRETTY_SURVEY_NAME.get(source_name, str(source_name))



TARGET_NAME_KEYS: Dict[DataSource, str] = {
    DataSource.GAIA_ALERTS: "Gaia Alerts name",
    DataSource.ZTF: "ZTF name",
    DataSource.CPCS: "CPCS name",
    DataSource.AAVSO: "AAVSO name",
    DataSource.TNS: "TNS name",
    DataSource.ASASSN: "ASASSN url",
    DataSource.OGLE_EWS: "OGLE EWS name",
    DataSource.ANTARES: "ANTARES name",
    DataSource.GAIA_DR2: "Gaia DR2 id",
    DataSource.ZTF_DR8: "ZTF DR8 id",
    DataSource.GAIA_DR3: "Gaia DR3 id",
    DataSource.SDSS: "SDSS id",
    DataSource.NEOWISE: "NEOWISE name",
    DataSource.ALLWISE: "ALLWISE name",
    DataSource.CRTS: "CRTS name",
    DataSource.LINEAR: "LINEAR name",
    DataSource.FIRST: "FIRST name",
    DataSource.PS1: "PS1 name",
    DataSource.DECAPS: "DECAPS name",
    DataSource.ATLAS: "ATLAS url",
    DataSource.KMT_NET: "KMT name",
    DataSource.LOFAR: "LOFAR2m name",
    DataSource.twomass: "2MASS name",
    DataSource.PTF: "PTF",
    DataSource.OGLE_OCVS: "OGLE OCVS name",
    DataSource.ASTRO_COLIBRI: "AstroCOLIBRI name",
    DataSource.GALEX: "GALEX name",
    DataSource.SWIFT_UVOT: "SwiftUVOT name",
    DataSource.FAVA: "FAVA name",

}



FILTERS: Dict[DataSource, List[str]] = {
    DataSource.GAIA_ALERTS: ["G"],
    DataSource.ZTF: ["g", "i", "r"],
    DataSource.AAVSO: ["V", "I", "R"],
    DataSource.ANTARES: ["R", "g"],
    DataSource.ZTF_DR8: ["g", "i", "r"],
    DataSource.GAIA_DR3: ["RP", "G", "BP"],
    DataSource.SDSS: ["u","g", "r", "i", "z"],
    DataSource.NEOWISE: ["W1", "W2"],
    DataSource.ALLWISE: ["W1", "W2"],
    DataSource.CRTS: ["CL"],
    DataSource.LINEAR: ["CL"],
    DataSource.FIRST: ["Flux 1.4GHz"],
    DataSource.PS1: ["g", "r", "i", "z"],
    DataSource.DECAPS: ["g", "r", "i", "z"],
    DataSource.CPCS: ["g", "r", "i", "z"], ##is it used anywhere?    it has to be specified because bhtom_broker reads it, but probably does not use
    DataSource.ASASSN: ["g", "V"], 
    DataSource.OGLE_EWS: ['I'],
    DataSource.ATLAS: ['o','c'],
    DataSource.KMT_NET: ['I'],
    DataSource.OGLE_OCVS: ['V','I'],
    DataSource.ASTRO_COLIBRI: [],
    DataSource.GALEX: [],
    DataSource.SWIFT_UVOT: [],
    DataSource.FAVA: [],
}


AAVSO_ACCEPTED_FLAGS: List[str] = ["V", "Z"]
# V - fully validated
# Z - passed automatic validation tests


ZTF_FILTERS: Dict[int, str] = {1: 'g', 2: 'r', 3: 'i'}
ZTF_DR8_FILTERS: Dict[str, str] = {1: 'g', 2: 'r', 3: 'i'}

PHOTOMETRY_BROKER_DATAPRODUCT_TYPE: str = 'broker_photometry'
