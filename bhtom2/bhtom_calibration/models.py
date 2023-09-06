from django.db import models
from bhtom_base.bhtom_dataproducts.models import DataProduct


class catalogs(models.Model):
    id = models.IntegerField(primary_key=True)
    survey = models.TextField(blank=False, editable=False)
    filters = models.TextField(blank=False, editable=False)
    isActive = models.BooleanField(default=True)


class calibration_data(models.Model):

    STATUS = [
        ('C', 'TO DO'),
        ('P', 'IN PROGRESS'),
        ('S', 'SUCCESS'),
        ('E', 'ERROR')
    ]

    id = models.AutoField(db_index=True, primary_key=True)
    dataproduct = models.ForeignKey(DataProduct, on_delete=models.CASCADE)
    use_catalog = models.ForeignKey(catalogs, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=1, choices=STATUS, default='C', db_index=True)
    status_message = models.TextField(null=True, blank=True)
    mjd = models.FloatField(null=False, blank=False)
    exp_time = models.FloatField(null=True, blank=True)
    mag = models.FloatField(null=True, blank=True)
    mag_error = models.FloatField(null=True, blank=True)
    ra = models.FloatField(null=True, blank=True)
    dec = models.FloatField(null=True, blank=True)
    zeropoint = models.FloatField(null=True, blank=True)
    outlier_fraction = models.FloatField(null=True, blank=True)
    scatter = models.FloatField(null=True, blank=True)
    npoints = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True, editable=False)
    modified = models.DateTimeField(null=True, blank=True, editable=True)
    start_processing = models.DateTimeField(null=True, blank=True, editable=True)
    best_filter = models.CharField(max_length=5, null=True, blank=True)
    survey = models.CharField(max_length=32, null=True, blank=True)
    match_distans = models.FloatField(default=0.5)
    no_plot = models.BooleanField(default=True)
    calibration_plot = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    number_tries = models.IntegerField(null=False, default=0)

    class Meta:
        verbose_name = 'cpcs processing file'
        verbose_name_plural = "calibration_data"
