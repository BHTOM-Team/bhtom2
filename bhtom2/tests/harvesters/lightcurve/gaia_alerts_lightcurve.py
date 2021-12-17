import json
from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from tom_dataproducts.models import ReducedDatum, DataProduct, DataProductGroup
from tom_observations.models import ObservationGroup, ObservationRecord
from tom_targets.models import Target

from bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve import update_gaia_lc

sample_file_two_lines = """
#Name, Date, RaDeg, DecDeg, AlertMag, HistoricMag, HistoricStdDev, Class, Published, Comment, TNSid
Gaia21eeo,2021-09-07 02:07:38,111.55315,-39.30836,18.70,20.22,0.64,"unknown",2021-09-09 08:19:08,"~2 mag brightening in a faint Gaia source",AT2021yjn
Gaia21een,2021-09-07 01:59:33,113.25287,-31.98319,17.82,20.04,0.72,"unknown",2021-09-09 08:19:02,"3 mag outburst in Gaia source, previous events seen, candidate CV",AT2021yjm
"""

sample_file_three_lines = """
#Name, Date, RaDeg, DecDeg, AlertMag, HistoricMag, HistoricStdDev, Class, Published, Comment, TNSid
Gaia21eeo,2021-09-07 02:07:38,111.55315,-39.30836,18.70,20.22,0.64,"unknown",2021-09-09 08:19:08,"~2 mag brightening in a faint Gaia source",AT2021yjn
Gaia21een,2021-09-07 01:59:33,113.25287,-31.98319,17.82,20.04,0.72,"unknown",2021-09-09 08:19:02,"3 mag outburst in Gaia source, previous events seen, candidate CV",AT2021yjm
Gaia21edy,2021-09-06 16:50:31,295.16969,14.58495,17.17,19.29,0.73,"unknown",2021-09-07 22:18:30,"outburst of candidate CV MGAB-V829",AT2021ygr
"""

sample_lightcurve_three_correct_lines = """
#Date JD(TCB) averagemag
2014-09-19 02:49:08,2456919.61745,untrusted
2014-09-20 02:49:08,2456920.61745,NaN
2014-10-31 1:40:22,2456961.56970,18.91
"""


def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.gaia_alert_name = "Gaia21edy"

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.gaia_alert_name = "Gaia21een"

    return target


class TestGaiaAlertsLightcurve(TestCase):

    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_update_lightcurve(self, _):

        target: Target = create_sample_target()

        target.save()

        update_gaia_lc(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 1)

        self.assertEqual(rd[0].value, json.dumps({
            'magnitude': 18.91,
            'filter': 'G_Gaia',
            'error': 0,
            'jd': 2456961.56970
        }))
        self.assertEqual(rd[0].data_type, 'photometry')
        self.assertEqual(rd[0].target, target)

    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_create_dataproduct(self, _):

        target: Target = create_sample_target()

        target.save()

        update_gaia_lc(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product
        dp_group: DataProductGroup = dp.group.all()[0]

        self.assertEqual(dp.target, target)
        self.assertEqual(dp.data_product_type, "photometry")
        self.assertEqual(dp.extra_data, json.dumps({"observer": "Gaia"}))
        self.assertEqual(dp_group.name, "Gaia")

    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_create_observation_record(self, _):

        target: Target = create_sample_target()

        target.save()

        update_gaia_lc(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product

        obs: ObservationRecord = dp.observation_record

        obs_group: ObservationGroup = obs.observationgroup_set.all()[0]

        self.assertEqual(obs.target, target)
        self.assertEqual(obs.user, None)
        self.assertEqual(obs.facility, "Gaia")
        self.assertEqual(obs_group.name, "Gaia")


    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_only_one_dataproduct_created_for_multiple_updates_for_one_target(self, _):

        target: Target = create_sample_target()

        target.save()

        update_gaia_lc(target)
        update_gaia_lc(target)

        data_products: List[DataProduct] = list(DataProduct.objects.all().filter(target=target))
        data_product_group: List[DataProductGroup] = list(DataProductGroup.objects.all().filter(name="Gaia"))

        self.assertEqual(len(data_products), 1)
        self.assertEqual(len(data_product_group), 1)


    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_only_one_dataproduct_group_created_for_updates_for_two_targets(self, _):

        target1: Target = create_sample_target()
        target2: Target = create_second_sample_target()

        target1.save()
        target2.save()

        update_gaia_lc(target1)
        update_gaia_lc(target2)

        data_product_group: List[DataProductGroup] = list(DataProductGroup.objects.all().filter(name="Gaia"))
        data_products: List[DataProduct] = list(data_product_group[0].dataproduct_set.all())

        self.assertEqual(len(data_product_group), 1)
        self.assertEqual(len(data_products), 2)


    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_only_one_observation_record_created_for_multiple_updates_for_one_target(self, _):

        target: Target = create_sample_target()

        target.save()

        update_gaia_lc(target)
        update_gaia_lc(target)

        observation_record: List[ObservationRecord] = list(ObservationRecord.objects.all().filter(target=target))
        observation_group: List[ObservationGroup] = list(ObservationGroup.objects.all().filter(name="Gaia"))

        self.assertEqual(len(observation_record), 1)
        self.assertEqual(len(observation_group), 1)


    @patch('bhtom2.harvesters.lightcurve.gaia_alerts_lightcurve.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_only_one_observation_record_group_created_for_updates_for_two_targets(self, _):

        target1: Target = create_sample_target()
        target2: Target = create_second_sample_target()

        target1.save()
        target2.save()

        update_gaia_lc(target1)
        update_gaia_lc(target2)

        observation_group: List[ObservationGroup] = list(ObservationGroup.objects.all().filter(name="Gaia"))
        observation_records: List[ObservationRecord] = list(observation_group[0].observation_records.all())

        self.assertEqual(len(observation_group), 1)
        self.assertEqual(len(observation_records), 2)
