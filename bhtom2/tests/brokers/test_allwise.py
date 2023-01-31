from decimal import Decimal
from typing import List
from unittest.mock import patch

from django.test import TestCase
from bhtom2.brokers.allwise import ALLWISEBroker
from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from bhtom_base.bhtom_targets.models import Target, TargetName

from bhtom2.brokers.bhtom_broker import LightcurveUpdateReport
from bhtom2.external_service.data_source_information import DataSource
from bhtom2.brokers.gaia_alerts import GaiaAlertsBroker

sample_response = """\                                                                               
\fixlen = T
\RowsRetrieved =                34
\ORIGIN  = 'IPAC Infrared Science Archive (IRSA), Caltech/JPL'
\SIMULATED_TABLE  = 'n'
\DATETIME= '2023-01-29 09:40:15'
\DataTag = 'ADS/IRSA.Gator#2023/0129/094015_11516'
\DATABASE= 'AllWISE Multiepoch Photometry Table (allwise_p3as_mep)'
\EQUINOX = 'J2000'
\SKYAREA = 'within 5 arcsec of  ra=90.26700 dec=-18.96770 Eq J2000 '
\StatusFile = '/workspace/TMP_6znnFJ_5024/Gator/irsa/11516/log.11516.html'
\SQL     = 'WHERE (no constraints) 
\SQL     = 'SELECT (9 column names follow in next row.)'
\ 
\ ra (deg) 
\ ___ right ascension (J2000)
\ dec (deg) 
\ ___ declination (J2000)
\ clon 
\ ___ Right ascention in Sexagesimal format.
\ clat 
\ ___ Declination in Sexagesimal format.
\ mjd (day) 
\ ___ modified Julian date of the mid-point of the observation of the frame
\ w1mpro_ep (mag) 
\ ___ Single-exposure profile-fit  magnitude, band 1
\ w1sigmpro_ep (mag) 
\ ___ Single-exposure profile-fit photometric measurement uncertainty, band 1
\ w2mpro_ep (mag) 
\ ___ Single-exposure profile-fit  magnitude, band 2
\ w2sigmpro_ep (mag) 
\ ___ Single-exposure profile-fit photometric measurement uncertainty, band 2
\ dist (arcsec) 
\ ___ Distance between the target position and each source in arcsec.
\ angle (deg) 
\ ___ Position Angle in degree.
\ 
|          ra|         dec|          clon|          clat|            mjd| w1mpro_ep| w1sigmpro_ep| w2mpro_ep| w2sigmpro_ep|           dist|       angle|
|      double|      double|          char|          char|         double|    double|       double|    double|       double|         double|      double|
|         deg|         deg|              |              |            day|       mag|          mag|       mag|          mag|         arcsec|         deg|
|        null|        null|          null|          null|           null|      null|         null|      null|         null|           null|        null|
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.66928720     10.804         0.025     10.943         0.025        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.73537550     10.800         0.021     10.870         0.031        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.80159120     10.839         0.023     10.896         0.031        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.86767960     10.792         0.027     10.857         0.027        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55271.00011090     10.803         0.029     10.851         0.030        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.00763990     10.809         0.024     10.855         0.031        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.60307150     10.814         0.022     10.826         0.025        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.27224790     10.777         0.021     10.881         0.031        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.33846360     10.844         0.030     10.889         0.029        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.40455190     10.811         0.023     10.862         0.024        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.47076760     10.817         0.030     10.895         0.035        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.53685580     10.788         0.024     10.885         0.023        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.53698320     10.808         0.028     10.878         0.028        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55270.13994390     10.803         0.022     10.870         0.025        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55470.02452760     10.893         0.027     10.852         0.030        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.55132680     10.827         0.028     10.867         0.032        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55271.13241490     10.777         0.025     10.861         0.027        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55271.26471880     10.815         0.026     10.853         0.025        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.29476180     10.830         0.025     10.859         0.036        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.42706590     10.761         0.096     10.906         0.027        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.55937000     10.814         0.029     10.918         0.033        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.69167410     10.754         0.029     10.908         0.031        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.75776240     10.797         0.028     10.849         0.035        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.82385080     10.760         0.024     10.885         0.026        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.89006660     10.787         0.027     10.913         0.030        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55461.95615500     10.848         0.039     10.868         0.026        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.02224340     10.783         0.029     10.907         0.027        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.08845900     10.830         0.025     10.922         0.037        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.15454740     10.810         0.028     11.044         0.034        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.22063580     10.772         0.037     10.867         0.026        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.22076310     10.829         0.027     10.923         0.036        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.28685150     10.774         0.025     10.911         0.029        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55462.41915560     10.821         0.033     10.913         0.027        0.123135   161.294692 
   90.2670116  -18.9677324   06h01m04.08s  -18d58m03.84s  55470.02465490     10.887         0.028     10.983         0.035        0.123135   161.294692
"""

