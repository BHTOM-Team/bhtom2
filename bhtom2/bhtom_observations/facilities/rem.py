from django import forms
from bhtom_base.bhtom_targets.models import Target
from crispy_forms.layout import Column, Div, HTML, Layout, Row, MultiWidgetField, Fieldset

from bhtom_base.bhtom_observations.facility import BaseManualObservationFacility, BaseManualObservationForm
from bhtom_base.bhtom_observations.widgets import FilterField
from bhtom_base.bhtom_observations.cadence import CadenceForm
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta

import random

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_rem.views')

SUCCESSFUL_OBSERVING_STATES = ['COMPLETED']
FAILED_OBSERVING_STATES = ['WINDOW_EXPIRED', 'CANCELED', 'FAILURE_LIMIT_REACHED', 'NOT_ATTEMPTED']
TERMINAL_OBSERVING_STATES = SUCCESSFUL_OBSERVING_STATES + FAILED_OBSERVING_STATES

valid_instruments = ['ROS2']
valid_filters = [['griz+H','griz+H'],['griz+J','griz+J'],['griz+Ks','griz+Ks'],['griz+z','griz+z']] #griz are always used in REM + infrared filter
#z_IRCam, J_IRCam, H_IRCam, K_IRCam,
        # H2_IRCam, JH_IRCam, JK_IRCam, HK_IRCam, JHK_IRCam, KH2_IRCam
# z -is the other half of the z band, H2 was an experiment, don't use. 
#infrared filters are behind the filter wheel, only one at a time can be used. 
rem_proposals = settings.FACILITIES.get('REM', {}).get('proposalIDs', [])
proposal_choices = [(str(proposal_id), description) for proposal_id, description in rem_proposals]


class REMPhotometricSequenceForm(BaseManualObservationForm):
#    name = forms.CharField()

    proposal_id = forms.ChoiceField(label="Proposal ID", choices=proposal_choices)

    start = forms.CharField(label="Start date [UT]",widget=forms.TextInput(attrs={'type': 'date'}))
    end = forms.CharField(label="End date [UT]",required=True, widget=forms.TextInput(attrs={'type': 'date'}))

#    observation_id = forms.CharField(required=False)
#    observation_params = forms.CharField(required=False, widget=forms.Textarea(attrs={'type': 'json'}))

    exposure_time = forms.IntegerField(label="Exposure time Opt [s]",initial=60,help_text="in sec per optical exposure") # in sec
    exposure_count = forms.IntegerField(initial=1, help_text="number of optical exposures per visit") # number of exposures per visit

    exposure_time_ir = forms.IntegerField(label="Exposure time IR [s]",initial=10,help_text="in sec per IR exposure") # in sec
    exposure_count_ir = forms.IntegerField(label="Number of NDIT in IR",initial=5,help_text="number of dithers in IR per exposure") 
   
    cadence = forms.FloatField(initial=1,help_text="days until next visit")  # in days to next visit
    filter = forms.ChoiceField(required=True, label='Filters', choices=valid_filters)

    mag_init=99.
    exposure_times = {}

    def __init__(self, *args, **kwargs):
        # Set default values for 'start', 'end', and 'name' in initial_data
        initial_data = kwargs.get('initial', {})
        current_date = datetime.now().strftime('%Y-%m-%d')
        next_day = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        initial_data.setdefault('start', current_date)
        initial_data.setdefault('end', next_day)
        kwargs['initial'] = initial_data
        
        super().__init__(*args, **kwargs)

        target = Target.objects.get(id=self.initial.get('target_id'))
        # initial_data.setdefault('name', f'BHTOM_REM_{target.name}')
        # kwargs['initial'] = initial_data

        # Precompute exposure time for each filter option
        self.mag_init = target.mag_last

        self.exposure_times = {}

        instrument = "ROS2"
        for filter_option, _ in valid_filters:
            self.exposure_times[filter_option] = int(self.exposure_time_calculator(
                mag=self.mag_init, filter_name=filter_option, instrument=instrument
            )) #it has to be int - REM's requirement
        
        # Set initial exposure time based on the first filter choice
        first_filter = self.fields['filter'].initial or valid_filters[0][0]
        initial_data.setdefault('exposure_time', self.exposure_times.get(first_filter))
        kwargs['initial'] = initial_data
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        selected_filter = cleaned_data.get('filter')
        if selected_filter:
            # Set the computed exposure_time directly in the form field : TODO does not work
            self.fields['exposure_time'].initial = self.exposure_times.get(selected_filter)
        return cleaned_data

    def layout(self):
        # Display a table of filters and exposure times
        filter_rows = "".join(f"<tr><td>{filter_option}</td><td>{self.exposure_times.get(filter_option)}</td></tr>" for filter_option, _ in valid_filters)
        mag = self.mag_init
        return Div(
#            Div('name'),
            Div('proposal_id'),
            Div(
                Div('start', css_class='col'),
                Div('end', css_class='col'),
                css_class='form-row'
            ),
            Div('filter'),
            HTML(f"<h6><i>Suggested exposure times for mag={mag}</i></h6><small><table><tr><th>Filter</th><th>Exposure Time</th></tr>{filter_rows}</table></small>"),
            Div('exposure_time'),
            Div('exposure_count'),
            Div('exposure_time_ir'),
            Div('exposure_count_ir'),
            Div('cadence'),
        )
    
    #   http://www.rem.inaf.it/?p=etc
    # 60s for V=15mag gives S/N=100 in optical
    #
    def exposure_time_calculator(self, mag, filter_name, instrument):
        if instrument not in valid_instruments:
            return -1
        if filter_name in [item for sublist in valid_filters for item in sublist]:
            pass
        else:
            return -1

        # Define a base exposure time for each filter
        filter_base_exposure_times = {
            'griz+J': 60,   # Example base exposure time for griz+J filter
            'griz+H': 60,   # Example base exposure time for griz+H filter
            'griz+Ks': 60,   # Example base exposure time for griz+Ks filter
            'griz+JHK': 60,
        }

        # Get the base exposure time for the selected filter
        base_exposure_time = filter_base_exposure_times.get(filter_name, 60)  # Default to 60s
        adjusted_exposure_time = base_exposure_time * (10**((mag-15)/2.5))
        return adjusted_exposure_time    


