from datetime import datetime
from django.db import models
from tom_targets.models import Target
from tom_dataproducts.models import DataProduct
from django_pgviews import view as pg


class ViewReducedDatum(pg.MaterializedView):
    """
    Optimization for the reduced data- a view is generated so that the data can be fetched quickly
    """
    concurrent_index = 'id'
    sql = """
        SELECT rd.id AS id,
        rd.target_id, rd.data_product_id, rd.data_type, rd.source_name, rd.timestamp, rd.value,
        dpobr.extra_data AS dp_extra_data,
        dpobr.obr_facility AS observation_record_facility
        FROM tom_dataproducts_reduceddatum AS rd
            LEFT JOIN (SELECT dp.id AS dp_id, dp.extra_data AS extra_data, obr.facility AS obr_facility
                FROM tom_dataproducts_dataproduct AS dp
                LEFT JOIN tom_observations_observationrecord AS obr ON dp.observation_record_id=obr.id) dpobr
                ON rd.data_product_id=dpobr.dp_id;

    """
    id = models.IntegerField(primary_key=True)
    target = models.ForeignKey(Target, null=False, on_delete=models.DO_NOTHING)
    data_product = models.ForeignKey(DataProduct, null=True, on_delete=models.DO_NOTHING)
    data_type = models.CharField(
        max_length=100,
        default=''
    )
    source_name = models.CharField(max_length=100, default='')
    timestamp = models.DateTimeField(null=False, blank=False, default=datetime.now, db_index=True)
    value = models.TextField(null=False, blank=False)
    # Data Product extra
    dp_extra_data = models.TextField(null=True, blank=True)
    observation_record_facility = models.TextField(null=True, blank=True)


def refresh_reduced_data_view():
    ViewReducedDatum.refresh(concurrently=True)
