from django.db.models.signals import pre_save
from django.dispatch import receiver
from bhtom_base.bhtom_targets.models import Target
from django.conf import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.coordinate_utils import fill_galactic_coordinates
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from bhtom2.bhtom_observatory import Observatory

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: Signals')


@receiver(pre_save, sender=Target)
def target_pre_save(sender, instance, *args, **kwargs):
    pass


@receiver(post_save, sender=User)
def send_activation_email(sender, instance, **kwargs):
    if instance.is_active and kwargs.get('update_fields') == {'is_active'}:
        send_mail(settings.EMAILTET_ACTIVATEUSER_TITLE, settings.EMAILTET_ACTIVATEUSER, settings.EMAIL_HOST_USER,
                      [instance.email], fail_silently=False)

@receiver(post_save, sender=Observatory)
def Observatory_pre_save(sender, instance, **kwargs):
    try:
        observatory_old = Observatory.objects.get(id=instance.pk)
    except Observatory.DoesNotExist:
        observatory_old = None

    user_email = None
    if observatory_old is not None:
        if observatory_old.isVerified == False and instance.isVerified == True and instance.user is not None:
            try:
                user_email = User.objects.get(id=instance.user.id)
            except Exception as e:
                user_email = None
            if user_email is not None:
                send_mail(settings.EMAILTEXT_ACTIVATEOBSERVATORY_TITLE, settings.EMAILTEXT_ACTIVATEOBSERVATORY, settings.EMAIL_HOST_USER,
                      [instance.email], fail_silently=False)
                logger.info('Ativate observatory' + instance.obsName + ', Send mail: ' + user_email.email)


