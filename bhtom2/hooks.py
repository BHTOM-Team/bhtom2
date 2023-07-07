from sqlite3 import IntegrityError
from typing import Dict, Optional

from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates, update_phot_class, update_sun_distance
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
from django.db import transaction

from bhtom2.utils.openai_utils import get_constel, latex_text_target

logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')

# actions done just after saving the target (in creation or update)
def target_post_save(target, created, **kwargs):

    if created:
        fill_galactic_coordinates(target)
        update_sun_distance(target)
        update_phot_class(target)
        names: Dict[DataSource, str] = query_all_services(target)

        for k, v in names.items():
            try: 
                #checking if given source is already in the database
                TargetName.objects.create(target=target, source_name=k.name, name=v)
            except Exception as e:
                logger.warning(f'{"Target {target} already exists under different name - this is not a problem anymore!"}')
#                raise e
                pass
            # te, _ = TargetExtra.objects.update_or_create(target=target,
            #                                              key=k,
            #                                              defaults={
            #                                                  'value': v
            #                                              })
            # te.save()
        #logger.info(f'Saved new names: {names} for target {target.name}')

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

        constellation = get_constel(target.ra, target.dec)
        te, _ = TargetExtra.objects.update_or_create(target=target,
        key='constellation',
        defaults={'value': constellation})
        te.save()

        #LW: setting AAVSO name always to the name
        #it can then be changed
        #first, checking if not exist yet:
        aavso_name = ""
        try:
            aavso_name: Optional[str] = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.AAVSO])
        except:
            pass
        if not aavso_name:
            aavso_name = target.name
            te, _ = TargetExtra.objects.update_or_create(target=target,
                                            key=TARGET_NAME_KEYS[DataSource.AAVSO],
                                            defaults={
                                                'value': aavso_name
                                            })
            te.save()



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



        #if we want to display filter-last, we should add this to extra fields.
        #now it is only dynamically computed in table list views.py
        target.save()
