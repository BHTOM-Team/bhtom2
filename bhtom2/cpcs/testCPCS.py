from bhtom2.external_service.connectWSDB import WSDBConnection
import numpy as np
import warnings
import astropy.io.ascii
import psycopg2
from io import StringIO

class TestCPCS(TestCase):

    # temp method for reading WSDB CPCS output
    def test_cpcs_query(self):

        fname = "/Users/wyrzykow/Downloads/obs.dat"
#        fname = "/Users/wyrzykow/Downloads/obs_AS_255_trim10k.dat"
        
        raColName = 'ALPHA_J2000'
        decColName = 'DELTA_J2000'
        _sex = astropy.io.ascii.sextractor.SExtractor()
        tab = _sex.read(fname)
        columns = [x for x in tab.columns]
        magcol, emagcol = select_mag(columns)
        if raColName not in columns or decColName not in columns:
            raise Exception(
                "Failed to find the columns with ra,dec named ALPHA_J2000,DELTA_J2000"
            )
        ra, dec = tab[raColName].data, tab[decColName].data
        mag = tab[magcol].data
        magerr = tab[emagcol].data

        WSDBConnection().doCalib((ra,dec,mag,magerr))

#         uploadQuery('curmatch', (ra, dec, mag, magerr),
#                    ('ra', 'dec', 'mag', 'magerr'),
#  #                  conn=conn,
#  #                  cur = cur,
#                    noCommit=True,
#                    temp=True,
#                    analyze=True)

#        conn.close()

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

