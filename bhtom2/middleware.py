import logging
import datetime

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.access_utils import can_access
from django.http import HttpResponseForbidden

logger: BHTOMLogger = BHTOMLogger(__name__, '[request, response]')
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('django_guid').setLevel(logging.WARNING)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        time1 = datetime.datetime.now()
        body = "".join(request.body.decode('utf-8').replace(' ', '').splitlines())
        body = (body[:75] + '..') if len(body) > 75 else body

        logger.info(f"Method: {request.method}, Path: {request.path}, IP: {request.META['REMOTE_ADDR']}, "
                    f"correlation_id: {request.correlation_id},  session_id: {request.session.session_key}, "
                    f"user: {request.user}, host: {request.META['HTTP_HOST']}, "
                    f"body: {body}")

        response = self.get_response(request)

        if hasattr(response, 'data'):
            body = response.data
            body = (body[:75] + '..') if len(body) > 75 else body
        else:
            body = ''
        time = datetime.datetime.now()-time1
        time = time.total_seconds()

        logger.info(f"uuid: {request.correlation_id}, Response - Status Code: {response.status_code}, time: {str(time)}" 
                    f" body: {body}")

        return response


class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not can_access(request):
            return HttpResponseForbidden("Access denied")
        response = self.get_response(request)
        return response