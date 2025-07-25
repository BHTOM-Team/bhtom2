import difflib

import bleach
import html
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
import re
import os

from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_observatory-model')


def sanitize_folder_name(name):
    # Replace special characters with underscores
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)

def sanitize_file_name(name):
    name_without_extension, extension = os.path.splitext(name)
    sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', name_without_extension)
    cleaned_name = bleach.clean(sanitized_name, tags=[], attributes={}, protocols=[], strip=True)
    return cleaned_name + extension

def example_file_path(instance, filename):
    return 'fits/exampleObservatoryFile/{0}/{1}'.format(sanitize_folder_name(instance.camera_name),
                                                        sanitize_file_name(filename))

class CleanData(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        char_fields = [field for field in self._meta.get_fields() if isinstance(field, (models.CharField, models.TextField))]

        for char_field in char_fields:
            field_value = getattr(self, char_field.name)
            if field_value is not None:
                value = field_value.replace('\r', '')
                escaped_value = html.escape(value)
                cleaned_value = bleach.clean(escaped_value, tags=[], attributes={}, protocols=[], strip=True)
                if escaped_value != cleaned_value:
                    output_list = [li for li in difflib.ndiff(escaped_value, cleaned_value) if li[0] != ' ']
                    logger.debug(f"Field '{char_field}' changed from '{field_value}' to '{cleaned_value}', {output_list}")
                    raise ValidationError(f"Invalid data format. Field: '{char_field.verbose_name}', Invalid chars: {output_list}.")

class Observatory(CleanData):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name='Observatory name', unique=True)
    lon = models.FloatField(null=False, blank=False, verbose_name='Longitude (East is positive) [deg]',
                            validators=[
                                MinValueValidator(-180.0, message="longitude must be greater than -180."),
                                MaxValueValidator(180.0, message="longitude must be less than 180.")
                            ], db_index=True)
    lat = models.FloatField(null=False, blank=False, verbose_name='Latitude (North is positive) [deg]',
                            validators=[
                                MinValueValidator(-180.0, message="latitude must be greater than -90."),
                                MaxValueValidator(180.0, message="latitude must be less than 90.")
                            ], db_index=True)
    altitude = models.FloatField(null=True, blank=False, default=0.0, verbose_name="Altitude [m]")
    calibration_flg = models.BooleanField(default='False', verbose_name='Only instrumental photometry file',
                                          db_index=True)
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. camera specifications, telescope info)")
    approx_lim_mag = models.FloatField(null=True, verbose_name="Approximate limit magnitude [mag]", default=18.0)
    filters = models.CharField(null=True, max_length=100, blank=True,
                               verbose_name="Filters (comma-separated list, as they are visible in " "FITS)",
                               default="V,R,I")
    authors = models.CharField(max_length=255, blank=True, null=True, verbose_name='Authors')
    acknowledgements =  models.CharField(max_length=255, blank=True, null=True, verbose_name='Acknowledgements')
    origin = models.CharField(max_length=255, blank=True, null=True, verbose_name='Origin')
    telescope = models.CharField(max_length=255, blank=True, null=True, verbose_name='Telescope name')
    aperture = models.FloatField(null=True, blank=True, default=0.0, verbose_name="Aperture [m]")
    focal_length = models.FloatField(null=True, blank=False, default=0.0, verbose_name="Focal length [mm]")
    seeing = models.FloatField(null=True, blank=True, default=0.0)
    created = models.DateTimeField(null=True, blank=False, editable=False, auto_now_add=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, editable=True, auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "observatories"
        unique_together = (('name', 'lon', 'lat'),)


class Camera(CleanData):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    observatory = models.ForeignKey(Observatory, on_delete=models.CASCADE, null=False)
    camera_name = models.CharField(max_length=255, verbose_name='Camera name', null=False)
    active_flg = models.BooleanField(default='False', db_index=True)
    prefix = models.CharField(max_length=100, null=True, blank=True, unique=True)
    gain = models.FloatField(null=True, blank=False, verbose_name='Gain [e/ADU]', default=2)
    example_file = models.FileField(upload_to=example_file_path, null=True, blank=False, verbose_name='Sample fits')
    readout_noise = models.FloatField(null=True, blank=False, verbose_name='Readout Noise [e]', default=2)
    binning = models.IntegerField(null=True, blank=False, default=1)
    saturation_level = models.FloatField(null=True, blank=False, verbose_name='Saturation Level [ADU]', default=63000)
    pixel_scale = models.FloatField(null=True, blank=False, verbose_name='Pixel Scale [arcseconds/pixel]', default=0.8)
    readout_speed = models.FloatField(null=True, verbose_name='Readout Speed [microseconds/pixel]', default=9999.0)
    pixel_size = models.FloatField(null=True, verbose_name='Pixel size [micrometers]', default=13.5)
    date_time_keyword = models.CharField(max_length=255, verbose_name='Date & Time keyword', default="DATE-OBS")
    time_keyword = models.CharField(max_length=255, verbose_name='Time keyword', default="TIME-OBS")
    exposure_time_keyword = models.CharField(max_length=255, verbose_name='Exposure time keyword', default="EXPTIME")
    mode_recognition_keyword = models.CharField(max_length=255, verbose_name='Mode recognition keyword name', null=True,
                                                blank=True, default='')
    additional_info = models.TextField(verbose_name='Additional info', null=True, blank=True, default='')
    created = models.DateTimeField(null=True, blank=False, editable=False, auto_now_add=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, editable=True, auto_now=True)

    def __str__(self):
        return self.prefix

    class Meta:
        verbose_name_plural = "cameras"
        unique_together = (('observatory', 'camera_name'),)

class ObservatoryMatrix(CleanData):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    active_flg = models.BooleanField(default='True')
    comment = models.TextField(null=True, blank=True,
                               verbose_name="Comments (e.g. hyperlink to the observatory website, camera "
                                            "specifications, telescope info)")
    created = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, editable=True, auto_now_add=True)
    number_of_uploaded_file = models.IntegerField(editable=True, default=0)
    file_size = models.FloatField(editable=True, default=0)
    last_file_process = models.DateTimeField(null=True, blank=True, editable=True)

    def __str__(self):
        return self.camera.observatory.name

    class Meta:
        verbose_name_plural = "observatory matrix"
        unique_together = (('user', 'camera'),)
