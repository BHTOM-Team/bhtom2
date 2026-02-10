from urllib.parse import urlencode

import plotly

import plotly.graph_objs as go
from django import template
from django.conf import settings

from django.core.paginator import Paginator
from django.shortcuts import reverse
from plotly import offline

import datetime, time
from astropy.time import Time

from bhtom2.bhtom_dataproducts.forms import DataProductUploadForm
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_dataproducts.models import ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target, TargetGaiaDr3, TargetGaiaDr2
from django.contrib.auth.models import User
from numpy import around

import numpy as np

from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats

register = template.Library()
logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_dataproducts: extras')

color_map = {
    'GSA(G)': ['black', 'hexagon', 8],
    'ZTF(zg)': ['green', 'x', 6],
    'ZTF(zi)': ['#800000', 'x', 6],
    'ZTF(zr)': ['red', 'x', 6],
    'WISE(W1)': ['#FFCC00', 'x', 3],
    'WISE(W2)': ['blue', 'x', 3],
    'CRTS(CL)': ['#FF1493', 'diamond', 4],
    'LINEAR(CL)': ['teal', 'diamond', 4],
    'SDSS(r)': ['red', 'square', 5],
    'SDSS(i)': ['#800000', 'square', 5],
    'SDSS(u)': ['#40E0D0', 'square', 5],
    'SDSS(z)': ['#ff0074', 'square', 5],
    'SDSS(g)': ['green', 'square', 5],
    'DECAPS(r)': ['red', 'star-square', 5],
    'DECAPS(i)': ['#800000', 'star-square', 5],
    'DECAPS(u)': ['#40E0D0', 'star-square', 5],
    'DECAPS(z)': ['#ff0074', 'star-square', 5],
    'DECAPS(g)': ['green', 'star-square', 5],
    'PS1(r)': ['red', 'star-open', 5],
    'PS1(i)': ['#800000', "star-open", 5],
    'PS1(z)': ['#ff0074', "star-open", 5],
    'PS1(g)': ['green', "star-open", 5],
    'RP(GAIA DR3)': ['#ff8A8A', 'circle', 4],
    'BP(GAIA DR3)': ['#8A8Aff', 'circle', 4],
    'G(GAIA DR3)': ['black', 'circle', 4],
    'I(GaiaSP)': ['#6c1414', '21', 4],
    'g(GaiaSP)': ['green', '21', 4],
    'R(GaiaSP)': ['#d82727', '21', 4],
    'V(GaiaSP)': ['darkgreen', '21', 4],
    'B(GaiaSP)': ['#000034', '21', 4],
    'z(GaiaSP)': ['#ff0074', '21', 4],
    'u(GaiaSP)': ['#40E0D0', '21', 4],
    'r(GaiaSP)': ['red', '21', 4],
    'U(GaiaSP)': ['#5ac6bc', '21', 4],
    'i(GaiaSP)': ['#800000', '21', 4],
    'ASASSN(g)': ['green', 'cross-thin', 2],  # add opacity
    'ASASSN(V)': ['darkgreen', 'cross-thin', 2],  # add opacity
    'OGLE(I)': ['#800080', 'diamond', 4],
    'ATLAS(c)': ['#1f7e7d', 'circle', 2],  # add opacity
    'ATLAS(o)': ['#f88f1e', 'circle', 2],  # add opacity
    'KMTNET(I)': ['#8c4646', 'diamond-tall', 2]
}


@register.inclusion_tag('bhtom_dataproducts/partials/recent_photometry.html')
def recent_photometry(target, limit=1):
    """
    Displays a table of the most recent photometric points for a target.
    """
    photometry = ReducedDatum.objects.filter(target=target, data_type='photometry').order_by('-timestamp')[:limit]
    return {'data': [{'timestamp': rd.timestamp,
                      'magnitude': rd.value,
                      'magerr': rd.error,
                      'filter': rd.filter,
                      'facility': rd.facility,
                      'observer': rd.observer} for rd in photometry
                     if rd.value_unit == ReducedDatumUnit.MAGNITUDE]}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_stats.html')
