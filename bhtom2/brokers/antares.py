import logging
import math
from datetime import datetime
from typing import Optional, List, Tuple

import pandas as pd
import requests

import antares_client
from antares_client.search import get_by_ztf_object_id, get_by_id
from antares_client._api.models import Locus

from astropy.time import Time, TimezoneInfo
from crispy_forms.layout import Div, Fieldset, Layout, HTML
from django import forms
import marshmallow
from django.db import transaction

from bhtom_base.bhtom_alerts.alerts import GenericQueryForm, GenericAlert
from bhtom_base.bhtom_dataproducts.models import ReducedDatum, DatumValue
from bhtom_base.bhtom_targets.models import Target, TargetName

from bhtom2.brokers.bhtom_broker import BHTOMBroker, LightcurveUpdateReport, return_for_no_new_points
from bhtom2.external_service.data_source_information import DataSource
from bhtom2.external_service.filter_name import filter_name

logger = logging.getLogger(__name__)

ANTARES_BASE_URL = 'https://antares.noirlab.edu'
ANTARES_API_URL = 'https://api.antares.noirlab.edu'
ANTARES_TAG_URL = ANTARES_API_URL + '/v1/tags'


def get_available_tags(url: str = ANTARES_TAG_URL):
    response = requests.get(url).json()
    tags = response.get('data', {})
    if response.get('links', {}).get('next'):
        return tags + get_available_tags(response['links']['next'])
    return tags


def get_tag_choices():
    tags = get_available_tags()
    return [(s['id'], s['id']) for s in tags]


# class ConeSearchWidget(forms.widgets.MultiWidget):

#     def __init__(self, attrs=None):
#         if not attrs:
#             attrs = {}
#         _default_attrs = {'class': 'form-control col-md-4', 'style': 'display: inline-block'}
#         attrs.update(_default_attrs)
#         print(attrs)
#         ra_attrs.update({'placeholder': 'Right Ascension'})
#         print(ra_attrs)

#         _widgets = (
#             forms.widgets.NumberInput(attrs=ra_attrs),
#             forms.widgets.NumberInput(attrs=attrs.update({'placeholder': 'Declination'})),
#             forms.widgets.NumberInput(attrs=attrs.update({'placeholder': 'Radius (degrees)'}))
#         )

#         super().__init__(_widgets, attrs)

#     def decompress(self, value):
#         return [value.ra, value.dec, value.radius] if value else [None, None, None]


# class ConeSearchField(forms.MultiValueField):
#     widget = ConeSearchWidget

#     def __init__(self, *args, **kwargs):
#         fields = (forms.FloatField(), forms.FloatField(), forms.FloatField())
#         super().__init__(fields=fields, *args, **kwargs)

#     def compress(self, data_list):
#         return data_list


