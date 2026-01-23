
import os

from confluent_kafka import Producer, KafkaError

import json

from django_guid import get_guid
from dotenv import dotenv_values

from settings import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger

secret = dotenv_values(os.path.join(settings.BASE_DIR, 'settings/env/.bhtom.env'))

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: kafka.calib_event')


class CalibCreateEventProducer:
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

    def send_message(self, data_product_id, target_name, dp_data):
        if self.producer is None:
            self.initialize_producer()

        value = {
            "data_product_id": data_product_id,
            "target": str(target_name),
            "data_product": str(dp_data)
        }
        guid = get_guid()

        message_json = json.dumps(value)
        self.producer.produce('Event_Calibration_File',
                              value=message_json,
                              headers={"Correlation-ID": guid}
                              )
        self.producer.poll(2)
