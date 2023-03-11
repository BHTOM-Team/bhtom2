from typing import Dict, Optional

from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates, update_sun_distance
from bhtom2.utils.extinction import ogle_extinction
from bhtom_base.bhtom_targets.models import TargetExtra, Target
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from django.dispatch import receiver
from django.db.models.signals import post_save


logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')

# @receiver(pre_save, sender=Target)
# def target_pre_save(sender, instance, **kwargs):
#     fill_galactic_coordinates(instance)
#     update_sun_distance(instance)
#     print('Target pre save hook: {}', str(instance))

# actions done just after saving the target (in creation or update)
def target_post_save(target, created, **kwargs):
    if created:
        fill_galactic_coordinates(target)
        update_sun_distance(target)
        names: Dict[str, str] = query_all_services(target)
        for k, v in names.items():
            te, _ = TargetExtra.objects.update_or_create(target=target,
                                                         key=k,
                                                         defaults={
                                                             'value': v
                                                         })
            te.save()
        logger.info(f'Saved new names: {names} for target {target.name}')


    # Fill in extinction
        extinction: Optional[float] = ogle_extinction(target)

        if extinction:
            te, _ = TargetExtra.objects.update_or_create(target=target,
                                                         key='E(V-I)',
                                                         defaults={
                                                             'value': extinction
                                                         })
            te.save()

            logger.info(f'Saved E(V-I) = {extinction} for target {target.name}')

        target.save()