class ANTARESBrokerForm(GenericQueryForm):
    # define form content
    ztfid = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'ZTF object id, e.g. ZTF19aapreis'})
        )
    tag = forms.MultipleChoiceField(required=False, choices=get_tag_choices)
    nobs__gt = forms.IntegerField(
        required=False,
        label='Detections Lower',
        widget=forms.TextInput(attrs={'placeholder': 'Min number of measurements'})
    )
    nobs__lt = forms.IntegerField(
        required=False,
        label='Detections Upper',
        widget=forms.TextInput(attrs={'placeholder': 'Max number of measurements'})
    )
    ra = forms.FloatField(
        required=False,
        label='RA',
        widget=forms.TextInput(attrs={'placeholder': 'RA (Degrees)'}),
        min_value=0.0
    )
    dec = forms.FloatField(
        required=False,
        label='Dec',
        widget=forms.TextInput(attrs={'placeholder': 'Dec (Degrees)'}),
        min_value=0.0
    )
    sr = forms.FloatField(
        required=False,
        label='Search Radius',
        widget=forms.TextInput(attrs={'placeholder': 'radius (Degrees)'}),
        min_value=0.0
    )
    mjd__gt = forms.FloatField(
        required=False,
        label='Min date of alert detection ',
        widget=forms.TextInput(attrs={'placeholder': 'Date (MJD)'}),
        min_value=0.0
    )
    mjd__lt = forms.FloatField(
        required=False,
        label='Max date of alert detection',
        widget=forms.TextInput(attrs={'placeholder': 'Date (MJD)'}),
        min_value=0.0
    )
    mag__min = forms.FloatField(
        required=False,
        label='Min magnitude of the latest alert',
        widget=forms.TextInput(attrs={'placeholder': 'Min Magnitude'}),
        min_value=0.0
    )
    mag__max = forms.FloatField(
        required=False,
        label='Max magnitude of the latest alert',
        widget=forms.TextInput(attrs={'placeholder': 'Max Magnitude'}),
        min_value=0.0
    )
    esquery = forms.JSONField(
        required=False,
        label='Elastic Search query in JSON format',
        widget=forms.TextInput(attrs={'placeholder': '{"query":{}}'}),
    )

    # cone_search = ConeSearchField()
    # api_search_tags = forms.MultipleChoiceField(choices=get_tag_choices)

    # TODO: add section for searching API in addition to consuming stream

    # TODO: add layout
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.common_layout,
            HTML('''
                <p>
                Users can query objects in the ANTARES database using one of the following
                three methods: 1. an object ID by ZTF, 2. a simple query form with constraints
                of object brightness, position, and associated tag, 3. an advanced query with
                Elastic Search syntax.
            </p>
            '''),
            HTML('<hr/>'),
            HTML('<p style="color:blue;font-size:30px">Query by object name</p>'),
            Fieldset(
                 'ZTF object ID',
                 'ztfid'
            ),
            HTML('<hr/>'),
            HTML('<p style="color:blue;font-size:30px">Simple query form</p>'),
            Fieldset(
                'Alert timing',
                Div(
                    Div(
                        'mjd__gt',
                        css_class='col',
                    ),
                    Div(
                        'mjd__lt',
                        css_class='col',
                    ),
                    css_class='form-row'
                    )
                ),
            Fieldset(
                'Number of measurements',
                Div(
                    Div(
                        'nobs__gt',
                        css_class='col',
                    ),
                    Div(
                        'nobs__lt',
                        css_class='col',
                    ),
                    css_class='form-row',
                )
            ),
            Fieldset(
                'Brightness of the latest alert',
                Div(
                    Div(
                        'mag__min',
                        css_class='col',
                    ),
                    Div(
                        'mag__max',
                        css_class='col',
                    ),
                    css_class='form-row'
                )
            ),
            Fieldset(
                'Cone Search',
                Div(
                    Div(
                        'ra',
                        css_class='col'
                    ),
                    Div(
                        'dec',
                        css_class='col'
                    ),
                    Div(
                        'sr',
                        css_class='col'
                    ),
                    css_class='form-row'
                )
            ),
            Fieldset(
                'View Tags',
                'tag'
            ),
            HTML('<hr/>'),
            HTML('<p style="color:blue;font-size:30px">Advanced query</p>'),
            Fieldset(
                 '',
                 'esquery'
            ),
            HTML('''
                <p>
                Please see <a href="https://noao.gitlab.io/antares/client/tutorial/searching.html">ANTARES
                 Documentation</a> for a detailed description of advanced searches.
                </p>
            ''')
            # HTML('<hr/>'),
            # Fieldset(
            #     'API Search',
            #     'api_search_tags'
            # )
        )

    def clean(self):
        cleaned_data = super().clean()

        # Ensure all cone search fields are present
        if any(cleaned_data[k] for k in ['ra', 'dec', 'sr']) and not all(cleaned_data[k] for k in ['ra', 'dec', 'sr']):
            raise forms.ValidationError('All of RA, Dec, and Search Radius must be included to perform a cone search.')
        # default value for cone search
        if not all(cleaned_data[k] for k in ['ra', 'dec', 'sr']):
            cleaned_data['ra'] = 180.
            cleaned_data['dec'] = 0.
            cleaned_data['sr'] = 180.
        # Ensure alert timing constraints have sensible values
        if all(cleaned_data[k] for k in ['mjd__lt', 'mjd__gt']) and cleaned_data['mjd__lt'] <= cleaned_data['mjd__gt']:
            raise forms.ValidationError('Min date of alert detection must be earlier than max date of alert detection.')

        # Ensure number of measurement constraints have sensible values
        if (all(cleaned_data[k] for k in ['nobs__lt', 'nobs__gt'])
                and cleaned_data['nobs__lt'] <= cleaned_data['nobs__gt']):
            raise forms.ValidationError('Min number of measurements must be smaller than max number of measurements.')

        # Ensure magnitude constraints have sensible values
        if (all(cleaned_data[k] for k in ['mag__min', 'mag__max'])
                and cleaned_data['mag__max'] <= cleaned_data['mag__min']):
            raise forms.ValidationError('Min magnitude must be smaller than max magnitude.')

        # Ensure using either a stream or the advanced search form
        # if not (cleaned_data['tag'] or cleaned_data['esquery']):
        #    raise forms.ValidationError('Please either select tag(s) or use the advanced search query.')

        # Ensure using either a stream or the advanced search form
        if not (cleaned_data['ztfid'] or cleaned_data['tag'] or cleaned_data['esquery']):
            raise forms.ValidationError(
                'Please either enter the ZTF ID, or select tag(s), or use the advanced search query.'
            )

        return cleaned_data


