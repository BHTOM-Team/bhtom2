import logging
from datetime import datetime
from urllib.parse import urlencode

import numpy as np
import plotly.graph_objs as go
from django import template
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.shortcuts import reverse
from guardian.shortcuts import get_objects_for_user
from plotly import offline
from astropy.time import Time

from bhtom_base.bhtom_dataproducts.forms import DataProductUploadForm
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.processors.data_serializers import SpectrumSerializer
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target

from numpy import around 

from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats

register = template.Library()

color_map = {
        'GSA(G)':     ['black','hexagon',10], 
        'ZTF(zg)':    ['green','cross',4],
        'ZTF(zi)':    ['#800000','cross',4],
        'ZTF(zr)':    ['red','cross',4],
        'WISE(W1)':   ['#FFCC00', 'x',2],
        'WISE(W2)':   ['blue', 'x', 2],
        'CRTS(CL)':   ['#FF1493', 'diamond', 4],
        'LINEAR(CL)': ['teal', 'diamond', 4],
        'SDSSDR(r)':  ['red ', 'square' , 5],
        'SDSSDR(i)':  [ '#800000', 'square' , 5],
        'SDSSDR(u)':  ['#40E0D0'  , 'square' , 5],
        'SDSSDR(z)':  ['#ff0074' , 'square' , 5],
        'SDSSDR(g)':  ['green', 'square' , 5],
        'DECAPS(r)':  ['red ', 'star-square' , 5],
        'DECAPS(i)':  [ '#800000', 'star-square' , 5],
        'DECAPS(u)':  ['#40E0D0'  , 'star-square' , 5],
        'DECAPS(z)':  ['#ff0074' , 'star-square' , 5],
        'DECAPS(g)':  ['green', 'star-square' , 5],
        'PS1(r)': ['red', 'star-open', 5],
        'PS1(i)': ['#800000', "star-open", 5],
        'PS1(z)': ['#ff0074', "star-open", 5],
        'PS1(g)': ['green', "star-open", 5],
         'SDSS_DR14(r)':  ['red ', 'square' , 5],
         'SDSS_DR14(i)':  [ '#800000', 'square' , 5],
         'SDSS_DR14(u)':  ['#40E0D0'  , 'square' , 5],
         'SDSS_DR14(z)':  ['#ff0074' , 'square' , 5],
         'SDSS_DR14(g)':  ['green', 'square' , 5],
         'RP(GAIA_DR3)':  ['#ff8A8A', 'circle' , 4],
         'BP(GAIA_DR3)':  ['#8A8Aff', 'circle' , 4],
         'G(GAIA_DR3)':   ['black', 'circle', 4],
        'I(GaiaSP)':  ['#6c1414','21', 4],
        'g(GaiaSP)':  ['green','21', 4],
        'R(GaiaSP)':  ['#d82727','21', 4],
        'V(GaiaSP)':  ['darkgreen','21', 4],
        'B(GaiaSP)':  ['#000034','21', 4],
        'z(GaiaSP)':  ['#ff0074','21', 4],
        'u(GaiaSP)':  ['#40E0D0','21', 4],
        'r(GaiaSP)':  ['red','21', 4],
        'U(GaiaSP)':  ['#5ac6bc','21', 4],
        'i(GaiaSP)':  ['#800000','21' , 4],
        'ASASSN(g)':  ['green', 'cross-thin',2], #add opacity
        'ASASSN(V)':  ['darkgreen', 'cross-thin',2], #add opacity
    }


@register.inclusion_tag('bhtom_dataproducts/partials/recent_photometry.html')
def recent_photometry(target, limit=1):
    """
    Displays a table of the most recent photometric points for a target.
    """
    photometry = ReducedDatum.objects.filter(data_type='photometry', target=target).order_by('-timestamp')[:limit]
    return {'data': [{'timestamp': rd.timestamp,
                      'magnitude': rd.value,
                      'filter': rd.filter,
                      'facility': rd.facility} for rd in photometry
                     if rd.value_unit == ReducedDatumUnit.MAGNITUDE]}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_stats.html')
