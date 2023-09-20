from bhtom2.kafka.producer.reducedDatumEvent import ReducedDatumEventProducer
from bhtom2.kafka.producer.targetEvent import TargetCreateEventProducer

from bhtom2.kafka.topic import kafkaTopic
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_alerts import alerts
from bhtom_base.bhtom_dataproducts.models import BrokerCadence, ReducedDatum

logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_targets: hooks]')


# actions done just after saving the target (in creation or update)
def target_post_save(target, created=False):
    if created:
        try:
            TargetCreateEventProducer().send_message(kafkaTopic.createTarget, target)
            logger.info("Send Create target Event, %s" % str(target.name))
        except Exception as e:
            logger.error("Error targetEvent, %s" % str(e))

    try:
        brokers = alerts.get_service_classes()
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
