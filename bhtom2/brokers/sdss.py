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


class SDSSBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class SDSSBroker(BHTOMBroker):
    name = 'SDSS_DR14'  # Add the DataSource.XXX.name here -- DataSource is an enum with all possible sources of data
    # bhtom2.external_service.data_source_information

    form = SDSSBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.SDSS_DR14)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "SDSS_DR14"
        self.__OBSERVER_NAME: str = "SDSS_DR14"

        self.__target_name_key: str = TARGET_NAME_KEYS.get(self.data_source, self.data_source.name)

        # If the data should be checked from time to time (for alerts), assing the self.__update_cadence
        # If the data should be fetched just once, leave None
        # Remember to pass it in astropy.unit format, e.g. 6*u.h for 6 hours
        self.__update_cadence = None

        # If you are going to perform searches by coordinates, you might want to change the max_separation
        # Remember to pass it in astropy.unit format as well
        # Here: 5 arcseconds
        self.__cross_match_max_separation = 0.5*u.arcsec

    def fetch_alerts(self, parameters):
        pass

    def fetch_alert(self, target_name):
        pass

    def to_generic_alert(self, alert):
        pass

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:

        # Change the log message
        self.logger.debug(f'Updating SDSS_DR14 lightcurve for target: {target.name}')

        ra, dec = target.ra, target.dec

        radius = self.__cross_match_max_separation

        sqlsdss=("Select mjd, psfmag_g, psfmag_r, psfmag_i, psfmag_z, psfmagerr_g, psfmagerr_r, psfmagerr_i, psfmagerr_z from sdssdr14.photoobjall "+
            "WHERE psfmag_g>0 AND psfmag_r>0 AND psfmag_i>0 AND psfmag_z>0 "+
            "AND q3c_radial_query(ra, dec, %f, %f, f{radius}/3600.);")%(ra, dec)
        sdssres=[]
        try:
            sdssres=WSDBConnection().run_query(sqlsdss)
        except Exception as e:
            self.logger.error(f'Error with WSDB connection for SDSS for {target.name}: {e}')

        # Process the data here to obtain a numpy array, list, or whatever feels comfortable to process
        data: List[Tuple] = sdssres

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
                
                reduced_datum_g = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum[0],
                                            value=datum[1], #filter g
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[5],
                                            filter='SDSS_DR14(g)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                reduced_datum_r = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum[0],
                                            value=datum[2], #filter r
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[6],
                                            filter='SDSS_DR14(r)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)
                
                reduced_datum_i = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum[0],
                                            value=datum[3], #filter i
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[7],
                                            filter='SDSS_DR14(i)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                reduced_datum_z = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp,
                                            mjd=datum[0],
                                            value=datum[4], #filter z
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[8],
                                            filter='SDSS_DR14(z)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                reduced_datums.extend([reduced_datum_g,reduced_datum_r,reduced_datum_i,reduced_datum_z])

            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                lightcurveupdatereport = LightcurveUpdateReport(new_points=new_points)
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
        
        return lightcurveupdatereport
