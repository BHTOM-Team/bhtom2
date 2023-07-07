import astropy.io.fits as pyfits
import astrolibpy.match_lists as match_lists
import sqlutilpy as sqlutil
import numpy as np
import scipy.optimize
import math
import sys
import astrolibpy.sphdist as sphdist
import re
import numpy as np
import os
import collections
import time
import astropy.io.ascii
from config import DBConfig, PlotConfig
from utils import isFits
import matplotlib
try:
    import OrderedDict
except:
    import collections as OrderedDict
try:
    from cStringIO import StringIO
except ImportError:
    # for python3
    from io import BytesIO as StringIO

matplotlib.use('Agg')
matplotlib.rc(
    'font', **{
        'size': PlotConfig.fontSize,
        'sans-serif': ['Helvetica'],
        'family': 'sans-serif'
    })
matplotlib.rc('figure', **{'dpi': PlotConfig.dpi})

import matplotlib.pyplot as plt
import logging
import healpy
from config import CalibConfig

logger = logging.getLogger('flask_code')


class CalibException(Exception):
    pass


class CalibResults:
    def __init__(self,
                 zp=None,
                 scatter=None,
                 fracOut=None,
                 cmag=None,
                 omag=None):
        self.zp = zp
        self.scatter = scatter
        self.fracOut = fracOut
        self.cmag = cmag
        self.omag = omag


def select_mag(columns):
    """
	Select MAG_AUTO or MAG_APER whichever is present
	"""
    if 'MAG_BEST' in columns and 'MAGERR_BEST' in columns:
        magcol = 'MAG_BEST'
        emagcol = 'MAGERR_BEST'
    elif 'MAG_AUTO' in columns and 'MAGERR_AUTO' in columns:
        magcol = 'MAG_AUTO'
        emagcol = 'MAGERR_AUTO'
    elif 'MAG_APER' in columns and 'MAGERR_APER' in columns:
        magcol = 'MAG_APER'
        emagcol = 'MAGERR_APER'
    else:
        magcol, emagcol = None, None
    return magcol, emagcol


def getdata(fname, forceType=None):
    """
	Read the catalog.
	Depending on the extension it will either assume ascii or fits format
	"""
    raColName = 'ALPHA_J2000'
    decColName = 'DELTA_J2000'

    if isFits(fname) or forceType == 'fits':
        tabtype = 'fits'
    elif not isFits(fname) or forceType == 'ascii':
        tabtype = 'ascii'
    else:
        raise CalibException('Unknown file type')

    if tabtype == 'ascii':
        try:
            _sex = astropy.io.ascii.sextractor.SExtractor()
            tab = _sex.read(fname)

        except:
            raise CalibException("Failed to read the data file")
        columns = [x for x in tab.columns]
        magcol, emagcol = select_mag(columns)
        if raColName not in columns or decColName not in columns:
            raise CalibException(
                "Failed to find the columns with ra,dec named ALPHA_J2000,DELTA_J2000"
            )
        ras, decs = tab[raColName].data, tab[decColName].data
        mags = tab[magcol].data
        magerrs = tab[emagcol].data
    elif tabtype == 'fits':
        try:
            hdus = pyfits.open(fname)
        except:
            raise CalibException("Failed to read the data file")

        goodhdus = []
        firsthdu = True
        for hdu in hdus:
            if (isinstance(hdu, pyfits.hdu.table.BinTableHDU)
                    or isinstance(hdu, pyfits.hdu.table.TableHDU)):
                columns = hdu.data.columns.names
                if raColName in columns and decColName in columns:
                    if firsthdu:
                        magcol, emagcol = select_mag(columns)
                        if magcol is not None:
                            firsthdu = False
                        else:
                            continue
                    else:
                        # Select the magnitude columns
                        # based on the first sensible HDU
                        pass
                    if magcol in columns and emagcol in columns:
                        goodhdus.append(hdu)

        if len(goodhdus) == 0:
            raise CalibException("""Failed to find to find FITS Table with 
	ra,dec columns ALPHA_J2000,DELTA_J2000,
	magnitude columns (MAG_BEST or MAG_AUTO or MAG_APER)
	and corresponding magnitude errors """)

        ras = []
        decs = []
        mags = []
        magerrs = []
        for hdu in goodhdus:
            ra, dec, mag, magerr = [
                hdu.data[_] for _ in [raColName, decColName, magcol, emagcol]
            ]
            ras.append(ra)
            decs.append(dec)
            mags.append(mag)
            magerrs.append(magerr)
        ras, decs, mags, magerrs = [
            np.concatenate(_) for _ in [ras, decs, mags, magerrs]
        ]
    else:
        raise CalibException('Unknown file type')

    return (ras, decs, mags, magerrs)


