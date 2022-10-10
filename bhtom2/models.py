from django.contrib.auth.models import User
from django.db import models

from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum
from bhtom_base.bhtom_targets.models import Target


class Observatory(models.Model):
    """
    User-defined observatory
    """

    name = models.CharField(max_length=255, verbose_name='Observatory name', unique=True)
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    longitude = models.FloatField(null=False, blank=False, verbose_name='Longitude (West is positive) [deg]')
    latitude = models.FloatField(null=False, blank=False, verbose_name='Latitude (North is positive) [deg]')
    altitude = models.FloatField(null=False, blank=False, default=0.0, verbose_name="Altitude [m]")
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website)")
    verified = models.BooleanField(default='False')


class Instrument(models.Model):
    """
    User-defined instrument
    """

    MATCHING_RADIUS = [
        ('0.5', '0.5 arcsec'),
        ('1', '1 arcsec'),
        ('2', '2 arcsec'),
        ('4', '4 arcsec'),
        ('6', '6 arcsec')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    observatory = models.ForeignKey(Observatory, on_delete=models.CASCADE)
    verified = models.BooleanField(default='True')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, camera specifications, telescope info)")

    matchDist = models.CharField(max_length=10, choices=MATCHING_RADIUS, default='2',
                                 verbose_name='Matching radius')

    gain = models.FloatField(null=False, blank=False,
                             verbose_name='Gain [e/ADU]', default=2)
    readout_noise = models.FloatField(null=False, blank=False,
                                      verbose_name='Readout Noise [e]', default=2)
    binning = models.IntegerField(null=False, blank=False, default=1)
    saturation_level = models.FloatField(null=False, blank=False,
                                         verbose_name='Saturation Level [ADU]', default=63000)
    pixel_scale = models.FloatField(null=False, blank=False,
                                    verbose_name='Pixel Scale [arcseconds/pixel]', default=0.8)
    readout_speed = models.FloatField(verbose_name='Readout Speed [microseconds/pixel]',
                                      default=9999.0)
    pixel_size = models.FloatField(verbose_name='Pixel size [micrometers]', default=13.5)
    approx_lim_mag = models.FloatField(verbose_name="Approximate limit magnitude [mag]",
                                       default=18.0)
    filters = models.CharField(max_length=100, blank=True,
                               verbose_name="Filters (comma-separated list, as they are visible in FITS)",
                               default="V,R,I")

    obs_info_file = models.FileField(upload_to='uploads/obs_info', null=True, blank=False, verbose_name='Obs Info')
    sample_fits = models.FileField(upload_to='uploads/sample_fits', null=False, blank=False,
                                   verbose_name='Sample FITS file')

    def __str__(self):
        return self.user.username
