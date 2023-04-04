import openai
from django.conf import settings

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import TargetExtra, Target

logger: BHTOMLogger = BHTOMLogger(__name__, '[OpenAI]')

API_KEY = settings.OPENAI_API_KEY

#finds the constellation name given the coordinates
#returns one name in Latin
def get_constel(ra,dec):

    # Set up the OpenAI API client
    openai.api_key = API_KEY
    
    model_engine = "text-davinci-003"

    prompt = f"find the constellation for coordinates {ra}, {dec} and answer in one word with the latin name."

        # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # extracting useful part of response
    response = completion.choices[0].text

    return response

#any type of prompt
def get_response(prompt):
    # Set up the OpenAI API client
    openai.api_key = API_KEY
    
    model_engine = "text-davinci-003"

        # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # extracting useful part of response
    response = completion.choices[0].text

    return response
