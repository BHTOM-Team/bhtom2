from django.db.models.signals import pre_save
from django.dispatch import receiver
from bhtom_base.bhtom_targets.models import Target

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: Signals')


@receiver(pre_save, sender=Target)
def target_pre_save(sender, instance, *args, **kwargs):
    pass
