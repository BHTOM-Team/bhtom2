from datetime import datetime
from typing import Optional, List, Tuple
import pandas as pd
from io import StringIO
import requests
from bhtom2.external_service.external_service_request import query_external_service
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

from bhtom_base.bhtom_targets.models import  TargetExtra

class CRTSBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class CRTSBroker(BHTOMBroker):
    name = "CRTS"

    form = CRTSBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.CRTS)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "CRTS"
        self.__OBSERVER_NAME: str = "CRTS"

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

        RadiusCRTS = str(0.1) #in arcmin
        ra_str = str(target.ra)
        dec_str = str(target.dec)
        # search radius = 0.003 deg, ~10 arcsec, for testing 
        query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad="+RadiusCRTS+"&DB=photcat&OUT=web&SHORT=short”"
        # res = requests.get(query)._content
        # res_str = res.decode()

        hasName = ""
        try:
            hasName = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.CRTS]).value
        except:
            hasName = ""
        
        #extracts the data only if there is no CRTS name
        if (hasName!=""):
            self.logger.debug(f'CRTS data already downloaded. Skipping. {target.name}')
            return return_for_no_new_points()

        #downloading data only if not done before
        try:        
            res_str: str = query_external_service(query, 'CRTS')
#            res_tab = res_str.split("null|\n",1)[1]
        except Exception:
                # Empty response or error in connection
            self.logger.warning(f'Warning: CRTS server down or error in connecting - no response for {target.name}')
            return return_for_no_new_points()

        try:
            df = pd.read_html(StringIO(res_str), match='Photometry of Objs')
            df = df[0]
            #setting CRTS name when data found
            inventName: Optional[str] = "CRTS+J"+ra_str+"_"+dec_str
            TargetExtra.objects.update_or_create(target=target,
                                            key=TARGET_NAME_KEYS[DataSource.CRTS],
                                            defaults={
                                                'value': inventName
                                            })
            self.logger.info(f"CRTS data found for {target.name}. Downloaded and stored as {inventName}")
            
        except Exception:
           # Response not empty, but there is no data - no Coverage
           self.logger.warning(f'Warning: CRTS returned no observations (no coverage) for {target.name}')
           return return_for_no_new_points()

        try:
            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for _, datum in df.iterrows():
                timestamp = Time(datum.MJD, format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                reduced_datum = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=datum.MJD,
                                           value=datum.Mag,
                                           source_name=self.name,
                                           source_location='Caltech',  # e.g. alerts url
                                           error=datum.Magerr,
                                           filter='CRTS(CL)',
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME,
                                           value_unit = ReducedDatumUnit.MAGNITUDE)
                                           
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"Catalina Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()
            
        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
def getCitation():
    return "CITATION TO CRTS and acknowledgment."