sample_response_no_coverage="""\                                                                               
\fixlen = T
\RowsRetrieved =                 0
\ORIGIN  = 'IPAC Infrared Science Archive (IRSA), Caltech/JPL'
\SIMULATED_TABLE  = 'n'
\DATETIME= '2023-01-30 15:28:24'
\DataTag = 'ADS/IRSA.Gator#2023/0130/152824_3334'
\DATABASE= 'AllWISE Multiepoch Photometry Table (allwise_p3as_mep)'
\EQUINOX = 'J2000'
\SKYAREA = 'within 5 arcsec of  ra=0.00000 dec=+0.00000 Eq J2000 '
\StatusFile = '/workspace/TMP_6znnFJ_5024/Gator/irsa/3334/log.3334.html'
\SQL     = 'WHERE (no constraints) 
\SQL     = 'SELECT (9 column names follow in next row.)'
\ 
\ ra (deg) 
\ ___ right ascension (J2000)
\ dec (deg) 
\ ___ declination (J2000)
\ clon 
\ ___ Right ascention in Sexagesimal format.
\ clat 
\ ___ Declination in Sexagesimal format.
\ mjd (day) 
\ ___ modified Julian date of the mid-point of the observation of the frame
\ w1mpro_ep (mag) 
\ ___ Single-exposure profile-fit  magnitude, band 1
\ w1sigmpro_ep (mag) 
\ ___ Single-exposure profile-fit photometric measurement uncertainty, band 1
\ w2mpro_ep (mag) 
\ ___ Single-exposure profile-fit  magnitude, band 2
\ w2sigmpro_ep (mag) 
\ ___ Single-exposure profile-fit photometric measurement uncertainty, band 2
\ dist (arcsec) 
\ ___ Distance between the target position and each source in arcsec.
\ angle (deg) 
\ ___ Position Angle in degree.
\ 
|          ra|         dec|          clon|          clat|            mjd| w1mpro_ep| w1sigmpro_ep| w2mpro_ep| w2sigmpro_ep|           dist|       angle|
|      double|      double|          char|          char|         double|    double|       double|    double|       double|         double|      double|
|         deg|         deg|              |              |            day|       mag|          mag|       mag|          mag|         arcsec|         deg|
|        null|        null|          null|          null|           null|      null|         null|      null|         null|           null|        null|
"""

def create_sample_target() -> Target:
    target: Target = Target(
        name="Gaia20fnr",
        ra=Decimal(90.2670097),
        dec=Decimal(-18.967703),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save()
    TargetName.objects.create(target=target, source_name=DataSource.GAIA.name, name='Gaia20fnr')

    return target


def create_second_sample_target() -> Target:
    target: Target = Target(
        name="GaiaXXX",
        ra=Decimal(95.2670097),
        dec=Decimal(-20.967703),
        type='SIDEREAL',
        epoch=2000,
    )

    target.save(names={DataSource.GAIA.name: "GaiaXXX"})

    return target


class ALLWISELightcurveUpdateTestCase(TestCase):
    
    @patch('bhtom2.brokers.allwise.query_external_service',
           return_value=sample_response)
    def test_update_allwise_with_coverage(self, _):

        allwise_broker: ALLWISEBroker = ALLWISEBroker()

        target: Target = Target(
            name="Gaia20fnr",
            ra=Decimal(90.2670097),
            dec=Decimal(-18.967703),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = allwise_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        print("TESTRD",rd)

        self.assertEqual(len(rd), 68)
        self.assertEqual(report.new_points, 68)

    
    @patch('bhtom2.brokers.allwise.query_external_service',
           return_value=sample_response_no_coverage)
    def test_update_allwise_no_coverage(self, _):

        allwise_broker: ALLWISEBroker = ALLWISEBroker()

        target: Target = Target(
            name="Gaia21een",
            ra=Decimal(113.25287),
            dec=Decimal(-31.98319),
            type='SIDEREAL',
            epoch=2000,
        )

        target.save()

        report: LightcurveUpdateReport = allwise_broker.process_reduced_data(target)

        rd: List[ReducedDatum] = list(ReducedDatum.objects.all())

        self.assertEqual(len(rd), 0)
        self.assertEqual(report.new_points, 0)
