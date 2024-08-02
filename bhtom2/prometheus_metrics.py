from django.http import HttpResponse
from prometheus_client import Counter, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

USER_REGISTRATION_COUNT = Counter('django_user_registration_total', 'Total user registrations')
USER_LOGIN_COUNT = Counter('django_user_login_total', 'Total user logins')
CAMERA_REGISTRATION_COUNT = Counter('django_camera_registration_total', 'Total camera registrations')
LAST_USER_LOGIN_TIME = Gauge('django_user_last_login_timestamp', 'Timestamp of the last user login')


def custom_metrics(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)