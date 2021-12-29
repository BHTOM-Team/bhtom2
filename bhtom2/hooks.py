from typing import Dict
from tom_targets.models import Target, TargetExtra

from bhtom2.external_service.catalog_name_lookup import query_simbad_for_names
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')


def target_post_save(target, created, **kwargs):
    names: Dict[str, str] = query_simbad_for_names(target)
    for k, v in names.items():
        te, created = TargetExtra.objects.get_or_create(target=target,
                                                        key=k,
                                                        value=v)
        if created:
            te.save()
    logger.info(f'Saved new names: {names} for target {target.name}')
