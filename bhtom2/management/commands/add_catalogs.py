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
        {'id': 10, 'survey': 'APASS', 'filters': 'B', 'isActive': False},
        {'id': 11, 'survey': 'APASS', 'filters': 'V', 'isActive': False},
        {'id': 12, 'survey': 'APASS', 'filters': 'g', 'isActive': False},
        {'id': 13, 'survey': 'APASS', 'filters': 'r', 'isActive': False},
        {'id': 14, 'survey': 'APASS', 'filters': 'i', 'isActive': False},
        {'id': 15, 'survey': '2MASS', 'filters': 'J', 'isActive': True},
        {'id': 16, 'survey': '2MASS', 'filters': 'H', 'isActive': True},
        {'id': 17, 'survey': '2MASS', 'filters': 'K', 'isActive': True},
        {'id': 18, 'survey': 'OGLE3', 'filters': 'V', 'isActive': False},
        {'id': 19, 'survey': 'OGLE3', 'filters': 'I', 'isActive': False},
        {'id': 20, 'survey': 'DECAPS', 'filters': 'g', 'isActive': False},
        {'id': 21, 'survey': 'DECAPS', 'filters': 'r', 'isActive': False},
        {'id': 22, 'survey': 'DECAPS', 'filters': 'i', 'isActive': False},
        {'id': 23, 'survey': 'DECAPS', 'filters': 'z', 'isActive': False},
        {'id': 24, 'survey': 'GaiaSP', 'filters': 'u', 'isActive': True},
        {'id': 25, 'survey': 'GaiaSP', 'filters': 'g', 'isActive': True},
        {'id': 26, 'survey': 'GaiaSP', 'filters': 'r', 'isActive': True},
        {'id': 27, 'survey': 'GaiaSP', 'filters': 'i', 'isActive': True},
        {'id': 28, 'survey': 'GaiaSP', 'filters': 'z', 'isActive': True},
        {'id': 29, 'survey': 'GaiaSP', 'filters': 'U', 'isActive': True},
        {'id': 30, 'survey': 'GaiaSP', 'filters': 'B', 'isActive': True},
        {'id': 31, 'survey': 'GaiaSP', 'filters': 'V', 'isActive': True},
        {'id': 32, 'survey': 'GaiaSP', 'filters': 'R', 'isActive': True},
        {'id': 33, 'survey': 'GaiaSP', 'filters': 'I', 'isActive': True},
    ]


class Command(BaseCommand):
    def handle(self, *args, **options):

        for row in getCatalogs():
            record, create = Catalogs.objects.get_or_create(id=row['id'], survey=row['survey'], filters=row['filters'],
                                                            isActive=row['isActive'])

            if create:
                record.save()
                print('Creating survey: %s filter: %s' % (row['survey'], row['filters']))
