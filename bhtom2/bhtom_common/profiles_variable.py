from django.conf import settings


def profile_variable(request):
    return {
        'PROFILE': settings.PROFILE
    }
