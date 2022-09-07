# import math
# from datetime import datetime
# from typing import Optional, Any, Dict, List, Tuple
#
# from alerce.exceptions import APIError, ObjectNotFoundError
# from astropy.time import Time, TimezoneInfo
# from django.db import transaction
#
# from bhtom2 import settings
# from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
# from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
# from bhtom2.external_service.data_source_information import DataSource, FILTERS, ZTF_DR8_FILTERS
# from bhtom2.external_service.external_service_request import query_external_service
# from bhtom_base.bhtom_dataproducts.models import ReducedDatum, DatumValue
# from bhtom_base.bhtom_targets.models import Target, TargetExtra
#
#
# # For DR8
# class ZTFBroker(BHTOMBroker):
#     name = DataSource.ZTF_DR8
#     form = None
#
#     def __init__(self):
#         super().__init__(DataSource.ZTF_DR8)
#
#         try:
#             self.__base_url: str = settings.ZTF_DR_PATH
#         except Exception as e:
#             self.logger.error(f'No ZTF_DR_PATH in settings found!')
#             self.__base_url = 'https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves'
#
#         self.__FACILITY_NAME: str = "ZTF"
#         self.__OBSERVER_NAME: str = "ZTF"
#
#         # 2 arcseconds
#         self.__MATCHING_RADIUS: float = 2 * 0.000278
#
#     def fetch_alerts(self, parameters):
#         pass
#
#     def fetch_alert(self, target_name):
#         pass
#
#     def to_generic_alert(self, alert):
#         pass
#
#     def save_ztf_dr8_name_if_missing(self, target: Target, ztf_dr8_id: int):
#         if not self.get_target_name(target):
#             te, _ = TargetExtra.objects.update_or_create(target=target,
#                                                          key=self.target_name_key,
#                                                          defaults={
#                                                              'value': str(ztf_dr8_id)
#                                                          })
#             te.save()
#
#     def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:
#
#         ztf_name: Optional[str] = self.get_target_name(target)
#         base_url: str = self.__base_url
#
#         self.logger.debug(f'Updating ZTF Data Releases for {target.name} with ZTF oid {ztf_name}')
#
#         if ztf_name is None or ztf_name == '':
#             self.logger.debug(f'No ZTF DR8 id for {target.name}')
#             return return_for_no_new_points()
#
#         print_with_sign = lambda i: ("+" if i > 0 else "") + str(i)
#
#         query_parameters: Dict[str, Any] = {
#             "POS": f'CIRCLE{print_with_sign(target.ra)}{print_with_sign(target.dec)}{print_with_sign(self.__MATCHING_RADIUS)}',
#             "BAD_CATFLAGS_MASK": str(32768),
#             "FORMAT": "csv",
#             "COLLECTION": "ztf_dr8",
#         }
#
#         # "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE+255.9302+11.8654+0.0028&BANDNAME=r&NOBS_MIN=3&TIME=58194.0+58483.0&BAD_CATFLAGS_MASK=32768&FORMAT=csv"
#
#         try:
#             response: Dict[str, Any] = query_external_service(base_url, service_name=DataSource.ZTF.name,
#                                                               params="&".join("%s=%s" % (k, v) for k, v in
#                                                                               query_parameters.items()))
#         # No such object on ZTF
#         except ObjectNotFoundError as e:
#             raise NoResultException(f'No ZTF data found for {target.name} with ZTF name {ztf_name}')
#         except APIError as e:
#             raise InvalidExternalServiceResponseException(f'Invalid ZTF response for {target.name}: {e}')
#         except Exception as e:
#             self.logger.error(f'Error while updating ZTF DR8 for {target.name} with ZTF name {ztf_name}: {e}')
#             return return_for_no_new_points()
#
#         # detections:
#         # 'mjd', 'candid', 'fid', 'pid', 'diffmaglim', 'isdiffpos', 'nid', 'distnr', 'magpsf', 'magpsf_corr',
#         # 'magpsf_corr_ext', 'magap', 'magap_corr', 'sigmapsf', 'sigmapsf_corr', 'sigmapsf_corr_ext', 'sigmagap',
#         # 'sigmagap_corr', 'ra', 'dec', 'rb', 'rbversion', 'drb', 'magapbig', 'sigmagapbig', 'rfid', 'has_stamp',
#         # 'corrected', 'dubious', 'candid_alert', 'step_id_corr', 'phase', 'parent_candid'
#
#         # non_detections:
#         # mjd, fid, diffmaglim
#
#         # TODO: add non-detections
#
#         detections = response['detections']
#         nondetections = response['non_detections']
#
#         new_points: int = 0
#
#         data: List[Tuple[datetime, DatumValue]] = []
#
#         if len(detections) > 0:
#             self.save_ztf_dr8_name_if_missing(target, detections[0]['pid'])
#         else:
#             return return_for_no_new_points()
#
#         for entry in detections:
#             try:
#                 mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
#                 mag: float = float(entry['magpsf_corr'])
#
#                 if (mag is not None) and (not math.isnan(mag)):
#                     self.logger.debug(f'None magnitude for target {target.name}')
#
#                     magerr: float = float(entry['sigmapsf_corr'])
#                     filter: str = ZTF_DR8_FILTERS[entry['fid']]
#
#                     if filter not in FILTERS[self.data_source]:
#                         self.logger.warning(f'Invalid ZTF DR8 filter for {target.name}: {filter}')
#
#
#                     data.append((mjd.to_datetime(timezone=TimezoneInfo()),
#                                  DatumValue(value=mag,
#                                             error=magerr,
#                                             mjd=mjd.mjd,
#                                             filter=self.filter_name(filter),
#                                             data_type='photometry')))
#
#                     self.update_last_jd_and_mag(mjd.jd, mag)
#             except Exception as e:
#                 self.logger.error(f'Error while processing reduced datapoint for {target.name} with '
#                                   f'ZTF DR8 oid {ztf_name}: {e}')
#                 continue
#
#         for entry in nondetections:
#             try:
#                 mjd: Time = Time(entry['mjd'], format='mjd', scale='utc')
#                 mag: float = float(entry['diffmaglim'])
#
#                 if (mag is not None) and (not math.isnan(mag)):
#                     self.logger.debug(f'None limit magnitude for target {target.name}')
#
#                     filter: str = ZTF_DR8_FILTERS[entry['fid']]
#
#                     if filter not in FILTERS[self.data_source]:
#                         self.logger.warning(f'Invalid ZTF DR8 filter for {target.name}: {filter}')
#
#                     data.append((mjd.to_datetime(timezone=TimezoneInfo()),
#                                  DatumValue(value=mag,
#                                             mjd=mjd.mjd,
#                                             filter=self.filter_name(filter),
#                                             data_type='photometry_nondetection')))
#             except Exception as e:
#                 self.logger.error(f'Error while processing non-detection reduced datapoint for {target.name} with '
#                                   f'ZTF DR8 oid {ztf_name}: {e}')
#                 continue
#
#         try:
#             data = list(set(data))
#             reduced_datums = [ReducedDatum(target=target, data_type=datum[1].data_type,
#                                            timestamp=datum[0], mjd=datum[1].mjd, value=datum[1].value,
#                                            source_name=self.name,
#                                            source_location=self.__base_url,
#                                            error=datum[1].error,
#                                            filter=datum[1].filter, observer=self.__OBSERVER_NAME,
#                                            facility=self.__FACILITY_NAME) for datum in data]
#             with transaction.atomic():
#                 new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
#         except Exception as e:
#             self.logger.error(f'Error while saving reduced datapoints for {target.name} with '
#                               f'ZTF DR8 oid {ztf_name}: {e}')
#             return return_for_no_new_points()
#
#         return LightcurveUpdateReport(new_points=new_points,
#                                       last_jd=self.last_jd,
#                                       last_mag=self.last_mag)