def photometry_stats(target):
    import pandas as pd

    """
    Displays a table of the the photometric data stats for a target.
    """
    stats,columns = get_photometry_stats(target)
    sort_by='Facility'    
    sort_by_asc=True
    df: pd.DataFrame = pd.DataFrame(data=stats,
                                    columns=columns).sort_values(by=sort_by, ascending=sort_by_asc)

    data_list = []
    for index, row in df.iterrows():
        data_dict = {'Facility': row['Facility'],
                    'Filters': row['Filters'],
                    'Data_points': row['Data_points'],
                    'Min_MJD': row['Earliest_time'],
                    'Max_MJD': row['Latest_time']}
        data_list.append(data_dict)

    return {'data': data_list}

@register.inclusion_tag('bhtom_dataproducts/partials/dataproduct_list_for_target.html', takes_context=True)
def dataproduct_list_for_target(context, target):
    """
    Given a ``Target``, returns a list of ``DataProduct`` objects associated with that ``Target``
    """
    if settings.TARGET_PERMISSIONS_ONLY:
        target_products_for_user = target.dataproduct_set.all()
    else:
        target_products_for_user = get_objects_for_user(
            context['request'].user, 'bhtom_dataproducts.view_dataproduct', klass=target.dataproduct_set.all())
    return {
        'products': target_products_for_user,
        'target': target
    }


@register.inclusion_tag('bhtom_dataproducts/partials/saved_dataproduct_list_for_observation.html')
def dataproduct_list_for_observation_saved(data_products, request):
    """
    Given a dictionary of dataproducts from an ``ObservationRecord``, returns the subset that are saved to the TOM. This
    templatetag paginates the subset of ``DataProduct``, and therefore requires the request to have a 'page_saved' key.

    This templatetag is intended to be used with the ``all_data_products()`` method from a facility, as it returns a
    dictionary with keys of ``saved`` and ``unsaved`` that have values of lists of ``DataProduct`` objects.
    """
    page = request.GET.get('page_saved')
    paginator = Paginator(data_products['saved'], 25)
    products_page = paginator.get_page(page)
    return {'products_page': products_page}


@register.inclusion_tag('bhtom_dataproducts/partials/unsaved_dataproduct_list_for_observation.html')
def dataproduct_list_for_observation_unsaved(data_products):
    """
    Given a dictionary of dataproducts from an ``ObservationRecord``, returns a list of the subset that are not saved to
    the TOM.

    This templatetag is intended to be used with the ``all_data_products()`` method from a facility, as it returns a
    dictionary with keys of ``saved`` and ``unsaved`` that have values of lists of ``DataProduct`` objects.
    """
    return {'products': data_products['unsaved']}


@register.inclusion_tag('bhtom_dataproducts/partials/dataproduct_list.html', takes_context=True)
def dataproduct_list_all(context):
    """
    Returns the full list of data products in the TOM, with the most recent first.
    """
    if settings.TARGET_PERMISSIONS_ONLY:
        products = DataProduct.objects.all().order_by('-created')
    else:
        products = get_objects_for_user(context['request'].user, 'bhtom_dataproducts.view_dataproduct')
    return {'products': products}


@register.inclusion_tag('bhtom_dataproducts/partials/upload_dataproduct.html', takes_context=True)
def upload_dataproduct(context, obj):
    user = context['user']
    initial = {}
    if isinstance(obj, Target):
        initial['target'] = obj
        initial['referrer'] = reverse('bhtom_base.bhtom_targets:detail', args=(obj.id,))
    elif isinstance(obj, ObservationRecord):
        initial['observation_record'] = obj
        initial['referrer'] = reverse('bhtom_base.bhtom_observations:detail', args=(obj.id,))
    form = DataProductUploadForm(initial=initial)
    if not settings.TARGET_PERMISSIONS_ONLY:
        if user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = user.groups.all()
    return {'data_product_form': form}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target.html', takes_context=True)
