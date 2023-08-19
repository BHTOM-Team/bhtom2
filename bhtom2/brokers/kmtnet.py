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

logger: BHTOMLogger = BHTOMLogger(__name__, '[KMT_NET Broker]')

import io

kmtnet_base_url = 'https://www.astrouw.edu.pl/ogle/ogle4/ews'


class KMTNETBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class KMTNETBroker(BHTOMBroker):
    name = "KMT_NET"

    form = KMTNETBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.KMT_NET)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "KMT_NET"
        self.__OBSERVER_NAME: str = "KMT"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        try:
            self.__base_url: str = settings.KMT_NET_PATH
        except Exception as e:
            self.logger.warning(f'No KMT_NET_PATH in settings found!')
            self.__base_url = 'https://kmtnet.kasi.re.kr/~ulens/event' 

#     def fetch_alerts(self, parameters):
#         """Must return an iterator"""
#         response = query_external_service(f'{self.__base_url}/2011/lenses.par', self.name, 'content')
# #https://www.astrouw.edu.pl/ogle/ogle4/ews/2011/lenses.par


#         alert_list = []
#         pattern = re.compile(r'\s+')
#         rows = [pattern.split(line.strip()) for line in response.splitlines()]
#         headers = rows[0]
#         for row in rows[1:]:
#             print(dict(zip(headers, row)))
#             alert = dict(zip(headers, row))
#             alert_list.append(alert)
            
#         print("OGLE: ",alert_list)

#         if parameters['cone'] is not None and len(parameters['cone']) > 0:
#             cone_params = parameters['cone'].split(',')
#             if len(cone_params) > 3:
#                 parameters['cone_ra'] = float(cone_params[0])
#                 parameters['cone_dec'] = float(cone_params[1])
#                 parameters['cone_radius'] = float(cone_params[2]) * u.deg
#                 parameters['cone_centre'] = SkyCoord(float(cone_params[0]),
#                                                      float(cone_params[1]),
#                                                      frame="icrs", unit="deg")

#         filtered_alerts = []
#         if parameters.get('target_name'):
#             for alert in alert_list:
#                 if parameters['target_name'] in alert['name']:
#                     filtered_alerts.append(alert)

#         elif 'cone_radius' in parameters.keys():
#             for alert in alert_list:
#                 c = SkyCoord(float(alert['RA(J2000)']), float(alert['Dec(J2000)']),
#                              frame="icrs", unit="deg")
#                 if parameters['cone_centre'].separation(c) <= parameters['cone_radius']:
#                     filtered_alerts.append(alert)

#         else:
#             filtered_alerts = alert_list

#         return iter(filtered_alerts)


#     def fetch_alert(self, target_name):
#         pass

