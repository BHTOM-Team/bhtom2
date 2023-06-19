from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom2.brokers.cpcs import CPCSBroker
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target, TargetName, TargetExtra

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import TARGET_NAME_KEYS, DataSource
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

sample_response = """
{"magerr": [-1.0, -1.0, 0.08244965970516205], "catalog": ["APASS", "APASS", "APASS"], "mag": [20.23844337463379, 19.472387313842773, 18.653060913085938], "hashtag": ["LHardy_pt5m_c6ddcf76393ed9bfd1978affaeb54fd5", "LHardy_pt5m_c6ddcf76393ed9bfd1978affaeb54fd5", "LHardy_pt5m_c6ddcf76393ed9bfd1978affaeb54fd5"], "id": [163840, 163841, 163842], "mjd": [58728.947504, 58728.952083, 58728.955911], "observatory": ["Liam Hardy pt5m", "Liam Hardy pt5m", "Liam Hardy pt5m"], "filter": ["B", "V", "r"], "alert_name": "ivo://Gaia19drz", "caliberr": [0.06757491081953049, 0.30385541915893555, 0.12389542907476425], "observatory_id": [59, 59, 59]}
"""

def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia21edy",
        ra=Decimal(295.16969),
        dec=Decimal(14.58495),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save()
    TargetName.objects.create(target=target, source_name=DataSource.CPCS.name, name='ivo://Gaia21edy')

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
    TargetName.objects.create(target=target, source_name=DataSource.CPCS.name, name='ivo://Gaia21een')

    return target


class CPCSLightcurveUpdateTestCase(TestCase):
    
    @patch('bhtom2.brokers.catalina.query_external_service',
           return_value=sample_response)
    def test_update_cpcs(self, _):

        cpcs_broker: CPCSBroker = CPCSBroker()

        target=create_sample_target()
        # target: Target = Target(
        #     name="Gaia21een",
        #     ra=Decimal(113.25287),
        #     dec=Decimal(-31.98319),
        #     type='SIDEREAL',
        #     epoch=2000,
        # )

        # inventName="ivo://"+target.name

        # TargetName.objects.create(target=target, source_name=DataSource.CPCS.name, name=inventName)

        # target.save()

        cpcs_name = TargetName.objects.get(target=target, source_name=DataSource.CPCS.name)
        print("CPCS NAME: ",cpcs_name.name)
        self.assertEqual(cpcs_name.name, "ivo://Gaia21edy")

        report: LightcurveUpdateReport = cpcs_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())
        print("LEN: ",len(rd), report.new_points)
        self.assertEqual(len(rd), 172)
        self.assertEqual(report.new_points, 172)
  
  