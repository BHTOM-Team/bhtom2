from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from bhtom_base.bhtom_targets.models import Target
from django.conf import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.mail import send_mail
from bhtom2.bhtom_observatory.models import Observatory

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: Signals')


@receiver(pre_save, sender=Target)
def target_pre_save(sender, instance, *args, **kwargs):
    pass


@receiver(pre_save, sender=User)
def send_activation_email(sender, instance, **kwargs):
    try:
        user_old = User.objects.get(id=instance.id)
    except Exception as e:
        user_old = None
        logger.error('Activate user error: ' + str(e))

    if user_old is not None:
        if instance.is_active and not user_old.is_active:
            try:
                send_mail(settings.EMAILTET_ACTIVATEUSER_TITLE, settings.EMAILTET_ACTIVATEUSER, settings.EMAIL_HOST_USER,
                      [instance.email], fail_silently=False)
                logger.info('Activate user' + instance.name + ', Send mail: ' + instance.email)
            except Exception as e:
                logger.error('Activate user error: ' + str(e))


@receiver(pre_save, sender=Observatory)
def Observatory_pre_save(sender, instance, **kwargs):
    try:
        observatory_old = Observatory.objects.get(id=instance.pk)
    except Observatory.DoesNotExist:
        observatory_old = None

    if observatory_old is not None:
        if observatory_old.active_flg is False and instance.active_flg is True and observatory_old.user_id is not None:
            try:
                user = User.objects.get(id=observatory_old.user_id)
                send_mail(settings.EMAILTEXT_ACTIVATEOBSERVATORY_TITLE, settings.EMAILTEXT_ACTIVATEOBSERVATORY,
                          settings.EMAIL_HOST_USER,
                          [user.email], fail_silently=False)
                logger.info('Activate observatory' + instance.name + ', Send mail: ' + user.email)
            except Exception as e:
                logger.info('Activate observatory error: ' + str(e))
