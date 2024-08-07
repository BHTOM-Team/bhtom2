import logging
import datetime


from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.utils.access_utils import can_access
from django.http import HttpResponseForbidden

loggerRequest: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: request')
loggerResponse: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: response')

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('django_guid').setLevel(logging.WARNING)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        time1 = datetime.datetime.now()
        body = self.extract_request_body(request)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META['REMOTE_ADDR']

        loggerRequest.info(f"Method: {request.method}, Path: {request.path}, IP: {ip}, "
                           f"Correlation-ID: {request.correlation_id}, session_id: {request.session.session_key}, "
                           f"user: {request.user}, host: {request.META['HTTP_HOST']}, "
                           f"body: {body}")

        response = self.get_response(request)

        body = self.extract_response_body(response)

        time = datetime.datetime.now() - time1
        time = time.total_seconds()

        loggerResponse.info(f"Method: {request.method}, Path: {request.path}, IP: {ip}, "
                            f"Correlation-ID: {request.correlation_id}, session_id: {request.session.session_key}, "
                            f" user: {request.user}, host: {request.META['HTTP_HOST']}, "
                            f"time: {str(time)}, status code: {response.status_code}, body: {body}")

        return response

    def extract_request_body(self, request):
        # Extract and log the request body, excluding files
        if request.method in ['POST', 'PUT']:
            body = {}
            for key, value in request.POST.items():
                if key == 'password' or key == 'password1' or key == 'password2':
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