def mapper(x):
    """
	Map -inf...inf to 0..1
	"""
    return np.arctan(x) * 1 / np.pi + 0.5


def mapperI(x):
    return np.tan((x - 0.5) * np.pi)


def sigmapper(x):
    return (x)**2 + 0.0001  # 0.01 is the minimum precision, LW changed to 0.0001


def sigmapperI(x):
    return (np.maximum(x - 0.0001, 0))**.5  # 0.01 is the minimum precision; LW changed to 0.0001


assert (sigmapperI(sigmapper(1)) == 1)
assert (math.fabs(mapperI(mapper(0.5)) - 0.5) < 1e-10)


#edat - errors in catalog; eobs - errors in obs
def func(p, res=None, edat=0, eobs=0):
    """
	Likelihood function
	"""
    A = p[0]
    frac = mapper(p[1])
    sig = sigmapper(p[2])
    res1 = res - A
    sig1 = (sig**2 + edat**2 + eobs**2)**0.5 ##LW added error-bar in observation; however can we then use the obs_error later and combine with the calib erro?
    npdf = 1 / sig1 / (2 * np.pi) ** 0.5 * \
     np.exp(-0.5 * ((res1) / sig1) ** 2)
    sig2 = 3.  # outlier          ###LW changed from 5 to 3
    noutpdf = 1 / sig2 / 2. * \
     np.exp(-np.abs(res1))

    like = np.log(frac * noutpdf + (1 - frac) * npdf + 1e-30)
    val = like.sum()
    if not np.isfinite(val):
        return -1e100
    return val


class Survey:
    def __init__(self, name, filters, query, fitsfoot=None):
        self.name = name
        self.filters = filters
        self.query = query
        self.fitsfoot = fitsfoot
        if self.fitsfoot is not None:
            datfoot, headfoot = pyfits.getdata(self.fitsfoot, header=True)
            self.nsidefoot = int(headfoot['NSIDE'])
            npix = 12 * self.nsidefoot**2
            assert (npix == len(datfoot))
            self.ipixesfoot = set(np.arange(npix)[datfoot > 0])

    def check_pos(self, ra, dec):
        # returns true if inside the footprint
        if self.fitsfoot is not None:
            cur_ipix = healpy.ang2pix(self.nsidefoot,
                                      np.deg2rad(90 - dec),
                                      np.deg2rad(ra),
                                      nest=True)
            cur_ipixes = healpy.get_all_neighbours(self.nsidefoot,
                                                   cur_ipix,
                                                   nest=True)

            cur_ipixes = list(cur_ipixes) + [cur_ipix]
            retval = any([_ in self.ipixesfoot for _ in cur_ipixes])
            return retval

        else:
            # if there is no footprint we always return true
            return True


class SurveyList(OrderedDict.OrderedDict):  # collections.OrderedDict):
    def add(self, x):
        self[x.name] = x


