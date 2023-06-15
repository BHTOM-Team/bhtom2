# importing the required module
import logging
from os import path

import astropy
from astropy.time import Time
from django import template
import csv
import math

from bhtom_base.bhtom_targets.templatetags.targets_extras import deg_to_sexigesimal
from bhtom2.utils.bhtom_logger import BHTOMLogger
import numpy as np
from guardian.shortcuts import get_objects_for_user
from scipy import optimize
from datetime import date
import time
import pandas as pd
import warnings
import json

import MulensModel as mm
import matplotlib.pyplot as plt
from matplotlib import gridspec
import scipy.optimize as op
from collections import OrderedDict, defaultdict
import plotly.graph_objs as go
import plotly.offline as opy



from bhtom_base.bhtom_dataproducts.forms import DataProductUploadForm
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, ReducedDatumUnit
from bhtom_base.bhtom_dataproducts.processors.data_serializers import SpectrumSerializer
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target

from django.conf import settings

logger: BHTOMLogger = BHTOMLogger(__name__, '[Microlensing_Tags]')

register = template.Library()


@register.inclusion_tag('bhtom_dataproducts/partials/microlensing_for_target.html', takes_context=True)
def microlensing_for_target(context, target, sel, init_t0, init_te, init_u0, logu0, fixblending, auto_init, filter_counts):
    error_message = ""
    if init_t0 != '':  init_t0 = float(init_t0)
    if init_te != '':  init_te = float(init_te)
    if init_u0 != '':  init_u0 = float(init_u0)

    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(target=target,
                                             data_type=settings.DATA_PRODUCT_TYPES['photometry'][0]
                                             )

    else:
        datums = get_objects_for_user(context['request'].user,
                                      'bhtom_viewreduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                          target=target,
                                          data_type__in=[settings.DATA_PRODUCT_TYPES['photometry'][0]]))
        
    selected_filters = [f for f, checked in sel.items() if checked]    

    times = defaultdict(list)
    mags = defaultdict(list)
    errors = defaultdict(list)
    filters = selected_filters

    for datum in datums:
        if str(datum.filter) in selected_filters:
            try:
                filter = datum.filter
                times[filter].append(datum.mjd+2400000.5) #store JD here
                mags[filter].append(datum.value)
                errors[filter].append(datum.error)
            except Exception:
                logger("Error reading datapoint "+str(datum))
                continue


    #Reading Gaia ephemeris file from statics
    try:
        gaiaephem_path = path.join(settings.STATIC_ROOT, 'Gaia_ephemeris.txt')
    except Exception as e:
        logger.error("Gaia ephemeris file not found")
        return {
            'error_message': "ERROR: Gaia ephemeris file not found",
        }

    #setup for Mulens
    name=target.name
    ras = deg_to_sexigesimal(target.ra,'hms')
    decs = deg_to_sexigesimal(target.dec,'dms')
    coords=ras+" "+decs
    print("Target for microlensing: ",name, coords)

    mulens_datas = OrderedDict()

    num_points_all=0
    for filter in filters:
        mulens_datas[filter] = mm.MulensData(
		    data_list = (times[filter], mags[filter], errors[filter]),
		    phot_fmt = 'mag',
            add_2450000=False,
            plot_properties={'label': filter, 'marker' : 'o'}
            )
        num_points_all+=len(times[filter])

        if (filter=='G(GAIA_ALERTS)' or filter=='G(GAIA)' or filter=='BP(GAIA)' or filter=='RP(GAIA)' or filter=='G(Gaia)' or filter=='BP(Gaia)' or filter=='RP(Gaia)'):
            mulens_datas[filter] = mm.MulensData(
                data_list = (times[filter], mags[filter], errors[filter]),
                phot_fmt = 'mag',
                ephemerides_file = gaiaephem_path,
                add_2450000=False,
                plot_properties={'label': filter, 'marker' : 'o', 'marker' : '.', 'markersize':15, 'zorder': 100})
	

    #guessing some of the parameters for init, from the first data set
    largets_set = max(filters, key=lambda x: len(times[x]))
    largets_set_index = filters.index(largets_set)
    maxmag = mulens_datas[largets_set].mag.min()
    minmag = mulens_datas[largets_set].mag.max()
    index = mulens_datas[largets_set].mag.argmin()
    smartt0 = mulens_datas[largets_set].time[index]
    delta_m = minmag-maxmag 
    smartu0 = invert_delta_mag(delta_m)

    print("LARGEST: ", largets_set, delta_m)
    params = dict()
    params['t_0'] = smartt0# full JD has to go here!!!
    params['u_0'] = smartu0
    if (logu0 == 'on'): params['u_0'] = np.log10(params['u_0'])

    smartte = 50.
    params['t_E'] = smartte

    if init_t0 == '' or auto_init:
        init_t0 = smartt0
    if init_te == '' or auto_init:
        init_te = smartte
    if init_u0 == '' or auto_init:
        init_u0 = smartu0
    # if (logu0 == '') or auto_init:
    #     logu0 = ''
    if (fixblending == 'off') :
        fixblending = '' #this is because only empty string will be read as unchecked box


    ############ figure of raw data:
    fig = go.Figure(layout=dict(width=1000, height=500))

    for filter in filters:
        fig.add_trace(go.Scatter(x=np.array(times[filter])-2450000., y=mags[filter], 
                          error_y=dict(type='data', array=errors[filter]), 
                          mode='markers', name=str(filter)))

    fig.update_layout(title="%s"%(name), 
                      xaxis_title="JD-2450000.0", 
                      xaxis=dict(
                        tickformat='.1f' # format the ticks to one decimal place
                        ),
                      yaxis_title="Brightness [mag]", 
                      hovermode='closest', 
                      showlegend=True, 
                          legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                        ),
                      template='plotly_white')

    fig.update_yaxes(autorange="reversed")

    # # Set y0 and y1 to the minimum and maximum values of the y-axis range
    min_y = min(mag for filter in mags for mag in mags[filter])
    max_y = max(mag for filter in mags for mag in mags[filter])
    
    fig.add_shape(
    type="line",
    x0=init_t0-2450000.,
    x1=init_t0-2450000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="red", width=2,  dash="dash",))
    fig.add_shape(
    type="line",
    x0=init_t0-init_te-2450000.,
    x1=init_t0-init_te-2450000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="blue", width=2,  dash="dot",))
    fig.add_shape(
    type="line",
    x0=init_t0+init_te-2450000.,
    x1=init_t0+init_te-2450000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="blue", width=2,  dash="dot",))

    div = opy.plot(fig, auto_open=False, output_type='div', show_link=False)

    ########### MODELLING
    start_time = time.time()

    my_model = mm.Model(params)

    #defining dictionary with zeroblending
    zeroBlendingDict= dict()
    zeroBlendingDict = { i : 0 for i in tuple(mulens_datas.values()) }
    
    if (fixblending=='on'): 
        my_event = mm.Event(datasets=(tuple(mulens_datas.values())), model=my_model, fix_blend_flux=zeroBlendingDict) 
    else:
        my_event = mm.Event(datasets=(tuple(mulens_datas.values())), model=my_model)


    parameters_to_fit = ["t_0", "u_0", "t_E"]
    initial_guess = [params["t_0"], params["u_0"], params["t_E"]]

    n_dim = len(parameters_to_fit)
    n_data = num_points_all
    ndof=n_data-n_dim
    logu0_bool = True if logu0 == 'on' else False

    try:
        result = op.minimize(
            chi2_fun, x0=initial_guess, args=(parameters_to_fit, my_event, logu0_bool),
            method='Nelder-Mead')
        print(result.x)
        (fit_t_0, fit_u_0, fit_t_E) = result.x

        # Save the best-fit parameters
        chi2 = chi2_fun(result.x, parameters_to_fit, my_event, logu0_bool)

        # Output the fit parameters
        if (logu0_bool):
            fit_msg = 'Best Fit: t_0 = {0:12.5f}, log(u_0) = {1:6.5f}, t_E = {2:8.3f}'.format(fit_t_0, np.power(10, fit_u_0), fit_t_E)
        else:
            fit_msg = 'Best Fit: t_0 = {0:12.5f}, u_0 = {1:6.5f}, t_E = {2:8.3f}'.format(fit_t_0, fit_u_0, fit_t_E)
        
        print(fit_msg)
        fit_chi = 'Chi2 = {0:12.2f}  Chi2/ndof = {1:12.2f}'.format(chi2,(chi2/ndof))
        print(fit_chi)

        mag0_dict = {}
        fs_dict = {}

        for filt in filters:
            f_source, f_blend = my_event.get_flux_for_dataset(mulens_datas[filt])
            mag0 = mm.utils.Utils.get_mag_from_flux(f_source + f_blend)
            fs = f_source / (f_source + f_blend)
            mag0_dict[filt] = np.around(mag0[0],3)
            fs_dict[filt] = np.around(fs[0],3) #the result was an 1-element array

        print("Mag0 values:")
        print(mag0_dict)
        print("\nFs values:")
        print(fs_dict)

        info_executionTime = "Time of fitting execution: %s seconds" % '{0:.3f}'.format((time.time() - start_time))

        #FIG:
        best = result.x
        tstart = best[0]-1000.
        tstop = best[0]+500.

        plt.figure(figsize=(10, 6))
        grid = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        axes = plt.subplot(grid[0])
        my_event.plot_data(subtract_2450000=True)
        if (fixblending=='on'): 
            lab1 = "no-bl."
        else:
            lab1 = "blended"
    #    my_event.plot_model(color='black', t_start=tstart, t_stop=tstop, lw=2, subtract_2450000=True, label=lab1)#, data_ref=1)
        my_event.plot_model(color='magenta', ls='--', t_start=tstart, t_stop=tstop, subtract_2450000=True, label=lab1)#, data_ref=0)
        plt.grid()
        plt.title(("%s")%(name))
        xlim1= best[0]-500.-2450000
        xlim2 = best[0]+500.-2450000
        plt.xlim(xlim1, xlim2)

        plt.legend(loc='best')

        axes = plt.subplot(grid[1])
        my_event.plot_residuals(subtract_2450000=True, show_errorbars=True)
        #difference between models:
        # (source_flux1, blend_flux1) = my_event.get_ref_fluxes('G_Gaia')
        # (source_flux2, blend_flux2) = my_event_parallax.get_ref_fluxes('G_Gaia')
        # xmodel = np.linspace(xlim1+2450000, xlim2+2450000, num=200)
        # ymodel1=my_model.get_lc(xmodel, source_flux=source_flux1, blend_flux=blend_flux1)
        # ymodel2=my_model_parallax.get_lc(xmodel, source_flux=source_flux2, blend_flux=blend_flux2)
        # difmodel = ymodel2-ymodel1
        # plt.plot(xmodel-2450000, difmodel, ls='--',color='magenta')

        plt.xlim(xlim1, xlim2)
        plt.ylim(-0.23,0.23)
        plt.grid()

        import io
        import base64

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    except:
        return {
                    'selected_filters': selected_filters,
        'sel': sel,
        'error_message': error_message,
        'target': target,
        'plot_div': div,
        'init_t0': init_t0,
        'init_te': init_te,
        'init_u0': init_u0,
        'logu0': logu0,
        'fixblending': fixblending,
        'auto_init': auto_init,
        'filter_counts': filter_counts,
        'error_message': "ERROR fitting microlensing model",
        }


    return {
        'selected_filters': selected_filters,
        'sel': sel,
        'error_message': error_message,
        'target': target,
        'plot_div': div,
        'init_t0': init_t0,
        'init_te': init_te,
        'init_u0': init_u0,
        'logu0': logu0,
        'fixblending': fixblending,
        'auto_init': auto_init,
        'filter_counts': filter_counts,
        'fit_msg':fit_msg,
        'fit_chi':fit_chi,
        'mag0_dict': mag0_dict,
        'fs_dict': fs_dict,
        'executionTime': info_executionTime,
        'image':image_base64,
        # 'criticalLevel_value': str('{0:.3f}'.format(chi2_table)),
        # 'Chi2Test': "Chi2 test: ",
        # 'Chi2Test_value': str('{0:.3f}'.format(chi2_best)),
        # 'NDF': 'NDF: ',
        # 'NDF_value': str(NDF),
        # 'Chi2NDF': "Chi2/NDF: ",
        # 'Chi2NDF_value': str('{0:.3f}'.format(mchi2_best)),
        # 'conclusion': info_conclusion,
        # 'plot': offline.plot(go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False),
        # 'microStartTime': info_start_time,
        # 'microStartTime_value': info_start_time_value,
        # 'microEndTime': info_end_time,
        # 'microEndTime_value': info_end_time_value,
        # 'duration': info_duration,
        # 'duration_value': info_duration_value,
        # 'remainingTime': info_remainingTime,
        # 'remainingTime_value': info_remainingTime_value,
        # 'maximumMagnitude': info_maximumMagnitude,
        # 'maximumMagnitude_value': info_maximumMagnitude_value,
        # 'maximumMagnitudeTime': info_maximumMagnitudeTime,
        # 'maximumMagnitudeTime_value': info_maximumMagnitudeTime_value,
        # 't0': info_t0,
        # 't0_check': info_t0_check,
        # 'te': info_te,
        # 'te_check': info_te_check,
        # 'u0': info_u0,
        # 'u0_check': info_u0_check,
        # 'I0': info_I0,
        # 'I0_check': info_I0_check,
        # 'fs': info_fs,
        # 'executionTime': info_executionTime,
    }


