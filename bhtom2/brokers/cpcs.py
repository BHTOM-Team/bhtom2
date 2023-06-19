from datetime import datetime
import json
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

from bhtom_base.bhtom_targets.models import  TargetExtra, TargetName

from bhtom2 import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, '[CPCS Broker]')

def mag_error_with_calib_error(magerr: float, caliberr: float) -> float:
    return np.sqrt(magerr * magerr + caliberr * caliberr)

def filter_name(filter: str,
                catalog: str) -> str:
    return f'{filter}({catalog})'

CPCS_DATA_ACCESS_HASHTAG = settings.CPCS_DATA_ACCESS_HASHTAG
cpcs_base_url = settings.CPCS_BASE_URL


class CPCSBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class CPCSBroker(BHTOMBroker):
    name = "CPCS"

    form = CPCSBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.CPCS)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "CPCS"
        self.__OBSERVER_NAME: str = "CPCS"

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

        RadiusCPCS = str(1.0) #in arcsec
        ra_str = str(target.ra)
        dec_str = str(target.dec)

        #TODO: here we should search for an object based on ra,dec, but this is not yet possible, so we use the name

        # search radius = 0.003 deg, ~10 arcsec, for testing 
#        query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad="+RadiusCPCS+"&DB=photcat&OUT=web&SHORT=short”"
        # res = requests.get(query)._content
        # res_str = res.decode()

        cpcs_name = ""
        try:
            cpcs_name = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.CPCS]).value            
        except:
            try:
                cpcs_name = TargetName.objects.get(target=target, source_name=DataSource.CPCS.name)
            except:
                cpcs_name = ""
                self.logger.error(f'no CPCS name for {target.name}')
                return return_for_no_new_points()

        print("CPCS STARTS name found ",cpcs_name)
        try:        
            response: str = query_external_service(f'{cpcs_base_url}/get_alert_lc_data?alert_name={cpcs_name}',
                                               'CPCS', cookies={'hashtag': CPCS_DATA_ACCESS_HASHTAG})
            lc_data = json.loads(response)
        except:
            self.logger.error(f'CPCS data load error {target.name}')
            return return_for_no_new_points()
    
        try:
            reduced_datums = []
            for mjd, magerr, observatory, caliberr, mag, catalog, filter, id in zip(
                    lc_data['mjd'], lc_data['magerr'], lc_data['observatory'], lc_data['caliberr'], lc_data['mag'],
                    lc_data['catalog'], lc_data['filter'], lc_data['id']
             ):
                # Limits/non-detections are marked with magerr==-1 in CPCS
                if float(magerr) == -1:
                    continue

                mjd: float = float(mjd)

                # Adding calibration error in quad
                magerr_with_caliberr: float = mag_error_with_calib_error(float(magerr),
                                                                            float(caliberr))

                timestamp = Time(mjd, format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                reduced_datum = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=mjd,
                                            value=mag,
                                            source_name=self.name,
                                            source_location=f'{cpcs_base_url}/get_alert_lc_data?alert_name={cpcs_name}&{id}',  # e.g. alerts url
                                            error=magerr_with_caliberr,
                                            filter=filter_name(filter, catalog),
                                            observer=observatory,
                                            facility=observatory,
                                            value_unit = ReducedDatumUnit.MAGNITUDE)
                                            
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"CPCS Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'CPCS broker: Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()


        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
def getCitation():
    return "CITATION TO CPCS and acknowledgment."