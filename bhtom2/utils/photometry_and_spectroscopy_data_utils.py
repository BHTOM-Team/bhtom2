import json
import math
import operator
from tempfile import NamedTemporaryFile
from typing import Any, List, Optional, Tuple

import pandas as pd

from django.conf import settings
from bhtom_base.bhtom_targets.models import Target

from bhtom_base.bhtom_dataproducts.models import ReducedDatum
from .observation_data_extra_data_utils import decode_datapoint_extra_data, ObservationDatapointExtraData, OWNER_KEY

from numpy import around

SPECTROSCOPY: str = "spectroscopy"
FACILITY_KEY = "facility"


def load_datum_json(json_values):
    if json_values:
        if type(json_values) is dict:
            return json_values
        else:
            return json.loads(json_values.replace("\'", "\""))
    else:
        return {}


def decode_owner(extra_data_json_str: str) -> Optional[str]:
    extra_data: Optional[ObservationDatapointExtraData] = decode_datapoint_extra_data(json.loads(extra_data_json_str))
    return getattr(extra_data, 'owner', None)


def get_spectroscopy_observation_time_jd(reduced_datum: ReducedDatum) -> Optional[float]:
    from dateutil import parser
    from datetime import datetime
    from astropy.time import Time
    # Observation time might be included in the file, if spectrum is from an ASCII file.

    if reduced_datum.dp_extra_data:
        extra_data: Optional[ObservationDatapointExtraData] = decode_datapoint_extra_data(
            json.loads(reduced_datum.dp_extra_data))
        if getattr(extra_data, 'observation_time', None):
            try:
                observation_time: datetime = parser.parse(extra_data.observation_time)
                return Time(observation_time).jd
            except ValueError:
                return None
    return None


def get_photometry_data_table(target: Target) -> Tuple[List[List[str]], List[str]]:
    datums = ReducedDatum.objects.filter(target=target,
                                         data_type=settings.DATA_PRODUCT_TYPES['photometry'][0]
                                         ).values('mjd', 'value', 'error', 'facility', 'filter', 'observer')

    columns = ['mjd', 'value', 'error', 'facility', 'filter', 'observer']
    data = list(datums.values())

    return data, columns


def get_photometry_stats(target: Target) -> Tuple[List[List[str]], List[str]]:
    data, columns = get_photometry_data_table(target)

    df = pd.DataFrame(data=data, columns=columns)

    # For now, ignore anything after the ',' character if present
    # This is because sometimes Facility is in form "Facility, Observer"
    # and we only want to take the Facility name
    # If Facility is not present, then fill it with Owner value
    # If the Owner is blank too, fill it with "Unspecified"
    df['facility'] = df['facility'] \
        .apply(lambda x: None if (isinstance(x, float) and math.isnan(x)) else x) \
        .fillna(df['observer']) \
        .fillna('Unspecified') \
        .apply(lambda x: str(x).split(',', 1)[0])

    facilities = df['facility'].unique()

    columns: List[str] = ['facility', 'observer', 'filter', 'Data_points', 'Earliest_time', 'Latest_time']
    stats: List[List[Any]] = []

    for facility in facilities:
        observers = df[df['facility'] == facility]['observer'].unique()
        datapoints = len(df[df['facility'] == facility].index)
        filters = df[df['facility'] == facility]['filter'].unique()
        earliest_time = around(df[df['facility'] == facility]['mjd'].min(), 2)
        latest_time = around(df[df['facility'] == facility]['mjd'].max(), 2)

        stats.append([facility, ", ".join(observers), ", ".join(filters), datapoints, earliest_time, latest_time])

    stats = sorted(stats, key=operator.itemgetter(2), reverse=True)

    return stats, columns


def save_data_to_temporary_file(data: List[List[Any]],
                                columns: List[str],
                                filename: str,
                                sort_by: str = 'JD',
                                sort_by_asc: bool = True) -> Tuple[NamedTemporaryFile, str]:
    df: pd.DataFrame = pd.DataFrame(data=data,
                                    columns=columns).sort_values(by=sort_by, ascending=sort_by_asc)

    tmp: NamedTemporaryFile = NamedTemporaryFile(mode="w+",
                                                 suffix=".csv",
                                                 prefix=filename,
                                                 delete=False)

    with open(tmp.name, 'a') as f:
        f.write("#By downloading the data you agree to use this acknowledgment:\n")
        f.write(
            "#The data was obtained via BHTOM (https://bhtom.space), which has received funding from the European\n")
        f.write(
            "#Union's Horizon 2020 research and innovation program under grant agreement No. 101004719 (OPTICON-RadioNet Pilot).\n")
        f.write("#For more information about acknowledgement and data policy please visit https://about.bhtom.space\n")
    df.to_csv(tmp.name, index=False, sep=';', mode='a')

    return tmp, filename


def save_data_to_latex_table(data: List[List[Any]],
                             columns: List[str],
                             filename: str) -> Tuple[NamedTemporaryFile, str]:
    from .latex_utils import data_to_latex_table

    latex_table_str: str = data_to_latex_table(data=data, columns=columns, filename=filename)

    tmp: NamedTemporaryFile = NamedTemporaryFile(mode="w+",
                                                 suffix=".csv",
                                                 prefix=filename,
                                                 delete=False)

    with open(tmp.name, 'w') as f:
        f.write(latex_table_str)

    return tmp, filename


def get_photometry_stats_latex(target_id: int) -> Tuple[NamedTemporaryFile, str]:
    target: Target = Target.objects.get(pk=target_id)

    data, columns = get_photometry_stats(target)

    filename: str = "target_%s_photometry_stats.tex" % target.name

    return save_data_to_latex_table(data, columns, filename)


def get_photometry_data_stats(target: Target) -> Tuple[NamedTemporaryFile, str]:
    stats, columns = get_photometry_stats(target)

    filename: str = "target_%s_photometry_stats.csv" % target.name

    return save_data_to_temporary_file(stats, columns, filename, 'Data_points', False)


def save_photometry_data_for_target_to_csv_file(target: Target) -> Tuple[NamedTemporaryFile, str]:
    data, columns = get_photometry_data_table(target)

    filename: str = "target_%s_photometry.csv" % target.name

    return save_data_to_temporary_file(data, columns, filename)
