from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom2.brokers.sdss import SDSSBroker
from bhtom2.external_service.connectWSDB import WSDBConnection
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target, TargetName

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

sample_response = [(52258.30247521,
 20.957407, 20.80408, 20.706472, 20.855112, 0.044929855,  0.05652531,  0.05668118,  0.24416567,
  52258.29915815, 52258.29998742, 52258.30164595,52258.30081668,21.230421,0.12558867)]

def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save()
    TargetName.objects.create(target=target, source_name=DataSource.GAIA_ALERTS.name, name='Gaia21edy')

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(names={DataSource.GAIA_ALERTS.name: "Gaia21een"})

    return target


class SDSSLightcurveUpdateTestCase(TestCase):
    
    @patch('bhtom2.brokers.sdss.WSDBConnection.run_query',
           return_value=sample_response)
    def test_dont_update_lightcurve_when_no_gaia_name(self, _):

        sdss_broker: SDSSBroker = SDSSBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = sdss_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 5)
        self.assertEqual(report.new_points, 5)


