# import json
# from decimal import Decimal
# from typing import List, Set
# from unittest.mock import patch
#
# from django.test import TestCase
# from bhtom_base.bhtom_dataproducts.models import ReducedDatum
# from bhtom_base.bhtom_targets.models import Target
#
# from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
# from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
# from bhtom2.brokers.ztf import ZTFBroker
#
# sample_lightcurve_two_correct_lines = {'detections': [{'mjd': 59550.28425930021,
#                                                        'candid': '1796284252615015007',
#                                                        'fid': 1,
#                                                        'pid': 1796284252615,
#                                                        'diffmaglim': 20.5075,
#                                                        'isdiffpos': 1,
#                                                        'nid': 1796,
#                                                        'distnr': 0.25123456,
#                                                        'magpsf': 18.648088,
#                                                        'magpsf_corr': 18.492537,
#                                                        'magpsf_corr_ext': None,
#                                                        'magap': 18.6157,
#                                                        'magap_corr': None,
#                                                        'sigmapsf': 0.087919265,
#                                                        'sigmapsf_corr': 0.07564124,
#                                                        'sigmapsf_corr_ext': 0.07618386,
#                                                        'sigmagap': 0.0698,
#                                                        'sigmagap_corr': None,
#                                                        'ra': 121.6741244,
#                                                        'dec': 38.878892,
#                                                        'rb': 0.95,
#                                                        'rbversion': 't17_f5_c3',
#                                                        'drb': 0.99997854,
#                                                        'magapbig': 18.5526,
#                                                        'sigmagapbig': 0.0835,
#                                                        'rfid': 708120126,
#                                                        'has_stamp': True,
#                                                        'corrected': True,
#                                                        'dubious': False,
#                                                        'candid_alert': None,
#                                                        'step_id_corr': 'correction_1.0.6',
#                                                        'phase': 0.0,
#                                                        'parent_candid': None},
#                                                       {'mjd': 59550.38187499996,
#                                                        'candid': '1796381872615015011',
#                                                        'fid': 2,
#                                                        'pid': 1796381872615,
#                                                        'diffmaglim': 20.624456,
#                                                        'isdiffpos': 1,
#                                                        'nid': 1796,
#                                                        'distnr': 0.32544687,
#                                                        'magpsf': 18.716454,
#                                                        'magpsf_corr': 18.522156,
#                                                        'magpsf_corr_ext': None,
#                                                        'magap': 18.7526,
#                                                        'magap_corr': None,
#                                                        'sigmapsf': 0.07501104,
#                                                        'sigmapsf_corr': 0.06242632,
#                                                        'sigmapsf_corr_ext': 0.06272002,
#                                                        'sigmagap': 0.0744,
#                                                        'sigmagap_corr': None,
#                                                        'ra': 121.6740928,
#                                                        'dec': 38.8788868,
#                                                        'rb': 0.9442857,
#                                                        'rbversion': 't17_f5_c3',
#                                                        'drb': 0.9999511,
#                                                        'magapbig': 18.6753,
#                                                        'sigmagapbig': 0.088,
#                                                        'rfid': 708120226,
#                                                        'has_stamp': True,
#                                                        'corrected': True,
#                                                        'dubious': False,
#                                                        'candid_alert': None,
#                                                        'step_id_corr': 'correction_1.0.6',
#                                                        'phase': 0.0,
#                                                        'parent_candid': None}],
#                                        'non_detections': [{'mjd': 59522.34593749978,
#                                                            'fid': 2,
#                                                            'diffmaglim': 20.4739}]}
#
# sample_lightcurve_two_correct_lines_with_Nones = {'detections': [{'mjd': 59550.28425930021,
#                                                                   'candid': '1796284252615015007',
#                                                                   'fid': 1,
#                                                                   'pid': 1796284252615,
#                                                                   'diffmaglim': 20.5075,
#                                                                   'isdiffpos': 1,
#                                                                   'nid': 1796,
#                                                                   'distnr': 0.25123456,
#                                                                   'magpsf': 18.648088,
#                                                                   'magpsf_corr': None,
#                                                                   'magpsf_corr_ext': None,
#                                                                   'magap': 18.6157,
#                                                                   'magap_corr': None,
#                                                                   'sigmapsf': 0.087919265,
#                                                                   'sigmapsf_corr': 0.07564124,
#                                                                   'sigmapsf_corr_ext': 0.07618386,
#                                                                   'sigmagap': 0.0698,
#                                                                   'sigmagap_corr': None,
#                                                                   'ra': 121.6741244,
#                                                                   'dec': 38.878892,
#                                                                   'rb': 0.95,
#                                                                   'rbversion': 't17_f5_c3',
#                                                                   'drb': 0.99997854,
#                                                                   'magapbig': 18.5526,
#                                                                   'sigmagapbig': 0.0835,
#                                                                   'rfid': 708120126,
#                                                                   'has_stamp': True,
#                                                                   'corrected': True,
#                                                                   'dubious': False,
#                                                                   'candid_alert': None,
#                                                                   'step_id_corr': 'correction_1.0.6',
#                                                                   'phase': 0.0,
#                                                                   'parent_candid': None},
#                                                                  {'mjd': 59550.38187499996,
#                                                                   'candid': '1796381872615015011',
#                                                                   'fid': 2,
#                                                                   'pid': 1796381872615,
#                                                                   'diffmaglim': 20.624456,
#                                                                   'isdiffpos': 1,
#                                                                   'nid': 1796,
#                                                                   'distnr': 0.32544687,
#                                                                   'magpsf': 18.716454,
#                                                                   'magpsf_corr': 18.522156,
#                                                                   'magpsf_corr_ext': None,
#                                                                   'magap': 18.7526,
#                                                                   'magap_corr': None,
#                                                                   'sigmapsf': 0.07501104,
#                                                                   'sigmapsf_corr': 0.06242632,
#                                                                   'sigmapsf_corr_ext': 0.06272002,
#                                                                   'sigmagap': 0.0744,
#                                                                   'sigmagap_corr': None,
#                                                                   'ra': 121.6740928,
#                                                                   'dec': 38.8788868,
#                                                                   'rb': 0.9442857,
#                                                                   'rbversion': 't17_f5_c3',
#                                                                   'drb': 0.9999511,
#                                                                   'magapbig': 18.6753,
#                                                                   'sigmagapbig': 0.088,
#                                                                   'rfid': 708120226,
#                                                                   'has_stamp': True,
#                                                                   'corrected': True,
#                                                                   'dubious': False,
#                                                                   'candid_alert': None,
#                                                                   'step_id_corr': 'correction_1.0.6',
#                                                                   'phase': 0.0,
#                                                                   'parent_candid': None}],
#                                                   'non_detections': []}
#
#
# def create_sample_target() -> Target:
#     target: Target = Target(
#         name="ZTF21acqpcmx",
#         ra=Decimal(338.044708),
#         dec=Decimal(-20.124389),
#         type='SIDEREAL',
#         epoch=2000,
#     )
#
#     target.save(extras={TARGET_NAME_KEYS[DataSource.ZTF_DR8]: "1796284252615"})
#
#     return target
#
#
# def create_second_sample_target() -> Target:
#     target: Target = Target(
#         name="ZTF21acqspkc",
#         ra=Decimal(121.674083),
#         dec=Decimal(+38.878839),
#         type='SIDEREAL',
#         epoch=2000,
#     )
#
#     target.save(extras={TARGET_NAME_KEYS[DataSource.ZTF_DR8]: "1796284252616"})
#
#     return target
#
#
# class ZTFLightcurveUpdateTestCase(TestCase):
#
#     @patch('bhtom2.brokers.ztf.query_external_service',
#            return_value=sample_lightcurve_two_correct_lines)
#     def test_dont_update_lightcurve_when_no_ztf_name(self, _):
#         ztf_broker: ZTFBroker = ZTFBroker()
#
#         target: Target = Target(
#             name="ZTF21acqpcmx",
#             ra=Decimal(338.044708),
#             dec=Decimal(-20.124389),
#             type='SIDEREAL',
#             epoch=2000,
#         )
#
#         target.save()
#
#         report: LightcurveUpdateReport = ztf_broker.process_reduced_data(target)
#
#         rd: List[ReducedDatum] = list(ReducedDatum.objects.all())
#
#         self.assertEqual(len(rd), 0)
#         self.assertEqual(report.new_points, 0)
#         self.assertEqual(report.last_jd, None)
#         self.assertEqual(report.last_mag, None)
#
#     @patch('bhtom2.brokers.ztf.query_external_service',
#            return_value=sample_lightcurve_two_correct_lines)
#     def test_update_lightcurve(self, _):
#         ztf_broker: ZTFBroker = ZTFBroker()
#
#         target: Target = create_sample_target()
#
#         target.save()
#
#         report: LightcurveUpdateReport = ztf_broker.process_reduced_data(target)
#
#         rd: List[ReducedDatum] = list(ReducedDatum.objects.all())
#
#         self.assertEqual(len(rd), 3)
#
#         detections: ReducedDatum = ReducedDatum.objects.filter(data_type='photometry', mjd__lt=59550.3)[0]
#
#         self.assertEqual(detections.data_type, 'photometry')
#         self.assertEqual(detections.target, target)
#         self.assertEqual(report.new_points, 3)
#
#         self.assertAlmostEqual(detections.value, 18.492537, 3)
#         self.assertEqual(detections.filter, 'g(ZTF_DR8)')
#         self.assertEqual(detections.observer, 'ZTF')
#         self.assertEqual(detections.facility, 'ZTF')
#         self.assertAlmostEqual(detections.error, 0.07564, 3)
#         self.assertAlmostEqual(detections.mjd, 59550.28425930, 3)
#
#         self.assertEqual(report.last_jd, 2459550.88187500)
#         self.assertEqual(report.last_mag, 18.522156)
#
#     @patch('bhtom2.brokers.ztf.query_external_service',
#            return_value=sample_lightcurve_two_correct_lines)
#     def test_update_lightcurve_save_non_detection(self, _):
#         ztf_broker: ZTFBroker = ZTFBroker()
#
#         target: Target = create_sample_target()
#
#         target.save()
#
#         report: LightcurveUpdateReport = ztf_broker.process_reduced_data(target)
#
#         rd: List[ReducedDatum] = list(ReducedDatum.objects.all())
#
#         self.assertEqual(len(rd), 3)
#
#         nondetection: ReducedDatum = ReducedDatum.objects.filter(data_type='photometry_nondetection')[0]
#
#         self.assertEqual(nondetection.data_type, 'photometry_nondetection')
#         self.assertEqual(nondetection.target, target)
#         self.assertEqual(nondetection.filter, 'r(ZTF_DR8)')
#         self.assertEqual(nondetection.observer, 'ZTF')
#         self.assertEqual(nondetection.facility, 'ZTF')
#         self.assertAlmostEqual(nondetection.value, 20.4739, 3)
#         self.assertAlmostEqual(nondetection.mjd, 59522.34593750, 3)
#
#         self.assertEqual(report.new_points, 3)
#         self.assertEqual(report.last_mag, 18.522156)
#
#     @patch('bhtom2.brokers.ztf.query_external_service',
#            return_value=sample_lightcurve_two_correct_lines_with_Nones)
#     def test_update_lightcurve_dont_save_none_magnitude(self, _):
#         ztf_broker: ZTFBroker = ZTFBroker()
#
#         target: Target = create_sample_target()
#
#         ztf_broker.process_reduced_data(target)
#
#         rd: List[ReducedDatum] = list(ReducedDatum.objects.all())
#
#         self.assertEqual(len(rd), 1)
