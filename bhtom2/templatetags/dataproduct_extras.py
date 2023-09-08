from datetime import datetime
from urllib.parse import urlencode

import plotly
from django.template import Context, loader
from bhtom2.external_service.data_source_information import DataSource

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

from bhtom2.bhtom_dataproducts.forms import DataProductUploadForm
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.processors.data_serializers import SpectrumSerializer
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target, TargetName

from numpy import around

from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats

register = template.Library()
logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_dataproducts: extras]')

color_map = {
    'GSA(G)': ['black', 'hexagon', 8],
    'ZTF(zg)': ['green', 'x', 6],
    'ZTF(zi)': ['#800000', 'x', 6],
    'ZTF(zr)': ['red', 'x', 6],
    'WISE(W1)': ['#FFCC00', 'x', 3],
    'WISE(W2)': ['blue', 'x', 3],
    'CRTS(CL)': ['#FF1493', 'diamond', 4],
    'LINEAR(CL)': ['teal', 'diamond', 4],
    'SDSS(r)': ['red ', 'square', 5],
    'SDSS(i)': ['#800000', 'square', 5],
    'SDSS(u)': ['#40E0D0', 'square', 5],
    'SDSS(z)': ['#ff0074', 'square', 5],
    'SDSS(g)': ['green', 'square', 5],
    'DECAPS(r)': ['red ', 'star-square', 5],
    'DECAPS(i)': ['#800000', 'star-square', 5],
    'DECAPS(u)': ['#40E0D0', 'star-square', 5],
    'DECAPS(z)': ['#ff0074', 'star-square', 5],
    'DECAPS(g)': ['green', 'star-square', 5],
    'PS1(r)': ['red', 'star-open', 5],
    'PS1(i)': ['#800000', "star-open", 5],
    'PS1(z)': ['#ff0074', "star-open", 5],
    'PS1(g)': ['green', "star-open", 5],
    'RP(GAIA_DR3)': ['#ff8A8A', 'circle', 4],
    'BP(GAIA_DR3)': ['#8A8Aff', 'circle', 4],
    'G(GAIA_DR3)': ['black', 'circle', 4],
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
                      'filter': rd.filter,
                      'facility': rd.facility} for rd in photometry
                     if rd.value_unit == ReducedDatumUnit.MAGNITUDE]}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_stats.html')
def photometry_stats(target):
    import pandas as pd

    """
    Displays a table of the the photometric data stats for a target.
    """
    stats, columns = get_photometry_stats(target)
    sort_by = 'Facility'
    sort_by_asc = True
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


