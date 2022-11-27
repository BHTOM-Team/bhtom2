import math
from datetime import datetime
from typing import Optional, Any, Dict, List, Tuple

from alerce.exceptions import APIError, ObjectNotFoundError
from astropy.time import Time, TimezoneInfo
from django.db import transaction

from bhtom2 import settings
from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.exceptions.external_service import NoResultException, InvalidExternalServiceResponseException
from bhtom2.external_service.data_source_information import DataSource, FILTERS, ZTF_DR8_FILTERS
from bhtom2.external_service.external_service_request import query_external_service
from bhtom_base.bhtom_dataproducts.models import ReducedDatum, DatumValue
from bhtom_base.bhtom_targets.models import Target, TargetExtra
from bhtom2.external_service.data_source_information import TARGET_NAME_KEYS

import pandas as pd
from io import StringIO


# For DR8
class ZTFBroker(BHTOMBroker):
    name = DataSource.ZTF_DR8
    form = None

    def __init__(self):
        super().__init__(DataSource.ZTF_DR8)

        try:
            self.__base_url: str = settings.ZTF_DR_PATH
        except Exception as e:
            self.logger.error(f'No ZTF_DR_PATH in settings found!')
            self.__base_url = 'https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves'

        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"

        # 2 arcseconds
        self.__MATCHING_RADIUS: float = 2 * 0.000278

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass

    def save_ztf_dr8_name_if_missing(self, target: Target, ztf_dr8_id: int):
        if not self.get_target_name(target):
            te, _ = TargetExtra.objects.update_or_create(target=target,
                                                         key=self.target_name_key,
                                                         defaults={
                                                             'value': str(ztf_dr8_id)
                                                         })
            te.save()

    def process_reduced_data(self, target: Target, alert=None) -> Optional[LightcurveUpdateReport]:

#       target.targetextra_set[TARGET_NAME_KEYS[DataSource.ZTF]] = ztf_name

        ztf_name: Optional[str] = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.ZTF])
        base_url: str = self.__base_url

        self.logger.debug(f'Updating ZTF Data Releases for {target.name} with ZTF oid {ztf_name}')

        if ztf_name is None or ztf_name == '':
            self.logger.debug(f'No ZTF DR8 id for {target.name}')
            return return_for_no_new_points()

        print_with_sign = lambda i: ("+" if i > 0 else "") + str(i)

        query_parameters: Dict[str, Any] = {
            "POS": f"CIRCLE {target.ra} {target.dec} {self.__MATCHING_RADIUS}",
            "BAD_CATFLAGS_MASK": str(32768),
            "FORMAT": "csv",
#            "COLLECTION": "ztf_dr8", #removed by LW to make it work - are we now reading the newest DR? - but the output has changed!!
        }

        # "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE+255.9302+11.8654+0.0028&BANDNAME=r&NOBS_MIN=3&TIME=58194.0+58483.0&BAD_CATFLAGS_MASK=32768&FORMAT=csv"

        try:
            response: Dict[str, Any] = query_external_service(base_url, service_name=DataSource.ZTF.name,
                                                              params="&".join("%s=%s" % (k, v) for k, v in
                                                                              query_parameters.items()))
        # No such object on ZTF
            res_tab = response.split("null|\n",1)[0]
            df = pd.read_csv(StringIO(res_tab), header=None, names=['oid','expid','hjd','mjd','mag','magerr','catflags','filtercode','ra','dec','chi','sharp','filefracday','field','ccdid','qid','limitmag','magzp','magzprms','clrcoeff','clrcounc','exptime','airmass','programid'], delim_whitespace=False)
            df=df[1:] #removes header
        except ObjectNotFoundError as e:
            raise NoResultException(f'No ZTF data found for {target.name} with ZTF name {ztf_name}')
        except APIError as e:
            raise InvalidExternalServiceResponseException(f'Invalid ZTF response for {target.name}: {e}')
        except Exception as e:
            self.logger.error(f'Error while updating ZTF DR8 for {target.name} with ZTF name {ztf_name}: {e}')
            return return_for_no_new_points()

        # TODO: add non-detections

        new_points: int = 0

        try:
                # Change the fields accordingly to the data format
                # Data could be a dict or pandas table as well
                reduced_datums = []
                for _, datum in df.iterrows():
#                    print(datum.mjd, datum.filtercode)
                    timestamp = Time(datum.mjd, format="mjd").to_datetime(timezone=TimezoneInfo())
                    reduced_datum = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum.mjd,
                                            value=datum.mag,
                                            source_name=self.name,
                                            source_location='IPAC/Caltech',  # e.g. alerts url
                                            error=datum.magerr,
                                            filter=f'ZTF({datum.filtercode})',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)
                    reduced_datums.extend([reduced_datum])

                with transaction.atomic():
                    new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                    self.logger.info(f"ZTF Broker returned {new_points} points for {target.name}")

        except Exception as e:
                self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
                return return_for_no_new_points()
                
        return LightcurveUpdateReport(new_points=new_points)
