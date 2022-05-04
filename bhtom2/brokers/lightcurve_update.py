from collections import namedtuple
from typing import Any, Optional, Iterable, Tuple

import numpy as np

from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target

LightcurveUpdateReport = namedtuple('LightcurveUpdateReport', ['new_points', 'last_jd', 'last_mag'])


class LightcurveUpdate:


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
