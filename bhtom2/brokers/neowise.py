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
from bhtom_base.bhtom_dataproducts.models import DatumValue
from bhtom_base.bhtom_dataproducts.models import ReducedDatum



class NEOWISEBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class NEOWISEBroker(BHTOMBroker):
    name = "NEOWISE"

    form = NEOWISEBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.NEOWISE)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "NEOWISE"
        self.__OBSERVER_NAME: str = "NEOWISE"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = 30*u.day

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

        ra_str = str(target.ra)
        dec_str = str(target.dec)
        query = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query?catalog=neowiser_p1bs_psd&spatial=cone&radius=5&radunits=arcsec&objstr="+ra_str+"+"+dec_str+"&outfmt=1&selcols=ra,dec,mjd,w1mpro,w1sigmpro,w2mpro,w2sigmpro"
        
        
        try:
            res_str: str = query_external_service(query, 'NEOWISE')
        except IndexError:
            self.logger.warning(f'Warning: NEOWISE server down or error in connecting - no response for {target.name}')
            return return_for_no_new_points()

        try:
            #df = pd.read_csv(StringIO(res_str), match='Photometry of Objs')
            res_tab = res_str.split("null|\n",1)[1]
            df = pd.read_csv(StringIO(res_tab), header=None, names=['ra', 'dec', 'clon', 'clat', 'mjd', 'w1mpro', 'w1sigmpro', 'w2mpro', 'w2sigmpro', 'dist', 'angle'], delim_whitespace=True)
            #df = df[0]
        except Exception:
            # Response not empty, but there is no data - no Coverage
            self.logger.warning(f'Warning: NEOWISE returned no observations (no coverage) for {target.name}')
            return return_for_no_new_points()

        
        
        #res = requests.get(query)._content
        #res_str = res.decode()
        #res_tab = res_str.split("null|\n",1)[1]
        #df = pd.read_csv(StringIO(res_tab), header=None, names=['ra', 'dec', 'clon', 'clat', 'mjd', 'w1mpro', 'w1sigmpro', 'w2mpro', 'w2sigmpro', 'dist', 'angle'], delim_whitespace=True)
   
        try:
            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for _, datum in df.iterrows():
                timestamp = Time(datum.mjd, format="mjd").to_datetime(timezone=TimezoneInfo())
                if (not np.isnan(datum.w1mpro) and not np.isnan(datum.w1sigmpro)):
                    reduced_datum_w1 = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=datum.mjd,
                                           value=datum.w1mpro,
                                           source_name=self.name,
                                           source_location='IPAC/Caltech',  # e.g. alerts url
                                           error=datum.w1sigmpro,
                                           filter='WISE(W1)',
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME)
                if (not np.isnan(datum.w2mpro) and not np.isnan(datum.w2sigmpro)):
                    reduced_datum_w2 = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=datum.mjd,
                                           value=datum.w2mpro,
                                           source_name=self.name,
                                           source_location='IPAC/Caltech',  # e.g. alerts url
                                           error=datum.w2sigmpro,
                                           filter='WISE(W2)',
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME)
                reduced_datums.extend([reduced_datum_w1,reduced_datum_w2])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"NEOWISE Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()
            
        return LightcurveUpdateReport(new_points=new_points)