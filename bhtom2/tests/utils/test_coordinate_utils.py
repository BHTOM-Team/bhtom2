from django.test import TestCase
from tom_targets.models import Target

from bhtom2.utils.coordinate_utils import fill_galactic_coordinates


class TestGalacticCoordsAutomaticFillIn(TestCase):
    def test_dont_fill_in_if_galactic_coords_passed(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=15.00,
                                galactic_lng=15.00)
        fill_galactic_coordinates(target)
        self.assertAlmostEqual(target.galactic_lat, 15.00)
        self.assertAlmostEqual(target.galactic_lng, 15.00)

    def test_fill_in_if_galactic_coords_not_passed(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=None,
                                galactic_lng=None)
        fill_galactic_coordinates(target)
        self.assertAlmostEqual(target.galactic_lng, 118.50, delta=1e-2)
        self.assertAlmostEqual(target.galactic_lat, -50.77, delta=1e-2)

    def test_dont_fill_in_if_ra_not_passed(self):
        target: Target = Target(name='Test',
                                ra=None,
                                dec=12.00,
                                galactic_lat=None,
                                galactic_lng=None)
        fill_galactic_coordinates(target)
        self.assertIsNone(target.galactic_lng)
        self.assertIsNone(target.galactic_lat)

    def test_dont_fill_in_if_dec_not_passed(self):
        target: Target = Target(name='Test',
                                ra=12.00,
                                dec=None,
                                galactic_lat=None,
                                galactic_lng=None)
        fill_galactic_coordinates(target)
        self.assertIsNone(target.galactic_lng)
        self.assertIsNone(target.galactic_lat)

    def test_dont_fill_in_if_ra_and_dec_not_passed(self):
        target: Target = Target(name='Test',
                                ra=None,
                                dec=None,
                                galactic_lat=None,
                                galactic_lng=None)
        fill_galactic_coordinates(target)
        self.assertIsNone(target.galactic_lng)
        self.assertIsNone(target.galactic_lat)

    def test_fill_in_if_galactic_lng_not_passed(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=1.00,
                                galactic_lng=None)
        fill_galactic_coordinates(target)
        self.assertAlmostEqual(target.galactic_lng, 118.50, delta=1e-2)
        self.assertAlmostEqual(target.galactic_lat, -50.77, delta=1e-2)

    def test_fill_in_if_galactic_lat_not_passed(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=None,
                                galactic_lng=1.00)
        fill_galactic_coordinates(target)
        self.assertAlmostEqual(target.galactic_lng, 118.50, delta=1e-2)
        self.assertAlmostEqual(target.galactic_lat, -50.77, delta=1e-2)