class ANTARESBroker(BHTOMBroker):
    name = 'ANTARES'
    form = ANTARESBrokerForm

    def __init__(self):
        super().__init__(DataSource.ANTARES)
        self.__FACILITY_NAME: str = "ZTF"
        self.__OBSERVER_NAME: str = "ZTF"


    @classmethod
    def alert_to_dict(cls, locus):
        """
        Note: The ANTARES API returns a Locus object, which in the TOM Toolkit
        would otherwise be called an alert.

        This method serializes the Locus into a dict so that it can be cached by the view.
        """
        return {
            'locus_id': locus.locus_id,
            'ra': locus.ra,
            'dec': locus.dec,
            'properties': locus.properties,
            'tags': locus.tags,
            # 'lightcurve': locus.lightcurve.to_json(),
            'catalogs': locus.catalogs,
            'alerts': [{
                'alert_id': alert.alert_id,
                'mjd': alert.mjd,
                'properties': alert.properties
            } for alert in locus.alerts]
        }

    def fetch_alerts(self, parameters: dict) -> iter:
        tags = parameters.get('tag')
        nobs_gt = parameters.get('nobs__gt')
        nobs_lt = parameters.get('nobs__lt')
        sra = parameters.get('ra')
        sdec = parameters.get('dec')
        ssr = parameters.get('sr')
        mjd_gt = parameters.get('mjd__gt')
        mjd_lt = parameters.get('mjd__lt')
        mag_min = parameters.get('mag__min')
        mag_max = parameters.get('mag__max')
        elsquery = parameters.get('esquery')
        ztfid = parameters.get('ztfid')
        if ztfid:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "properties.ztf_object_id": ztfid
                                }
                            }
                        ]
                    }
                }
            }
        elif elsquery:
            query = elsquery
        else:
            filters = []

        if nobs_gt or nobs_lt:
            nobs_range = {'range': {'properties.num_mag_values': {}}}
            if nobs_gt:
                nobs_range['range']['properties.num_mag_values']['gte'] = nobs_gt
            if nobs_lt:
                nobs_range['range']['properties.num_mag_values']['lte'] = nobs_lt
            filters.append(nobs_range)

        if mjd_lt:
            mjd_lt_range = {'range': {'properties.newest_alert_observation_time': {'lte': mjd_lt}}}
            filters.append(mjd_lt_range)

        if mjd_gt:
            mjd_gt_range = {'range': {'properties.oldest_alert_observation_time': {'gte': mjd_gt}}}
            filters.append(mjd_gt_range)

        if mag_min or mag_max:
            mag_range = {'range': {'properties.newest_alert_magnitude': {}}}
            if mag_min:
                mag_range['range']['properties.newest_alert_magnitude']['gte'] = mag_min
            if mag_max:
                mag_range['range']['properties.newest_alert_magnitude']['lte'] = mag_max
            filters.append(mag_range)

        if sra and ssr:  # TODO: add cross-field validation
            ra_range = {'range': {'ra': {'gte': sra-ssr, 'lte': sra+ssr}}}
            filters.append(ra_range)

        if sdec and ssr:  # TODO: add cross-field validation
            dec_range = {'range': {'dec': {'gte': sdec-ssr, 'lte': sdec+ssr}}}
            filters.append(dec_range)

        if tags:
            filters.append({'terms': {'tags': tags}})

        query = {
                "query": {
                    "bool": {
                        "filter": filters
                    }
                }
            }

        loci = antares_client.search.search(query)
