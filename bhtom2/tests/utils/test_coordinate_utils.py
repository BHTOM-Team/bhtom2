from django.test import TestCase
from bhtom_base.bhtom_targets.models import Target, TargetExtra

from bhtom2.utils.coordinate_utils import fill_galactic_coordinates, update_sun_distance
from datetime import datetime
from astropy.time import Time


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

class TestSunDistanceAutomaticFillIn(TestCase):
    def test_fill_sun(self):
        target: Target = Target(name='Test',
                                ra=10.00,
                                dec=12.00,
                                galactic_lat=15.00,
                                galactic_lng=15.00)
        target.save() 
        te, _ = TargetExtra.objects.update_or_create(target=target,
        key='sun_separation',
        defaults={'value': 100})
        te.save()
        ss= TargetExtra.objects.get(target=target,key='sun_separation').value
        time_to_compute = Time(datetime(2023, 3, 10, 9, 12, 29))
        update_sun_distance(target, time_to_compute=time_to_compute)
        ss= TargetExtra.objects.get(target=target,key='sun_separation').value
        self.assertAlmostEqual(ss, 26)
