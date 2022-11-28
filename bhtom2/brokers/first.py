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
from bhtom_base.bhtom_dataproducts.models import DatumValue, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.models import ReducedDatum

'''Broker reading FIRST radio data from WSDB'''

class FIRSTBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class FIRSTBroker(BHTOMBroker):
    name = 'FIRST'  # Add the DataSource.XXX.name here -- DataSource is an enum with all possible sources of data
    # bhtom2.external_service.data_source_information

    form = FIRSTBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.FIRST)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "FIRST"
        self.__OBSERVER_NAME: str = "FIRST"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        # If you are going to perform searches by coordinates, you might want to change the max_separation
        # Remember to pass it in astropy.unit format as well
        # Here: 5 arcseconds
        self.__cross_match_max_separation = 5*u.arcsec

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:

        # Change the log message
        self.logger.debug(f'Updating FIRST lightcurve for target: {target.name}')

        ra, dec = target.ra, target.dec

        radius = self.__cross_match_max_separation.value

        #fint is integrated flux at 1.4GHz, while f.fpeak is the peak flux
        #NOTE: ep_jd is the MEAN epok, and s_ep_jd_ is its rms - could be up to 6 years!!! 
        sqlfirst=("select f.ep_jd_, f.fint, f.rms from first_2014.main as f where q3c_radial_query(f.raj2000, f.dej2000, %f, %f, %f/3600.);")%(ra, dec, radius)
        firstres=[]
        try:
            firstres=WSDBConnection().run_query(sqlfirst)
        except Exception as e:
            self.logger.error(f'Error with WSDB connection for FIRST for {target.name}: {e}')

        # Process the data here to obtain a numpy array, list, or whatever feels comfortable to process
        data: List[Tuple] = firstres

        # Leave the try/except so that any erronerous data doesn't cause anything to break


        lightcurveupdatereport = return_for_no_new_points()

        #0     1 .       2 .      3          4        5            6             7             8
        #mjd, psfmag_g, psfmag_r, psfmag_i, psfmag_z, psfmagerr_g, psfmagerr_r, psfmagerr_i, psfmagerr_z

        try:
            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for datum in data:
                timestamp = Time(datum[0], format="jd").to_datetime(timezone=TimezoneInfo())
                mjd = Time(datum[0], format="jd").mjd
                
                reduced_datum = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=mjd,
                                            value=datum[1], #flux
                                            value_unit=ReducedDatumUnit.MILLIJANSKY,
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[2],
                                            filter='FIRST(Flux 1.4GHz)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                reduced_datums.extend([reduced_datum])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                lightcurveupdatereport = LightcurveUpdateReport(new_points=new_points)
                self.logger.info(f"FIRST Broker returned {new_points} points for {target.name}")
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
        
        return lightcurveupdatereport



'''INFO ON THE SURVEY to cite?: http://cdsbib.u-strasbg.fr/cgi-bin/cdsbib?2015ApJ...801...26H '''
'''columns described: https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=VIII/92'''
