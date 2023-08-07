import os
import logging

from aiokafka import AIOKafkaConsumer
from dotenv import dotenv_values

from django.conf import settings

from bhtom2.bhtom_targets.utils import update_template_cache

secret = dotenv_values(os.path.join(settings.BASE_DIR, 'settings/.db.env'))

loggerRequest = logging.getLogger('django.request')
loggerDebug = logging.getLogger(__name__)


async def consumeKafkaMessages(topic):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=secret.get("kafka_servers"),
        group_id=secret.get("bhtom2"),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        retry_backoff_ms=1000,
        session_timeout_ms=60000,  # 1 minute
        heartbeat_interval_ms=20000,
        consumer_timeout_ms=1000,
        fetch_max_wait_ms=5000,
        request_timeout_ms=10000
    )

    try:
        await consumer.start()
        loggerDebug.info(
            "<-------------------Connect to kafka, start consuming message, topic: %s-------------->" % str(topic))

        async for message in consumer:
            try:
                update_template_cache()
                await consumer.commit()
            except Exception as e:
                loggerDebug.error("Error in consumer kafka: " + str(e))
    finally:
        await consumer.stop()
