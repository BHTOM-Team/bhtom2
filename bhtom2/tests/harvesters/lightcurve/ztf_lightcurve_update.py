import json
from decimal import Decimal
from typing import List, Set
from unittest.mock import patch

from django.test import TestCase
from tom_dataproducts.models import ReducedDatum, DataProduct, DataProductGroup
from tom_observations.models import ObservationRecord, ObservationGroup
from tom_targets.models import Target

from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.harvesters.lightcurve.lightcurve_update import LightcurveUpdateReport
from bhtom2.harvesters.lightcurve.ztf_lightcurve_update import ZTFLightcurveUpdate

sample_lightcurve_two_correct_lines = {'detections': [{'mjd': 59550.28425930021,
                                                       'candid': '1796284252615015007',
                                                       'fid': 1,
                                                       'pid': 1796284252615,
                                                       'diffmaglim': 20.5075,
                                                       'isdiffpos': 1,
                                                       'nid': 1796,
                                                       'distnr': 0.25123456,
                                                       'magpsf': 18.648088,
                                                       'magpsf_corr': 18.492537,
                                                       'magpsf_corr_ext': None,
                                                       'magap': 18.6157,
                                                       'magap_corr': None,
                                                       'sigmapsf': 0.087919265,
                                                       'sigmapsf_corr': 0.07564124,
                                                       'sigmapsf_corr_ext': 0.07618386,
                                                       'sigmagap': 0.0698,
                                                       'sigmagap_corr': None,
                                                       'ra': 121.6741244,
                                                       'dec': 38.878892,
                                                       'rb': 0.95,
                                                       'rbversion': 't17_f5_c3',
                                                       'drb': 0.99997854,
                                                       'magapbig': 18.5526,
                                                       'sigmagapbig': 0.0835,
                                                       'rfid': 708120126,
                                                       'has_stamp': True,
                                                       'corrected': True,
                                                       'dubious': False,
                                                       'candid_alert': None,
                                                       'step_id_corr': 'correction_1.0.6',
                                                       'phase': 0.0,
                                                       'parent_candid': None},
                                                      {'mjd': 59550.38187499996,
                                                       'candid': '1796381872615015011',
                                                       'fid': 2,
                                                       'pid': 1796381872615,
                                                       'diffmaglim': 20.624456,
                                                       'isdiffpos': 1,
                                                       'nid': 1796,
                                                       'distnr': 0.32544687,
                                                       'magpsf': 18.716454,
                                                       'magpsf_corr': 18.522156,
                                                       'magpsf_corr_ext': None,
                                                       'magap': 18.7526,
                                                       'magap_corr': None,
                                                       'sigmapsf': 0.07501104,
                                                       'sigmapsf_corr': 0.06242632,
                                                       'sigmapsf_corr_ext': 0.06272002,
                                                       'sigmagap': 0.0744,
                                                       'sigmagap_corr': None,
                                                       'ra': 121.6740928,
                                                       'dec': 38.8788868,
                                                       'rb': 0.9442857,
                                                       'rbversion': 't17_f5_c3',
                                                       'drb': 0.9999511,
                                                       'magapbig': 18.6753,
                                                       'sigmagapbig': 0.088,
                                                       'rfid': 708120226,
                                                       'has_stamp': True,
                                                       'corrected': True,
                                                       'dubious': False,
                                                       'candid_alert': None,
                                                       'step_id_corr': 'correction_1.0.6',
                                                       'phase': 0.0,
                                                       'parent_candid': None}],
                                       'non_detections': [{'mjd': 59522.34593749978,
                                                           'fid': 2,
                                                           'diffmaglim': 20.4739},
                                                          {'mjd': 59522.454074100126, 'fid': 1, 'diffmaglim': 20.8706},
                                                          {'mjd': 59524.44842590019, 'fid': 2, 'diffmaglim': 20.6626},
                                                          {'mjd': 59524.516979199834, 'fid': 1, 'diffmaglim': 20.9345},
                                                          {'mjd': 59526.450405099895, 'fid': 1, 'diffmaglim': 20.8343},
                                                          {'mjd': 59526.50885420013, 'fid': 2, 'diffmaglim': 20.5514},
                                                          {'mjd': 59529.415011600126, 'fid': 2, 'diffmaglim': 20.2561},
                                                          {'mjd': 59529.51506939996, 'fid': 1, 'diffmaglim': 20.4769},
                                                          {'mjd': 59531.393124999944, 'fid': 1, 'diffmaglim': 20.7168},
                                                          {'mjd': 59531.44623839995, 'fid': 2, 'diffmaglim': 20.6564},
                                                          {'mjd': 59536.43453700002, 'fid': 1, 'diffmaglim': 19.5238},
                                                          {'mjd': 59536.488622699864, 'fid': 2, 'diffmaglim': 20.0576},
                                                          {'mjd': 59538.3020601999, 'fid': 2, 'diffmaglim': 19.4798},
                                                          {'mjd': 59538.39106479986, 'fid': 1, 'diffmaglim': 19.4221}]}

