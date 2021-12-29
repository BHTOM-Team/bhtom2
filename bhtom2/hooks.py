from typing import Dict
from tom_targets.models import Target, TargetExtra

from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger

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
