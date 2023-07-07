from django.test import TestCase
from bhtom2.bhtom_observations.facilities.rem import REM


class REMTestCase(TestCase):
    def setUp(self):
        self.rem = REM()

    def test_exposure_time_calculator(self):
        # Test valid input
        mag = 15
        instrument = 'ROS2'
        filter = 'griz+J'
        expected_output = 251
        val=self.rem.exposure_time_calculator(mag, filter, instrument)
        self.assertAlmostEqual(val, expected_output, 0)

        # Test invalid instrument
        mag = 14
        filter = "griz+J"
        instrument = "InvalidInstrument"
        expected_output = -1
        self.assertEqual(self.rem.exposure_time_calculator(mag, filter, instrument), expected_output)

        # Test invalid filter
        mag = 14
        filter = "InvalidFilter"
        instrument = "ROS2"
        expected_output = -1
        self.assertEqual(self.rem.exposure_time_calculator(mag, filter, instrument), expected_output)


    def test(self):
        self.rem.compute_for_all()