sample_lightcurve_two_correct_lines_with_Nones = {'detections': [{'mjd': 59550.28425930021,
                                                                  'candid': '1796284252615015007',
                                                                  'fid': 1,
                                                                  'pid': 1796284252615,
                                                                  'diffmaglim': 20.5075,
                                                                  'isdiffpos': 1,
                                                                  'nid': 1796,
                                                                  'distnr': 0.25123456,
                                                                  'magpsf': 18.648088,
                                                                  'magpsf_corr': None,
                                                                  'magpsf_corr_ext': None,
                                                                  'magap': 18.6157,
                                                                  'magap_corr': None,
                                                                  'sigmapsf': 0.087919265,
                                                                  'sigmapsf_corr': 0.07564124,
                                                                  'sigmapsf_corr_ext': 0.07618386,
                                                                  'sigmagap': 0.0698,
                                                                  'sigmagap_corr': None,
                                                                  'ra': 121.6741244,
                                                                  'dec': 38.878892,
                                                                  'rb': 0.95,
                                                                  'rbversion': 't17_f5_c3',
                                                                  'drb': 0.99997854,
                                                                  'magapbig': 18.5526,
                                                                  'sigmagapbig': 0.0835,
                                                                  'rfid': 708120126,
                                                                  'has_stamp': True,
                                                                  'corrected': True,
                                                                  'dubious': False,
                                                                  'candid_alert': None,
                                                                  'step_id_corr': 'correction_1.0.6',
                                                                  'phase': 0.0,
                                                                  'parent_candid': None},
                                                                 {'mjd': 59550.38187499996,
                                                                  'candid': '1796381872615015011',
                                                                  'fid': 2,
                                                                  'pid': 1796381872615,
                                                                  'diffmaglim': 20.624456,
                                                                  'isdiffpos': 1,
                                                                  'nid': 1796,
                                                                  'distnr': 0.32544687,
                                                                  'magpsf': 18.716454,
                                                                  'magpsf_corr': 18.522156,
                                                                  'magpsf_corr_ext': None,
                                                                  'magap': 18.7526,
                                                                  'magap_corr': None,
                                                                  'sigmapsf': 0.07501104,
                                                                  'sigmapsf_corr': 0.06242632,
                                                                  'sigmapsf_corr_ext': 0.06272002,
                                                                  'sigmagap': 0.0744,
                                                                  'sigmagap_corr': None,
                                                                  'ra': 121.6740928,
                                                                  'dec': 38.8788868,
                                                                  'rb': 0.9442857,
                                                                  'rbversion': 't17_f5_c3',
                                                                  'drb': 0.9999511,
                                                                  'magapbig': 18.6753,
                                                                  'sigmagapbig': 0.088,
                                                                  'rfid': 708120226,
                                                                  'has_stamp': True,
                                                                  'corrected': True,
                                                                  'dubious': False,
                                                                  'candid_alert': None,
                                                                  'step_id_corr': 'correction_1.0.6',
                                                                  'phase': 0.0,
                                                                  'parent_candid': None}],
                                                  'non_detections': []}


