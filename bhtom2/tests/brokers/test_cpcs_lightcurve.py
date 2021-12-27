import json
from decimal import Decimal
from typing import Dict, Any, List
from unittest.mock import patch

from django.test import TestCase

from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target

from bhtom2.brokers.cpcs_lightcurve import update_cpcs_lc


correct_three_points: Dict[str, Any] = {
    'mjd': [59481.8427481, 59481.8442782, 59483.1534276],
    'magerr': [0.004800000227987766,
               0.004800000227987766,
               0.006300000008195639],
    'alert_name': 'ivo://Gaia21efs',
    'observatory': ['Observatory1, Owner1', 'Observatory2, Owner2', 'Observatory1, Owner2'],
    'caliberr': [0.021286796778440475,
                 0.02218688279390335,
                 0.024377815425395966],
    'mag': [16.771121978759766, 16.77216339111328, 16.722705841064453],
    'catalog': ['APASS', 'APASS', 'DECAPS'],
    'filter': ['g', 'g', 'i'],
    'id': [220728, 220729, 220730]
}


class CPCSLightcurveTest(TestCase):

    @patch('bhtom2.harvesters.lightcurve.cpcs_lightcurve.query_external_service',
           return_value=json.dumps(correct_three_points))
    def test_save_three_datapoints_if_correct(self, _):
        target: Target = Target(
            name="Gaia21efs",
            ra=Decimal(307.42454),
            dec=Decimal(31.29525),
            type='SIDEREAL',
            epoch=2000,
        )

        target.calib_server_name = "ivo://Gaia21efs"
        target.save()

        # TODO: why is there an error while refreshing the ReducedDatumView?

        update_cpcs_lc(target)

        rds: ReducedDatum = ReducedDatum.objects.all()

        values: List[Dict[str, Any]] = [json.loads(rd.value) for rd in rds]
        mags: List[float] = [v['magnitude'] for v in values]
        filters: List[str] = [v['filter'] for v in values]

        self.assertEqual(len(rds), 3)
        self.assertListEqual(mags, [16.771121978759766, 16.77216339111328, 16.722705841064453])
        self.assertListEqual(filters, ['g(APASS)', 'g(APASS)', 'i(DECAPS)'])