def photometry_stats(target):
    import pandas as pd

    """
    Displays a table of the the photometric data stats for a target.
    """

    stats, columns = get_photometry_stats(target)
    sort_by = 'facility'
    sort_by_asc = True
    df: pd.DataFrame = pd.DataFrame(data=stats,
                                    columns=columns).sort_values(by=sort_by, ascending=sort_by_asc)

    data_list = []
    for index, row in df.iterrows():
        data_dict = {'Facility': row['facility'],
                     'Observers': row['observer'],
                     'Filters': row['filter'],
                     'Data_points': row['Data_points'],
                     'Min_MJD': row['Earliest_time'],
                     'Max_MJD': row['Latest_time']}
        data_list.append(data_dict)

    return {'data': data_list}


@register.inclusion_tag('bhtom_dataproducts/partials/gaia_stats.html')
def gaia_stats(target):
    """
    Displays a table of the stats and info from Gaia DR2 and DR3 for a target.
    """

    data_list = []
    try:
        gaiaDr2 = TargetGaiaDr2.objects.get(target=target)
        gaiaDr3 = TargetGaiaDr3.objects.get(target=target)
    except (TargetGaiaDr2.DoesNotExist, TargetGaiaDr3.DoesNotExist):
        return {'data': data_list}
    except Exception as e:
        logger.error("Error in GaiaDr2/3: " + str(e))
        return {'data': data_list}

    data_dict = {'Parameter': 'parallax [mas]',
                 'GDR2': f'{around(gaiaDr2.parallax, 3)} ± {around(gaiaDr2.parallax_error, 3)}',
                 'GDR3': f'{around(gaiaDr3.parallax, 3)} ± {around(gaiaDr3.parallax_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'PM RA [mas/yr]',
                 'GDR2': f'{around(gaiaDr2.pmra, 3)} ± {around(gaiaDr2.pmra_error, 3)}',
                 'GDR3': f'{around(gaiaDr3.pmra, 3)} ± {around(gaiaDr3.pmra_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'PM Dec [mas/yr]',
                 'GDR2': f'{around(gaiaDr2.pmdec, 3)} ± {around(gaiaDr2.pmdec_error, 3)}',
                 'GDR3': f'{around(gaiaDr3.pmdec, 3)} ± {around(gaiaDr3.pmdec_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'RUWE / AEN [mas]',
                 'GDR2': f"{around(gaiaDr2.ruwe, 3)} / {around(gaiaDr2.astrometric_excess_noise, 3)}" if gaiaDr2.ruwe is not None else "-",
                 'GDR3': f'{around(gaiaDr3.ruwe, 3)} / {around(gaiaDr3.astrometric_excess_noise, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'Dist_med_geo [kpc]',
                 'GDR2': '-',
                 'GDR3': f'{around(gaiaDr3.r_med_geo / 1000., 3)}'
                 }
    data_list.append(data_dict)

    return {'data': data_list}
    