#        if ztfid:
#            loci = get_by_ztf_object_id(ztfid)
        alerts = []
        while len(alerts) < 20:
            try:
                locus = next(loci)
            except (marshmallow.exceptions.ValidationError, StopIteration):
                break
            alerts.append(self.alert_to_dict(locus))
        return iter(alerts)

    def fetch_alert(self, id):
        alert = get_by_ztf_object_id(id)
        return alert

    def process_reduced_data(self, target, alert=None) -> Optional[LightcurveUpdateReport]:
        antares_name: Optional[str] = self.get_target_name(target)

        if not antares_name:
            self.logger.debug(f'No ANTARES Name for {target.name}')
            return return_for_no_new_points()

        result: Optional[Locus] = get_by_id(antares_name)

        if not result:
            return_for_no_new_points()

        lightcurve: Optional[pd.DataFrame] = result._lightcurve

        if lightcurve is None:
            self.logger.debug(f'Target {target.name} with ANTARES name {antares_name} has no lightcurve')
            return_for_no_new_points()

        new_points: int = 0
        data: List[Tuple[datetime, DatumValue]] = []

        for _, row in lightcurve.iterrows():
            try:
                mjd: Time = Time(float(row['ant_mjd']), format='mjd', scale='utc')
                filter: str = filter_name(DataSource.ZTF.name,row['ant_passband'].lower()) #from ANTARES the filters will be called ZTF(r) and ZTF(g), but from ZTF DR they are ZTF(zr) and ZTF(zg) - making it consistent here
                if (filter=="ZTF(r)"): filter="ZTF(zr)"
                if (filter=="ZTF(g)"): filter="ZTF(zg)"
                
                # Detection
                mag: float = float(row['ant_mag_corrected'])
                magerr: float = float(row['ant_magerr_corrected'])

                # Detection
                if not math.isnan(mag):
                    data.append((mjd.to_datetime(timezone=TimezoneInfo()),
                                 DatumValue(value=mag,
                                            filter=filter,
                                            mjd=mjd.mjd,
                                            error=magerr)))

#                    self.update_last_jd_and_mag(mjd.jd, mag)

                # TODO: add mag limits
            except Exception as e:
                self.logger.error(f'Error while processing reduced datapoint for target {target.name} with '
                                  f'ANTARES name {antares_name}: {e}')
                continue

        try:
            data = list(set(data))
            reduced_datums = [ReducedDatum(target=target, data_type='photometry',
                                           timestamp=datum[0], mjd=datum[1].mjd, value=datum[1].value,
                                           source_name=self.name,
                                           source_location=f'https://antares.noirlab.edu/loci/{antares_name}',
                                           error=datum[1].error,
                                           filter=datum[1].filter, observer=self.__OBSERVER_NAME,
                                           facility=self.__FACILITY_NAME) for datum in data]
            with transaction.atomic():
                new_points = len(ReducedDatum.objects.bulk_create(reduced_datums, ignore_conflicts=True))
        except Exception as e:
            self.logger.error(f'Error while saving reduced datapoints for target {target.name} with '
                              f'ANTARES name {antares_name}: {e}')
            return return_for_no_new_points()

        return LightcurveUpdateReport(new_points=new_points)
                                    #     ,last_jd=self.last_jd,
                                    #   last_mag=self.last_mag)




    def to_target(self, alert: dict) -> Target:
        target = Target.objects.create(
            name=alert['properties']['ztf_object_id'],
            type='SIDEREAL',
            ra=alert['ra'],
            dec=alert['dec'],
        )
        antares_name = TargetName(target=target, name=alert['locus_id'])
        aliases = [antares_name]
        if alert['properties'].get('horizons_targetname'):  # TODO: review if any other target names need to be created
            aliases.append(TargetName(name=alert['properties'].get('horizons_targetname')))
        return target, [], aliases

    def to_generic_alert(self, alert):
        url = f"{ANTARES_BASE_URL}/loci/{alert['locus_id']}"
        timestamp = Time(
            alert['properties'].get('newest_alert_observation_time'), format='mjd', scale='utc'
        ).to_datetime(timezone=TimezoneInfo())
        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=alert['locus_id'],
            name=alert['properties']['ztf_object_id'],
            ra=alert['ra'],
            dec=alert['dec'],
            mag=alert['properties'].get('newest_alert_magnitude', ''),
            score=alert['alerts'][-1]['properties'].get('ztf_rb', '')
        )