# classical lens, no effects
def ulens(t, t0, te, u0, I0, fs=1):
    tau = (t - t0) / te
    x = tau
    y = u0
    u = np.sqrt(x * x + y * y)
    ampl = (u * u + 2) / (u * np.sqrt(u * u + 4))
    F = ampl * fs + (1 - fs)
    I = I0 - 2.5 * np.log10(F)
    return I

def invert_ampl(A):
    #from Sahu 1997
    from math import sqrt
    u=sqrt(2.)* (A*(A*A-1)**(-1/2.)-1)**(1/2.)
    return u

def invert_delta_mag(dm):
    ampl = 10**(0.4*dm)
    return invert_ampl(ampl)

# it's chi suqared!
def chi2_fun(theta, parameters_to_fit, event, logu0):
    """
    Calculate chi2 for given values of parameters
    Keywords :
        theta: *np.ndarray*
            Vector of parameter values, e.g.,
            `np.array([5380., 0.5, 20.])`.
        parameters_to_fit: *list* of *str*
            List of names of parameters corresponding to theta, e.g.,
            `['t_0', 'u_0', 't_E']`.
        event: *MulensModel.Event*
            Event which has datasets for which chi2 will be calculated.
        logu0: boolean
    Returns :
        chi2: *float*
            Chi2 value for given model parameters.
    """
    # First we have to change the values of parameters in
    # event.model.parameters to values given by theta.
    for (parameter, value) in zip(parameters_to_fit, theta):
        if (parameter=='t_E'): value=np.abs(value)
        if (parameter=='rho'): value=np.abs(value)
        if (logu0==True): 
          if (parameter=='u_0'): value=np.power(10., -np.abs(value))               # LOG U0!

        setattr(event.model.parameters, parameter, value)


    # After that, calculating chi2 is trivial:
    return event.get_chi2()