def photometry_for_target(context, target, width=1000, height=600, background=None, label_color=None, grid=True):
    """
    Renders a photometric plot for a target.

    This templatetag requires all ``ReducedDatum`` objects with a data_type of ``photometry`` to be structured with the
    following keys in the JSON representation: magnitude, error, filter

    :param width: Width of generated plot
    :type width: int

    :param height: Height of generated plot
    :type width: int

    :param background: Color of the background of generated plot. Can be rgba or hex string.
    :type background: str

    :param label_color: Color of labels/tick labels. Can be rgba or hex string.
    :type label_color: str

    :param grid: Whether to show grid lines.
    :type grid: bool
    """


    photometry_data = {}
    radio_data = {}

    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                             value_unit=ReducedDatumUnit.MAGNITUDE)

        radio_datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                             value_unit=ReducedDatumUnit.MILLIJANSKY)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'bhtom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                          target=target,
                                          data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                          value_unit=ReducedDatumUnit.MAGNITUDE))

        radio_datums = get_objects_for_user(context['request'].user,
                                      'bhtom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                        target=target,
                                        data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                        value_unit=ReducedDatumUnit.MILLIJANSKY))

    # set the datum max and min the silly way, we already iterate through all the datums anyway
    magnitude_min = -100
    magnitude_max = 100

    radio_min = 1e7
    radio_max = -1e7

    for datum in datums:
        photometry_data.setdefault(datum.filter, {})

        if datum.value:
            photometry_data[datum.filter].setdefault('time', []).append(datum.timestamp)
            photometry_data[datum.filter].setdefault('magnitude', []).append(around(datum.value,3))
            photometry_data[datum.filter].setdefault('error', []).append(around(datum.error,3))
            photometry_data[datum.filter].setdefault('facility', []).append(datum.facility)

            magnitude_min = (datum.value+datum.error) if (datum.value+datum.error) > magnitude_min else magnitude_min
            magnitude_max = (datum.value-datum.error) if (datum.value-datum.error) < magnitude_max else magnitude_max

    for radio_datum in radio_datums:
        radio_data.setdefault(radio_datum.filter, {})

        if radio_datum.value:
            radio_data[radio_datum.filter].setdefault('time', []).append(radio_datum.timestamp)
            radio_data[radio_datum.filter].setdefault('magnitude', []).append(around(radio_datum.value,3))
            radio_data[radio_datum.filter].setdefault('error', []).append(around(radio_datum.error,3))

            radio_min = (radio_datum.value-radio_datum.error) if (radio_datum.value-radio_datum.error) < radio_min else radio_min
            radio_max = (radio_datum.value+radio_datum.error) if (radio_datum.value+radio_datum.error) > radio_max else radio_max

        # TODO: handle limits
        # photometry_data[datum.filter].setdefault('limit', []).append(datum.value.get('limit'))

    # Calculate min/max values for ranges and ticks
    magnitude_range = magnitude_min-magnitude_max
    radio_range = radio_max-radio_min

    try:
#        magnitude_dtick_digit = (round(np.log10(magnitude_range))-1)
        magnitude_range = 10
    except:
        magnitude_dtick_digit = 1
        radio_range = 10
    
    try:
        if (radio_range>0):
            radio_dtick_digit = (round(np.log10(radio_range)) - 1)
        else:
                    radio_dtick_digit = 1
    except:
        radio_dtick_digit = 1

    plot_data = []

##MAG:
    mjds_to_plot = {}
    mjds_lim_to_plot = {}
    for filter_name, filter_values in photometry_data.items():
        if filter_values['magnitude']:
            mjds_to_plot[filter_name]=Time(filter_values['time'], format="datetime").mjd
        if filter_values.get('limit'):
            mjds_lim_to_plot[filter_name]=Time(filter_values['time'], format="datetime").mjd

    for filter_name, filter_values in photometry_data.items():
        if filter_values['magnitude']:
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['magnitude'],
                mode='markers',
                opacity=0.75,
                marker=dict(
                    color=color_map.get(filter_name, ['gray', 'circle', 4])[0], #default ['gray', 'circle', 6]
                    symbol=color_map.get(filter_name, ['gray', 'circle', 4])[1],
                    size=color_map.get(filter_name, ['gray', 'circle', 4])[2]
                    ),
                name=filter_name,
                error_y=dict(
                    type='data',
                    array=filter_values['error'],
                    visible=True
                ),
                text=mjds_to_plot[filter_name], 
                customdata=filter_values['facility'],
