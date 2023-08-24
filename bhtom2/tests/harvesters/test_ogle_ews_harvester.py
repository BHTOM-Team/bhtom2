import os
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import patch

from django.test import TestCase

from django.conf import settings
from bhtom_base.bhtom_catalogs.harvester import MissingDataException
from bhtom_base.bhtom_targets.models import Target

from bhtom2.harvesters.ogleews import fetch_alerts_csv, search_term_in_ogleews_data, get, \
    OGLEEWSHarvester, cone_search


from pyfakefs.fake_filesystem_unittest import Patcher

from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException

from pandas import DataFrame

from astropy.coordinates import Angle, SkyCoord


#these are parts of lenses par
sample_lenspar_three_lines = """
\n
\n
2011-BLG-0001 BLG500.01 129412 17:54:00.05 -29:06:06.0
2011-BLG-0002 BLG500.08 102027 17:54:44.93 -28:54:13.5
2011-BLG-0003 BLG501.07 52013 17:49:39.07 -30:27:08.4
"""

#these are not lenspar, but cached files
sample_file_two_lines = """
2011-BLG-0001,BLG500.01,129412,17:54:00.05,-29:06:06.0
2011-BLG-0002,BLG500.08,102027,17:54:44.93,-28:54:13.5
"""

sample_file_three_lines = """
2011-BLG-0001,BLG500.01,129412,17:54:00.05,-29:06:06.0
2011-BLG-0002,BLG500.08,102027,17:54:44.93,-28:54:13.5
2011-BLG-0003,BLG501.07,52013,17:49:39.07,-30:27:08.4
"""

#2011-BLG-0001:
sample_lightcurve_three_correct_lines = """
2455260.85336 17.131 0.015 5.94 1033.0
2455260.90029 17.130 0.013 4.76 1123.0
2455261.79151 17.175 0.015 5.34 1026.0
"""

#test file, not the original one
OGLE_EWS_CACHE_FILE: str = os.path.join(settings.BASE_DIR, "bhtom2/cache/ogle_lenses.txt")


