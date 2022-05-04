from collections import namedtuple
from functools import lru_cache
from typing import List, Optional

import numpy as np
from tom_alerts.alerts import GenericBroker
from tom_targets.models import Target

from bhtom2.external_service.data_source_information import DataSource, FILTERS, TARGET_NAME_KEYS
from bhtom2.external_service.filter_name import filter_name
from bhtom2.utils.bhtom_logger import BHTOMLogger

LightcurveUpdateReport = namedtuple('LightcurveUpdateReport', ['new_points', 'last_jd', 'last_mag'])


def return_for_no_new_points() -> LightcurveUpdateReport:
    return LightcurveUpdateReport(new_points=0,
                                  last_jd=None,
                                  last_mag=None)


class BHTOMBroker(GenericBroker):
    def __init__(self, data_source: DataSource):
        self.__data_source: DataSource = data_source
        self.__filters: List[str] = FILTERS[self.__data_source]
        self.__logger: BHTOMLogger = BHTOMLogger(__name__, f'[{self.__data_source.name} Lightcurve Update]')

        self.__last_jd: Optional[np.float64] = None
        self.__last_mag: Optional[np.float64] = None
        self.__target_name_key: str = TARGET_NAME_KEYS[self.__data_source]

    def filter_name(self, filter: str) -> str:
        return filter_name(filter, self.__data_source.name)

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

    @lru_cache(maxsize=32)
    def get_target_name(self, target: Target) -> Optional[str]:
        try:
            internal_name: str = target.extra_fields[self.target_name_key]
        except Exception as e:
            self.__logger.error(f'Error while accessing internal name for {target.name}: {e}')
            return ''
        return internal_name if internal_name else ''

    def update_last_jd_and_mag(self, last_jd: Optional[np.float64], last_mag: Optional[np.float64]):
        if not last_jd:
            return

        if not self.__last_jd or last_jd > self.__last_jd:
            self.__last_jd = last_jd

            if last_mag:
                self.__last_mag = last_mag

    def fetch_alerts(self, parameters: dict):
        pass

    def to_generic_alert(self, alert):
        pass