from datetime import datetime
from typing import Optional, List, Tuple
import pandas as pd
from io import StringIO
import requests
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



class CRTSBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class CRTSBroker(BHTOMBroker):
    name = DataSource.CRTS

    form = CRTSBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.CRTS)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "CRTS"
        self.__OBSERVER_NAME: str = "CRTS"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.__data_source, self.__data_source.name)

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

        ra_str = str(target.ra)
        dec_str = str(target.dec)
        # search radius = 0.003 deg, ~10 arcsec, for testing 
        query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad=0.003&DB=photcat&OUT=web&SHORT=short”"
        res = requests.get(query)._content
        res_str = res.decode()
        res_tab = res_str.split("null|\n",1)[1]
        df = pd.read_html(StringIO(res_str), match='Photometry of Objs')
        df = df[0]

        try:
            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for _, datum in df.iterrows():
                timestamp = Time(datum.MJD, format="mjd").to_datetime(timezone=TimezoneInfo())
                reduced_datum = ReducedDatum(target=target,
                                           data_type='photometry',
                                           timestamp=timestamp,
                                           mjd=datum.MJD,
                                           value=datum.Mag,
                                           source_name=self.name,
                                           source_location='Caltech',  # e.g. alerts url
                                           error=datum.Magerr,
                                           filter='CRTS',
                                           observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME)
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()
            
        return LightcurveUpdateReport(new_points=new_points)
