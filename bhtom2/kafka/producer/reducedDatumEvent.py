import logging
import os

from confluent_kafka import Producer, KafkaError

import json

from django_guid import get_guid
from dotenv import dotenv_values

from bhtom2 import settings

secret = dotenv_values(os.path.join(settings.BASE_DIR, 'bhtom2/.bhtom.env'))


class ReducedDatumEventProducer:
    def __init__(self):
        self.producer = None

    def initialize_producer(self):
        conf = {
            'bootstrap.servers': secret.get("KAFKA_HOST_PORT")
        }
        try:
            self.producer = Producer(conf)
        except KafkaError as e:
            logging.error("Kafka Procucer error: " + str(e))

    def send_message(self, topic, target, broker, isNew=False):
        if self.producer is None:
            self.initialize_producer()

        value = {
            "name": target.name,
            "broker": broker,
            "setTargetName": isNew
        }

        guid = get_guid()

        message_json = json.dumps(value)
        self.producer.produce(topic,
                              value=message_json,
                              headers={"correlation_id": guid}
                              )
        self.producer.poll()
