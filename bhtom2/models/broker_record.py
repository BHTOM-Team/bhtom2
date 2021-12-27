from django.db import models


class BrokerRecord(models.Model):
    """
    Class representing a data broker - for storing observation facility and owner

    A DataProduct corresponds to any file containing data, from a FITS, to a PNG, to a CSV. It can optionally be
    associated with a specific observation, and is required to be associated with a target.

    :param product_id: The identifier of the data product used by its original source.
    :type product_id: str
    """

    name = models.CharField(max_length=255,
                            unique=True,
                            null=False,
                            help_text='Survey/broker name')
    facility_name = models.CharField(max_length=255,
                                     unique=False,
                                     null=False,
                                     help_text='Facility name - telescope, space observatory, etc.')
    observer_name = models.CharField(max_length=255,
                                     unique=False,
                                     null=False,
                                     help_text='Scientific group or individual observer\'s name')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
