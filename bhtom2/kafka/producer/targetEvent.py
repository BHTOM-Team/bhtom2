import logging
import os

from confluent_kafka import Producer, KafkaError

import json

from dotenv import dotenv_values

from bhtom2 import settings

secret = dotenv_values(os.path.join(settings.BASE_DIR, 'bhtom2/.bhtom.env'))


class KafkaProducer:
    def __init__(self):
        self.producer = None

    def initialize_producer(self):
        conf = {
            'bootstrap.servers': secret.get("kafka_servers")
        }
        try:
            self.producer = Producer(conf)
        except KafkaError as e:
            logging.error("error ")

    def send_message(self, topic, target):
        if self.producer is None:
            self.initialize_producer()

        value = {
            "id": target.id,
            "name": target.name,
            "ra": target.ra,
            "dec": target.dec
        }

        message_json = json.dumps(value)
        self.producer.produce(topic, value=message_json)
        self.producer.poll()
