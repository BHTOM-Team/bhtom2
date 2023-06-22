from sqlite3 import IntegrityError
from typing import Dict, Any, Tuple, List

from django.db.models import Count

import csv
from bhtom2.harvesters.gaia_alerts import GaiaAlertsHarvester
from bhtom_base.bhtom_targets.models import Target, TargetName, TargetExtra
from io import StringIO
from django.db.models import ExpressionWrapper, FloatField
from django.db.models.functions.math import ACos, Cos, Radians, Pi, Sin
from django.conf import settings
from math import radians
from bhtom_base.bhtom_common.hooks import run_hook
from astropy.coordinates import Angle
from astropy import units as u
from django.db import transaction


def import_targets(targets):
    """
    Imports a set of targets into the TOM and saves them to the database.

    Additionally, performs post hook for each target (names, creation date)

    :param targets: String buffer of targets
    :type targets: StringIO

    :returns: dictionary of successfully imported targets, as well errors
    :rtype: dict
    """
    # TODO: Replace this with an in memory iterator
    targetreader = csv.DictReader(targets, dialect=csv.excel)
    targets = []
    errors = []
    base_target_fields = [field.name for field in Target._meta.get_fields()]
    for index, row in enumerate(targetreader):
        if not any(row.values()):
            # If all values in the row are empty, then it is considered empty
            print(f"Row {index} is empty")
            continue
        # filter out empty values in base fields, otherwise converting empty string to float will throw error
        row = {k.strip(): v.strip() for (k, v) in row.items() if not (k.strip() in base_target_fields and not v.strip())}
        target_extra_fields = []
        target_names = {}
        target_fields = {}

        #gets all possible source names, written in upper case
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
        for extra in target_extra_fields:
            row.pop(extra[0])


        # if "ra" not in target_fields :
        #     raise ValueError("Error: 'ra' not found in import field names")
        # if "dec" not in target_fields :
        #     raise ValueError("Error: 'dec' not found in import field names")
        if "ra" not in target_fields and "GAIA_ALERTS" not in target_names:
            raise ValueError("Error: 'ra' not found in import field names")
        if "dec" not in target_fields and "GAIA_ALERTS" not in target_names:
            raise ValueError("Error: 'dec' not found in import field names")
            

        try:
            #special case when Gaia Alerts name is provided, then not using Ra,Dec from the file
            #TODO: should be generalised for any special source name, e.g. ZTF, for which we have a harvester
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
                        classif: str = catalog_data["classif"]

                        # extras : Dict[str] = {}
                        # extras["classification"] = classif
                        # extras["importance"] = str(9.99)
                        # extras["discovery_date"] = disc
                        # extras["cadence"] = str(1.0)

                        t0: Target = harvester.to_target()
                        ex0: TargetExtra = harvester.to_extras()
                        # #extracting fields:
                        gaia_fields = {}
                        gaia_extras = {}
                        gaia_extras.update(ex0)
                        #copying all from Gaia target to gaia fields
                        for attr, value in t0.__dict__.items():
                            if not attr.startswith('_'):
                                gaia_fields[attr] = value
                        #preserving extra fields from the csv file:
                        # Iterate over the items in gaia_extras
                        for k, v in gaia_extras.items():
                            # Check if the key already exists in target_extra_fields
                            if k not in [key for key, value in target_extra_fields]:
                                # If the key is not already in target_extra_fields, append a new tuple with the key-value pair
                                target_extra_fields.append((k, v))
                        #overwriting all classical fields:
                        target_fields.update(gaia_fields)
                        print("Import: Gaia Alerts harvester used to fill the target info as ",gaia_alerts_name)
#                        ra = t0.ra
#                        dec = t0.dec
#                        target_fields = {"ra": ra, "dec": dec}


            target = Target.objects.create(**target_fields)

            for extra in target_extra_fields:
                TargetExtra.objects.create(target=target, key=extra[0], value=extra[1])
            for name in target_names.items():
                if name:
                    source_name = name[0].upper().replace('_NAME', '')
                    TargetName.objects.create(target=target, source_name=source_name, name=name[1])

            #if type field not present, setting SIDERAL as default
            if "type" not in row:
                target.type=Target.SIDEREAL

            try:
                run_hook('target_post_save', target=target, created=True)
            except Exception as e:
                print("Error in import hook:",e)
                pass

            print("IMPORT: target to append:", target)
            targets.append(target)
        except Exception as e:
            error = 'Error on line {0}: {1}'.format(index + 2, str(e))
            errors.append(error)

    return {'targets': targets, 'errors': errors}