#                customdata = filter_values['error'],
            # hovertemplate='<br>'.join([
            # "%{x}",
            # "%{y:.2f}",
            # "%{customdata}",
            # ]),
            hovertemplate='%{x|%Y/%m/%d %H:%M:%S.%L}\
                <br>MJD= %{text:.6f}\
            <br>mag= %{y:.3f}&#177;%{error_y.array:3f}\
            <br>%{customdata}'
            )     
            plot_data.append(series)
        elif filter_values.get('limit'):  #limit in MAG
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['limit'],
                mode='markers',
                opacity=0.5,
                marker=dict(color=color_map.get(filter_name, ['gray', 'circle', 4])[0], symbol=6),  # upside down triangle
                name=filter_name+" limit",
                text=mjds_lim_to_plot[filter_name],
                hovertemplate='%{x|%Y/%m/%d %H:%M:%S.%L}\
                <br>MJD= %{text:.6f}\
            <br>limit mag= (%{y:.3f})'
            )
            plot_data.append(series)


##RADIO:
    mjds_radio_to_plot = {}
    mjds_radio_lim_to_plot = {}
    for filter_name, filter_values in radio_data.items():
        if filter_values['magnitude']:
            mjds_radio_to_plot[filter_name]=Time(filter_values['time'], format="datetime").mjd
        if filter_values.get('limit'):
            mjds_radio_lim_to_plot[filter_name]=Time(filter_values['time'], format="datetime").mjd

    for filter_name, filter_values in radio_data.items():
        if filter_values['magnitude']:
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['magnitude'],
                mode='markers',
                opacity=0.75,
                marker=dict(color=color_map.get(filter_name, ['gray', 'circle', 4])[0], symbol='diamond', line_color='black', line_width=2),
                name=filter_name,
                error_y=dict(
                    type='data',
                    array=filter_values['error'],
                    visible=True
                ),
            text=mjds_radio_to_plot[filter_name],
            hovertemplate='%{x|%Y/%m/%d %H:%M:%S.%L}\
                <br>MJD= %{text:.6f}\
            <br>flux= %{y:.3f}&#177;%{error_y.array:3f}',

                yaxis="y2"
            )
            plot_data.append(series)
        elif filter_values.get('limit'):
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['limit'],
                mode='markers',
                opacity=0.5,
                marker=dict(color=color_map.get(filter_name, ['gray', 'circle', 4])[0], symbol=6),  # upside down triangle
                name=filter_name+" limit",
                text=mjds_radio_lim_to_plot[filter_name],
                hovertemplate='%{x|%Y/%m/%d %H:%M:%S.%L}\
                <br>MJD= %{text:.6f}\
            <br>limit flux= (%{y:.3f})'
            )
            plot_data.append(series)

    layout = go.Layout(
        height=height,
        width=width,
        paper_bgcolor=background,
        plot_bgcolor=background

    )
    layout.legend.font.color = label_color
    fig = go.Figure(data=plot_data, layout=layout)

    fig.update_layout(
        margin=dict(t= 40, r= 20, b= 40, l= 80),
        xaxis=dict(
            autorange=True,
            title="date",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            ),
        ),
        yaxis=dict(
            autorange=False,
            range=[np.ceil(magnitude_min), np.floor(magnitude_max)],
            title="magnitude",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            ),
        ),
        yaxis2=dict(
            autorange=False,
            range=[np.floor(radio_min), np.ceil(radio_max)],
            title="mJy",
            titlefont=dict(
                color="black"
            ),
            tickfont=dict(
                color="black"
            ),
            overlaying="y",
            side="right",
            showgrid=False,# Turn off the grid for the secondary y-axis
        ),
        legend=dict(
            yanchor="top",
            y=-0.15,
            xanchor="left",
            x=0.0,
            orientation="h"
        )
    )
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }

