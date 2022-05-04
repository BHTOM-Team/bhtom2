from typing import Optional
from unittest.mock import patch

from django.test import TestCase
from bhtom_targets.models import Target

from bhtom2.utils.extinction import ogle_extinction


class TestExtinction(TestCase):
    def test_return_correct_extinction(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=3.00,
                                galactic_lng=0.00)

        result: Optional[float] = ogle_extinction(target)

        self.assertAlmostEqual(result, 2.597)

    def test_return_none_if_no_galactic_coordinates(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=None,
                                galactic_lng=None)
        result: Optional[float] = ogle_extinction(target)

        self.assertIsNone(result)

    def test_return_none_if_outside_bulge(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=10,
                                galactic_lng=3)
        result: Optional[float] = ogle_extinction(target)

        self.assertIsNone(result)
