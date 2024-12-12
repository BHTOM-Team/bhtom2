from django.core.management.base import BaseCommand

from bhtom2.bhtom_calibration.models import Catalogs


def getCatalogs():
    return [
        {'id': 1, 'survey': 'SDSS', 'filters': 'u', 'isActive': False},
        {'id': 2, 'survey': 'SDSS', 'filters': 'g', 'isActive': False},
        {'id': 3, 'survey': 'SDSS', 'filters': 'r', 'isActive': False},
        {'id': 4, 'survey': 'SDSS', 'filters': 'i', 'isActive': False},
        {'id': 5, 'survey': 'SDSS', 'filters': 'z', 'isActive': False},
        {'id': 6, 'survey': 'SDSS', 'filters': 'B', 'isActive': False},
        {'id': 7, 'survey': 'SDSS', 'filters': 'V', 'isActive': False},
        {'id': 8, 'survey': 'SDSS', 'filters': 'R', 'isActive': False},
        {'id': 9, 'survey': 'SDSS', 'filters': 'I', 'isActive': False},
        {'id': 10, 'survey': 'SDSS', 'filters': 'any', 'isActive': False},
        {'id': 11, 'survey': 'APASS', 'filters': 'B', 'isActive': False},
        {'id': 12, 'survey': 'APASS', 'filters': 'V', 'isActive': False},
        {'id': 13, 'survey': 'APASS', 'filters': 'g', 'isActive': False},
        {'id': 14, 'survey': 'APASS', 'filters': 'r', 'isActive': False},
        {'id': 15, 'survey': 'APASS', 'filters': 'i', 'isActive': False},
        {'id': 16, 'survey': 'APASS', 'filters': 'any', 'isActive': False},
        {'id': 17, 'survey': '2MASS', 'filters': 'J', 'isActive': True},
        {'id': 18, 'survey': '2MASS', 'filters': 'H', 'isActive': True},
        {'id': 19, 'survey': '2MASS', 'filters': 'K', 'isActive': True},
        {'id': 20, 'survey': '2MASS', 'filters': 'any', 'isActive': True},
        {'id': 21, 'survey': 'OGLE3', 'filters': 'V', 'isActive': False},
        {'id': 22, 'survey': 'OGLE3', 'filters': 'I', 'isActive': False},
        {'id': 23, 'survey': 'OGLE3', 'filters': 'any', 'isActive': False},
        {'id': 24, 'survey': 'DECAPS', 'filters': 'g', 'isActive': False},
        {'id': 25, 'survey': 'DECAPS', 'filters': 'r', 'isActive': False},
        {'id': 26, 'survey': 'DECAPS', 'filters': 'i', 'isActive': False},
        {'id': 27, 'survey': 'DECAPS', 'filters': 'z', 'isActive': False},
        {'id': 28, 'survey': 'DECAPS', 'filters': 'any', 'isActive': False},
        {'id': 29, 'survey': 'GaiaSP', 'filters': 'u', 'isActive': True},
        {'id': 30, 'survey': 'GaiaSP', 'filters': 'g', 'isActive': True},
        {'id': 31, 'survey': 'GaiaSP', 'filters': 'r', 'isActive': True},
        {'id': 32, 'survey': 'GaiaSP', 'filters': 'i', 'isActive': True},
        {'id': 33, 'survey': 'GaiaSP', 'filters': 'z', 'isActive': True},
        {'id': 34, 'survey': 'GaiaSP', 'filters': 'U', 'isActive': True},
        {'id': 35, 'survey': 'GaiaSP', 'filters': 'B', 'isActive': True},
        {'id': 36, 'survey': 'GaiaSP', 'filters': 'V', 'isActive': True},
        {'id': 37, 'survey': 'GaiaSP', 'filters': 'R', 'isActive': True},
        {'id': 38, 'survey': 'GaiaSP', 'filters': 'I', 'isActive': True},
        {'id': 39, 'survey': 'GaiaSP', 'filters': 'any', 'isActive': True},
        {'id': 40, 'survey': 'any', 'filters': 'u', 'isActive': False},
        {'id': 41, 'survey': 'any', 'filters': 'g', 'isActive': False},
        {'id': 42, 'survey': 'any', 'filters': 'r', 'isActive': False},
        {'id': 43, 'survey': 'any', 'filters': 'i', 'isActive': False},
        {'id': 44, 'survey': 'any', 'filters': 'z', 'isActive': False},
        {'id': 45, 'survey': 'any', 'filters': 'B', 'isActive': False},
        {'id': 46, 'survey': 'any', 'filters': 'V', 'isActive': False},
        {'id': 47, 'survey': 'any', 'filters': 'R', 'isActive': False},
        {'id': 48, 'survey': 'any', 'filters': 'I', 'isActive': False},
        {'id': 49, 'survey': 'any', 'filters': 'J', 'isActive': False},
        {'id': 50, 'survey': 'any', 'filters': 'H', 'isActive': False},
        {'id': 51, 'survey': 'any', 'filters': 'K', 'isActive': False},
        {'id': 52, 'survey': 'any', 'filters': 'U', 'isActive': False},
        {'id': 53, 'survey': 'GaiaSP', 'filters': 'ugriz', 'isActive': True},
        {'id': 54, 'survey': 'GaiaSP', 'filters': 'UBVRI', 'isActive': True},
        {'id': 55, 'survey': 'GaiaDR3', 'filters': 'any', 'isActive': True},
        {'id': 56, 'survey': 'GaiaDR3', 'filters': 'G', 'isActive': True},
        {'id': 57, 'survey': 'GaiaDR3', 'filters': 'GBP', 'isActive': True},
        {'id': 58, 'survey': 'GaiaDR3', 'filters': 'GRP', 'isActive': True}
    ]


class Command(BaseCommand):
    def handle(self, *args, **options):

        for row in getCatalogs():
            record, create = Catalogs.objects.get_or_create(id=row['id'], survey=row['survey'], filters=row['filters'],
                                                            isActive=row['isActive'])

            if create:
                record.save()
                print('Creating survey: %s filter: %s' % (row['survey'], row['filters']))