class TestOGLEEWSHarvester(TestCase):

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value="something,2,3,4,5")
    def test_create_csv_cache_file_if_not_present(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'bhtom2/cache'))
            fetch_alerts_csv()
            self.assertTrue(os.path.exists(OGLE_EWS_CACHE_FILE))

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value="\n\nsomething,2,3,4,5")
    def test_update_csv_cache_file_if_present(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            fetch_alerts_csv()
            self.assertEqual(open(OGLE_EWS_CACHE_FILE, 'r').readline().strip(), '"something,2,3,4,5"')

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_lenspar_three_lines)
    def test_raise_no_result_exception_if_csv_correct_and_doesnt_contain_term_and_alerts_dont_contain_term(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_two_lines)
            self.assertRaises(MissingDataException, search_term_in_ogleews_data, "Something")

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_file_three_lines)
    def test_return_term_if_csv_correct_and_doesnt_contain_term_and_alerts_correct(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_two_lines)
            self.assertRaises(MissingDataException, search_term_in_ogleews_data, "2011-BLG-0003")

            # term_data: DataFrame = search_term_in_ogleews_data("2011-BLG-0003")
            # self.assertEqual(term_data['name'], "2011-BLG-0003")
            # self.assertEqual(term_data['field'], 'BLG501.07')
            # self.assertEqual(term_data['starno'], 52013)


    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_file_three_lines)
    def test_return_term_if_csv_correct_and_contains_term(self, mocked_query):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_two_lines)
            term_data: DataFrame = search_term_in_ogleews_data("2011-BLG-0001")
            self.assertEqual(term_data['name'], "2011-BLG-0001")
            self.assertEqual(term_data['field'], 'BLG500.01')
            self.assertEqual(term_data['starno'], 129412)
            self.assertFalse(mocked_query.called)

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_file_three_lines)
    def test_get_term_dict_if_csv_correct_and_doesnt_contain_term_and_alerts_correct(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_two_lines)
            with self.assertRaises(MissingDataException):
                term_result: Dict[str, Any] = get("2011-BLG-0003")
            # expected_result: Dict[str, Any] = {
            #     "name": "2011-BLG-0003",
            #     "field": "BLG501.07",
            #     "starno": 52013,
            #     "ra": "17:49:39.07",
            #     "dec": "-30:27:08.4",
            # }
            # for key in ["name", "field", "starno","ra","dec"]:
            #     self.assertEqual(term_result[key], expected_result[key])

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_file_three_lines)
    def test_get_term_dict_if_csv_correct_and_contains_term(self, mocked_query):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_two_lines)
            term_result: Dict[str, Any] = get("2011-BLG-0001")
            print(term_result)
            expected_result: Dict[str, Any] = {
                "OGLE EWS name": "2011-BLG-0001",
                "field": "BLG500.01",
                "starno": 129412,
                "ra": "17:54:00.05",
                "dec": "-29:06:06.0",
            }
            for key in ["OGLE EWS name", "field", "starno","ra","dec"]:
                self.assertEqual(term_result[key], expected_result[key])
            # for key in ["ra", "dec"]:
            #     self.assertAlmostEqual(term_result[key], expected_result[key], 3)
            self.assertEqual(term_result, expected_result)
            self.assertFalse(mocked_query.called)

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_lenspar_three_lines)
    def test_get_target_if_csv_correct_and_doesnt_contain_term_and_alerts_correct(self, _):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_three_lines)

            harvester = OGLEEWSHarvester()
            harvester.query("2011-BLG-0003")
            target: Target = harvester.to_target()

            expected_target: Target = Target(name="2011-BLG-0003",
                                             ra=float(267.4127916666667),
                                             dec=float(-30.452333333333332),
                                             type='SIDEREAL',
                                             epoch=2000, )

            self.assertEqual(target.name, expected_target.name)
            self.assertAlmostEqual(target.ra, expected_target.ra,3)
            self.assertAlmostEqual(target.dec, expected_target.dec,3)
            self.assertEqual(target.type, expected_target.type)
            self.assertEqual(target.epoch, expected_target.epoch)

    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_lenspar_three_lines)
    def test_cone_search(self, mocked_query):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_three_lines)
            coords = SkyCoord(267.4127916666667,-30.452333333333332,unit="deg")
            radius: Angle = Angle(2, unit="arcsec")
            term_data: DataFrame = cone_search(coords, radius)
            print("OGLE TEST: ",term_data['name'])
            #self.assertEqual(term_data['name'], "2011-BLG-0003")
            unique_names = term_data['name'].unique()
            assert len(unique_names) == 1 and unique_names[0] == "2011-BLG-0003", "Unexpected name value"


    @patch('bhtom2.harvesters.ogleews.query_external_service', return_value=sample_file_three_lines)
    def test_extras(self, mocked_query):
        with Patcher() as patcher:
            patcher.fs.create_dir(os.path.join(settings.BASE_DIR, 'cache'))
            patcher.fs.create_file(OGLE_EWS_CACHE_FILE)
            with open(OGLE_EWS_CACHE_FILE, 'w') as w:
                w.write(sample_file_three_lines)
            harvester = OGLEEWSHarvester()
            harvester.query("2011-BLG-0003")
            target: Target = harvester.to_target()
            ex = harvester.to_extras()

            expected_target: Target = Target(name="2011-BLG-0003",
                                            ra=Decimal(268.5002083),
                                            dec=Decimal(-29.10166666),                                             type='SIDEREAL',
                                            epoch=2000, )

            self.assertEqual(ex["importance"], "9.99")
            self.assertEqual(ex["cadence"], "1.0")
            self.assertEqual(ex["classification"],"ulens candidate")

#            print(hasattr(harvester, 'to_extras'))