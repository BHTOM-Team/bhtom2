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

class ATLASBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class ATLASBroker(BHTOMBroker):
    name = "ATLAS"

    form = ATLASBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.ATLAS)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "ATLAS"
        self.__OBSERVER_NAME: str = "ATLAS"

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

        # RadiusATLAS = str(0.1) #in arcmin
        # ra_str = str(target.ra)
        # dec_str = str(target.dec)
        # # search radius = 0.003 deg, ~10 arcsec, for testing 
        # query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad="+RadiusATLAS+"&DB=photcat&OUT=web&SHORT=short”"
        # # res = requests.get(query)._content
        # # res_str = res.decode()

        ATLAS_name = ""
        try:
            ATLAS_name = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.ATLAS]).value            
        except:
            try:
                ATLAS_name = TargetName.objects.get(target=target, source_name=DataSource.ATLAS.name).name
            except:
                ATLAS_name = ""
                self.logger.warning(f'no ATLAS name for {target.name}')
                return return_for_no_new_points()
            


        #downloading data only if not done before - DIFFERENTIAL MAG!!
        #from temporary URL created by a request
#        https://fallingstar-data.com/forcedphot/static/results/job644041.txt
        #TODO: they also have real names

        url=ATLAS_name

        try:
            with requests.Session() as s:
                textdata = s.get(url).text

            df = pd.read_csv(io.StringIO(textdata.replace("###", "")), delim_whitespace=True)

            # remove rows where mag_err >= 1
            df = df[df['dm'] < 1]
            df = df[df['m']>0] #removes negative mags, but they come from negative flux
            print("ATLAS: ",df)

            if len(df) < 1:
                self.logger.error('[ATLAS PHOTOMETRY] Empty table!')
                return return_for_no_new_points()
        
        except Exception as e:
            # Empty response or error in connection
            self.logger.warning(f'ATLAS returned no observations for {target.name}')
            self.logger.error(f'ATLAS data reading error: {e}')
            return return_for_no_new_points()
        
        try:
            reduced_datums = []
            for _, datum in df.iterrows():

                mjd = datum.MJD #MJD of the start of the exposure, all exposures: 30s
                timestamp = Time(datum.MJD, format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                fil = "ATLAS(" + datum.F + ")"
                mag = datum.m #AB mag
                dm = datum.dm
                reduced_datum = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=mjd,
                                           value=mag,
                                           source_name=self.name,
                                           source_location=url,
                                           error=dm,
                                           filter = fil, 
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME, #the ATLAS data file on which the measurements were made
                                           value_unit = ReducedDatumUnit.MAGNITUDE)
                                           
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"ATLAS Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()
            
        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
#it returns a dictionary with citations and acknowledgment, TODO: split into two methods?
def getCitation():
    cite="""
    Cite: Tonry et al. (2018), Smith et al. (2020), Heinze et al. (2018), Shingles et al. (2021), https://fallingstar-data.com/forcedphot/ 
    """
    ackn="""
    This work has made use of data from the Asteroid Terrestrial-impact Last Alert System (ATLAS) project. The Asteroid Terrestrial-impact Last Alert System (ATLAS) project is primarily funded to search for near earth asteroids through NASA grants NN12AR55G, 80NSSC18K0284, and 80NSSC18K1575; byproducts of the NEO search include images and catalogs from the survey area. This work was partially funded by Kepler/K2 grant J1944/80NSSC19K0112 and HST GO-15889, and STFC grants ST/T000198/1 and ST/S006109/1. The ATLAS science products have been made possible through the contributions of the University of Hawaii Institute for Astronomy, the Queen’s University Belfast, the Space Telescope Science Institute, the South African Astronomical Observatory, and The Millennium Institute of Astrophysics (MAS), Chile."""

    return {'cite':cite,'ackn':ackn}