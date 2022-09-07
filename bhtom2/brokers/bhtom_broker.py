from collections import namedtuple
from functools import lru_cache
from typing import List, Optional

import numpy as np

from bhtom2.external_service.data_source_information import DataSource, FILTERS, get_pretty_survey_name
from bhtom2.external_service.filter_name import filter_name
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_alerts.alerts import GenericBroker
from bhtom_base.bhtom_targets.models import Target

import astropy.units as u

LightcurveUpdateReport = namedtuple('LightcurveUpdateReport', ['new_points'])


def return_for_no_new_points() -> LightcurveUpdateReport:
    return LightcurveUpdateReport(new_points=0)


class BHTOMBroker(GenericBroker):
    def __init__(self, data_source: DataSource):
        self.__data_source: DataSource = data_source
        self.__filters: List[str] = FILTERS[self.__data_source]
        self.__logger: BHTOMLogger = BHTOMLogger(__name__,
                                                 f'[{get_pretty_survey_name(self.__data_source.name)} Lightcurve Update]')

        self.__last_jd: Optional[np.float64] = None
        self.__last_mag: Optional[np.float64] = None
        self.__target_name_key: str = self.__data_source.name

        # How often should the catalog be checked- as an astropy quantity. Default is 1 day
        # Leave none if constant data release (e.g. should be fetched only once)
        self.__update_cadence: Optional[u.Quantity] = 1*u.d

        # Max separation for the cross-match to classify measurements as one object
        self.__cross_match_max_separation: u.Quantity = 5*u.arcsec

    def filter_name(self, filter: str) -> str:
        return filter_name(filter, get_pretty_survey_name(self.__data_source.name))

    @property
    def data_source(self) -> DataSource:
        return self.__data_source

    @property
    def logger(self) -> BHTOMLogger:
        return self.__logger

    @property
    def last_jd(self) -> Optional[float]:
        return self.__last_jd

    @property
    def last_mag(self) -> Optional[float]:
        return self.__last_mag

    @property
    def target_name_key(self) -> str:
        return self.__target_name_key

    @property
    def update_cadence(self) -> Optional[u.Quantity]:
        return self.__update_cadence

    @property
    def cross_match_max_separation(self) -> u.Quantity:
        return self.__cross_match_max_separation

    @lru_cache(maxsize=32)
    def get_target_name(self, target: Target) -> Optional[str]:
        try:
            internal_name: str = target.aliases.get(source_name=self.target_name_key)
        except Exception as e:
            self.__logger.error(f'Error while accessing internal name for {target.name}: {e}')
            return ''
        return internal_name if internal_name else ''

    def fetch_alerts(self, parameters: dict):
        pass

    def to_generic_alert(self, alert):
        pass
