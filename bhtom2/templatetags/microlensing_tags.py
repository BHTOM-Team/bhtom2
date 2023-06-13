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
def microlensing_for_target(context, target, sel, init_t0, init_te, init_u0, logu0, auto_init):
    error_message = ""
    if init_t0 != '':  init_t0 = float(init_t0)
    if init_te != '':  init_te = float(init_te)
    if init_u0 != '':  init_u0 = float(init_u0)
    if logu0 != '' : logu0 = bool(logu0)
    if auto_init != '': auto_init = bool(auto_init)

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
                times[filter].append(datum.mjd)
                mags[filter].append(datum.value)
                errors[filter].append(datum.error)
            except Exception:
                logger("Error reading datapoint "+str(datum))
                continue


    #Reading Gaia ephemeris file from statics
    try:
        gaiaephem_path = path.join('static', 'Gaia_ephemeris.txt')
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
    #blending fixed (set to 0) when true
    fixblending=True




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

    params = dict()
    params['t_0'] = smartt0# full JD has to go here!!!
    delta_m = minmag-maxmag 
    smartu0 = (10**(0.4 * delta_m) - 1) / (10**(0.4 * delta_m) + 1)
    params['u_0'] = smartu0
    if (logu0): params['u_0'] = np.log10(params['u_0'])

    smartte = 50.
    params['t_E'] = smartte
    my_model = mm.Model(params)

    #first time run:
    if init_t0 == '' or auto_init:
        init_t0 = smartt0
    if init_te == '' or auto_init:
        init_te = smartte
    if init_u0 == '' or auto_init:
        init_u0 = params['u_0']
    if (logu0 == '') or auto_init:
        logu0 = False
 
    ############ figure of raw data:
    fig = go.Figure(layout=dict(width=1000, height=500))

    for filter in filters:
        fig.add_trace(go.Scatter(x=np.array(times[filter])-50000., y=mags[filter], 
                          error_y=dict(type='data', array=errors[filter]), 
                          mode='markers', name=str(filter)))

    fig.update_layout(title="%s"%(name), 
                      xaxis_title="MJD-50000.0", 
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
    x0=init_t0-50000.,
    x1=init_t0-50000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="red", width=2,  dash="dash",))
    fig.add_shape(
    type="line",
    x0=init_t0-init_te-50000.,
    x1=init_t0-init_te-50000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="blue", width=2,  dash="dot",))
    fig.add_shape(
    type="line",
    x0=init_t0+init_te-50000.,
    x1=init_t0+init_te-50000.,
    y0=min_y,
    y1=max_y,
    line=dict(color="blue", width=2,  dash="dot",))

    div = opy.plot(fig, auto_open=False, output_type='div', show_link=False)

    ########### MODELLING
    if num_points_all == 0:  # checking if there is any data
        logger.error("No Data")
        return {
            'selected_filters': "", #forcing empty, to reload default set
            'error_message': "ERROR: No data",
        }
#     else:
#         # title
#         # get time of modeling
#         start_time = time.time()
#         # ulensing modelling
#         t0 = x[-1]
#         chi2_best = 100000
#         mchi2_best = 100000
#         NDF = 0
#         errors = ''
#         for i in range(10, 600, 25):
#             for j in [0.1, 0.01]:
#                 try:
#                     with warnings.catch_warnings():
#                         warnings.simplefilter("ignore")  # supressing covariance warning
#                         popt, pcov = optimize.curve_fit(ulens, xdata=x, ydata=y, p0=np.asarray([t0, i, j, y.max()]))
#                 except RuntimeError as error:
#                     pass
#                 # chi^2 test
#                 try:
#                     chi2 = lambda popt, x, y, err: sum(((ulens(x, *popt) - y) / err) ** 2)
#                     tmp1 = chi2(popt, x, y, err)
#                     tmp2 = chi2(popt, x, y, err) / (len(x) - 4)
#                     tmp = np.asarray(pcov)
#                     if mchi2_best > tmp2 and not np.isinf(tmp).any():
#                         chi2_best = tmp1
#                         mchi2_best = tmp2
#                         popt_best = popt
#                         pcov_best = pcov
#                         NDF = len(x) - 4
#                 except ZeroDivisionError as error:
#                     return {
#                         'errors': "ERROR: Divide by 0! The error of y is 0!",
#                     }
#                 except UnboundLocalError as error:
#                     pass
#         if NDF <= 250:
#             round_NDF = NDF
#         elif 250 < NDF <= 1000:
#             round_NDF = myround(NDF)
#         else:
#             round_NDF = 1000
#             errors = "ERROR: NDF out of range"
#         chi2_table = 1 #
        
#         info_conclusion = ''
#         if chi2_best <= chi2_table:
#             info_conclusion = "There is NO reason to reject the hypothesis - this phenomenon may be microlensing at the expected confidence level: " + str(
#                 100 - alfa * 100) + "%"
#         else:
#             info_conclusion = "There is a reason for rejecting the hypothesis - This phenomenon CANNOT be microlensing at the expected confidence level: " + str(
#                 100 - alfa * 100) + "%"

#             # time of miscrolensing and max magnitude
#         microlensing_start_time = 0
#         microlensing_end_time = 0
#         max_mag = 1000  # big number because of inversion

