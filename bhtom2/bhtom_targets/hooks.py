from bhtom2.kafka.producer.reducedDatumEvent import ReducedDatumEventProducer
from bhtom2.kafka.producer.targetEvent import TargetCreateEventProducer

from bhtom2.kafka.topic import kafkaTopic
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_alerts import alerts

logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_targets: hooks]')


# actions done just after saving the target (in creation or update)
def target_post_save(target, created):

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
