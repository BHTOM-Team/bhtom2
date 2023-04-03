from astropy.coordinates import Angle, SkyCoord
import astropy.units as u
from bhtom_base.bhtom_targets.models import Target, TargetExtra

from bhtom2.utils.bhtom_logger import BHTOMLogger

from numpy import around
from astropy.coordinates import get_sun, SkyCoord
from datetime import datetime
from astropy.time import Time

logger: BHTOMLogger = BHTOMLogger(__name__, '[Coordinate Utils]')


def fill_galactic_coordinates(target: Target) -> Target:
    """
    Automatically calculate galactic coordinates for a target
    (if they aren't already filled in), using ra and dec
    @param target: Observation target
    @return: Observation target (changed in-place)
    """

    # If at least one of ra and dec is unfilled, return without changing
    # (there is nothing to calculate basing on)
    if not target.ra or not target.dec:
        return target

    # If the galactic coordinates are filled in, return without changing
    if target.galactic_lat and target.galactic_lng:
        return target

    coordinates: SkyCoord = SkyCoord(ra=target.ra,
                                     dec=Angle(target.dec, unit=u.deg).wrap_at('90d').degree,
                                     unit='deg')
                                     
    # rounding galactic coords to 6 decimal points
    glat = around(coordinates.galactic.b.degree, 6)
    glng = around(coordinates.galactic.l.degree,6)
    target.galactic_lat = glat
    target.galactic_lng = glng

    # Target.objects.update_or_create(target=target, key='galactic_lat', 
    # defaults={'value':glat})

    logger.debug(f'Filling in galactic coordinates for target {target.name}...')

    return target

def update_sun_distance(target: Target, time_to_compute=None):
    """
    Computes the Sun-target distance in degrees for NOW 
    and fills the Extra field for this target.
    No decimal points, rounding to degrees.
    Optional parameter is of Time format
    """
    #SUN's position now:
    if (time_to_compute == None):
        tt=Time(datetime.utcnow())
    else:
        tt=time_to_compute

    sun_pos = get_sun(tt)
    obj_pos = SkyCoord(target.ra, target.dec, unit=u.deg)
    Sun_sep = around(sun_pos.separation(obj_pos).deg,0)
    TargetExtra.objects.update_or_create(target=target,
        key='sun_separation',
        defaults={'value': Sun_sep})

    return target

# computes priority based on dt 
# if observed within the cadence, then returns just the pure target priority
# if not, then priority increases
def computePriority(dt, imp, cadence):
    ret = 0
    # if (dt<cadence): ret = 1 #ok
    # else:
    #     if (cadence!=0 and dt/cadence>1 and dt/cadence<2): ret = 2
    #     if (cadence!=0 and dt/cadence>2): ret = 3

    # alternative - linear scale
    if (cadence != 0):
        ret = dt / cadence
    return around(ret * imp,1)

# computes dt (mjd_last - mjd_now) and then priority 
# if observed within the cadence, then returns just the pure target priority
# if not, then priority increases
def computeDtAndPriority(mjd_last, imp, cadence,time_to_compute:Time=None):
    ret = 0
    if (time_to_compute == None):
        tt=Time(datetime.utcnow())
    else:
        tt=time_to_compute

    dt = tt.mjd- mjd_last

    return computePriority(dt, imp, cadence)