def create_sample_target() -> Target:
    target: Target = Target(
        name="ZTF21acqpcmx",
        ra=Decimal(338.044708),
        dec=Decimal(-20.124389),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(extras={TARGET_NAME_KEYS[DataSource.ZTF]: "ZTF21acqpcmx"})

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="ZTF21acqspkc",
        ra=Decimal(121.674083),
        dec=Decimal(+38.878839),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(extras={TARGET_NAME_KEYS[DataSource.GAIA]: "ZTF21acqspkc"})

    return target


class TestZTFLightcurveUpdate(TestCase):

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_dont_update_lightcurve_when_no_ztf_name(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = Target(
            name="ZTF21acqpcmx",
            ra=Decimal(338.044708),
            dec=Decimal(-20.124389),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = ztf_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 0)
        self.assertEqual(report.new_points, 0)
        self.assertEqual(report.last_jd, None)
        self.assertEqual(report.last_mag, None)

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_update_lightcurve(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        target.save()

        report: LightcurveUpdateReport = ztf_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 2)

        self.assertEqual(rd[0].value, json.dumps({
            'magnitude': 18.492537,
            'filter': 'g(ZTF)',
            'error': 0.07564124,
            'jd': 2459550.78425930
        }))
        self.assertEqual(rd[0].data_type, 'photometry')
        self.assertEqual(rd[0].target, target)
        self.assertEqual(report.new_points, 2)
        self.assertEqual(report.last_jd, 2459550.88187500)
        self.assertEqual(report.last_mag, 18.522156)

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines_with_Nones)
    def test_update_lightcurve_dont_save_none_magnitude(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        ztf_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 1)

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_create_dataproduct(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        ztf_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product
        dp_group: DataProductGroup = dp.group.all()[0]

        self.assertEqual(dp.target, target)
        self.assertEqual(dp.data_product_type, "photometry")
        self.assertEqual(dp.extra_data, json.dumps({"observer": "ZTF"}))
        self.assertEqual(dp_group.name, "ZTF")

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_create_observation_record(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        ztf_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product

        obs: ObservationRecord = dp.observation_record

        obs_group: ObservationGroup = obs.observationgroup_set.all()[0]

        self.assertEqual(obs.target, target)
        self.assertEqual(obs.user, None)
        self.assertEqual(obs.facility, "ZTF")
        self.assertEqual(obs_group.name, "ZTF")

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_only_one_dataproduct_per_filter_created_for_multiple_updates_for_one_target(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()
        ztf_lightcurve_update2: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        target.save()

        ztf_lightcurve_update.update_lightcurve(target)
        ztf_lightcurve_update.update_lightcurve(target)
        ztf_lightcurve_update2.update_lightcurve(target)

        data_products: List[DataProduct] = list(DataProduct.objects.all().filter(target=target))
        data_product_group: List[DataProductGroup] = list(DataProductGroup.objects.all().filter(name="ZTF"))

        self.assertEqual(len(data_products), 2)
        self.assertEqual(len(data_product_group), 1)

    @patch('bhtom2.harvesters.lightcurve.ztf_lightcurve_update.Alerce.query_lightcurve',
           return_value=sample_lightcurve_two_correct_lines)
    def test_only_one_observation_record_per_filter_created_for_multiple_updates_for_one_target(self, _):
        ztf_lightcurve_update: ZTFLightcurveUpdate = ZTFLightcurveUpdate()
        ztf_lightcurve_update2: ZTFLightcurveUpdate = ZTFLightcurveUpdate()

        target: Target = create_sample_target()

        target.save()

        ztf_lightcurve_update.update_lightcurve(target)
        ztf_lightcurve_update.update_lightcurve(target)
        ztf_lightcurve_update2.update_lightcurve(target)

        observation_record: List[ObservationRecord] = list(ObservationRecord.objects.all().filter(target=target))
        observation_group: List[ObservationGroup] = list(ObservationGroup.objects.all().filter(name="ZTF"))

        filters: Set[str] = set([obr.parameters.get('filter') for obr in observation_record])

        self.assertEqual(len(observation_record), 2)
        self.assertEqual(filters, {'g(ZTF)', 'r(ZTF)'})

        self.assertEqual(len(observation_group), 1)
