import asyncio
import logging
from kafka.errors import KafkaConnectionError

from bhtom2.kafka.consumer.calibrationEvent import consumeKafkaMessages
from bhtom2.kafka.topic import kafkaTopic

logger = logging.getLogger(__name__)


def start_consumers():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = [calibrationConsumerTask(kafkaTopic.calibrationEvent)]

    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


async def calibrationConsumerTask(topic):
    while True:
        try:
            await consumeKafkaMessages(topic)
        except KafkaConnectionError:
            await asyncio.sleep(10)
            logger.info("<-------------Connection error, restart calibration consumer----------->")
        except Exception as e:
            logger.error("Error on calibration consumer task: %s" % str(e))
            break