class REM(BaseManualObservationFacility):
    name = 'REM'
    SITES = {
        'REM': {
            'sitecode': 'REM',
            'latitude': -29.26,
            'longitude': -70.73,
            'elevation': 2400
        }
    }
    observation_forms = {
        'PHOTOMETRIC_SEQUENCE': REMPhotometricSequenceForm,
    }

    def get_form(self, observation_type):
        return self.observation_forms['PHOTOMETRIC_SEQUENCE']

    def validate_observation(self, observation_payload):
        # TODO: ?
        return []

    def get_terminal_observing_states(self):
        return TERMINAL_OBSERVING_STATES

    def get_observing_sites(self):
        return self.SITES

    def cancel_observation(self, observation_id):
        return []

    def get_observation_url(self, observation_id):
        return ''

    def all_data_products(self, observation_record):
        return []


    def submit_observation(self, observation_payload):
        #print(observation_payload)
        # Retrieve target information using the target_id
        target_id = observation_payload['target_id']
        target = Target.objects.get(id=target_id)

        # Extract target details
        # removing spaces in target name (REM requirement)
        target_name = target.name.replace(" ", "_")  # or use .replace(" ", "")
        ra = target.ra
        dec = target.dec

        template = """
[STARTREMOB]



# Target data
[TARGET]

# Category
TargetCategory: NotClassifiedSource
# Available categories:
# SCHGRB (#Scheduled GRB), Star, AGN, LMXRB (# LMXRB), HMXRB (# HMXRB),
# FlaringStar, OpenCluster, GlobularCluster, Planetary Nebula,
# Supernova Remnant, NotClassifiedSource, Galaxy, SoftGamma-RayRepeater
# SolarSystemObject, ActiveSupernova (# Supernova still active), Nebula

# no spaces are allowed in name
TargetName: {target_name}

# RA degrees.dddd, J2000
RA: {ra}

# DEC degrees.dddd, J2000
DEC: {dec}

# Equinox year.dd (this parameter is optional, else is 2000.0)
Equinox: 2000.0

# Optical camera data
[ROSS]

# 1 if optical data are desidered, else 0
OptFlag: 1

# seconds, total requested time must be less than 1 hour
Exptime: {exptime}

# Camera focus (optional)
OptFocus: 0

# CCD sensitivity (optional)
# Sensitivity options:
# CCDslowsens, CCDslowhigh, CCDfastsens, CCDfasthigh, CCDultrasens, CCDultrahigh
OptSensitivity: CCDslowsens

# number of exposures
OptNInt: {expcount}


# Infrared camera data

[REMIR]

# 1 if infrared data are desidered, else 0
IRFlag: 1

# detector integration time, seconds
DIT: {exptime_ir}

# filter
IRFilter: {ir_filter}

# number of exposure DITx5 long
IRNInt: {expcount_ir}

# Available filter are: z_IRCam, J_IRCam, H_IRCam, K_IRCam,
# H2_IRCam, JH_IRCam, JK_IRCam, HK_IRCam, JHK_IRCam, KH2_IRCam


# PI data

[PI]

# PI name, no spaces are allowed
PIName: BHTOM

# PI institute, no spaces are allowed
PIInst: Warsaw

# PI e-mail
PIEmail: {email}



# Observation data and access permission

[DATA]

# your proposal Id
PropId: {proposal_id}

# Password for OBS activation
PassWd: REMObsPwd

# Minimum airmass (this item is optional)
MinAirmass: 0.0

# Maximum airmass (this item is optional)
MaxAirmass: 2.5

# Minimum Julian Date (this item is optional, 0 means no constraints)
MinJD: {start_jd}

# Maximum Julian Date (this item is optional, 0 means no constraints)
MaxJD: {end_jd}

# Strict starting Julian Date (this item is optional, 0 means no constraints)
StrictJD: 0.

# Maximum Moon fraction (this item is optional)
MaxMoonFraction: 1.0

# Periodical target? (this item is optional, 0 means no periodicity)
PeriodicalTarget: 1

# Period (this item is optional, days)
Period: {cadence}

# Priority (this item is optional, 0 is the maximum priority, then 1, 2, etc.)
Priority: 2



# Jitter data (optional)
# LW: NO JITTER
#[JITTER]

# Number of jittered OBs to create 
#JitteredOBs: 0 

# Min jittering radius (arcmin)
#MinJitteringRadius: 0.1

# Max jittering radius (arcmin)
#MaxJitteringRadius: 2.0

[ENDREMOB]
        """

        email = settings.FACILITIES.get('REM', {}).get('email', ['wyrzykow@gmail.com'])
        # Get start and end dates from observation_payload
        start_date_str = observation_payload['params']['start']
        end_date_str = observation_payload['params']['end']

        # Convert to Julian Dates
        start_jd = self.date_to_julian_date(start_date_str)
        end_jd = self.date_to_julian_date(end_date_str)

        selected_filter = observation_payload['params']['filter']
        # Parse the selected filter to get the infrared part
        filter_parts = selected_filter.split('+')
        if len(filter_parts) > 1:
            filter_ir = f"{filter_parts[1]}_IRCam"
        else:
            # Handle case if there is no "+" in the filter (optional)
            filter_ir = "JHK_IRCam"  # default value

        # Format the template
        filled_template = template.format(
            target_name=target_name,
            ra=ra,
            dec=dec,
            proposal_id = observation_payload['params']['proposal_id'],
            email=email,
            cadence = observation_payload['params']['cadence'],
            exptime = observation_payload['params']['exposure_time'],
            exptime_ir = observation_payload['params']['exposure_time_ir'],
            expcount = observation_payload['params']['exposure_count'],
            expcount_ir = observation_payload['params']['exposure_count_ir'],
            start_jd=start_jd,
            end_jd=end_jd,
            ir_filter=filter_ir

        )

        # Now, the filled_template contains the complete formatted text
        # print(filled_template)

        recipient_email = ["remobs@www.rem.inaf.it","wyrzykow@gmail.com"]
        # Send the email
        self.send_template_email(filled_template, recipient_email)
        obs_id = random.randint(10000, 99999)
        return [obs_id]



    def date_to_julian_date(self,date_str):
        """
        Convert a date string in 'YYYY-MM-DD' format to Julian Date.
        """
        # Parse the date string into a datetime object
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Calculate Julian Date
        julian_date = dt.toordinal() + 1721424.5 + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
        return julian_date
 
    #recipients can be a single string or a list of strings
    def send_template_email(self, filled_template, recipients):
        # Ensure recipients is a list even if a single email is passed
        if isinstance(recipients, str):
            recipients = [recipients]  # Convert single email to list

        subject = "REM_OBS"  # Don't change!
        from_email = settings.EMAIL_HOST_USER  # Ensure this is configured correctly

        try:
            send_mail(
                subject=subject,
                message=filled_template,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False  # Set to True in production to suppress errors
            )
            print(f"Failed to send email: {e}")  # Replace with proper logging
        
        except Exception as e:
            # Optionally, log the error or take other actions
            print(f"Failed to send email: {e}")  # Replace with proper logging
            return False  # Indicate failure