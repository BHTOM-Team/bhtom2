from django.db import models
from django.contrib.auth.models import User


class Observatory(models.Model):
    name = models.CharField(max_length=255, verbose_name='Observatory name', unique=True)
    lon = models.FloatField(null=False, blank=False, verbose_name='Longitude (West is positive) [deg]')
    lat = models.FloatField(null=False, blank=False, verbose_name='Latitude (North is positive) [deg]')
    altitude = models.FloatField(null=False, blank=False, default=0.0, verbose_name="Altitude [m]")
    cpcsOnly = models.BooleanField(default='False', verbose_name='Only instrumental photometry file')
    prefix = models.CharField(max_length=255, null=True, blank=True)
    example_file = models.FileField(upload_to='user_fits', null=False, blank=False, verbose_name='Sample fits')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, camera "
                                            "specifications, telescope info)")
    isActive = models.BooleanField(default='True')
    gain: models.FloatField = models.FloatField(null=False, blank=False, verbose_name='Gain [e/ADU]', default=2)
    readout_noise: models.FloatField = models.FloatField(null=False, blank=False, verbose_name='Readout Noise [e]',
                                                         default=2)
    binning: models.IntegerField = models.IntegerField(null=False, blank=False, default=1)
    saturation_level: models.FloatField = models.FloatField(null=False, blank=False,
                                                            verbose_name='Saturation Level [ADU]', default=63000)
    pixel_scale: models.FloatField = models.FloatField(null=False, blank=False,
                                                       verbose_name='Pixel Scale [arcseconds/pixel]', default=0.8)
    readout_speed: models.FloatField = models.FloatField(verbose_name='Readout Speed [microseconds/pixel]',
                                                         default=9999.0)
    pixel_size: models.FloatField = models.FloatField(verbose_name='Pixel size [micrometers]', default=13.5)
    approx_lim_mag: models.FloatField = models.FloatField(verbose_name="Approximate limit magnitude [mag]",
                                                          default=18.0)
    filters: models.CharField = models.CharField(max_length=100, blank=True,
                                                 verbose_name="Filters (comma-separated list, as they are visible in "
                                                              "FITS)",
                                                 default="V,R,I")
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created = models.DateTimeField(null=True, blank=True, editable=False)
    modified = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Obs info"


class ObservatoryMatrix(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    observatory_id = models.ForeignKey(Observatory, on_delete=models.CASCADE)
    isActive = models.BooleanField(default='True')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, camera "
                                            "specifications, telescope info)")

    def __str__(self):
        return self.user_id.username
