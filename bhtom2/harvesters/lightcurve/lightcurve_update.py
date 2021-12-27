from collections import namedtuple
from functools import lru_cache
from typing import List, Dict, Any, Optional, Iterable, Tuple

import numpy as np
from tom_dataproducts.models import DataProductGroup, DataProduct, ReducedDatum
from tom_observations.models import ObservationRecord, ObservationGroup
from tom_targets.models import Target

from bhtom2.external_service.data_source_information import DataSource, FILTERS, TARGET_NAME_KEYS
from bhtom2.harvesters.utils.filter_name import filter_name
from bhtom2.utils.bhtom_logger import BHTOMLogger

LightcurveUpdateReport = namedtuple('LightcurveUpdateReport', ['new_points', 'last_jd', 'last_mag'])


class LightcurveUpdate:
    def __init__(self, data_source: DataSource):
        self.__data_source: DataSource = data_source
        self.__filters: List[str] = FILTERS[self.__data_source]
        self.__logger: BHTOMLogger = BHTOMLogger(__name__, f'[{self.__data_source.name} Lightcurve Update]')

        self.__last_jd: Optional[np.float64] = None
        self.__last_mag: Optional[np.float64] = None
        self.__target_name_key: str = TARGET_NAME_KEYS[self.__data_source]

        data_product_group, created = DataProductGroup.objects.get_or_create(name=self.__data_source.name)
        if created:
            data_product_group.save()

        self.__data_product_group: DataProductGroup = data_product_group

        observation_group, created = ObservationGroup.objects.get_or_create(name=self.__data_source.name)
        if created:
            observation_group.save()

        self.__observation_group: ObservationGroup = observation_group

    @property
    def data_source(self) -> DataSource:
        return self.__data_source

    @property
    def logger(self):
        return self.__logger

    @property
    def data_product_group(self):
        return self.__data_product_group

    @property
    def observation_group(self):
        return self.__observation_group

    @lru_cache(maxsize=32)
    def get_target_name(self, target: Target) -> Optional[str]:
        internal_name: Optional[str] = None
        try:
            internal_name: str = target.targetextra_set.get(key=self.__target_name_key).value
        except Exception as e:
            self.__logger.error(f'Error while accessing internal name for {target.name}: {e}')

        return internal_name

    @lru_cache(maxsize=32)
    def get_observation_record(self,
                               target: Target,
                               filter: str,
                               observatory_name: str) -> ObservationRecord:
        observation_record, created = ObservationRecord.objects.get_or_create(facility=observatory_name,
                                                                              user=None,
                                                                              target=target,
                                                                              parameters={
                                                                                  'filter': filter_name(filter,
                                                                                                        self.__data_source.name)
                                                                              })

        if created:
            observation_record.save()
            observation_record.observationgroup_set.add(self.__observation_group)

        return observation_record

    @lru_cache(maxsize=32)
    def get_dataproduct(self,
                        target: Target,
                        filter: str,
                        observatory_name: str,
                        observer_name: str) -> DataProduct:
        from bhtom2.dataproducts.dataproduct_extra_data import encode_extra_data

        data_product, created = DataProduct.objects.get_or_create(target=target,
                                                                  observation_record=self.get_observation_record(target,
                                                                                                                 filter,
                                                                                                                 observatory_name),
                                                                  extra_data=encode_extra_data(observer=observer_name),
                                                                  data_product_type="photometry")

        if created:
            data_product.group.add(self.__data_product_group.id)
            data_product.save()

        return data_product

    def update_last_jd_and_mag(self, last_jd: Optional[np.float64], last_mag: Optional[np.float64]):
        if not last_jd:
            return

        if not self.__last_jd or last_jd > self.__last_jd:
            self.__last_jd = last_jd

            if last_mag:
                self.__last_mag = last_mag

    def fetch_data_from_data_source(self, target: Target) -> Iterable:
        return [{}]

    def process_row_to_reduced_datum(self, target: Target,
                                     internal_target_name: str,
                                     datum: Any) -> Tuple[Optional[ReducedDatum],
                                                          bool,
                                                          Optional[np.float64],
                                                          Optional[np.float64]]:
        return None, False, None, None

    def update_lightcurve(self, target: Target) -> LightcurveUpdateReport:
        new_data: Iterable = self.fetch_data_from_data_source(target)
        new_points: int = 0

        target_internal_name = self.get_target_name(target)

        for datum in new_data:
            try:
                reduced_datum, created, jd, mag = self.process_row_to_reduced_datum(target, target_internal_name, datum)
                if reduced_datum and created:
                    new_points += 1
                    self.update_last_jd_and_mag(jd, mag)
            except Exception as e:
                self.__logger.error(f'Exception when processing reduced datum for {target.name}: {e}')
                continue

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.__last_jd,
                                      last_mag=self.__last_mag)
