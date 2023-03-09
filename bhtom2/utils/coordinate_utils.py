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
    target.galactic_lat = around(coordinates.galactic.b.degree, 6)
    target.galactic_lng = around(coordinates.galactic.l.degree,6)

    logger.debug(f'Filling in galactic coordinates for target {target.name}...')

    return target

def update_sun_distance(target: Target):
    """
    Computes the Sun-target distance in degrees for NOW 
    and fills the Extra field for this target.
    No decimal points, rounding to degrees.
    """
    #SUN's position now:
    sun_pos = get_sun(Time(datetime.utcnow()))

    obj_pos = SkyCoord(target.ra, target.dec, unit=u.deg)
    Sun_sep = around(sun_pos.separation(obj_pos).deg,0)
    TargetExtra.objects.update_or_create(target=target,
    key='sun_separation',
    defaults={'value': Sun_sep})

    return target