### static and simpler version of the plot for massive list table
@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target_icon.html', takes_context=True)
def photometry_for_target_icon(context, target, width=800, height=400, background=None, label_color=None, grid=True):
    """
    Renders a photometric plot for a target.

    This templatetag requires all ``ReducedDatum`` objects with a data_type of ``photometry`` to be structured with the
    following keys in the JSON representation: magnitude, error, filter

    :param width: Width of generated plot
    :type width: int

    :param height: Height of generated plot
    :type width: int

    :param background: Color of the background of generated plot. Can be rgba or hex string.
    :type background: str

    :param label_color: Color of labels/tick labels. Can be rgba or hex string.
    :type label_color: str

    :param grid: Whether to show grid lines.
    :type grid: bool
    """



    photometry_data = {}
    radio_data = {}

    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                             value_unit=ReducedDatumUnit.MAGNITUDE)

        radio_datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                             value_unit=ReducedDatumUnit.MILLIJANSKY)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'bhtom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                          target=target,
                                          data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                          value_unit=ReducedDatumUnit.MAGNITUDE))

        radio_datums = get_objects_for_user(context['request'].user,
                                      'bhtom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                        target=target,
                                        data_type=settings.DATA_PRODUCT_TYPES['photometry'][0],
                                        value_unit=ReducedDatumUnit.MILLIJANSKY))

    # set the datum max and min the silly way, we already iterate through all the datums anyway
    magnitude_min = -100
    magnitude_max = 100

    radio_min = 1e7
    radio_max = -1e7

    for datum in datums:
        photometry_data.setdefault(datum.filter, {})

        if datum.value:
            photometry_data[datum.filter].setdefault('time', []).append(datum.timestamp)
            photometry_data[datum.filter].setdefault('magnitude', []).append(datum.value)
            photometry_data[datum.filter].setdefault('error', []).append(datum.error)

            magnitude_min = (datum.value+datum.error) if (datum.value+datum.error) > magnitude_min else magnitude_min
            magnitude_max = (datum.value-datum.error) if (datum.value-datum.error) < magnitude_max else magnitude_max

    for radio_datum in radio_datums:
        radio_data.setdefault(radio_datum.filter, {})

        if radio_datum.value:
            radio_data[radio_datum.filter].setdefault('time', []).append(radio_datum.timestamp)
            radio_data[radio_datum.filter].setdefault('magnitude', []).append(radio_datum.value)
            radio_data[radio_datum.filter].setdefault('error', []).append(radio_datum.error)

            radio_min = (radio_datum.value-radio_datum.error) if (radio_datum.value-radio_datum.error) < radio_min else radio_min
            radio_max = (radio_datum.value+radio_datum.error) if (radio_datum.value+radio_datum.error) > radio_max else radio_max

        # TODO: handle limits
        # photometry_data[datum.filter].setdefault('limit', []).append(datum.value.get('limit'))

    # Calculate min/max values for ranges and ticks
    magnitude_range = magnitude_min-magnitude_max
    radio_range = radio_max-radio_min

    try:
