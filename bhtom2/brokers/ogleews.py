import csv
from datetime import datetime
import json
import re
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

from astropy.coordinates import SkyCoord

logger: BHTOMLogger = BHTOMLogger(__name__, '[OGLE_EWS Broker]')

import io

ogleews_base_url = 'https://www.astrouw.edu.pl/ogle/ogle4/ews'


class OGLEEWSBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class OGLEEWSBroker(BHTOMBroker):
    name = "OGLE_EWS"

    form = OGLEEWSBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.OGLE_EWS)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "OGLE_EWS"
        self.__OBSERVER_NAME: str = "OGLE"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        # If you are going to perform searches by coordinates, you might want to change the max_separation
        # Remember to pass it in astropy.unit format as well
        # Here: 3 arcseconds
        self.__cross_match_max_separation = 3*u.arcsec
        # 5 arcseconds
        self.__MATCHING_RADIUS: float = 5 * u.arcsec

        try:
            self.__base_url: str = settings.OGLE_EWS_PATH
        except Exception as e:
            self.logger.warning(f'No OGLE_EWS_PATH in settings found!')
            self.__base_url = 'https://www.astrouw.edu.pl/ogle/ogle4/ews/'  #ONLY OGLE-IV

    def fetch_alerts(self, parameters):
        """Must return an iterator"""
        response = query_external_service(f'{self.__base_url}/2011/lenses.par', self.name, 'content')
#https://www.astrouw.edu.pl/ogle/ogle4/ews/2011/lenses.par


        alert_list = []
        pattern = re.compile(r'\s+')
        rows = [pattern.split(line.strip()) for line in response.splitlines()]
        headers = rows[0]
        for row in rows[1:]:
            print(dict(zip(headers, row)))
            alert = dict(zip(headers, row))
            alert_list.append(alert)
            
        print("OGLE: ",alert_list)

        if parameters['cone'] is not None and len(parameters['cone']) > 0:
            cone_params = parameters['cone'].split(',')
            if len(cone_params) > 3:
                parameters['cone_ra'] = float(cone_params[0])
                parameters['cone_dec'] = float(cone_params[1])
                parameters['cone_radius'] = float(cone_params[2]) * u.deg
                parameters['cone_centre'] = SkyCoord(float(cone_params[0]),
                                                     float(cone_params[1]),
                                                     frame="icrs", unit="deg")

        filtered_alerts = []
        if parameters.get('target_name'):
            for alert in alert_list:
                if parameters['target_name'] in alert['name']:
                    filtered_alerts.append(alert)

        elif 'cone_radius' in parameters.keys():
            for alert in alert_list:
                c = SkyCoord(float(alert['RA(J2000)']), float(alert['Dec(J2000)']),
                             frame="icrs", unit="deg")
                if parameters['cone_centre'].separation(c) <= parameters['cone_radius']:
                    filtered_alerts.append(alert)

        else:
            filtered_alerts = alert_list

        return iter(filtered_alerts)


    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass
 
    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:
     
        # We are going to probably obtain some response from an API call or using a python package
        #response: str = ''

        RadiusOGLE_EWS = str(1.0) #in arcsec
        ra_str = str(target.ra)
        dec_str = str(target.dec)

        #TODO: here we should search for an object based on ra,dec, but this is not yet possible, so we use the name

        # search radius = 0.003 deg, ~10 arcsec, for testing 
#        query = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi?RA="+ra_str+"&Dec="+dec_str+"&Rad="+RadiusOGLE_EWS+"&DB=photcat&OUT=web&SHORT=short”"
        # res = requests.get(query)._content
        # res_str = res.decode()

        ogleews_name = ""
        try:
            ogleews_name = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.OGLE_EWS]).value            
        except:
            try:
                ogleews_name = TargetName.objects.get(target=target, source_name=DataSource.OGLE_EWS.name).name
            except:
                ogleews_name = ""
                self.logger.error(f'no OGLE_EWS name for {target.name}')
                return return_for_no_new_points()

        print("OGLE_EWS STARTS name found ",ogleews_name)

        text = ogleews_name.split('-')
        year = text[1]
        num = text[3]

        url = ("https://www.astrouw.edu.pl/ogle/ogle4/ews/%s/blg-%s/phot.dat")%(year, num)

        try:        
            response: str = query_external_service(url,
                                                'OGLE_EWS')
            ogleLc = pd.read_csv(StringIO(response), delim_whitespace=True, header=None)
        except Exception as e:
            print("OGLE: ",e)
            self.logger.error(f'OGLE_EWS data load error {target.name}')
            return return_for_no_new_points()
    
        try:
            reduced_datums = []
            for row in ogleLc.values:
                hjd = row[0]
                mag = row[1]
                magerr = row[2]

                if float(magerr) > 9:
                    continue

                mjd: float = float(hjd-2400000.5)

                timestamp = Time(mjd, format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                reduced_datum = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=mjd,
                                            value=mag,
                                            source_name=self.name,
                                            source_location=url,
                                            error=magerr,
                                            filter='OGLE(I)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME,
                                            value_unit = ReducedDatumUnit.MAGNITUDE)
                                            
                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                self.logger.info(f"OGLE_EWS Broker returned {new_points} points for {target.name}")

        except Exception as e:
            self.logger.error(f'OGLE_EWS broker: Error while saving reduced datapoints for {target.name}: {e}')
            return return_for_no_new_points()


        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
def getCitation():
    return "CITATION TO OGLE_EWS Udalski(2015) and acknowledgment."
