import json
from typing import Dict, Optional, Any, Iterable, Tuple

import numpy as np
from alerce.core import Alerce
from alerce.exceptions import APIError, ObjectNotFoundError
from astropy.time import Time, TimezoneInfo
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, ZTF_FILTERS, FILTERS
from bhtom2.brokers.lightcurve_update import LightcurveUpdate
from bhtom2.external_service.filter_name import filter_name


class ZTFLightcurveUpdate(LightcurveUpdate):
    def __init__(self):
        super().__init__(DataSource.ZTF)

        self.__alerce: Alerce = Alerce()

        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"

    def fetch_data_from_data_source(self, target: Target) -> Iterable:
        ztf_name: Optional[str] = self.get_target_name(target)

        if not ztf_name:
            self.logger.debug(f'No ZTF name for {target.name}')
            return [{}]

        query: Dict[str, Any] = {'detections': []}

        try:
            query: Dict[str, Any] = self.__alerce.query_lightcurve(ztf_name)
        # No such object on ZTF
        except ObjectNotFoundError as e:
            raise NoResultException(f'No ZTF data found for {target.name}')
        except APIError as e:
            raise InvalidExternalServiceResponseException(f'Invalid ALeRCE response for {target.name}: {e}')

        return query['detections']

    def process_row_to_reduced_datum(self, target: Target, internal_target_name: str, datum: Any) -> Tuple[
        Optional[ReducedDatum],
        bool,
        Optional[np.float64],
        Optional[np.float64]]:
        mjd: Time = Time(datum['mjd'], format='mjd', scale='utc')
        mag: float = float(datum['magpsf_corr'])

        if mag is None:
            self.logger.warning(f'None magnitude for target {target.name}')
            return None, False, None, None

        magerr: float = float(datum['sigmapsf_corr'])

        filter: str = ZTF_FILTERS[int(datum['fid'])]

        if filter not in FILTERS[self.data_source]:
            self.logger.warning(f'Invalid ZTF filter for {target.name}: {filter}')

        value = {
            'magnitude': mag,
            'filter': filter_name(filter, self.data_source.name),
            'error': magerr,
            'jd': mjd.jd
        }

        rd, created = ReducedDatum.objects.get_or_create(
            timestamp=mjd.to_datetime(timezone=TimezoneInfo()),
            value=json.dumps(value),
            source_name='ALeRCE',
            source_location='ALeRCE',
            data_product=self.get_dataproduct(target, filter,
                                              self.__FACILITY_NAME,
                                              self.__OBSERVER_NAME),
            data_type='photometry',
            target=target)

        return rd, created, mjd.jd, mag
