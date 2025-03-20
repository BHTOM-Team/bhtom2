from django import template
from astropy.coordinates import Angle
from astropy import units as u

import numpy as np

register = template.Library()


@register.filter
def deg_to_sexigesimal(value, fmt):
    """
    Displays a degree coordinate value in sexigesimal, given a format of hms or dms.
    """
    a = Angle(value, unit=u.degree)
    if fmt == 'hms':
        return '{0:02.0f}:{1:02.0f}:{2:06.3f}'.format(a.hms.h, a.hms.m, a.hms.s)
    elif fmt == 'dms':
        rep = a.signed_dms
        sign = '-' if rep.sign < 0 else '+'
        dd = rep.d
        mm = rep.m
        ss = rep.s

        ##this fixes the error in rounding seconds, e.g. for dec=54.4
        if np.abs(rep.s - 59.999) < 0.001:
            ss = 0
            mm += 1
        if mm == 60:
            mm = 0
            dd += 1
        return '{0}{1:02.0f}:{2:02.0f}:{3:06.3f}'.format(sign, dd, mm, ss)
    else:
        return 'fmt must be "hms" or "dms"'


@register.filter
def get_item(dictionary, key):
    """
    Custom filter that retrieves the value of a dictionary based on a given key.
    """
    return dictionary.get(key)


@register.inclusion_tag('bhtom_targets/partials/target_table.html')
def target_table(targets):
    """
    Returns a partial for a table of targets, used in the target_list.html template
    by default
    """
    return {'object_list': targets}

@register.filter
def substring(value, arg):
    """
    Splits the string into a list of substrings at each point where 
    the separator occurs.
    """
    indices = list(map(int, arg.split(',')))
    start = indices[0]
    end = indices[1] if len(indices) > 1 else None
    return value[start:end]

@register.inclusion_tag('bhtom_targets/partials/aladin_public.html')
def aladin_public(target):
    """
    Displays Aladin skyview of the given target along with basic finder chart annotations including a compass
    and a scale bar. This templatetag only works for sidereal targets.
    """
    return {'target': target}