@register.inclusion_tag('bhtom_dataproducts/partials/dataproduct_list_for_target.html', takes_context=True)
def dataproduct_list_for_target(context, target):
    """
    Given a ``Target``, returns a list of ``DataProduct`` objects associated with that ``Target``
    """

    target_products = target.dataproduct_set.order_by('-created')[:10]

    for row in target_products:
        try:
            row.photometry_data = row.photometry_data.split('/')[-1]
            row.observatory.observatory.prefix = row.observatory.observatory.prefix.split('_CpcsOnly')[0]
        except Exception:
            continue

    return {
        'products': target_products,
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
    initial['user'] = user
    initial["users"] =  User.objects.filter(is_active=True).order_by('first_name')
    form = DataProductUploadForm(initial=initial)

    return {'data_product_form_from_user': form}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target.html', takes_context=True)
def photometry_for_target(context, target, width=1000, height=600, background=None, label_color=None, grid=True):
    fig = None
    if target.photometry_plot is not None and target.photometry_plot != '':
        base_path = settings.DATA_PLOTS_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.photometry_plot))

            # Get the current UTC time
            current_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

            # Calculate the y-range from your data traces
            y_values = [trace['y'] for trace in fig['data'] if 'y' in trace]
            y_min = np.min([np.min(values) for values in y_values])
            y_max = np.max([np.max(values) for values in y_values])

            # Add a vertical dashed line at the current date
            line_trace = go.Scatter(
                x=[current_date, current_date],
                y=[y_min-2, y_max+2],  # This will make the line span the entire plot in Y
                mode='lines',
                name='NOW',
                line=dict(
                    color="Grey",  # Change the color here
                    width=1,
                    dash="dash",  # This makes the line dashed.
                ),
                showlegend=True
            )
            fig.add_trace(line_trace)

            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except Exception as e:
            logger.warning("Plot(filters) does not exist" + str(e))

    layout = go.Layout(
        height=height,
        width=width,
        paper_bgcolor=background,
        plot_bgcolor=background

    )
    layout.legend.font.color = label_color
    fig = go.Figure(data=[], layout=layout)

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target_obs.html', takes_context=True)
def photometry_for_target_obs(context, target, width=1000, height=600, background=None, label_color=None, grid=True):
    fig = None
    if target.photometry_plot_obs is not None and target.photometry_plot_obs != '':
        base_path = settings.DATA_PLOTS_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.photometry_plot_obs))

            # Get current date as a string in 'YYYY-MM-DD' format + hours+mins+seconds
            current_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

            # Calculate the y-range from your data traces
            y_values = [trace['y'] for trace in fig['data'] if 'y' in trace]
            y_min = np.min([np.min(values) for values in y_values])
            y_max = np.max([np.max(values) for values in y_values])

            # Add a vertical dashed line at the current date
            line_trace = go.Scatter(
                x=[current_date, current_date],
                y=[y_min-2, y_max+2],  # This will make the line span the entire plot in Y
                mode='lines',
                name='NOW',
                line=dict(
                    color="Grey",  # Change the color here
                    width=1,
                    dash="dash",  # This makes the line dashed.
                ),
                showlegend=True
            )
            fig.add_trace(line_trace)

            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except:
            logger.warning("Plot(observers) does not exist")

    layout = go.Layout(
        height=height,
        width=width,
        paper_bgcolor=background,
        plot_bgcolor=background

    )
    layout.legend.font.color = label_color
    fig = go.Figure(data=[], layout=layout)

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }

@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target_highenergy.html', takes_context=True)
def photometry_for_target_highenergy(context, target, width=1000, height=600, background=None, label_color=None, grid=True):
    fig = None
    if target.photometry_plot_highenergy is not None and target.photometry_plot_obs != '':
        base_path = settings.DATA_PLOTS_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.photometry_plot_highenergy))

            # Get current date as a string in 'YYYY-MM-DD' format + hours+mins+seconds
            current_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

            # Calculate the y-range from your data traces
            y_values = [trace['y'] for trace in fig['data'] if 'y' in trace]
            y_min = np.min([np.min(values) for values in y_values])
            y_max = np.max([np.max(values) for values in y_values])

            # Add a vertical dashed line at the current date
            line_trace = go.Scatter(
                x=[current_date, current_date],
                y=[y_min-2, y_max+2],  # This will make the line span the entire plot in Y
                mode='lines',
                name='NOW',
                line=dict(
                    color="Grey",  # Change the color here
                    width=1,
                    dash="dash",  # This makes the line dashed.
                ),
                showlegend=True
            )
            fig.add_trace(line_trace)

            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except:
            logger.warning("Plot(high energy) does not exist")

    layout = go.Layout(
        height=height,
        width=width,
        paper_bgcolor=background,
        plot_bgcolor=background

    )
    layout.legend.font.color = label_color
    fig = go.Figure(data=[], layout=layout)

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

    if target.photometry_icon_plot is not None and target.photometry_icon_plot != '':
        base_path = settings.DATA_PLOTS_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.photometry_icon_plot))
            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except:
            logger.warning("Plot does not exist")

    layout = go.Layout(
        height=height,
        width=width,
        paper_bgcolor=background,
        plot_bgcolor=background

    )
    layout.legend.font.color = label_color
    fig = go.Figure(data=[], layout=layout)

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False, config=dict({'staticPlot': True}))
    }


@register.inclusion_tag('bhtom_dataproducts/partials/spectroscopy_for_target.html', takes_context=True)
def spectroscopy_for_target(context, target, dataproduct=None):

    if target.spectroscopy_plot is not None and target.spectroscopy_plot != '':
        base_path = settings.DATA_PLOTS_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.spectroscopy_plot))
            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except:
            logger.warning("Plot not exist")

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

    fig = go.Figure(data=[], layout=layout)

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }


@register.inclusion_tag('bhtom_dataproducts/partials/update_broker_data_button.html', takes_context=True)
def update_broker_data_button(context):
    return {'query_params': urlencode(context['request'].GET.dict())}
