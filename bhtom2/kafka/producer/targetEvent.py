import os

from confluent_kafka import Producer, KafkaError

import json

from django_guid import get_guid
from dotenv import dotenv_values

from settings import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger

secret = dotenv_values(os.path.join(settings.BASE_DIR, 'settings/env/.bhtom.env'))

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: kafka.target_event')


class TargetCreateEventProducer:
    def __init__(self):
        self.producer = None

    def initialize_producer(self):
        conf = {
            'bootstrap.servers': secret.get("KAFKA_HOST_PORT")
        }
        try:
            self.producer = Producer(conf)
        except KafkaError as e:
            logger.error("Kafka Producer error: " + str(e))

    def send_message(self, topic, target):
        if self.producer is None:
            self.initialize_producer()

        value = {
            "target_id": target.id,
            "target": target.name,
            "ra": target.ra,
            "dec": target.dec,
            "radius": 0.5
        }

        guid = get_guid()

        message_json = json.dumps(value)
        self.producer.produce(topic,
                              value=message_json,
                              headers={"Correlation-ID": guid}
                              )
        self.producer.poll(2)