#        magnitude_dtick_digit = (round(np.log10(magnitude_range))-1)
        magnitude_range = 10
    except:
        magnitude_dtick_digit = 1
        radio_range = 10
    
    try:
        if (radio_range>0):
            radio_dtick_digit = (round(np.log10(radio_range)) - 1)
        else:
            radio_dtick_digit = 1
    except:
        radio_dtick_digit = 1

    plot_data = []
    for filter_name, filter_values in photometry_data.items():
        if filter_values['magnitude']:
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['magnitude'],
                mode='markers',
                marker=dict(
                    color=color_map.get(filter_name, ['gray', 'circle', 4])[0], #default ['gray', 'circle', 6]
                    symbol=color_map.get(filter_name, ['gray', 'circle', 4])[1],
                    size=color_map.get(filter_name, ['gray', 'circle', 4])[2]
                    ),
                name=filter_name,
                error_y=dict(
                    type='data',
                    array=filter_values['error'],
                    visible=True,
                    thickness=1.5,
                    width=0
                ),
            )
            plot_data.append(series)

    for filter_name, filter_values in radio_data.items():
        if filter_values['magnitude']:
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['magnitude'],
                mode='markers',
                marker=dict(color=color_map.get(filter_name, ['gray', 'circle', 4])[0], symbol='diamond', line_color='black', line_width=2),
                name=filter_name,
                error_y=dict(
                    type='data',
                    array=filter_values['error'],
                    visible=True                    
                ),
                yaxis="y2"
            )
            plot_data.append(series)
        elif filter_values.get('limit'):
            series = go.Scatter(
                x=filter_values['time'],
                y=filter_values['limit'],
                mode='markers',
                opacity=0.5,
                marker=dict(color=color_map.get(filter_name, ['gray', 'circle', 4])[0], symbol=6),  # upside down triangle
                name=filter_name + ' non-detection',
            )
            plot_data.append(series)

    layout = go.Layout(
        height=height,
        width=width,
        # paper_bgcolor=background,
        # plot_bgcolor=background
        paper_bgcolor='white',  # Change the background color to white
        plot_bgcolor='white'  # Change the plot area background color to white
    )

    layout.legend.font.color = label_color
    #no legend shown in icon view
    layout.update(showlegend=True)
    
    fig = go.Figure(data=plot_data, layout=layout)
    fig.update_layout(
    title=target.name,
    margin=dict(t=40, r=20, b=40, l=80),
    xaxis=dict(
        autorange=True,
        title="date",
        titlefont=dict(
            color="#1f77b4"
        ),
        tickfont=dict(
            color="#1f77b4"
        ),
        showgrid=False,  # Do not show grid lines on the x-axis
        showticklabels=True,
        ticks="inside",
        showline=True, linewidth=2, linecolor='#1f77b4'
    ),
    yaxis=dict(
        autorange=False,
        range=[np.ceil(magnitude_min), np.floor(magnitude_max)],
        title="magnitude",
        titlefont=dict(
            color="#1f77b4"
        ),
        tickfont=dict(
            color="#1f77b4"  # Change the tick color to black
        ),
        showgrid=False,  # Do not show grid lines on the y-axis
        showticklabels=True,  # Show tick labels on the y-axis
        ticks="inside",   # Place the tick marks inside the plot area
        showline=True, linewidth=2, linecolor='#1f77b4'
    ),
    yaxis2=dict(
        autorange=False,
        range=[np.floor(radio_min), np.ceil(radio_max)],
        title="mJy",
        titlefont=dict(
            color="black"
        ),
        tickfont=dict(
            color="black"
        ),
        overlaying="y",
        side="right",
        showgrid=False,  # Do not show grid lines on the yaxis2
    ),
    legend_tracegroupgap=1,
    legend=dict(
#        yanchor="top",
        y=-0.20,
#        xanchor="right",
        x=0.00,
#        font=dict(size=8)
    orientation="h",
    yanchor="top",
    xanchor="left",
    )
    )
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=True, config=dict({'staticPlot':True}))
    }


@register.inclusion_tag('bhtom_dataproducts/partials/spectroscopy_for_target.html', takes_context=True)
def spectroscopy_for_target(context, target, dataproduct=None):
    """
    Renders a spectroscopic plot for a ``Target``. If a ``DataProduct`` is specified, it will only render a plot with
    that spectrum.
    """
    spectral_dataproducts = DataProduct.objects.filter(target=target,
                                                       data_product_type=settings.DATA_PRODUCT_TYPES['spectroscopy'][0])
    if dataproduct:
        spectral_dataproducts = DataProduct.objects.get(data_product=dataproduct)

    plot_data = []
    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(data_product__in=spectral_dataproducts)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'bhtom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(data_product__in=spectral_dataproducts))
    for datum in datums:
        deserialized = SpectrumSerializer().deserialize(datum.value)
        plot_data.append(go.Scatter(
            x=deserialized.wavelength.value,
            y=deserialized.flux.value,
            name=datetime.strftime(datum.timestamp, '%Y%m%d-%H:%M:%s')
        ))

    layout = go.Layout(
        height=600,
        width=700,
        xaxis=dict(
            tickformat="d"
        ),
        yaxis=dict(
            tickformat=".1eg"
        )
    )
    return {
        'target': target,
        'plot': offline.plot(go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False)
    }


@register.inclusion_tag('bhtom_dataproducts/partials/update_broker_data_button.html', takes_context=True)
def update_broker_data_button(context):
    return {'query_params': urlencode(context['request'].GET.dict())}
