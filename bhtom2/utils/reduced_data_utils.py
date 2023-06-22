from django.conf import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger
from guardian.shortcuts import get_objects_for_user
from typing import Any, List, Tuple
from django.contrib.auth.models import User

from bhtom_base.bhtom_dataproducts.models import ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_targets.models import Target

from tempfile import NamedTemporaryFile
import pandas as pd


logger: BHTOMLogger = BHTOMLogger(__name__, '[Reduced Datum utils]')


def get_photometry_data_table(target: Target) -> Tuple[List[List[str]], List[str]]:

    logger.debug(
        f'Downloading photometry as a table for target {target.name}...')

    datums = ReducedDatum.objects.filter(target=target,
                                         data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                         value_unit=ReducedDatumUnit.MAGNITUDE)

    columns: List[str] = ['MJD', 'Magnitude',
                          'Error', 'Facility', 'Filter', 'Observer']
    data: List[List[Any]] = []

    data = [[datum.mjd,
             datum.value,
             datum.error,
             datum.facility,
             datum.filter,
             datum.observer] for datum in datums]

    return data, columns


def get_radio_data_table(target_id: int) -> Tuple[List[List[str]], List[str]]:
    target: Target = Target.objects.get(pk=target_id)

    logger.debug(
        f'Downloading radio data as a table for target {target.name}...')

    radio_datums = ReducedDatum.objects.filter(target=target,
                                               data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                               value_unit=ReducedDatumUnit.MILLIJANSKY)

    columns: List[str] = ['MJD', 'mJy',
                          'Error', 'Facility', 'Filter', 'Observer']
    data: List[List[Any]] = []

    data = [[datum.mjd,
             datum.value,
             datum.error,
             datum.facility,
             datum.filter,
             datum.observer] for datum in radio_datums]

    return data, columns


def save_data_to_temporary_file(data: List[List[Any]],
                                columns: List[str],
                                filename: str,
                                sort_by: str = 'MJD',
                                sort_by_asc: bool = True) -> Tuple[NamedTemporaryFile, str]:
    df: pd.DataFrame = pd.DataFrame(data=data,
                                    columns=columns).sort_values(by=sort_by, ascending=sort_by_asc)

    tmp: NamedTemporaryFile = NamedTemporaryFile(mode="w+",
                                                 suffix=".csv",
                                                 prefix=filename,
                                                 delete=False)

    with open(tmp.name, 'w') as f:
        df.to_csv(f.name,
                  index=False,
                  sep=';')

    return tmp, filename


def save_data_to_latex_table(data: List[List[Any]],
                             columns: List[str],
                             filename: str) -> Tuple[NamedTemporaryFile, str]:
    from .latex_utils import data_to_latex_table

    latex_table_str: str = data_to_latex_table(
        data=data, columns=columns, filename=filename)

    tmp: NamedTemporaryFile = NamedTemporaryFile(mode="w+",
                                                 suffix=".csv",
                                                 prefix=filename,
                                                 delete=False)

    with open(tmp.name, 'w') as f:
        f.write(latex_table_str)

    return tmp, filename


def save_photometry_data_for_target_to_csv_file(target_id_name) -> Tuple[NamedTemporaryFile, str]:
    #if target_id is int, this is the id, if str this is name:
    if isinstance(target_id_name, int):
        target: Target = Target.objects.get(pk=target_id_name)
    else:
        target: Target = Target.objects.get(name=target_id_name)

    data, columns = get_photometry_data_table(target)

    filename: str = "target_%s_photometry.csv" % target.name

    return save_data_to_temporary_file(data, columns, filename)


def save_radio_data_for_target_to_csv_file(target_id: int) -> Tuple[NamedTemporaryFile, str]:
    target: Target = Target.objects.get(pk=target_id)

    data, columns = get_radio_data_table(target_id)

    filename: str = "target_%s_radio.csv" % target.name

    return save_data_to_temporary_file(data, columns, filename)
