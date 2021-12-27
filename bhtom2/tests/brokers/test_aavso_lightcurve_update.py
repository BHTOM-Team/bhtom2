import json
from decimal import Decimal
from typing import List, Dict, Any
from unittest.mock import patch

from django.test import TestCase
from tom_dataproducts.models import ReducedDatum, DataProduct, DataProductGroup
from tom_observations.models import ObservationGroup, ObservationRecord
from tom_targets.models import Target

from bhtom2.brokers.aavso_lightcurve_update import AAVSOLightcurveUpdate
from bhtom2.brokers.lightcurve_update import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS


sample_lightcurve_two_correct_lines = """
JD~mag~uncert~band~by~comCode~compStar1~compStar2~charts~comment~transformed~airmass~val~cmag~kmag~starName~obsAffil~mtype~adsRef~digitizer~credit~obsID~fainterThan~obsType~software~obsName~obsCountry
2459233.548478~13.068~0.011~V~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.074~Z~18.646~18.936~GAIA20FNR~Facility~STD~~~~1285239870~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname, Firstname~BE
2459233.549045~13.087~0.010~V~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.073~Z~18.634~18.934~GAIA20FNR~Facility~STD~~~~1285239871~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname, Firstname~BE
"""

sample_lightcurve_four_correct_lines = """
JD~mag~uncert~band~by~comCode~compStar1~compStar2~charts~comment~transformed~airmass~val~cmag~kmag~starName~obsAffil~mtype~adsRef~digitizer~credit~obsID~fainterThan~obsType~software~obsName~obsCountry
2459233.548478~13.068~0.011~V~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.074~Z~18.646~18.936~GAIA20FNR~Facility~STD~~~~1285239870~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname, Firstname~BE
2459233.549045~13.087~0.010~I~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.073~Z~18.634~18.934~GAIA20FNR~Facility~STD~~~~1285239871~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname, Firstname~BE
2459233.548478~13.068~0.011~V~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.074~Z~18.646~18.936~GAIA20FNR~Facility2~STD~~~~1285239870~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname2, Firstname2~BE
2459233.549045~13.087~0.010~V~HMB~~UCAC4 355-010729~UCAC4 355-010648~~STANDARD MAG: C = 12.907 K = 13.254~0~1.073~Z~18.634~18.934~GAIA20FNR~Facility~STD~~~~1285239871~0~CCD~LESVEPHOTOMETRY V1.2.0.118~Surname3, Firstname3~BE
"""


def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia20fnr",
        ra=Decimal(90.267),
        dec=Decimal(-18.9677),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(extras={TARGET_NAME_KEYS[DataSource.AAVSO]: "Gaia20fnr"})

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(extras={TARGET_NAME_KEYS[DataSource.AAVSO]: "Gaia21een"})

    return target


class AAVSOLightcurveUpdateTestCase(TestCase):

    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_dont_update_lightcurve_when_no_gaia_name(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = aavso_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 0)
        self.assertEqual(report.new_points, 0)
        self.assertEqual(report.last_jd, None)
        self.assertEqual(report.last_mag, None)

    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_update_lightcurve(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = create_sample_target()

        report: LightcurveUpdateReport = aavso_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 2)

        first_value: Dict[Any, Any] = json.loads(rd[0].value)

        self.assertEqual(first_value['magnitude'], 13.068)
        self.assertEqual(first_value['filter'], 'V(AAVSO)')
        self.assertAlmostEqual(first_value['error'], 0.011, 3)
        self.assertAlmostEqual(first_value['jd'], 2459233.548478, 6)
        self.assertEqual(rd[0].data_type, 'photometry')
        self.assertEqual(rd[0].target, target)
        self.assertEqual(report.new_points, 2)
        self.assertEqual(report.last_jd, 2459233.549045)
        self.assertEqual(report.last_mag, 13.087)

    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_create_dataproduct(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = create_sample_target()

        aavso_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product
        dp_group: DataProductGroup = dp.group.all()[0]

        self.assertEqual(dp.target, target)
        self.assertEqual(dp.data_product_type, "photometry")
        self.assertEqual(dp.extra_data, json.dumps({"observer": "Surname, Firstname"}))
        self.assertEqual(dp_group.name, "AAVSO")

    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_create_observation_record(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = create_sample_target()

        aavso_lightcurve_update.update_lightcurve(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        dp: DataProduct = rd[0].data_product

        obs: ObservationRecord = dp.observation_record

        obs_group: ObservationGroup = obs.observationgroup_set.all()[0]

        self.assertEqual(obs.target, target)
        self.assertEqual(obs.user, None)
        self.assertEqual(obs.facility, "Facility")
        self.assertEqual(obs_group.name, "AAVSO")


    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_four_correct_lines)
    def test_only_one_dataproduct_per_filter_and_observer_created_for_multiple_updates_for_one_target(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()
        aavso_lightcurve_update_2: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = create_sample_target()

        aavso_lightcurve_update.update_lightcurve(target)
        aavso_lightcurve_update.update_lightcurve(target)
        aavso_lightcurve_update_2.update_lightcurve(target)

        data_products: List[DataProduct] = list(DataProduct.objects.all().filter(target=target))
        data_product_group: List[DataProductGroup] = list(DataProductGroup.objects.all().filter(name="AAVSO"))

        self.assertEqual(len(data_products), 4)
        self.assertEqual(len(data_product_group), 1)


    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_four_correct_lines)
    def test_only_one_dataproduct_group_created_for_updates_for_two_targets(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target1: Target = create_sample_target()
        target2: Target = create_second_sample_target()

        aavso_lightcurve_update.update_lightcurve(target1)
        aavso_lightcurve_update.update_lightcurve(target2)

        data_product_group: List[DataProductGroup] = list(DataProductGroup.objects.all().filter(name="AAVSO"))
        data_products: List[DataProduct] = list(data_product_group[0].dataproduct_set.all())

        self.assertEqual(len(data_product_group), 1)
        self.assertEqual(len(data_products), 8)


    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_four_correct_lines)
    def test_only_one_observation_record_per_filter_and_facility_created_for_multiple_updates_for_one_target(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()
        aavso_lightcurve_update_2: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target: Target = create_sample_target()

        aavso_lightcurve_update.update_lightcurve(target)
        aavso_lightcurve_update.update_lightcurve(target)
        aavso_lightcurve_update_2.update_lightcurve(target)

        observation_record: List[ObservationRecord] = list(ObservationRecord.objects.all().filter(target=target))
        observation_group: List[ObservationGroup] = list(ObservationGroup.objects.all().filter(name="AAVSO"))

        self.assertEqual(len(observation_record), 3)
        self.assertEqual(len(observation_group), 1)


    @patch('bhtom2.brokers.aavso_lightcurve_update.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_only_one_observation_record_group_created_for_updates_for_two_targets(self, _):

        aavso_lightcurve_update: AAVSOLightcurveUpdate = AAVSOLightcurveUpdate()

        target1: Target = create_sample_target()
        target2: Target = create_second_sample_target()

        aavso_lightcurve_update.update_lightcurve(target1)
        aavso_lightcurve_update.update_lightcurve(target2)

        observation_group: List[ObservationGroup] = list(ObservationGroup.objects.all().filter(name="AAVSO"))
        observation_records: List[ObservationRecord] = list(observation_group[0].observation_records.all())

        self.assertEqual(len(observation_group), 1)
        self.assertEqual(len(observation_records), 2)