@register.inclusion_tag('bhtom_dataproducts/partials/gaia_stats.html')
def gaia_stats(target):
    import pandas as pd
    from astroquery.gaia import Gaia

    """
    Displays a table of the stats and info from Gaia DR2 and DR3 for a target.
    """
    # LATEX: from 18cbf Kruszynska22
    # \begin{table}
    # \caption{\label{tab:gdrsVals}Gaia astrometric parameters for the source star in Gaia18cbf.}.
    #      \centering
    #         \begin{tabular}{c c c}
    #         \hline
    #         \noalign{\smallskip}
    #              Parameter &  GDR2 & GEDR3 \\
    #              \noalign{\smallskip}
    #         \hline
    #         \hline
    #         \noalign{\smallskip}
    #              $\varpi$ [mas] & $-1.11\pm0.70$ &  $-0.36\pm0.59$ \\
    #              $\mu_{\alpha}$ [$\mathrm{mas} \, \mathrm{yr}^{-1}$] & $-0.68\pm1.96$ & $-1.83\pm0.68$ \\
    #              $\mu_{\delta}$ [$\mathrm{mas}\, \mathrm{yr}^{-1}$] & $-0.76\pm1.16$ & $-1.82\pm0.46$ \\
    #         \noalign{\smallskip}
    #         \hline
    #         \noalign{\smallskip}
    #          \multicolumn{3}{c}{Bailer-Jones et al. distances} \\
    #         \noalign{\smallskip}
    #         \hline
    #         \noalign{\smallskip}
    #              $r_{\rm est}$ [kpc] &  $4.4^{+3.2}_{-2.9}$ & --\\
    #              $r_{\rm geo, est}$ [kpc] &  -- & $5.4^{+2.2}_{-1.9}$ \\
    #              $r_{\rm photgeo, est}$ [kpc] &  -- & $7.8^{+2.0}_{-1.4}$ \\
    #         \noalign{\smallskip}
    #         \hline
    #         \end{tabular}
    # \end{table}

    # TODO: add check for Gaia DR2 name and use in queries, also display in the table
    # do we want to show the ra dec too?

    # TODO: this will be bloody slow, as the query will be run every time we go to Publication...

    data_list = []
    try:
        gaia_name = TargetName.objects.get(target=target, source_name=DataSource.GAIA_DR3.name).name
    except:
        return {'data': data_list}

    source_id = gaia_name

    # Initialize all variables to 0
    parallax3 = parallax3_error = pmra3 = pmra3_error = pmdec3 = pmdec3_error = ruwe3 = aen3 = 0
    parallax2 = parallax2_error = pmra2 = pmra2_error = pmdec2 = pmdec2_error = aen2 = ruwe2 = 0
    r3_med_geo = 0

    job = Gaia.launch_job(f"select  \
                        parallax, parallax_error, \
                        pmra, pmra_error, pmdec, pmdec_error, ruwe, astrometric_excess_noise \
                        from gaiadr3.gaia_source where source_id={source_id};")
    r3 = job.get_results().to_pandas()
    if not r3.empty:
        r3 = r3.iloc[0]  # assuring only first row will be read
        parallax3, parallax3_error = r3.parallax.item(), r3.parallax_error.item()
        pmra3, pmra3_error = r3.pmra.item(), r3.pmra_error.item()
        pmdec3, pmdec3_error = r3.pmdec.item(), r3.pmdec_error.item()
        ruwe3 = r3.ruwe.item()
        aen3 = r3.astrometric_excess_noise.item()

    job = Gaia.launch_job(f"select  \
                        parallax, parallax_error, \
                        pmra, pmra_error, pmdec, pmdec_error,astrometric_excess_noise \
                        from gaiadr2.gaia_source where source_id={source_id};")
    r2 = job.get_results().to_pandas()
    if not r2.empty:
        r2 = r2.iloc[0]  # assuring only first row will be read
        parallax2 = r2.parallax.item()
        parallax2_error = r2.parallax_error.item()
        pmra2 = r2.pmra.item()
        pmra2_error = r2.pmra_error.item()
        pmdec2 = r2.pmdec.item()
        pmdec2_error = r2.pmdec_error.item()
        aen2 = r2.astrometric_excess_noise.item()

    job = Gaia.launch_job(f"select  \
                        ruwe \
                        from gaiadr2.ruwe where source_id={source_id};")
    ruwe2 = job.get_results().to_pandas().ruwe.item()

    job = Gaia.launch_job(f"select  \
                        r_med_geo,     r_lo_geo,      r_hi_geo,  r_med_photogeo,  r_lo_photogeo,  r_hi_photogeo\
                        from external.gaiaedr3_distance where source_id={source_id};")
    r = job.get_results().to_pandas()
    if not r.empty:
        r = r.iloc[0]
        r3_med_geo = r.r_med_geo.item()

    # external.external.gaiadr2_geometric_distance
    # external.external.gaiaedr3_distance

    data_dict = {'Parameter': 'parallax [mas]',
                 'GDR2': f'{around(parallax2, 3)}&plusmn;{around(parallax2_error, 3)}',
                 'GDR3': f'{around(parallax3, 3)}&plusmn;{around(parallax3_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'PM RA [mas/yr]',
                 'GDR2': f'{around(pmra2, 3)}&plusmn;{around(pmra2_error, 3)}',
                 'GDR3': f'{around(pmra3, 3)}&plusmn;{around(pmra3_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'PM Dec [mas/yr]',
                 'GDR2': f'{around(pmdec2, 3)}&plusmn;{around(pmdec2_error, 3)}',
                 'GDR3': f'{around(pmdec3, 3)}&plusmn;{around(pmdec3_error, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'RUWE / AEN [mas]',
                 'GDR2': f'{around(ruwe2, 3)} / {around(aen2, 3)}',
                 'GDR3': f'{around(ruwe3, 3)} / {around(aen3, 3)}'
                 }
    data_list.append(data_dict)

    data_dict = {'Parameter': 'Dist_med_geo [kpc]',
                 'GDR2': '-',
                 'GDR3': f'{around(r3_med_geo / 1000., 3)}'
                 }
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
    initial['user'] = user
    form = DataProductUploadForm(initial=initial)

    return {'data_product_form_from_user': form}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target.html', takes_context=True)
def photometry_for_target(context, target, width=1000, height=600, background=None, label_color=None, grid=True):
    fig = None
    if target.photometry_plot is not None and target.photometry_plot != '':
        base_path = settings.DATA_FILE_PATH
        try:
            fig = plotly.io.read_json(base_path + str(target.photometry_plot))
            return {
                'target': target,
                'plot': offline.plot(fig, output_type='div', show_link=False)
            }
        except:
            logger.warning("Plot not exist")

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
    fig = None
    if (target.photometry_plot != None and target.photometry_plot != ''):
        fig = open(target.photometry_plot, 'r')
    else:
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


@register.inclusion_tag('bhtom_dataproducts/partials/spectroscopy_for_target.html', takes_context=True)
def spectroscopy_for_target(context, target, dataproduct=None):
    fig = None
    if target.spectroscopy_plot is not None and target.spectroscopy_plot != '':
        base_path = settings.DATA_FILE_PATH
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
