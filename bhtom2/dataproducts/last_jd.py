from bhtom_base.bhtom_targets.models import Target
import logging
from typing import Optional
from sentry_sdk import capture_exception
from bhtom_base.bhtom_base import settings
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, ReducedDatumUnit

logger: logging.Logger = logging.getLogger(__name__)


def update_last_jd(target: Target,
                   jd: Optional[float] = None,
                   mag: Optional[float] = None):
    '''
    Update JD of the last observation for the target if the passed observation has been the latest one
    :param target:
    :param mag: Magnitude of the observation
    :param jd: JD of the observation
    :return:
    '''

    try:
        # Get the latest JD saved in the database
        previous_jd = target.extra_fields.get('last_jd')

        if jd and (previous_jd is None or jd > previous_jd):
            target.save(extras={'last_jd': jd})
            logger.debug(f'Saving new latest JD for {target}: {jd}')

            if mag:
                target.save(extras={'last_mag': mag})
                logger.debug(f'Saving new latest magnitude for {target}: {mag}')
    except Exception as e:
        logger.error(f'Error while updating last JD and magnitude for {target}: {e}')
        capture_exception(e)

def get_last(target: Target):
    '''
    Derives the last JD 
    as well as approximate colour
    to derive the last mag roughly in G-band
    '''
    datums = ReducedDatum.objects.filter(target=target,
                                            data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                            value_unit=ReducedDatumUnit.MAGNITUDE)
    photometry_data = {}
    last_mjd=-10000
    last_mag=100
    last_filter=''
    mean_color=0.0
    mean_i=0.0
    n_i=0
    mean_r=0.0
    n_r=0
    mean_g=0.0
    n_g=0
    mean_V=0.0
    n_V=0

    i_filters = ["i(","(I)", "(zi)", "(i)"]
    r_filters = ["r(","(R)", "(zr)", "(r)"]
    g_filters = ["g(", "(zg)", "(g)"]
    V_filters = ["V(","(V)"]
    G_filters = ["G(","(G)","g(Gaia)"] #g(Gaia) to be removed

    return_mag = 0
    approxsign=""

    for datum in datums:
        photometry_data.setdefault(datum.filter, {})
        # print(datum.filter!="WISE(W1)")
        # mean_color
        #excluding WISE filters
        if ((datum.filter!="WISE(W1)") and (datum.filter!="WISE(W2)") and (datum.mjd > last_mjd)) :
            last_mjd = datum.mjd
            last_mag = datum.value
            last_filter= datum.filter


        if any(x in datum.filter for x in i_filters): 
            mean_i+=datum.value
            n_i+=1
        if any(x in datum.filter for x in r_filters): 
            mean_r+=datum.value
            n_r+=1
        if any(x in datum.filter for x in g_filters): 
            mean_g+=datum.value
            n_g+=1
        if any(x in datum.filter for x in V_filters): 
            mean_V+=datum.value
            n_V+=1

    if (n_i>0): mean_i=mean_i/n_i
    if (n_r>0): mean_r=mean_r/n_r
    if (n_g>0): mean_g=mean_g/n_g
    if (n_V>0): mean_V=mean_V/n_V

    return_mag = last_mag ##if everything fails, we just return last mag and the name of the filter
    approxsign="x"

    #assuming r is close enough to G
    if (any(x in last_filter for x in G_filters)
    or 
    any(x in last_filter for x in r_filters)): 
        return_mag = last_mag
        approxsign=""
    else:
        #shifting the last mag by colour to match G
        #from V to G/r using V-r
        if (mean_r!=0 and mean_V!=0 and any(x in last_filter for x in V_filters)):
            return_mag = last_mag-(mean_V-mean_r)
            approxsign="~"
        #from g to G/r using g-r
        if (mean_g!=0 and mean_r!=0 and any(x in last_filter for x in g_filters)):
            return_mag = last_mag-(mean_g-mean_r)
            approxsign="~"
        #from i to G/r using i-r
        if (mean_i!=0 and mean_r!=0 and any(x in last_filter for x in i_filters)):
            return_mag = last_mag-(mean_i-mean_r)
            approxsign="~"
        #from g to G/r using g-i
        if (mean_g!=0 and mean_i!=0 and any(x in last_filter for x in g_filters)):
            return_mag = last_mag-(mean_g-mean_i)/2.
            approxsign="~"

    return return_mag, last_mjd, last_filter, approxsign