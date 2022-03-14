from typing import Dict, Optional
from tom_targets.models import Target, TargetExtra

from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates
from bhtom2.utils.extinction import ogle_extinction

logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')


def target_post_save(target, created, **kwargs):
    if created:
        names: Dict[str, str] = query_all_services(target)
        for k, v in names.items():
            te, _ = TargetExtra.objects.update_or_create(target=target.id,
                                                         key=k,
                                                         defaults={
                                                             'value': v
                                                         })
            te.save()
        logger.info(f'Saved new names: {names} for target {target.name}')

    # Fill in extinction
        extinction: Optional[float] = ogle_extinction(target)

        if extinction:
            te, _ = TargetExtra.objects.update_or_create(target=target.id,
                                                         key='E(V-I)',
                                                         defaults={
                                                             'value': extinction
                                                         })
            te.save()

            logger.info(f'Saved E(V-I) = {extinction} for target {target.name}')