#     def to_generic_alert(self, alert):
#         pass
 
    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:
        import urllib.request

        # We are going to probably obtain some response from an API call or using a python package
        #response: str = ''

        RadiusKMT_NET = str(1.0) #in arcsec
        ra_str = str(target.ra)
        dec_str = str(target.dec)

        #TODO: here we should search for an object based on ra,dec, but this is not yet possible, so we use the name

        #KMT-2016-BLG-1533 or 2016-BLG-1533
        kmtnet_name = ""
        try:
            kmtnet_name = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.KMT_NET]).value            
        except:
            try:
                kmtnet_name = TargetName.objects.get(target=target, source_name=DataSource.KMT_NET.name).name
            except:
                kmtnet_name = ""
                self.logger.error(f'no KMT_NET name for {target.name}')
                return return_for_no_new_points()

        print("KMT_NET STARTS name found ",kmtnet_name)

        #trimming the KMT or KMT- beginning TODO: should be done while setting the alias in Create/Update
        if kmtnet_name.startswith("KMT-"):
            kmtnet_name = kmtnet_name.replace("KMT-","")

        if kmtnet_name.startswith("KMT "):
            kmtnet_name = kmtnet_name.replace("KMT ","")

        #e.g. 2016-BLG-1533
        text = kmtnet_name.split('-')
        year = text[0].strip()
        num = text[2].strip()

        from html import escape

        ##searching for the field name in https://kmtnet.kasi.re.kr/~ulens/event/2016/listpage.dat
        listurl = 'https://kmtnet.kasi.re.kr/~ulens/event/'+escape(year)+'/listpage.dat'

        field = ""
        # Open the URL as a file
        with urllib.request.urlopen(listurl) as f:
            for line in f:
                # Decode the line to convert bytes to string
                line = line.decode('utf-8')
            
                # Split the line into columns
                columns = line.split()

                # Check if the first column matches the target
                if columns[0] == "KMT-"+kmtnet_name:
                    field=columns[1]
                    break

        fNum = field[3:5]
        fNum2 = "4" + fNum[1:]

        eventNr = "KB"+year[-2:]+num

        try:  #per all sites

            obs = ["KMTA", "KMTC", "KMTS"]
            urls = []
            for site in obs:

                if(year == "2015"): 
                    urls=["https://kmtnet.kasi.re.kr/~ulens/event/2015/pysis/%s/%s%s_I.pysis"%(eventNr, site,fNum)]
                else:
                    url1 = "https://kmtnet.kasi.re.kr/~ulens/event/%s/data/%s/pysis/%s%s_I.pysis"%(year, eventNr, site, fNum)
                    url2= "https://kmtnet.kasi.re.kr/~ulens/event/%s/data/%s/pysis/%s%s_I.pysis"%(year, eventNr, site, fNum2)
                    urls = [url1, url2]
                    #second url might not exist
                    
#                print("KMTNET : urls:",urls)

                obser=("%s_%s")%(self.__OBSERVER_NAME,site)

                reduced_datums = []

                for url in urls:
                    response = requests.get(url)
                    if response.status_code == 200:
                        response: str = query_external_service(url,
                                                            'KMT_NET')
                        text = response
                        lines = text.split('\n')
                        if(len(lines)>1):
                            for l in lines:
                                if(l[0:1]!="<"):
                                    if(len(l)>0):
                                        col = l.split()
                                        if(col[0] != "#"):# and abs(float(col[1])-0.)>1e-8 and float(col[4])>0. and abs(-99.0 - float(col[1]))>1e-8):
                                            if (year == "2015"):
                                                m = float(col[1])
                                                er = float(col[2])
                                                fwhm = 4 #no value provided
                                            else:
                                                m = float(col[3])
                                                er = float(col[4])
                                                fwhm = float(col[5])
                                                sky = float(col[6]) #could be stored in future
                                                secz = float(col[7]) #airmass
                                            if(er<1 and fwhm<10 and fwhm>0):
                                                mjd: float = float(col[0])+2450000-2400000.5
                                                timestamp = Time(mjd, format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                                                reduced_datum = ReducedDatum(target=target,
                                                    data_type='photometry',
                                                    timestamp=timestamp,
                                                    mjd=mjd,
                                                    value=m,
                                                    source_name=self.name,
                                                    source_location=url,
                                                    error=er,
                                                    filter='KMTNET(I)',
                                                    observer=obser,
                                                    facility=self.__FACILITY_NAME,
                                                    value_unit = ReducedDatumUnit.MAGNITUDE)
                                                    
                                                reduced_datums.extend([reduced_datum])
        except Exception as e:
                print("KMT ERROR: ",e)
                self.logger.error(f'KMT_NET data load error {target.name}')
                return return_for_no_new_points()

        with transaction.atomic():
            new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
            self.logger.info(f"KMT_NET Broker returned {new_points} points for {target.name}")


        return LightcurveUpdateReport(new_points=new_points)

#returns a Latex String with citation needed when using data from this broker
def getCitation():
    return "CITATION TO KMTNET and acknowledgment."
