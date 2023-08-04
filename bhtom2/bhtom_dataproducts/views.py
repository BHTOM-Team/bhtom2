from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from rest_framework.views import APIView
from django.http import HttpResponse
import requests
from bhtom2.utils.bhtom_logger import BHTOMLogger
from django.conf import settings
from .forms import DataProductUploadForm


logger = BHTOMLogger(__name__, '[BHTOM2 views]')


class DataProductUploadView(LoginRequiredMixin, FormView):
    """
    View that handles manual upload of DataProducts. Requires authentication.
    """
    form_class = DataProductUploadForm

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if not settings.TARGET_PERMISSIONS_ONLY:
            if self.request.user.is_superuser:
                form.fields['groups'].queryset = Group.objects.all()
            else:
                form.fields['groups'].queryset = self.request.user.groups.all()
        return form

    def form_valid(self, form):
        """
        Runs after ``DataProductUploadForm`` is validated. Saves each ``DataProduct`` and calls ``run_data_processor``
        on each saved file. Redirects to the previous page.
        """
        # ... (remaining unchanged)

    def form_invalid(self, form):
        """
        Adds errors to Django messaging framework in the case of an invalid form and redirects to the previous page.
        """
        # ... (remaining unchanged)


class FitsUploadAPIView(APIView):
    def post(self, request):
        # Extract the POST data from the original request
        post_data = request.POST
        # Extract the authorization header from the original request
        authorization_header = request.headers.get('Authorization')

        # Set headers for the POST request to upload-service
        headers = {
            'Authorization': authorization_header,
        }

        # Make a POST request to upload-service with the extracted data
        response = requests.post(settings.UPLOAD_SERVICE_URL + 'upload/', data=post_data, files=request.FILES, headers=headers)

        return HttpResponse(response.content, status=response.status_code)

