from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User


def example_file_path(instance, filename):
    return 'exampleObservatoryFile/{0}/{1}'.format(instance.name, filename)


class Observatory(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name='Observatory name', unique=True)
    lon = models.FloatField(null=False, blank=False, verbose_name='Longitude (West is positive) [deg]',
                            validators=[
                                MinValueValidator(-180.0, message="longitude must be greater than -180."),
                                MaxValueValidator(180.0, message="longitude must be less than 180.")
                            ], db_index=True)
    lat = models.FloatField(null=False, blank=False, verbose_name='Latitude (North is positive) [deg]',
                            validators=[
                                MinValueValidator(-180.0, message="latitude must be greater than -90."),
                                MaxValueValidator(180.0, message="latitude must be less than 90.")
                            ], db_index=True)
    calibration_flg = models.BooleanField(default='False', verbose_name='Only instrumental photometry file',
                                          db_index=True)
    prefix = models.CharField(max_length=100, null=True, blank=True)
    example_file = models.FileField(upload_to=example_file_path, null=True, blank=True, verbose_name='Sample fits')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, "
                                            "camera specifications, telescope info)")
    active_flg = models.BooleanField(default='False', db_index=True)
    altitude = models.FloatField(null=False, blank=False, default=0.0, verbose_name="Altitude [m]")
    gain = models.FloatField(null=False, blank=False, verbose_name='Gain [e/ADU]', default=2)
    readout_noise = models.FloatField(null=False, blank=False, verbose_name='Readout Noise [e]', default=2)
    binning = models.IntegerField(null=False, blank=False, default=1)
    saturation_level = models.FloatField(null=False, blank=False, verbose_name='Saturation Level [ADU]', default=63000)
    pixel_scale = models.FloatField(null=False, blank=False, verbose_name='Pixel Scale [arcseconds/pixel]', default=0.8)
    readout_speed = models.FloatField(verbose_name='Readout Speed [microseconds/pixel]', default=9999.0)
    pixel_size = models.FloatField(verbose_name='Pixel size [micrometers]', default=13.5)
    approx_lim_mag = models.FloatField(verbose_name="Approximate limit magnitude [mag]", default=18.0)
    filters = models.CharField(max_length=100, blank=True,
                               verbose_name="Filters (comma-separated list, as they are visible in " "FITS)",
                               default="V,R,I")
    created = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, editable=True, auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "observatories"
        unique_together = (('name', 'lon', 'lat'),)


class ObservatoryMatrix(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    observatory = models.ForeignKey(Observatory, on_delete=models.CASCADE)
    active_flg = models.BooleanField(default='True')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, camera "
                                            "specifications, telescope info)")
    created = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, editable=True, auto_now_add=True)
    number_of_uploaded_file = models.IntegerField(editable=True, default=0)
    last_file_process = models.DateTimeField(null=True, blank=True, editable=True)

    def __str__(self):
        return self.observatory.name

    class Meta:
        verbose_name_plural = "observatory matrix"
        unique_together = (('user', 'observatory'),)