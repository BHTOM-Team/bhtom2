from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom2.brokers.linear import LINEARBroker
from bhtom2.external_service.connectWSDB import WSDBConnection
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target, TargetName

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

import numpy as np
import warnings
import astropy.io.ascii
import psycopg2
from io import StringIO

sample_response = [(52288,
  20.113611,
  0.025659233)]

def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save()
    TargetName.objects.create(target=target, source_name=DataSource.GAIA.name, name='Gaia21edy')

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21een",
        ra=Decimal(113.25287),
        dec=Decimal(-31.98319),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(names={DataSource.GAIA.name: "Gaia21een"})

    return target


class LINEARLightcurveUpdateTestCase(TestCase):
    
    @patch('bhtom2.brokers.linear.WSDBConnection.run_query',
           return_value=sample_response)
    def test_dont_update_lightcurve_when_no_gaia_name(self, _):

        linear_broker: LINEARBroker = LINEARBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = linear_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 1)
        self.assertEqual(report.new_points, 1)