def do_survey(survey, obs_ra, obs_dec, match_dist, conn=None, useFilter=None):
    "Calibrate using a survey"

    razp = obs_ra[0]
    radelta = 180 - razp
    ramin, ramax = (((obs_ra + radelta) % 360 - radelta).min(),
                    ((obs_ra + radelta) % 360 - radelta).max())
    ramean = (ramin + ramax) * .5
    ramin, ramax, ramean = [(_ + 360) % 360 for _ in [ramin, ramax, ramean]]
    # put everyting between 0 and 360
    decmin, decmax = obs_dec.min(), obs_dec.max()
    decmean = (decmin + decmax) * .5

    surveyObj = si.surveys[survey]
    query = si.surveys[survey].query
    filters = si.surveys[survey].filters
    nmag = len(filters)

    if useFilter is not None:
        assert (useFilter in filters)
        filterPos = filters.index(useFilter)
        filters = [filters[filterPos]]
    curhash = {}
    [curhash.__setitem__(x, None) for x in filters]

    if not surveyObj.check_pos(ramean, decmean):
        return curhash

    res = sqlutil.get(str.format(query, **{'matchDist': match_dist}),
                      conn=conn,
                      preamb='set statement_timeout to 60000;')
    # put timeout to 60 sec

    assert (len(res) == (2 + 2 * nmag))
    obs_mag, obs_emag = res[0:2]
    cat_mags = res[2:nmag + 2]
    cat_emags = res[2 + nmag:2 + 2 * nmag]

    if useFilter is not None: 
        cat_mags = (cat_mags[filterPos], )
        cat_emags = (cat_emags[filterPos], )

    if len(obs_mag) == 0:
        return curhash
    
    obs_mag_match = obs_mag
    obs_emag_match = obs_emag

    for ii, (curcat_mag, curcat_emag,
             curtit) in enumerate(zip(cat_mags, cat_emags, filters)):

        def linear_residuals(params, x, y, xe, ye):
            m, b = params
            y_pred = m * x + b
            residuals = (y - y_pred) / ye
            residuals = np.append(residuals, (x - xe) / xe)
            return np.sum(residuals**2)

        #special case test for DECAPS only first and only when not forced filter (because the filter list is trimmed earlier - TODO!)
        if ((surveyObj.name=="DECAPS" or surveyObj.name=="APASS") and useFilter is None):
            if (surveyObj.name=="DECAPS"):
                g_filterPos = filters.index("g")
                i_filterPos = filters.index("i")
                g_mags = cat_mags[g_filterPos]
                g_emags = cat_emags[g_filterPos]
                i_mags = cat_mags[i_filterPos]
                i_emags = cat_emags[i_filterPos]

            if (surveyObj.name=="APASS"):
                g_filterPos = filters.index("V")
                i_filterPos = filters.index("i")
                g_mags = cat_mags[g_filterPos]
                g_emags = cat_emags[g_filterPos]
                i_mags = cat_mags[i_filterPos]
                i_emags = cat_emags[i_filterPos]

            x=g_mags-i_mags
            xe=np.sqrt(i_emags*i_emags+g_emags*g_emags)
            y=i_mags-obs_mag
            ye=np.sqrt(i_emags*i_emags+obs_emag*obs_emag)

            validInd = np.isfinite(y) & np.isfinite(ye) & np.isfinite(x) & np.isfinite(xe) &\
              (ye < 0.5) & (xe < 0.5)

            params0 = [-1.0, 0.0]
            res = scipy.optimize.minimize(linear_residuals, params0, args=(x[validInd],y[validInd],xe[validInd],ye[validInd]), method='Nelder-Mead')['x']

            color_slope=res[0]
            color_shift=res[1]

            #shifting observations by fitted colorterm
            #and continuing the ZP finding 

#            y-x*color_slope
            new_obs = obs_mag[validInd]+color_slope*x[validInd]
            new_obs_e = obs_emag[validInd] ##ignoring color_slope error and (g-r) error-bars
            curcat_mag = curcat_mag[validInd]
            curcat_emag = curcat_emag[validInd]

            obs_mag_match = new_obs
            obs_emag_match = new_obs_e

        #AFTER COLORS:
        validInd = np.isfinite(curcat_mag) & np.isfinite(curcat_emag) & \
         (curcat_emag < CalibConfig.maxCatErr)

        delta = obs_mag_match[validInd] - curcat_mag[validInd]
        _curedat = curcat_emag[validInd]
        _obs_errors = obs_emag_match[validInd]

        def curlike(p, *args):
            val = -func(p, res=delta, edat=_curedat, eobs=_obs_errors)
            return val


        cen0 = np.median(delta)
        mad = 1.68 * np.median(np.abs(delta - cen0))
        outfrac0 = ((np.abs(delta - cen0) > 3 * mad).astype(int) * 1.).mean()
        outfrac0 = np.minimum(outfrac0, 0.5)
        p0 = [cen0, mapperI(outfrac0), sigmapperI(mad)]
        retx = scipy.optimize.minimize(curlike, p0, method='Nelder-Mead')['x']
        A = retx[0]
        frac = mapper(retx[1])
        sig = sigmapper(retx[2])

        curhash[curtit] = CalibResults(zp=A,
                                       fracOut=frac,
                                       scatter=sig,
                                       cmag=curcat_mag[validInd],
                                       omag=obs_mag_match[validInd])
    return curhash


