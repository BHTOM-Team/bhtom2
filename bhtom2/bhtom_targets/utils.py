import os
from sqlite3 import IntegrityError
from typing import Dict, Any, Tuple, List

from django.core.cache import cache
from django.db.models import Count

import csv

from django.http import HttpRequest
from django.shortcuts import render

from bhtom2.bhtom_targets.filters import TargetFilter
from bhtom2.harvesters.gaia_alerts import GaiaAlertsHarvester
from bhtom2.templatetags.bhtom_targets_extras import target_table
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_targets.models import Target, TargetName, TargetExtra, TargetList
from io import StringIO
from django.db.models import ExpressionWrapper, FloatField
from django.db.models.functions.math import ACos, Cos, Radians, Pi, Sin
from django.conf import settings
from math import radians
from bhtom_base.bhtom_common.hooks import run_hook
from astropy.coordinates import Angle
from astropy import units as u
from django.db import transaction

from bhtom_base.bhtom_targets.utils import cone_search_filter

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.utils')


def import_targets(targets):
    """
    Imports a set of targets into the TOM and saves them to the database.

    Additionally, performs post hook for each target (names, creation date)

    :param targets: String buffer of targets
    :type targets: StringIO

    :returns: dictionary of successfully imported targets, as well errors
    :rtype: dict
    """

    logger.debug("Beginning the IMPORT from a file.")
    # TODO: Replace this with an in memory iterator
    targetreader = csv.DictReader(targets, dialect=csv.excel)
    targets = []
    errors = []
    base_target_fields = [field.name for field in Target._meta.get_fields()]
    for index, row in enumerate(targetreader):
        logger.debug(f"import: {index} {row}")
        if not any(row.values()):
            # If all values in the row are empty, then it is considered empty
#            print(f"Row {index} is empty")
            continue
        # filter out empty values in base fields, otherwise converting empty string to float will throw error
        row = {k.strip(): v.strip() for (k, v) in row.items() if
               not (k.strip() in base_target_fields and not v.strip())}
        target_extra_fields = []
        target_names = {}
        target_fields = {}

        # gets all possible source names, written in upper case
        uppercase_source_names = [sc[0].upper() for sc in settings.SOURCE_CHOICES]

        for kk in row:
            k = kk.strip()
            row_k_value = row[k].strip()
            # Fields with <source_name>_name (e.g. Gaia_name, ZTF_name, where <source_name> is a valid
            # catalog) will be added as a name corresponding to this catalog
            k_source_name = k.upper().replace('_NAME', '')
            if k != 'name' and k.endswith('name') and k_source_name in uppercase_source_names:
                target_names[k_source_name] = row_k_value
            elif k not in base_target_fields:
                target_extra_fields.append((k, row_k_value))
            else:
                target_fields[k] = row_k_value

        # if "ra" not in target_fields :
        #     raise ValueError("Error: 'ra' not found in import field names")
        # if "dec" not in target_fields :
        #     raise ValueError("Error: 'dec' not found in import field names")
        if "ra" not in target_fields and "GAIA_ALERTS" not in target_names:
            raise ValueError("Error: 'ra' not found in import field names")
        if "dec" not in target_fields and "GAIA_ALERTS" not in target_names:
            raise ValueError("Error: 'dec' not found in import field names")

        try:
            # special case when Gaia Alerts name is provided, then not using Ra,Dec from the file
            # TODO: should be generalised for any special source name, e.g. ZTF, for which we have a harvester
            if "GAIA_ALERTS_name" in row:
                gaia_alerts_name = ""
                harvester = GaiaAlertsHarvester()
                for name in target_names.items():
                    source_name = name[0].upper().replace('_NAME', '')
                    if source_name == "GAIA_ALERTS":
                        gaia_alerts_name = name[1].lower().replace("gaia", "Gaia") #to be sure of the correct format, at least first letters
                        catalog_data=harvester.query(gaia_alerts_name)
                        ra: str = catalog_data["ra"]
                        dec: str = catalog_data["dec"]
                        disc: str = catalog_data["disc"]
                        #
                        #description: str = catalog_data["classif"]
                        importance = str(9.99) #by default importing from Gaia Alerts gets 9.99
                        cadence = str(1.0) #default cadence

                        target_fields = {"name":gaia_alerts_name,"ra": ra, "dec": dec, "epoch": 2000.0, "discovery_date":disc, "importance":importance, "cadence":cadence}