#         max_mag_time = 0
#         beg = False
#         fin = False
#         deviation = 0.999  # when mag decrease 0.1%
#         t = x[0]
#         info_start_time = ''
#         info_start_time_value = ''
#         info_end_time = ''
#         info_end_time_value = ''
#         while (beg == False or fin == False) and t < x[0] + 10000:
#             if ulens(t, *popt_best) <= ulens(x[0], *popt_best) * deviation and beg == False:
#                 microlensing_start_time = t
#                 info_start_time = "Microlensing start time: "
#                 info_start_time_value = str(jd_to_date(microlensing_start_time)) + " |" + str(
#                     microlensing_start_time)
#                 beg = True
#             elif ulens(t, *popt_best) > ulens(microlensing_start_time, *popt_best) and beg == True and fin == False:
#                 microlensing_end_time = t
#                 info_end_time = "Microlensing end time: "
#                 info_end_time_value = str(jd_to_date(microlensing_end_time)) + " |" + str(microlensing_end_time)
#                 fin = True
#             t += 0.5

#         # fit with prediction
#         if microlensing_end_time == 0:
#             microlensing_end_time = x[0]
#         time_plot = np.linspace(x[0], microlensing_end_time + 366, 1000)
#         # showing date on x axis
#         for i in range(len(time_plot) - 1):
#             current_datetime = Time(float(time_plot[i]), format='jd', scale='utc').to_datetime()
#             X_timestamp.append(current_datetime)
#             X_fit_timestamp.append(current_datetime)
#             if ulens(time_plot[i], *popt_best) <= max_mag and beg == True and fin == True:
#                     max_mag = ulens(time_plot[i], *popt_best)
#                     max_mag_time = time_plot[i]
#         time_plot_timestamp = np.asarray(X_fit_timestamp)

#         if fin == True and beg == True:
#             a = date(*jd_to_date(microlensing_start_time))
#             b = date(*jd_to_date(microlensing_end_time))
#             c = date.today()
#             max_mag = '{0:.3f}'.format(max_mag)
#             info_duration = "Duration of microlensing: "
#             info_duration_value = str(days_to_ymd((b - a).days))
#             info_remainingTime = "Remaining time of microlensing: "
#             if (b - c).days > 0:
#                 info_remainingTime_value = str(days_to_ymd((b - c).days))
#             else:
#                 info_remainingTime_value = "-"
#             info_maximumMagnitude = "Maximum magnitude: "
#             info_maximumMagnitude_value = "%s mag" % max_mag
#             info_maximumMagnitudeTime = "Expected time of maximum: "
#             info_maximumMagnitudeTime_value = str(jd_to_date(max_mag_time)) + " |" + str(max_mag_time)
#             # print fitted parameters
#             if abs(np.sqrt(pcov_best[0][0]) / popt_best[0]) <= errorSignificance:
#                 info_t0 = "t0: " + str('{0:.3f}'.format(popt_best[0])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[0][0]))) + ")"
#                 info_t0_check = "OK"
#             else:
#                 info_t0 = "t0: " + str('{0:.3f}'.format(popt_best[0])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[0][0]))) + ")"
#                 info_t0_check = "BIGGER THAN " + str(errorSignificance * 100) + "%"

#             if abs(np.sqrt(pcov_best[1][1]) / popt_best[1]) <= errorSignificance:
#                 info_te = "te: " + str('{0:.3f}'.format(popt_best[1])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[1][1]))) + ")"
#                 info_te_check = "OK"
#             else:
#                 info_te = "te: " + str('{0:.3f}'.format(popt_best[1])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[1][1]))) + ")"
#                 info_te_check = "BIGGER THAN " + str(errorSignificance * 100) + "%"

#             if abs(np.sqrt(pcov_best[2][2]) / popt_best[2]) <= errorSignificance:
#                 info_u0 = "u0: " + str('{0:.5f}'.format(abs(popt_best[2]))) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[2][2]))) + ")"
#                 info_u0_check = "OK"
#             else:
#                 info_u0 = "u0: " + str('{0:.5f}'.format(abs(popt_best[2]))) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[2][2]))) + ")"
#                 info_u0_check = "BIGGER THAN " + str(errorSignificance * 100) + "%"

#             if abs(np.sqrt(pcov_best[3][3]) / popt_best[3]) <= errorSignificance:
#                 info_I0 = "I0: " + str('{0:.3f}'.format(popt_best[3])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[3][3]))) + ")"
#                 info_I0_check = "OK"
#             else:
#                 info_I0 = "I0: " + str('{0:.3f}'.format(popt_best[3])) + " (" + str(
#                     '{0:.3f}'.format(np.sqrt(pcov_best[3][3]))) + ")"
#                 info_I0_check = "BIGGER THAN " + str(errorSignificance * 100) + "%"
#             info_fs = "fs: 1.0 (fixed)"

#             # execution time
#             info_executionTime = "Time of fitting execution: %s seconds" % '{0:.3f}'.format(
#                 (time.time() - start_time))
#         else:
# #            print("MICROLNEINS ERROR")
#             return {
#                 'target': target,
#                 'selected_filters': selected_filters,
#                 'sel': sel,
#                 'slevel': slevel,
#                 'errors': "ERROR: Cannot find fitted parameters",
#             }
        
#         # plotting fig
#         plot_data = [go.Scatter(
#             x=x_timestamp,
#             y=y,
#             mode='markers',
#             name="Experimental data with error bar",
#             error_y=dict(type='data',
#                          array=err,
#                          visible=True),
#         ), go.Scatter(
#             x=time_plot_timestamp,
#             y=ulens(time_plot, *popt_best),
#             mode='lines',
#             line=dict(shape='spline', smoothing=1.3),
#             name="Fit with prediction",
#         )
#         ]
#         layout = go.Layout(
#             title=dict(text=str(target)),
#             yaxis=dict(autorange='reversed', title='Magnitude [mag]'),
#             xaxis=dict(title='UTC time'),
#             height=600,
#             width=700,
#             legend=dict(
#                 orientation="h",
#                 yanchor="bottom",
#                 y=1.02,
#                 xanchor="right",
#                 x=1
#             )
#         )

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
        'auto_init': auto_init,
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


