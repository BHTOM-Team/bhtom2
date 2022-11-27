from datetime import datetime
from typing import Optional, List, Tuple

from django import forms
from django.db import transaction
import astropy.units as u
from astropy.time import Time, TimezoneInfo

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.connectWSDB import WSDBConnection
from bhtom2.external_service.data_source_information import DataSource, TARGET_NAME_KEYS
from bhtom_base.bhtom_alerts.alerts import GenericQueryForm
from bhtom_base.bhtom_dataproducts.models import DatumValue
from bhtom_base.bhtom_dataproducts.models import ReducedDatum

'''Broker reading LINEAR light curves from WSDB'''

class LINEARBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class LINEARBroker(BHTOMBroker):
    name = 'LINEAR'  # Add the DataSource.XXX.name here -- DataSource is an enum with all possible sources of data
    # bhtom2.external_service.data_source_information

    form = LINEARBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.LINEAR)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "LINEAR"
        self.__OBSERVER_NAME: str = "LINEAR"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        # If you are going to perform searches by coordinates, you might want to change the max_separation
        # Remember to pass it in astropy.unit format as well
        # Here: 5 arcseconds
        self.__cross_match_max_separation = 1*u.arcsec

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:

        # Change the log message
        self.logger.debug(f'Updating LINEAR lightcurve for target: {target.name}')

        ra, dec = target.ra, target.dec

        radius = self.__cross_match_max_separation.value

        sqllinear=("select s.mjd,s.mag,s.magerr FROM lineardb.sources as s, lineardb.objects as o where q3c_radial_query(o.ra, o.decl, %f, %f, %f/3600.) and o.objectid=s.objectid;")%(ra, dec, radius)
        linearres=[]
        try:
            linearres=WSDBConnection().run_query(sqllinear)
        except Exception as e:
            self.logger.error(f'Error with WSDB connection for LINEAR for {target.name}: {e}')

        # Process the data here to obtain a numpy array, list, or whatever feels comfortable to process
        data: List[Tuple] = linearres

        # Leave the try/except so that any erronerous data doesn't cause anything to break


        lightcurveupdatereport = return_for_no_new_points()

        #0     1 .       2 .      3          4        5            6             7             8
        #mjd, psfmag_g, psfmag_r, psfmag_i, psfmag_z, psfmagerr_g, psfmagerr_r, psfmagerr_i, psfmagerr_z

        try:
            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for datum in data:
                timestamp = Time(datum[0], format="mjd").to_datetime(timezone=TimezoneInfo())
                
                reduced_datum = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum[0],
                                            value=datum[1], #filter cl
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[2],
                                            filter='LINEAR(W)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                

                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                lightcurveupdatereport = LightcurveUpdateReport(new_points=new_points)
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
        
        return lightcurveupdatereport


''' finding Linear objectid'''
'''select objectid FROM lineardb.objects WHERE q3c_radial_query(ra, decl, 271.011321, 63.239322, 3/3600.);'''

'''getting a light curve by ra,dec - very slow??'''
'''select mjd,mag,magerr, calib, fwhm FROM lineardb.sources WHERE q3c_radial_query(ra, decl, 271.011321, 63.239322, 3/3600.);'''

'''getting a light curve by objectid'''
'''select mjd,mag,magerr FROM lineardb.sources WHERE objectid=21063425;'''

'''light curve by RA-DEC'''
'''select s.mjd,s.mag,s.magerr FROM lineardb.sources as s, lineardb.objects as o where q3c_radial_query(o.ra, o.decl, 217.5838739, 23.062370088, 3/3600.) and o.objectid=s.objectid;'''

'''INFO ON THE SURVEY: https://iopscience.iop.org/article/10.1088/0004-6256/142/6/190'''