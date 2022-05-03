from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom_base.tom_dataproducts.models import ReducedDatum
from bhtom_base.tom_targets.models import Target

from bhtom2.brokers.aavso import AAVSOBroker
from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
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


class AAVSOBrokerTestCase(TestCase):

    @patch('bhtom2.brokers.aavso.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_dont_update_lightcurve_when_no_aavso_name(self, _):

        aavso_broker: AAVSOBroker = AAVSOBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = aavso_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 0)
        self.assertEqual(report.new_points, 0)
        self.assertEqual(report.last_jd, None)
        self.assertEqual(report.last_mag, None)

    @patch('bhtom2.brokers.aavso.query_external_service',
           return_value=sample_lightcurve_two_correct_lines)
    def test_update_lightcurve(self, _):

        aavso_broker: AAVSOBroker = AAVSOBroker()

        target: Target = create_sample_target()

        report: LightcurveUpdateReport = aavso_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all().order_by('mjd'))

        rd: List[ReducedDatum]

        self.assertEqual(rd[0].value, 13.068)
        self.assertEqual(rd[0].filter, 'V(AAVSO)')
        self.assertAlmostEqual(rd[0].error, 0.011, 3)
        self.assertAlmostEqual(rd[0].mjd, 59233.048478, 6)
        self.assertEqual(rd[0].data_type, 'photometry')
        self.assertEqual(rd[0].target, target)

        self.assertEqual(report.new_points, 2)
        self.assertEqual(report.last_jd, 2459233.549045)
        self.assertEqual(report.last_mag, 13.087)
