from datetime import datetime
from typing import Optional, List, Tuple
import pandas as pd
from io import StringIO
import requests
from bhtom2.external_service.external_service_request import query_external_service
from bhtom2.utils.bhtom_logger import BHTOMLogger
import numpy as np
from django import forms
from django.db import transaction
import astropy.units as u
from astropy.time import Time, TimezoneInfo

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom_base.bhtom_alerts.alerts import GenericQueryForm
from bhtom_base.bhtom_dataproducts.models import DatumValue, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.models import ReducedDatum

from bhtom_base.bhtom_targets.models import  TargetExtra, TargetName

import io

class ASASSNBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class ASASSNBroker(BHTOMBroker):
    name = "ASASSN"

    form = ASASSNBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.ASASSN)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "ASASSN"
        self.__OBSERVER_NAME: str = "ASASSN"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        # If you are going to perform searches by coordinates, you might want to change the max_separation
        # Remember to pass it in astropy.unit format as well
        # Here: 5 arcseconds
        self.__cross_match_max_separation = 5*u.arcsec
        # 5 arcseconds
        self.__MATCHING_RADIUS: float = 5 * u.arcsec

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass
 
    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:
     
        # We are going to probably obtain some response from an API call or using a python package
        #response: str = ''

        # RadiusASASSN = str(0.1) #in arcmin
        # ra_str = str(target.ra)
        # dec_str = str(target.dec)
        # # search radius = 0.003 deg, ~10 arcsec, for testing 
        # query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad="+RadiusASASSN+"&DB=photcat&OUT=web&SHORT=short”"
        # # res = requests.get(query)._content
        # # res_str = res.decode()

        asassn_name = ""
        try:
            asassn_name = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.ASASSN]).value            
        except:
            try:
                asassn_name = TargetName.objects.get(target=target, source_name=DataSource.ASASSN.name).name
            except:
                asassn_name = ""
                self.logger.warning(f'no ASASSN name for {target.name}')
                return return_for_no_new_points()
            
    

        #downloading data only if not done before
        #it will read page e.g.: https://asas-sn.osu.edu/sky-patrol/coordinate/9078bdcd-86ee-4029-8b7d-b7563ed5d740/export.csv
        #so only 9078bdcd-86ee-4029-8b7d-b7563ed5d740 is needed in name
        
        if asassn_name.startswith("https://asas-sn.osu.edu/sky-patrol/coordinate/"):
            asassn_name= asassn_name.replace("https://asas-sn.osu.edu/sky-patrol/coordinate/", "")

        url = "https://asas-sn.osu.edu/sky-patrol/coordinate/" + asassn_name + "/export.csv"

        try:
            response = requests.get(url)
            content = response.content.decode('utf-8')

            df = pd.read_csv(io.StringIO(content), header=0)
            # remove rows where mag_err >= 1
            df = df[df['mag_err'] < 1]

            if len(df) < 1:
                self.logger.error('[ASAS-SN PHOTOMETRY] Empty table!')
                return return_for_no_new_points()
        
        except Exception as e:
            # Empty response or error in connection
            self.logger.warning(f'ASASSN returned no observations for {target.name}')
            print("ASASSN error: ",e)
            return return_for_no_new_points()
        
        try:
            reduced_datums = []
            for _, datum in df.iterrows():
                mjd = datum.HJD-2400000.5
                timestamp = Time(datum.HJD, format="jd", scale="utc").to_datetime(timezone=TimezoneInfo())
                reduced_datum = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=mjd,
                                           value=datum.mag,
                                           source_name=self.name,
                                           source_location='https://asas-sn.osu.edu',  # e.g. alerts url
                                           error=datum.mag_err,
                                           filter = "ASASSN(" + datum.Filter + ")",
                                           observer=self.__OBSERVER_NAME,
                                           facility=datum.Camera,
                                           value_unit = ReducedDatumUnit.MAGNITUDE)
                                           
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"ASASSN Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()
            
        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
def getCitation():
    return "CITATION TO ASASSN and acknowledgment."