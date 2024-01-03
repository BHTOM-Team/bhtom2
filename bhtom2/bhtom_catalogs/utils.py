import json
import requests
from django.conf import settings
from ..utils.bhtom_logger import BHTOMLogger

logger = BHTOMLogger(__name__, 'Your Logger Name')

def get_harvesters():
    try:
        response = requests.get(settings.HARVESTER_URL + 'getHarvesterList/')
        harvesters = response.json()  # Parse the response as JSON
    except Exception as e:
        logger.error("Error in harvester-service: " + str(e))
        harvesters = []
    return harvesters