class si:
    surveys = SurveyList()
    surveys.add(
        Survey('SDSS', ['u', 'g', 'r', 'i', 'z', 'B', 'V', 'R', 'I'],
               """
		with  x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							sdssdr9.phototag as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag, magerr, psfmag_u, psfmag_g, psfmag_r, psfmag_i, psfmag_z,
			psfmag_g+0.313*(psfmag_g-psfmag_r)+0.219,
			psfmag_g-0.566*(psfmag_g-psfmag_r)-0.016,
			psfmag_r-0.153*(psfmag_r-psfmag_i)-0.117,
			psfmag_i-0.386*(psfmag_i-psfmag_z)-0.397,
		psfmagerr_u, psfmagerr_g, psfmagerr_r, psfmagerr_i, psfmagerr_z,
			psfmagerr_g^2+(0.313^2*(psfmagerr_g^2+psfmagerr_r^2)),
			psfmagerr_g^2+(0.566^2*(psfmagerr_g^2+psfmagerr_r^2)),
			psfmagerr_r^2+(0.153^2*(psfmagerr_r^2+psfmagerr_i^2)),
			psfmagerr_i^2+(0.386^2*(psfmagerr_i^2+psfmagerr_z^2))
			from x			where type=6 and mode=1		""",
               fitsfoot='foots/sdssdr9.phototag.fits'))
    # magnitude transformations come from
    # http://www.sdss.org/dr6/algorithms/sdssUBVRITransform.html
    # Jordi et al 2006
    # surveys.add(
    #     Survey(
    #         'USNO', ['B1pg', 'B2pg', 'R1pg', 'R2pg', 'Ipg'], """
	# 	with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
	# 						usnob1.main as p
	# 				where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
	# 	select mag,magerr, b1mag, b2mag, r1mag, r2mag, imag,
	# 			0.1, 0.1, 0.1, 0.1, 0.1
	# 		from x;
	# 		"""))
    surveys.add(
        Survey(
            'APASS', ['B', 'V', 'g', 'r', 'i'], """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							apassdr9.main as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag,magerr, bjmag, vjmag, gmag, rmag, imag,
				ebjmag, evjmag, egmag, ermag,eimag
		from x;
		"""))
    surveys.add(
        Survey(
            'GAIA', ['G'], """
		with x as materialized (select m.mag,m.magerr,p. phot_g_mean_mag,
					p.phot_g_mean_flux,p.phot_g_mean_flux_error
						 from curmatch as m, 
							gaia_edr3.gaia_source as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag,magerr, phot_g_mean_mag,2.5*log(exp(1))*phot_g_mean_flux_error/phot_g_mean_flux 
		from x;
		"""))
    surveys.add(
        Survey('VSTATLAS', ['u', 'g', 'r', 'i', 'z'],
               """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							vst_1512.atlas_main as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag,magerr, mag_u,mag_g,mag_r,mag_i,mag_z,
				mag_err_u,mag_err_g,mag_err_r,mag_err_i,mag_err_z
		from x where classification_g=-1 and classification_r=-1;
		""",
               fitsfoot='foots/vst_1512.atlas_main.fits'))
    surveys.add(
        Survey(
            '2MASS', ['J', 'H', 'K'], """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							twomass.psc as p
					where q3c_join(m.ra,m.dec,p.ra,p.decl,{matchDist}))
		select mag,magerr,j_m, h_m, k_m, j_cmsig, h_cmsig, k_cmsig
		from x;
	 """))
    surveys.add(
        Survey('OGLE3', ['V', 'I'],
               """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							ogle3.main as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag,magerr, vmag, imag, vsig, isig
		from x;
	 """,
               fitsfoot='foots/ogle3.main.fits'))
    surveys.add(
        Survey(
            'PS1', ['g', 'r', 'i', 'z'], """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							panstarrs_dr1.stackobjectthin as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag, magerr, gpsfmag, rpsfmag, ipsfmag , zpsfmag,
		gpsfmagerr, rpsfmagerr, ipsfmagerr,  zpsfmagerr
		from x;
		"""))
    surveys.add(
        Survey('DECAPS', ['g', 'r', 'i', 'z'],
               """
		with x as materialized (select m.mag,m.magerr,p.* from curmatch as m, 
							decaps_dr1.main as p
					where q3c_join(m.ra,m.dec,p.ra,p.dec,{matchDist}))
		select mag,magerr,
-2.5*log(nullif(greatest(mean_g,0),0)) as mag_g, 
-2.5*log(nullif(greatest(mean_r,0),0)) as mag_r, 
-2.5*log(nullif(greatest(mean_i,0), 0)) as mag_i, 
-2.5*log(nullif(greatest(mean_z,0), 0)) as mag_z,
2.5/ln(10)*nullif(err_g,0)/nullif(mean_g,0) as err_g,
2.5/ln(10)*nullif(err_r,0)/nullif(mean_r,0) as err_r, 
2.5/ln(10)*nullif(err_i,0)/nullif(mean_i,0) as err_i,
2.5/ln(10)*nullif(err_z,0)/nullif(mean_z,0) as err_z
		from x;
		""",
               fitsfoot='foots/decaps_dr1.main.fits'))


