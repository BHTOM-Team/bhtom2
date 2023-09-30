import logging
import datetime

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.access_utils import can_access
from django.http import HttpResponseForbidden

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: request, response')
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('django_guid').setLevel(logging.WARNING)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        time1 = datetime.datetime.now()
        body = self.extract_request_body(request)

        logger.info(f"Method: {request.method}, Path: {request.path}, IP: {request.META['REMOTE_ADDR']}, "
                    f"correlation_id: {request.correlation_id}, session_id: {request.session.session_key}, "
                    f"user: {request.user}, host: {request.META['HTTP_HOST']}, "
                    f"body: {body}")

        response = self.get_response(request)

        body = self.extract_response_body(response)

        time = datetime.datetime.now() - time1
        time = time.total_seconds()

        logger.info(f"uuid: {request.correlation_id}, Response - Status Code: {response.status_code}, "
                    f"time: {str(time)} body: {body}")

        return response

    def extract_request_body(self, request):
        # Extract and log the request body, excluding files
        if request.method in ['POST', 'PUT']:
            body = {}
            for key, value in request.POST.items():
                if key == 'password':
                    body[key] = '*****'
                elif not isinstance(value, list):
                    body[key] = value
                else:
                    body[key] = value[0]  # If multiple values, just use the first one
            return body
        else:
            return ''

    def extract_response_body(self, response):
        # Extract and log the response body
        if hasattr(response, 'data'):
            return response.data
        else:
            return ''

class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not can_access(request):
            return HttpResponseForbidden("Access denied")
        response = self.get_response(request)
        return response