from bhtom2.kafka.producer.targetEvent import KafkaProducer
from bhtom2.kafka.topic import kafkaTopic
from bhtom2.utils.bhtom_logger import BHTOMLogger


logger: BHTOMLogger = BHTOMLogger(__name__, '[Hooks]')


# actions done just after saving the target (in creation or update)
def target_post_save(target, created, **kwargs):

    if created:
        try:
            KafkaProducer().send_message(kafkaTopic.targetEvent, target)
            logger.info("Send targetEvent, %s" % str(target.name))
        except Exception as e:
            logger.error("Erro targetEvent, %s" % str(e))
