from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from bhtom_catalogs.harvester import AbstractHarvester
from bhtom_targets.models import Target

from antares_client.search import get_by_ztf_object_id, get_by_id
from antares_client._api.models import Locus

from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom2.utils.bhtom_logger import BHTOMLogger

ALERT_SOURCE: DataSource = DataSource.ANTARES

logger: BHTOMLogger = BHTOMLogger(__name__, '[ANTARES Harvester]')


class ANTARESHarvester(AbstractHarvester):
    name = 'ANTARES'

    def query(self, term) -> Optional[Locus]:
        self.catalog_data: Optional[Locus] = get_by_id(term)
        if not self.catalog_data:
            self.catalog_data:  Optional[Locus] = get_by_ztf_object_id(term)

        return self.catalog_data

    def to_target(self) -> Optional[Target]:

        # catalog_data contains now all fields needed to create a target

        target = super().to_target()

        antares_name: str = self.catalog_data.locus_id
        ztf_name: str = self.catalog_data.properties.get('ztf_object_id', '')
        ra: float = self.catalog_data.ra
        dec: float = self.catalog_data.dec

        # Checking if the object already exists in our DB
        try:
            t0: Target = Target.objects.get(name=ztf_name)

            # TODO: add update?

            return t0
        except ObjectDoesNotExist:
            logger.error(f'Target {ztf_name} not found in the database.')
            pass

        try:
            # Creating a target object
            target.type = 'SIDEREAL'
            target.name = ztf_name
            target.ra = ra
            target.dec = dec
            target.epoch = 2000
            target.jdlastobs = 0.
            target.priority = 0.
            target.cadence = 1.

            target.targetextra_set[TARGET_NAME_KEYS[DataSource.ANTARES]] = antares_name
            target.targetextra_set[TARGET_NAME_KEYS[DataSource.ZTF]] = ztf_name

            logger.info(f'Successfully created target {ztf_name}')

        except Exception as e:
            logger.error(f'Exception while creating object {ztf_name}: {e}')

        return target
