import math
from io import StringIO
import json
from typing import Optional, List, Any, Dict, Tuple, Type

from alerce.exceptions import APIError, ObjectNotFoundError
from astropy.time import Time, TimezoneInfo
from numpy import genfromtxt
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target, TargetExtra

from bhtom2 import settings
from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, FILTERS, TARGET_NAME_KEYS, ZTF_DR8_FILTERS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.models.reduced_datum_value import reduced_datum_value


# For DR8
class ZTFBroker(BHTOMBroker):

    name = DataSource.ZTF_DR8
    form = None

    def __init__(self):
        super().__init__(DataSource.ZTF_DR8)

        try:
            self.__base_url: str = settings.ZTF_DR_PATH
        except Exception as e:
            self.logger.error(f'No ZTF_DR_PATH in settings found!')
            self.__base_url = 'https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves'

        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"

        # 2 arcseconds
        self.__MATCHING_RADIUS: float = 2*0.000278

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass


    def to_generic_alert(self, alert):
        pass

    def save_ztf_dr8_name_if_missing(self, target: Target, ztf_dr8_id: int):
        if not self.get_target_name(target):
            te, _ = TargetExtra.objects.update_or_create(target=target,
                                                         key=self.target_name_key,
                                                         defaults={
                                                             'value': str(ztf_dr8_id)
                                                         })
            te.save()

    def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:

        ztf_name: Optional[str] = self.get_target_name(target)
        base_url: str = self.__base_url

        self.logger.debug(f'Updating ZTF Data Releases for {target.name} with ZTF oid {ztf_name}')

        if ztf_name is None or ztf_name == '':
            self.logger.debug(f'No ZTF DR8 id for {target.name}')
            return return_for_no_new_points()

        print_with_sign = lambda i: ("+" if i > 0 else "") + str(i)

        query_parameters: Dict[str, Any] = {
            "POS": f'CIRCLE{print_with_sign(target.ra)}{print_with_sign(target.dec)}{print_with_sign(self.__MATCHING_RADIUS)}',
            "BAD_CATFLAGS_MASK": str(32768),
            "FORMAT": "csv",
            "COLLECTION": "ztf_dr8",
        }

        # "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE+255.9302+11.8654+0.0028&BANDNAME=r&NOBS_MIN=3&TIME=58194.0+58483.0&BAD_CATFLAGS_MASK=32768&FORMAT=csv"

        try:
            response: Dict[str, Any] = query_external_service(base_url, service_name=DataSource.ZTF.name,
                                                              params="&".join("%s=%s" % (k, v) for k, v in query_parameters.items()))
        # No such object on ZTF
        except ObjectNotFoundError as e:
            raise NoResultException(f'No ZTF data found for {target.name} with ZTF name {ztf_name}')
        except APIError as e:
            raise InvalidExternalServiceResponseException(f'Invalid ZTF response for {target.name}: {e}')
        except Exception as e:
            self.logger.error(f'Error while updating ZTF DR8 for {target.name} with ZTF name {ztf_name}: {e}')
            return return_for_no_new_points()

        # 0, 1, 2, 3, 4, 5, 6
        # 7, 8, 9, 10, 11, 12,
        # 13, 14, 15, 16, 17, 18,
        # 19, 20, 21, 22, 23
        # oid,expid,hjd,mjd,mag,magerr,catflags,
        # filtercode,ra,dec,chi,sharp,filefracday,
        # field,ccdid,qid,limitmag,magzp,magzprms,
        # clrcoeff,clrcounc,exptime,airmass,programid

        # Read only the interesting columns
        # oid, hjd, mjd, mag, magerr, filtercode

        # detections:
        # 'mjd', 'candid', 'fid', 'pid', 'diffmaglim', 'isdiffpos', 'nid', 'distnr', 'magpsf', 'magpsf_corr',
        # 'magpsf_corr_ext', 'magap', 'magap_corr', 'sigmapsf', 'sigmapsf_corr', 'sigmapsf_corr_ext', 'sigmagap',
        # 'sigmagap_corr', 'ra', 'dec', 'rb', 'rbversion', 'drb', 'magapbig', 'sigmagapbig', 'rfid', 'has_stamp',
        # 'corrected', 'dubious', 'candid_alert', 'step_id_corr', 'phase', 'parent_candid'

        # non_detections:
        # mjd, fid, diffmaglim

        # TODO: add non-detections

        detections = response['detections']

        new_points: int = 0

        if len(detections) > 0:
            self.save_ztf_dr8_name_if_missing(target, detections[0]['pid'])
        else:
            return return_for_no_new_points()

        # Omit the header
        for entry in detections:
            try:
                mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
                mag: float = float(entry['magpsf_corr'])

                if (mag is not None) and (not math.isnan(mag)):
                    self.logger.debug(f'None magnitude for target {target.name}')

                    magerr: float = float(entry['sigmapsf_corr'])
                    filter: str = ZTF_DR8_FILTERS[entry['fid']]

                    if filter not in FILTERS[self.data_source]:
                        self.logger.warning(f'Invalid ZTF DR8 filter for {target.name}: {filter}')

                    # Non detections have an error of 100.
                    if magerr > 1.:
                        continue

                    else:
                        value: Dict[str, Any] = reduced_datum_value(mag=mag, filter=self.filter_name(filter),
                                                                    error=magerr, jd=mjd.jd,
                                                                    observer=self.__OBSERVER_NAME,
                                                                    facility=self.__FACILITY_NAME)

                    rd, _ = ReducedDatum.objects.get_or_create(
                        timestamp=mjd.to_datetime(timezone=TimezoneInfo()),
                        value=value,
                        source_name='ZTF DR8',
                        source_location=self.__base_url,
                        data_type='photometry',
                        target=target)

                    rd.save()
                    new_points += 1

                    self.update_last_jd_and_mag(mjd.jd, mag)
            except Exception as e:
                self.logger.error(f'Error while processing reduced datapoint for {target.name} with '
                                  f'ZTF DR8 oid {ztf_name}: {e}')
                continue

        return LightcurveUpdateReport(new_points=new_points,
                                      last_jd=self.last_jd,
                                      last_mag=self.last_mag)