def quality_check(frac, sig, npoints):
    return (frac < CalibConfig.maxOutlFrac and npoints >= CalibConfig.minPoints
            and sig < CalibConfig.minPrecision)


def doit(fname,
         ra0=None,
         dec0=None,
         match_dist=2. / 3600,
         conn=None,
         useSurvey=None,
         useFilter=None,
         noPlot=False,
         forceType=None,
         imageFormat='png'):
    """
	Perform the calibration of the catalog using all the surveys
	"""

    time1 = time.time()
    outname = StringIO()
    ra, dec, mag, magerr = getdata(fname, forceType=forceType)
    sqlutil.upload('curmatch', (ra, dec, mag, magerr),
                   ('ra', 'dec', 'mag', 'magerr'),
                   conn=conn,
                   noCommit=True,
                   temp=True,
                   analyze=True)
    calibhash = {}

    if useSurvey is None:
        surveys = si.surveys.keys()
    elif useSurvey == 'any':
        surveys = []
        for curs in si.surveys.keys():
            if useFilter in si.surveys[curs].filters:
                surveys.append(curs)
        if len(surveys) == 0:
            raise CalibException('Unknown filter')
    else:
        assert (useSurvey in si.surveys)
        surveys = [useSurvey]

    try:
        for curname in surveys:
            if useSurvey == 'any':
                if useFilter not in si.surveys[curname].filters:
                    continue
            curhash = do_survey(curname,
                                ra,
                                dec,
                                match_dist,
                                conn=conn,
                                useFilter=useFilter)
            calibhash[curname] = curhash
    except:
        raise

    sigbest = 10000
    info = {'status': -1}

    ntotgood = 0
    statusDict = OrderedDict.OrderedDict()

    for curname in surveys:
        cursur = si.surveys[curname]

        if useFilter is not None:
            filterIter = [useFilter]
        else:
            filterIter = cursur.filters
        for curf in filterIter:
            val = calibhash[curname][curf]
            if val is None:
                continue

            zp, frac, sig, cmag, omag = (val.zp, val.fracOut, val.scatter,
                                         val.cmag, val.omag)
            npoints = len(cmag)
            isgood = quality_check(frac, sig, npoints)
            ntotgood += int(isgood)
            # print sig, frac, npoints
            if sig < sigbest and isgood:
                sigbest = sig
                info = {
                    'zp': zp,
                    'fracOut': frac,
                    'scatter': sig,
                    'survey': curname,
                    'filter': curf,
                    'npoints': npoints,
                    'status': 0
                }
            if isgood:
                statusDict[curname, curf] = 0

    if info['status'] == 0:  # good status
        statusDict[info['survey'], info['filter']] = 1

    if not noPlot:
        ntotgood = max(1, ntotgood)  # do not allow zeros

        ncolsplot = 6
        nrowsplot = int(math.ceil(int(ntotgood) * 1. / ncolsplot))

        # plotting
        hspace = 0.35
        wspace = 0.3
        left = 0.2
        right = 0.2
        top = 0.2
        bottom = 0.2
        plotbox = 1.8
        figheight = (plotbox * nrowsplot + hspace * (nrowsplot - 1) + top +
                     bottom)
        figwidth = (plotbox * ncolsplot + wspace * (ncolsplot - 1) + left +
                    right)
        figsize = (figwidth, figheight)

        fig = plt.figure(1, figsize=figsize)
        fig.set_size_inches(figsize)
        plt.clf()

        igood = 0
        for (curname, curf), curStatus in statusDict.items():
            val = calibhash[curname][curf]

            if val is None:
                continue

            zp, frac, sig, cmag, omag = (val.zp, val.fracOut, val.scatter,
                                         val.cmag, val.omag)
            npoints = len(cmag)

            igood += 1
            plt.subplot(nrowsplot, ncolsplot, igood)
            xr = [
                cmag.min() - 0.5,
                cmag[cmag < CalibConfig.goodMaxMag].max() + 0.5
            ]
            yr = [
                omag.min() - 0.5,
                omag[omag < CalibConfig.goodMaxMag].max() + 0.5
            ]
            xr[1] = xr[0] + max(xr[1] - xr[0], yr[1] - yr[0])
            yr[1] = yr[0] + max(xr[1] - xr[0], yr[1] - yr[0])

            xs = np.linspace(min(xr[0], yr[0]), max(xr[1], yr[1]))
            plt.plot(xs, xs + zp, color='grey', alpha=0.85)
            plt.plot(xs, xs + zp + sig, '--', color='grey', alpha=0.85)
            plt.plot(xs, xs + zp - sig, '--', color='grey', alpha=0.85)

            plt.plot(cmag, omag, '.', color='blue', alpha=0.15)
            if curStatus == 1:
                titcolor = 'red'
            else:
                titcolor = 'black'
            plt.plot(xs, xs + zp, color='black')

            plt.title(r'%s %s ZP = %.2f $\sigma$ = %.2f $f_{outl}$ = %.2f' %
                      (curname, curf, zp, sig, frac),
                      color=titcolor)

            plt.gca().set_xlim(xr[0], xr[1])
            plt.gca().set_ylim(yr[0], yr[1])
            plt.gca().minorticks_on()
        plt.subplots_adjust(bottom=bottom / figheight,
                            top=1 - (top / figheight),
                            left=left / figwidth,
                            right=1 - (right / figwidth),
                            wspace=wspace / plotbox,
                            hspace=hspace / plotbox)
        plt.savefig(outname, format=imageFormat)
        del fig

    if ra0 is not None and info['status'] == 0:
        dist = sphdist.sphdist(ra, dec, ra0, dec0)
        mindist = dist.min()
        ind = dist == mindist
        if mindist < match_dist:
            outmag = float(mag[ind]) - info['zp']
            outmagerr = float(magerr[ind])
            outres = [outmag, outmagerr]
        else:
            # upper limit
            outmag = (mag[mag < CalibConfig.goodMaxMag]).max() - info['zp']
            outmagerr = -1
            outres = [outmag, outmagerr]
    else:
        outres = [None, None]
    time2 = time.time()
    info['deltat'] = time2 - time1
    # print info
    return info, outname.getvalue(), outres


def check_wcs(fname):
    try:
        from urllib2 import urlopen
    except:
        from urllib.request import urlopen
    import sphdist
    import aplpy
    survey = 'all'
    ra, dec, mag, magerr = getdata(fname)
    ramin = ra.min()
    ramax = ((ra - ramin) % 360 + ramin).max()
    decmin = dec.min()
    decmax = dec.max()
    racen = .5 * (ramin + ramax)
    deccen = .5 * (decmin + decmax)
    radius = max(sphdist.sphdist(ra, dec, racen, deccen)) * 60 * 2
    # in arcmin
    url = 'http://archive.stsci.edu/cgi-bin/dss_search?v=%s&r=%fd&d=%fd&e=J2000&h=%f&w=%f&f=fits&c=none&fov=NONE&v3=' % (
        survey, racen, deccen, radius, radius)
    response = urlopen(url)
    html = response.read()
    f = StringIO(html)
    dat = pyfits.open(f)
    plt.clf()
    gc = aplpy.FITSFigure(dat, figure=plt.gcf())
    #gc.set_tick_labels_format('ddd.dddd', 'ddd.dddd')
    gc.show_grayscale()
    gc.show_markers(ra, dec)
    return gc
