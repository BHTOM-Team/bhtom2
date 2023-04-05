import openai
from django.conf import settings

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import TargetExtra, Target

logger: BHTOMLogger = BHTOMLogger(__name__, '[OpenAI]')

API_KEY = settings.OPENAI_API_KEY

#finds the constellation name given the coordinates
#returns one name in Latin
def get_constel(ra,dec):

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

#outputs a latex text with target information
#TODO this should be moved to the form, as the fields can be edited
def latex_text_target(target:Target):
    ra = target.ra
    dec= target.dec
    gall=target.galactic_lng
    galb=target.galactic_lat
    constel = get_constel(ra,dec)
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
    discdate=TargetExtra.objects.get(target=target, key='discovery_date')

    prompt_date=f"Rewrite datetime {discdate} UT in Month, day, year format, without time"
    date=get_response(prompt_date)
#    print("DATE: ",date)
    prompt_hjd=f"Compute full Heliocentric Julian Date (HJD) for date {discdate} and subtract 2450000.0 from the result. Output only subtracted value."
    hjd=get_response(prompt_hjd)
#    print("HJD=",hjd)

    prompt1=f"Rephrase and keep LaTeX: \\quad {name}"
    if (tns): prompt1+="({tns} according to the IAU transient name server)"
    prompt1+=f" {name} was discovered by \
            \\textit{{Gaia}} Science Alerts on {date} (HJD’ = HJD - 2450000.0 = {hjd}) \
            and was posted on the GSA website \\footnote{{\\href{{http://gsaweb.ast.cam.ac.uk/alerts/alert/{name}/}}{{http://gsaweb.ast.cam.ac.uk/alerts/alert/{name}/}}}}."
    if (aliases): prompt1+=f" Other surveys' names include: {aliases}. "
    prompt1+=f"The event was located at equatorial coordinates RA = {ra}, DEC = {dec} and galactic coordinates l = {gall}, b = {galb} \
        in constellation {constel}. \
            The finding chart with the event's location on the sky is presented in Figure \\ref{{fig:fchart}}."

    res = get_response(prompt1)
    return res[2:] #removing first two \n characters
