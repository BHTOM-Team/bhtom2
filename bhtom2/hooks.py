from sqlite3 import IntegrityError
from typing import Dict, Optional
from datetime import datetime, timedelta
import requests
import traceback
import os
from dotenv import dotenv_values
from bhtom2.external_service.catalog_name_lookup import query_all_services
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates, update_phot_class, update_sun_distance
from bhtom2.utils.extinction import ogle_extinction
from bhtom_base.bhtom_targets.models import TargetExtra, Target
from bhtom2.bhtom_observatory.models import Observatory
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum
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
from django.conf import settings
from bhtom2.utils.openai_utils import get_constel, latex_text_target
import json
logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Environment variables
secret = dotenv_values(os.path.join(BASE_DIR, 'bhtom2/.bhtom.env'))


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



def data_product_post_upload(dp, target, observatory, observation_filter, MJD, expTime, dry_run,
                             matchDist, comment, user, priority, facility_name=None, observer_name=None):
    url = 'data/' + format(dp)
    logger.info('Running post upload hook for DataProduct: {}'.format(url))
    instance = None

    if observatory is not None:
        try:
            observatory = Observatory.objects.get(id=observatory.id)
            matching_radius = matchDist
        except Exception as e:
            logger.error('data_product_post_upload_fits_file error: {}'.format(str(e)))

    if dp.data_product_type == 'fits_file' and observatory is not None:
        with open(url, 'rb') as file:
            try:
                instance = DataProduct.objects.create(
                    dataproduct_id=dp.id,
                    filter=observation_filter,
                    allow_upload=dry_run,
                    start_time=datetime.now(),
                    cpcs_time=datetime.now(),
                    matchDist=matching_radius,
                    priority=priority,
                    comment=comment,
                    data_stored=True
                )

                response = requests.post(secret.get('CCDPHOTD_URL'), {
                    'job_id': instance.file_id,
                    'instrument': observatory.obsName,
                    'webhook_id': secret.get('CCDPHOTD_WEBHOOK_ID'),
                    'priority': priority,
                    'instrument_prefix': observatory.prefix,
                    'target_name': target.name,
                    'target_ra': target.ra,
                    'target_dec': target.dec,
                    'username': user.username,
                    'dry_run': dry_run,
                    'fits_id': instance.file_id
                }, files={'fits_file': file})

                if response.status_code == 201:
                    logger.info('Successful send to CCDPHOTD, fits id: {}'.format(str(instance.file_id)))
                    instance.status = 'S'
                    instance.status_message = 'Sent to photometry'
                    instance.save()
                else:
                    error_message = 'CCDPHOTD error: {}'.format(response.status_code)
                    logger.info(error_message)
                    instance.status = 'E'
                    instance.status_message = error_message
                    instance.save()

            except Exception as e:
                logger.error('data_product_post_upload_fits_file error: {}'.format(str(e)))
                traceback.print_exc()
                if instance:
                    instance.delete()
                raise Exception(str(e))

    elif dp.data_product_type == 'photometry' and observatory is not None and MJD is not None and expTime is not None:
        target = Target.objects.get(id=dp.target_id)
        try:
            instance = DataProduct.objects.create(
                status='S',
                id=dp.id,
                status_message='Sent to Calibration',
                start_time=datetime.now(),
                cpcs_time=datetime.now(),
                filter=observation_filter,
                photometry_file=format(dp),
                mjd=MJD,
                expTime=expTime,
                allow_upload=dry_run,
                matchDist=matching_radius,
                data_stored=True
            )
            send_to_cpcs(url, instance, target.extra_fields['calib_server_name'])

        except Exception as e:
            logger.error('data_product_post_upload-photometry_cpcs error: {}'.format(str(e)))
            instance.delete()
            raise Exception(str(e))

    elif dp.data_product_type in ['spectroscopy', 'photometry', 'photometry_asassn']:
        try:
            if (dp.data_product_type == 'spectroscopy' or dp.data_product_type == 'photometry') and (facility_name or observer_name):
                dp.extra_data = {
                    'FACILITY_NAME_KEY': facility_name,
                    'OWNER_KEY': observer_name
                }
                dp.save(update_fields=["extra_data"])
                ReducedDatum.refresh(concurrently=True)
            elif dp.data_product_type == 'photometry_asassn':
                dp.extra_data = {
                    'FACILITY_NAME_KEY': "ASAS-SN",
                    'OWNER_KEY': "ASAS-SN"
                }
                dp.save(update_fields=["extra_data"])
                ReducedDatum.refresh(concurrently=True)

            instance = DataProduct.objects.create(
                user_id=user,
                dataproduct_id=dp,
                comment=comment,
                data_stored=True
            )
            logger.info('Successful create: {}'.format(str(dp.data_product_type)))

        except Exception as e:
            logger.error('data_product_post_upload error: {}'.format(str(e)))
            instance.delete()
            raise Exception(str(e))
        
def send_to_cpcs(result, fits, eventID):
    url_cpcs = settings.CPCS_BASE_URL + 'upload'
    logger.info('Send file to cpcs: ' + str(fits.file_id))
    try:
        if eventID is None or eventID == '':
            fits.status = 'E'
            fits.status_message = 'CPCS target name missing or not yet on CPCS'
            fits.save()
            logger.info('CPCS target name missing or not yet on CPCS')
        else:
            with open(format(result), 'rb') as file:
                response = requests.post(url_cpcs, {
                    'MJD': fits.mjd,
                    'EventID': eventID,
                    'expTime': fits.expTime,
                    'matchDist': fits.matchDist,
                    'dryRun': int(fits.allow_upload),
                    'forceFilter': fits.filter,
                    'fits_id': fits.file_id,
                    'outputFormat': 'json'
                }, files={'sexCat': file})

                if response.status_code in (201, 200):
                    json_data = json.loads(response.text)
                    fits.status = 'F'
                    fits.status_message = 'Finished'
                    fits.cpcs_plot = json_data['image_link']
                    fits.mag = json_data['mag']
                    fits.mag_err = json_data['mag_err']
                    fits.ra = json_data['ra']
                    fits.dec = json_data['dec']
                    fits.zeropoint = json_data['zeropoint']
                    fits.outlier_fraction = json_data['outlier_fraction']
                    fits.scatter = json_data['scatter']
                    fits.npoints = json_data['npoints']
                    fits.followupId = json_data['followup_id']
                    fits.cpsc_filter = json_data['filter']
                    fits.survey = json_data['survey']
                    fits.save()

                    logger.info('mag: {}, mag_err: {}, ra: {}, dec: {}, zeropoint: {}, npoints: {}, scatter: {}'.format(
                        fits.mag, fits.mag_err, fits.ra, fits.dec, fits.zeropoint, fits.npoints, fits.scatter
                    ))
                else:
                    if len(response.content.decode()) > 100:
                        fits.status_message = 'Cpcs error'
                    else:
                        fits.status_message = 'Cpcs error: {}'.format(response.content.decode())

                    fits.status = 'E'
                    fits.save()

    except Exception as e:
        logger.error('send_to_cpcs error: ' + str(e))
        fits.status = 'E'
        fits.status_message = 'Error: {}'.format(str(e))
        fits.save()