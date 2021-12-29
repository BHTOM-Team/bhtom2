from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

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

    target.save(extras={TARGET_NAME_KEYS[DataSource.Gaia]: "Gaia21edy"})

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(extras={TARGET_NAME_KEYS[DataSource.Gaia]: "Gaia21een"})

    return target


class GaiaLightcurveUpdateTestCase(TestCase):

    @patch('bhtom2.brokers.gaia_alerts.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_dont_update_lightcurve_when_no_gaia_name(self, _):

        gaia_alerts_broker: GaiaAlertsBroker = GaiaAlertsBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = gaia_alerts_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 0)
        self.assertEqual(report.new_points, 0)
        self.assertEqual(report.last_jd, None)
        self.assertEqual(report.last_mag, None)

    @patch('bhtom2.brokers.gaia_alerts.query_external_service',
           return_value=sample_lightcurve_three_correct_lines)
    def test_update_lightcurve(self, _):

        gaia_alerts_broker: GaiaAlertsBroker = GaiaAlertsBroker()

        target: Target = create_sample_target()

        report: LightcurveUpdateReport = gaia_alerts_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 1)

        self.assertEqual(rd[0].value, {
            'magnitude': 18.91,
            'filter': 'g(Gaia)',
            'error': -1.3434,
            'jd': 2456961.56970,
            'observer': 'Gaia',
            'facility': 'Gaia'
        })
        self.assertEqual(rd[0].data_type, 'photometry')
        self.assertEqual(rd[0].target, target)
        self.assertEqual(report.new_points, 1)
        self.assertEqual(report.last_jd, 2456961.56970)
        self.assertEqual(report.last_mag, 18.91)