#after adding description to the model:
#                        target_fields = {"name":gaia_alerts_name,"ra": ra, "dec": dec, "epoch": 2000.0, "discovery_date":disc, "importance":importance, "cadence":cadence, "description":description}
                        logger.info(f"Import: Gaia Alerts harvester used to fill the target info as {gaia_alerts_name}")

            target = Target.objects.create(**target_fields)

            for name in target_names.items():
                if name:
                    source_name = name[0].upper().replace('_NAME', '')
                    TargetName.objects.create(target=target, source_name=source_name, name=name[1])
                    logger.debug(f"Target {name} added to names for {source_name}")

            # if type field not present, setting SIDERAL as default
            if "type" not in row:
                target.type = Target.SIDEREAL
                logger.debug(f"Target {row} set by default to SIDEREAL.")

            try:
                run_hook('target_post_save', target=target, created=True)
            except Exception as e:
                logger.error(f"Error in import hook: {e}")
                pass

            logger.debug(f"IMPORT: target to append {target}")
            targets.append(target)
        except Exception as e:
            error = 'Error on line {0}: {1}'.format(index + 2, str(e))
            errors.append(error)
        logger.debug(f"Imported targets: {targets}")
        logger.debug(f"Import errors: {errors}")

    return {'targets': targets, 'errors': errors}


def get_aliases_from_queryset(queryset: Dict[str, Any]) -> Tuple[List, List]:
    """
    Extracts the passed aliases from the form queryset.

    :param queryset: data extracted from form as a dictionary
    :type queryset: Dict[str, Any]

    :returns: two lists- source names (e.g. survey names) and corresponding target names
    :rtype: Tuple[List, List]

    """
    target_source_names = [v for k, v in queryset.items() if
                           k.startswith('alias') and k.endswith('-source_name')]
    target_name_values = [v for k, v in queryset.items() if
                          k.startswith('alias') and k.endswith('-name')]
    return target_source_names, target_name_values


def get_nonempty_names_from_queryset(queryset: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Extracts the non-empty aliases from the form queryset.

    :param queryset: data extracted from form as a dictionary
    :type queryset: Dict[str, Any]

    :returns: list of (source_name, target_name)
    :rtype: List[Tuple[str, str]]
    """
    target_source_names, target_name_values = get_aliases_from_queryset(queryset)
    return [(source_name, name) for source_name, name in zip(target_source_names, target_name_values) if
            source_name.strip() and name.strip()]


def check_duplicate_source_names(target_names: List[Tuple[str, str]]) -> bool:
    """
    Checks for target names with duplicate source names.

    :param target_names: list of (source_name, target_name)
    :type target_names: List[Tuple[str, str]]

    :returns: are there duplicate source names
    :rtype: bool
    """
    nonempty_source_names: List[str] = [s for s, _ in target_names]
    return len(nonempty_source_names) != len(set(nonempty_source_names))


def check_for_existing_alias(target_names: List[Tuple[str, str]]) -> bool:
    return sum([len(TargetName.objects.filter(name=alias)) for _, alias in target_names]) > 0


def check_for_existing_coords(ra: float, dec: float, radius: float, queryset: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Extracts the cone_search found targets

    :param ra: RightAscension to search (decimal points)
    :type ra: float

    :param dec: Declination to search (decimal points)
    :type dec: float

    :param radius: search radius in degrees
    :type radius: float

    :param queryset: data extracted from form as a dictionary
    :type queryset: Dict[str, Any]

    :returns: list of target names at these coordinates
    :rtype: List[str]
    """
    existing_coords_names = []
    try:
        cc = cone_search_filter(queryset, ra, dec, radius)
        for target in cc:
            existing_coords_names.append(target.name)
    except Exception as e:
        pass

    return existing_coords_names


def coords_to_degrees(value, c_type):
    """
    Converts from any type of coordinate to decimal degrees

    :param value: Ra or Dec
    :type value: any (float or string)

    :param c_type: 'ra' or 'dec' tells if the value is RA or Dec
    :type c_type: string
    """
    try:
        a = float(value)
        return a
    except ValueError:
        try:
            if c_type == 'ra':
                a = Angle(value, unit=u.hourangle)
            else:
                a = Angle(value, unit=u.degree)
            return a.to(u.degree).value
        except Exception:
            raise Exception('Invalid format. Please use sexigesimal or degrees')


def update_targetList_cache():
    cachePath = os.path.join(settings.BASE_DIR, "bhtom2/cache/targetList")

    for file in os.listdir(cachePath):
        f = os.path.join(cachePath, file)
        if file.endswith('.djcache') and os.path.isfile(f):
            os.remove(f)

    context = {}
    target = Target.objects.all()
    context['object_list'] = target
    request = HttpRequest()
    render(request, 'bhtom_targets/partials/target_table.html', context)


def update_targetDetails_cache():
    cachePath = os.path.join(settings.BASE_DIR, "bhtom2/cache/targetDetails")

    for file in os.listdir(cachePath):
        f = os.path.join(cachePath, file)
        if file.endswith('.djcache') and os.path.isfile(f):
            os.remove(f)
