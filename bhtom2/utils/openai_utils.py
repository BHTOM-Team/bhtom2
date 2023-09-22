from datetime import datetime
import openai
from django.conf import settings

from bhtom2.templatetags.bhtom_targets_extras import deg_to_sexigesimal
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import TargetExtra, Target

import astropy.units as u
from astropy.coordinates import SkyCoord, get_constellation
from astropy.time import Time
from numpy import around

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: OpenAI')

API_KEY = settings.OPENAI_API_KEY

#finds the constellation name given the coordinates
#returns one name in Latin
# def get_constel(ra,dec):

#     openai.api_key = API_KEY
    
#     model_engine = "text-davinci-003"

#     prompt = f"find the constellation for coordinates {ra}, {dec} and answer in one word with the latin name."

#         # Generate a response
#     completion = openai.Completion.create(
#         engine=model_engine,
#         prompt=prompt,
#         max_tokens=1024,
#         n=1,
#         stop=None,
#         temperature=0.5,
#     )

#     # extracting useful part of response
#     response = completion.choices[0].text
  
#     return response[2:]

#returns a full constellation name, input ra dec is in degrees
def get_constel(ra:float, dec:float):
    coords = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame='icrs')
    # Create a Simbad object and query it for the object at the given coordinates
    constellation=get_constellation(coords, short_name=False)

    return constellation

#any type of prompt
def get_response(prompt):
    openai.api_key = API_KEY
    
    model_engine = "text-davinci-003"

    try:
        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7,
        )
        # extracting useful part of response
        response = completion.choices[0].text
    except:
        response="  Error in AI..."

#removes first 2x /n which are present in all responses
    return response[2:]

#outputs a latex text with target information
def latex_text_target(target:Target):
    prompt = latex_text_target_prompt(target)
    return get_response(prompt)

#outputs a latex text with target information
#returns only the prompt (which is built using AI too)
#prompt should be cast to get_response
def latex_text_target_prompt(target:Target):
    ra = deg_to_sexigesimal(target.ra,'hms')
    dec= deg_to_sexigesimal(target.dec,'dms')
    gall=target.galactic_lng
    galb=target.galactic_lat
    constel = get_constel(target.ra,target.dec)
#    print("CONSTEL: ",constel)
    name = target.name
    tns=""

    aliases = ""
    for alias in target.aliases.all():
        if (alias.source_name=="TNS"):
            tns=alias.name
        else:
            aliases+=alias.name+"("+alias.source_name+") "

#    print(target.aliases.all())
    # aliases = target.aliases.all
#    if aliases.source_name 
    #discovery date from extras
    #who found it first?
#    discdate=target.discovery_date
    discdate=str(target.discovery_date)

    # prompt_date=f"Rewrite datetime {discdate} UT in Month, day, year format, without time"
    # date=get_response(prompt_date)

#    print("DATE: ",date)
#    prompt_hjd=f"Compute full Heliocentric Julian Date (HJD) for date {discdate} and subtract 2450000.0 from the result. Output only subtracted value."
#    hjd=get_response(prompt_hjd)
    datetime_object = datetime.strptime(discdate, "%Y-%m-%d %H:%M:%S%z")
    date=datetime_object.strftime('%Y-%m-%d %H:%M')

    human_readable_create_date = target.created.strftime('%Y-%m-%d %H:%M')

    t_utc = Time(datetime_object, format='datetime', scale='utc')
    # Convert to MJD
    mjd = around(t_utc.mjd,5)

#    print("HJD=",hjd)

    epoch = target.epoch
    prompt1=f"Rephrase and keep LaTeX: \\quad {name}"
    if (tns): prompt1+="({tns} according to the IAU transient name server)"
    prompt1+=f" {name} was discovered by \
            \\textit{{Gaia}} Science Alerts (GSA) on {date} (MJD = {mjd}) \
            and was posted on the GSA website \\footnote{{\\href{{http://gsaweb.ast.cam.ac.uk/alerts/alert/{name}/}}{{http://gsaweb.ast.cam.ac.uk/alerts/alert/{name}/}}}}."
    if (aliases): prompt1+=f" Other surveys' names include: {aliases}. "
    prompt1+=f"The event was located at equatorial coordinates RA, Dec(J{epoch})= {ra}, {dec} and galactic coordinates l,b = {gall}, {galb} \
        in constellation {constel}. \
            The finding chart with the event's location on the sky is presented in Figure \\ref{{fig:fchart}}."
    prompt1+=f"The target was added to BHTOM2\\footnote{{\\url{{https://bhtom.space}}}} \\citep{{BHTOM2}} on {human_readable_create_date} for detailed follow-up observations."


    return prompt1

#generates a catchy title for the paper
#assuming it is a black hole candidate
def latex_target_title_prompt(target:Target):
    name = target.name

    constel = get_constel(target.ra,target.dec)

    prompt2 = f"Suggest a catchy title about "\
    f" a black hole candidate"\
    f" found with microlensing"\
    f" named {name}, found in the constellation {constel}."

    return prompt2
