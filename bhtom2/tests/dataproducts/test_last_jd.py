from django.test import TestCase
from bhtom_base.tom_targets.models import Target
from typing import Optional

from bhtom2.dataproducts.last_jd import update_last_jd


class LastJDTestCase(TestCase):
    def setUp(self):
        Target.objects.create(name="EmptyTarget")
        Target.objects.create(name="NonEmptyTarget")

        Target.objects.get(name="NonEmptyTarget").save(extras={'last_jd': 0, 'last_mag': 3})

    def test_update_JD_and_mag_empty_target(self):
        target: Target = Target.objects.get(name="EmptyTarget")
        update_last_jd(target, jd=1, mag=2)

        last_jd: Optional[float] = target.extra_fields.get('last_jd')
        last_mag: Optional[float] = target.extra_fields.get('last_mag')

        self.assertEqual(last_jd, 1)
        self.assertEqual(last_mag, 2)

    def test_update_JD_and_mag_nonempty_target(self):
        target: Target = Target.objects.get(name="NonEmptyTarget")
        update_last_jd(target, jd=1, mag=2)

        last_jd: Optional[float] = target.extra_fields.get('last_jd')
        last_mag: Optional[float] = target.extra_fields.get('last_mag')

        self.assertEqual(last_jd, 1)
        self.assertEqual(last_mag, 2)

    def test_update_JD_nonempty_target(self):
        target: Target = Target.objects.get(name="NonEmptyTarget")
        update_last_jd(target, jd=1)

        last_jd: Optional[float] = target.extra_fields.get('last_jd')
        last_mag: Optional[float] = target.extra_fields.get('last_mag')

        self.assertEqual(last_jd, 1)
        self.assertEqual(last_mag, 3)

    def test_update_JD_nonempty_target_if_same_jd(self):
        target: Target = Target.objects.get(name="NonEmptyTarget")
        update_last_jd(target, jd=1, mag=2)

        last_jd: Optional[float] = target.extra_fields.get('last_jd')
        last_mag: Optional[float] = target.extra_fields.get('last_mag')

        self.assertEqual(last_jd, 1)
        self.assertEqual(last_mag, 2)

    def test_dont_update_JD_nonempty_target_if_smaller_jd(self):
        target: Target = Target.objects.get(name="NonEmptyTarget")
        update_last_jd(target, jd=-1, mag=2)

        last_jd: Optional[float] = target.extra_fields.get('last_jd')
        last_mag: Optional[float] = target.extra_fields.get('last_mag')

        self.assertEqual(last_jd, 0)
        self.assertEqual(last_mag, 3)
