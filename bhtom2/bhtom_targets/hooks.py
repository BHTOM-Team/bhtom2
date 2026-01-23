from bhtom2.bhtom_targets.utils import update_targetList_cache
from bhtom2.kafka.producer.reducedDatumEvent import ReducedDatumEventProducer
from bhtom2.kafka.producer.targetEvent import TargetCreateEventProducer

from bhtom2.kafka.topic import kafkaTopic
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.bhtom_targets.utils import get_brokers
from bhtom_base.bhtom_dataproducts.models import BrokerCadence, ReducedDatum
from django_comments.models import Comment
import requests
from django.conf import settings
from django_guid import get_guid

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.hooks')


# actions done just after saving the target (in creation or update)
def target_post_save(target, created=False, user=None):
    logger.info(f"target_post_save: target={target}, created={created}, user={user}")
    if created:
        try:
            TargetCreateEventProducer().send_message(kafkaTopic.createTarget, target)
            logger.info("Send Create target Event, %s" % str(target.name))
        except Exception as e:
            logger.error("Error targetEvent, %s" % str(e))
        try:
            full_name = user.get_full_name() or user.username

            Comment.objects.create(
                user_id=user.id,
                user_name=user.username,
                user_email=user.email,
                object_pk=target.id,
                content_type_id=12,
                site_id=1,
                is_public=True,
                comment=f"Target created by {full_name}({user.username}) on {target.created}",
            )
        except Exception as e :
            logger.error("Error while create comment: " + str(e))
    try:
        brokers = get_brokers()
        for broker in brokers:
            ReducedDatumEventProducer().send_message(kafkaTopic.updateReducedDatum, target, broker, isNew=True)
        logger.info("Send Create reducedDatum Event, %s" % str(target.name))
    except Exception as e:
        logger.error("Error reducedDatum Event, %s" % str(e))


def update_alias(target, broker):
    try:
        brokerCadence = BrokerCadence.objects.get(target_id=target.id, broker_name=broker)
        brokerCadence.last_update = None
        brokerCadence.save()
    except BrokerCadence.DoesNotExist:
        logger.info("BrokerCadence not exist")
    except Exception as e:
        logger.error(str(e))

    try:
        datum = ReducedDatum.objects.filter(target=target, source_name=broker)
        datum.delete()
    except Exception as e:
        logger.error(str(e))

    try:
        ReducedDatumEventProducer().send_message(kafkaTopic.updateReducedDatum, target, broker, isNew=False,
                                                 plotForce=True)
    except Exception as e:
        logger.error(str(e))



def delete_alias(target, broker):

    try:
        datum = ReducedDatum.objects.filter(target=target, source_name=broker)
        datum.delete()
        headers = {
            'Correlation-ID': get_guid(),
        }
        post_data = {'target_id': target.id}
        response = requests.post(settings.CPCS_URL + '/target/updatePlot/', data=post_data,
                                     headers=headers)
        if response.status_code != 200:
             logger.info("Error, plot does not updated!")

    except Exception as e:
        logger.error(str(e))


def update_priority(target):

    logger.info("Update priority: " + str(target.name))

    try:
        logger.info("Start clean target list cache")
        update_targetList_cache()
    except Exception as e:
        logger.error("Clean cache error: %s" % str(e))


def update_force_reducedDatum(target):

    try:
        brokers = get_brokers()
        for broker in brokers:
            try:
                brokerCadence = BrokerCadence.objects.get(target_id=target.id, broker_name=broker)
                brokerCadence.last_update = None
                brokerCadence.save()
            except BrokerCadence.DoesNotExist:
                logger.debug("BrokerCadence not exist, broker: %s" % broker)
            except Exception as e:
                logger.error(str(e))

            ReducedDatumEventProducer().send_message(kafkaTopic.updateReducedDatum, target, broker, isNew=True)
        logger.info("Send update reducedDatum Event, %s" % str(target.name))
    except Exception as e:
        logger.error("Error reducedDatum Event, %s" % str(e))