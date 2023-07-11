from django.db import models
from bhtom_base.bhtom_dataproducts.models import DataProduct


class Catalogs(models.Model):
    id = models.IntegerField(primary_key=True)
    survey = models.TextField(blank=False, editable=False)
    filters = models.TextField(blank=False, editable=False)
    isActive = models.BooleanField(default=True)


class cpcsData(models.Model):

    id = models.AutoField(db_index=True, primary_key=True)
    dataproduct_id = models.ForeignKey(DataProduct, on_delete=models.CASCADE)
    status_message = models.TextField(null=True, blank=True)
    mjd = models.FloatField(null=True, blank=True)
    expTime = models.FloatField(null=True, blank=True)
    mag = models.FloatField(null=True, blank=True)
    mag_error = models.FloatField(null=True, blank=True)
    ra = models.FloatField(null=True, blank=True)
    dec = models.FloatField(null=True, blank=True)
    zeropoint = models.FloatField(null=True, blank=True)
    outlier_fraction = models.FloatField(null=True, blank=True)
    scatter = models.FloatField(null=True, blank=True)
    npoints = models.IntegerField(null=True, blank=True)
    processing_time = models.DateTimeField(null=True, blank=True, editable=False)
    created = models.DateTimeField(null=True, blank=True, editable=False)
    modified = models.DateTimeField(null=True, blank=True, editable=True)
    best_filter = models.CharField(max_length=5, null=True, blank=True)
    match_distans = models.FloatField(default=0.5)
    useCatalog = models.ForeignKey(Catalogs, on_delete=models.CASCADE)
    noPlot = models.BooleanField(default=True)
    cpcsPlot = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'cpcs processing file'
        verbose_name_plural = "cpcsData"
