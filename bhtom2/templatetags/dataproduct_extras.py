import logging
from datetime import datetime
from urllib.parse import urlencode
from django.template import Context, loader
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
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.processors.data_serializers import SpectrumSerializer
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target

from numpy import around

from bhtom2.utils.photometry_and_spectroscopy_data_utils import get_photometry_stats

register = template.Library()


@register.inclusion_tag('bhtom_dataproducts/partials/recent_photometry.html')
def recent_photometry(target, limit=1):
    """
    Displays a table of the most recent photometric points for a target.
    """
    time = datetime.now()
    photometry = ReducedDatum.objects.filter(data_type='photometry', target=target).order_by('-timestamp')[:limit]
    time2 = datetime.now()
    logging.info("recent photometry %s" % str(time - time2))
    return {'data': [{'timestamp': rd.timestamp,
                      'magnitude': rd.value,
                      'filter': rd.filter,
                      'facility': rd.facility} for rd in photometry
                     if rd.value_unit == ReducedDatumUnit.MAGNITUDE]}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_stats.html')
def photometry_stats(target):
    time = datetime.now()

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
    time2 = datetime.now()
    logging.info("photometry status %s" % str(time - time2))
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
    return {'data_product_form_from_user': form}


@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target.html', takes_context=True)
def photometry_for_target(context, target, width=1000, height=600, background=None, label_color=None, grid=True):

    fig = None
    if (target.photometry_plot != None and target.photometry_plot != ''):
        fig = loader.get_template(target.photometry_plot)
    else:
        layout = go.Layout(
            height=height,
            width=width,
            paper_bgcolor=background,
            plot_bgcolor=background

        )
        layout.legend.font.color = label_color
        fig = go.Figure(data=[], layout=layout)
    
    layout = go.Layout(
            height=height,
            width=width,
            paper_bgcolor=background,
            plot_bgcolor=background

        )
    layout.legend.font.color = label_color    
    
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }


### static and simpler version of the plot for massive list table
@register.inclusion_tag('bhtom_dataproducts/partials/photometry_for_target_icon.html', takes_context=True)
def photometry_for_target_icon(context, target, width=800, height=400, background=None, label_color=None, grid=True):

    fig = None
    if (target.photometry_plot != None and target.photometry_plot != ''):
        fig = loader.get_template(target.photometry_plot)
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
    if (target.spectroscopy_plot != None and target.spectroscopy_plot != '' ):
        fig = loader.get_template(target.spectroscopy_plot)
    else:
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
