from typing import Dict, Optional

from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates, update_sun_distance
from bhtom2.utils.extinction import ogle_extinction
from bhtom_base.bhtom_targets.models import TargetExtra, Target
from bhtom2.external_service.data_source_information import (TARGET_NAME_KEYS,
                                                             DataSource)
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.management import call_command
from io import StringIO
from bhtom2.dataproducts import last_jd
from bhtom2.utils.coordinate_utils import computeDtAndPriority
from bhtom_base.bhtom_targets.models import TargetName
from django.contrib import messages

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
        names: Dict[DataSource, str] = query_all_services(target)
        for k, v in names.items():
            try:
                TargetName.objects.create(target=target, source_name=k.name, name=v)
            except Exception as e:
                logger.warning(f'{"Target {target} already exists under different name - this should be caught ealier!"}')
                raise e
            # te, _ = TargetExtra.objects.update_or_create(target=target,
            #                                              key=k,
            #                                              defaults={
            #                                                  'value': v
            #                                              })
            # te.save()
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

        ##asking for all data (check for new data force)
        #TODO: make it run in the background?
        call_command('updatereduceddata', target_id=target.id, stdout=StringIO())

        mag_last, mjd_last, filter_last = last_jd.get_last(target)

        #everytime the list is rendered, the last mag and last mjd are updated per target
        te, _ = TargetExtra.objects.update_or_create(target=target,
        key='mag_last',
        defaults={'value': mag_last})
        te.save()

        te, _ = TargetExtra.objects.update_or_create(target=target,
        key='mjd_last',
        defaults={'value': mjd_last})
        te.save()

        try:
            imp = float(target.extra_field.get('importance'))
            cadence = float(target.extra_field.get('cadence'))
        except:
            imp = 1
            cadence = 1

        priority = computeDtAndPriority(mjd_last, imp, cadence)
        te, _ = TargetExtra.objects.update_or_create(target=target,
        key='priority',
        defaults={'value': priority})
        te.save()


        #if we want to display filter-last, we should add this to extra fields.
        #now it is only dynamically computed in table list views.py
        target.save()