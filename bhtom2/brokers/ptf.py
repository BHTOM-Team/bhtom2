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
from bhtom_base.bhtom_targets.models import TargetExtra

'''
THIS IS JUST A PLACEHOLDER! The correctly working code is in the Harvester. DO NOT USE THIS ONE!'''

class PTFBrokerQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)

    def clean(self):
        super().clean()


class PTFBroker(BHTOMBroker):
    name = 'PTF'  # Add the DataSource.XXX.name here -- DataSource is an enum with all possible sources of data
    # bhtom2.external_service.data_source_information

    form = PTFBrokerQueryForm

    def __init__(self):
        super().__init__(DataSource.PTF)  # Add the DataSource here

        # If the survey is e.g. a space survey, fill the facility and observer names in and treat is as a constant
        self.__FACILITY_NAME: str = "2MASS"
        self.__OBSERVER_NAME: str = "2MASS"

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


        ra, dec = target.ra, target.dec

        radius = self.__cross_match_max_separation.value

        hasName = ""
        try:
            hasName = TargetExtra.objects.get(target=target, key=TARGET_NAME_KEYS[DataSource.PTF]).value
        except:
            hasName = ""
        
        #extracts the data only if there is no CRTS name
        if (hasName!="" and self.__update_cadence == None):
            self.logger.debug(f'PTF data already downloaded. Skipping. {target.name}')
            return return_for_no_new_points()

        # Change the log message
        self.logger.debug(f'Updating PTF lightcurve for target: {target.name}')

        ## THIS IS WRONG BELOW! THIS CODE IS JUST PLACEHOLDER, use/edit the one in Harvester!
        sqlPTF=("""Select gpsfmag, rpsfmag, ipsfmag, zpsfmag, gpsfmagerr, rpsfmagerr, ipsfmagerr, zpsfmagerr, gepoch, repoch, iepoch, zepoch, objid from panstarrs_dr1.stackobjectthin 
        WHERE (ginfoflag3&panstarrs_dr1.detectionflags3('STACK_PRIMARY'))>0 AND q3c_radial_query(ra, dec, %f, %f, %f/3600.);""")%(ra, dec,radius)
        PTFres=[]
        try:
            PTFres=WSDBConnection().run_query(sqlPTF)
        except Exception as e:
            self.logger.error(f'Error with WSDB connection for PTF for {target.name}: {e}')

        # Process the data here to obtain a numpy array, list, or whatever feels comfortable to process
        data: List[Tuple] = PTFres


        # Leave the try/except so that any erronerous data doesn't cause anything to break

        lightcurveupdatereport = return_for_no_new_points()

        #0     1 .       2 .      3       4           5           6           7           8       9 .     10      11,      12
#     gpsfmag, rpsfmag, ipsfmag, zpsfmag, gpsfmagerr, rpsfmagerr, ipsfmagerr, zpsfmagerr, gepoch, repoch, iepoch, zepoch , objid
        try:
            row = data[0]  # Accessing the first row
            obj_str = str(row[12])

            inventName: Optional[str] = "PTF_"+obj_str
            TargetExtra.objects.update_or_create(target=target,
                                            key=TARGET_NAME_KEYS[DataSource.PTF],
                                            defaults={
                                                'value': inventName
                                            })
            
            self.logger.info(f"PTF data found for {target.name}. Downloaded and stored as {inventName}")

            # Change the fields accordingly to the data format
            # Data could be a dict or pandas table as well
            reduced_datums = []
            for datum in data:
                
                timestamp_g = Time(datum[8], format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                timestamp_r = Time(datum[9], format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                timestamp_i = Time(datum[10], format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                timestamp_z = Time(datum[11], format="mjd", scale="utc").to_datetime(timezone=TimezoneInfo())
                
                if (datum[0] is not None and datum[4] is not None):
                   reduced_datum_g = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp_g,
                                            mjd=datum[8],
                                            value=datum[0], #filter g
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[4],
                                            filter='PTF(g)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)
                   reduced_datums.append(reduced_datum_g)

                if (datum[1] is not None and datum[5] is not None):
                    reduced_datum_r = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp_r,
                                            mjd=datum[9],
                                            value=datum[1], #filter r
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[5],
                                            filter='PTF(r)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)
                
                    reduced_datums.append(reduced_datum_r)

                if (datum[2] is not None and datum[6] is not None):
                    reduced_datum_i = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp_i,
                                            mjd=datum[10],
                                            value=datum[2], #filter i
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[6],
                                            filter='PTF(i)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                    reduced_datums.append(reduced_datum_i)

                if (datum[3] is not None and datum[7] is not None):
                    reduced_datum_z = ReducedDatum(target=target,
                                            data_type='photometry',
                                            timestamp=timestamp_z,
                                            mjd=datum[11],
                                            value=datum[3], #filter z
                                            source_name=self.name,
                                            source_location='WSDB',  # e.g. alerts url
                                            error=datum[7],
                                            filter='PTF(z)',
                                            observer=self.__OBSERVER_NAME,
                                            facility=self.__FACILITY_NAME)

                    reduced_datums.append(reduced_datum_z)


            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
                lightcurveupdatereport = LightcurveUpdateReport(new_points=new_points)
                self.logger.info(f"PTF Broker returned {new_points} points for {target.name}")
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for {target.name}: {e}')
        
        return lightcurveupdatereport
