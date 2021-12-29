from typing import Dict, Optional, Any

from alerce.core import Alerce
from alerce.exceptions import APIError, ObjectNotFoundError
from astropy.time import Time, TimezoneInfo
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, ZTF_FILTERS, FILTERS
from bhtom2.models.reduced_datum_value import reduced_datum_value, reduced_datum_non_detection_value


class ZTFBroker(BHTOMBroker):

    name = DataSource.ZTF.name

    def __init__(self):
        super().__init__(DataSource.ZTF)

        self.__alerce: Alerce = Alerce()

        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"

    def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:

        ztf_name: Optional[str] = self.get_target_name(target)

        if not ztf_name:
            self.logger.debug(f'No ZTF name for {target.name}')
            return return_for_no_new_points()

        self.logger.debug(f'Updating ZTF Alerts Lightcurve for {target.name} with ZTF name {ztf_name}')

        try:
            query: Dict[str, Any] = self.__alerce.query_lightcurve(ztf_name)
        # No such object on ZTF
        except ObjectNotFoundError as e:
            raise NoResultException(f'No ZTF data found for {target.name} with ZTF name {ztf_name}')
        except APIError as e:
            raise InvalidExternalServiceResponseException(f'Invalid ALeRCE response for {target.name}: {e}')

        new_points: int = 0

        for entry in query['detections']:

            try:
                mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
                mag: float = float(entry['magpsf_corr'])

                if mag is not None:
                    self.logger.debug(f'None magnitude for target {target.name}')

                    magerr: float = float(entry['sigmapsf_corr'])

                    filter: str = ZTF_FILTERS[int(entry['fid'])]

                    if filter not in FILTERS[self.data_source]:
                        self.logger.warning(f'Invalid ZTF filter for {target.name}: {filter}')

                    value: Dict[str, Any] = reduced_datum_value(mag=mag, filter=self.filter_name(filter),
                                                                error=magerr, jd=mjd.jd,
                                                                observer=self.__OBSERVER_NAME,
                                                                facility=self.__FACILITY_NAME)

                    rd, _ = ReducedDatum.objects.get_or_create(
                        timestamp=mjd.to_datetime(timezone=TimezoneInfo()),
                        value=value,
                        source_name='ALeRCE',
                        source_location='ALeRCE',
                        data_type='photometry',
                        target=target)

                    rd.save()
                    new_points += 1

                    self.update_last_jd_and_mag(mjd.jd, mag)
            except Exception as e:
                self.logger.error(f'Error while processing reduced datapoint for {target.name} with '
                                  f'ZTF name {ztf_name}: {e}')

        for entry in query['non_detections']:

            try:
                mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
                limit: float = float(entry['diffmaglim'])

                if limit is not None:
                    self.logger.debug(f'None non-detection for target {target.name}')

                    filter: str = ZTF_FILTERS[int(entry['fid'])]

                    if filter not in FILTERS[self.data_source]:
                        self.logger.warning(f'Invalid ZTF filter for {target.name}: {filter}')

                    value: Dict[str, Any] = reduced_datum_non_detection_value(limit=limit,
                                                                              filter=self.filter_name(filter),
                                                                              jd=mjd.jd,
                                                                              observer=self.__OBSERVER_NAME,
                                                                              facility=self.__FACILITY_NAME)

                    rd, _ = ReducedDatum.objects.get_or_create(
                        timestamp=mjd.to_datetime(timezone=TimezoneInfo()),
                        value=value,
                        source_name='ALeRCE',
                        source_location='ALeRCE',
                        data_type='photometry',
                        target=target)

                    rd.save()
                    new_points += 1

            except Exception as e:
                self.logger.error(f'Error while processing reduced non-detection datapoint for {target.name} with '
                                  f'ZTF name {ztf_name}: {e}')

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.last_jd,
                                      last_mag=self.last_mag)
