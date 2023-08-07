from django.views.generic.edit import FormView
from django.urls import reverse
from urllib.parse import urlencode
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from bhtom2.bhtom_calibration.models import catalogs

from .forms import CatalogQueryForm
from bhtom_base.bhtom_catalogs.harvester import MissingDataException
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class CatalogQueryView(FormView):
    """
    View for querying a specific catalog.
    """

    form_class = CatalogQueryForm
    template_name = 'bhtom_catalogs/query_form.html'

    def form_valid(self, form):
        """
        Ensures that the form parameters are valid and runs the catalog query.

        :param form: CatalogQueryForm with required parameter`s
        :type form: CatalogQueryForm
        """
        try:
            #harvester might return a dictionary of extras
            self.target, self.ex = form.get_target()
#            print("extras from harvester: ",self.ex)  

        except MissingDataException:
            form.add_error('term', ValidationError('Object not found'))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects to the ``TargetCreateView``. Appends the target parameters to the URL as query parameters in order to
        autofill the ``TargetCreateForm``, including any additional names returned from the query.
        """
        target_params = self.target.as_dict()
        target_params['names'] = ','.join(getattr(self.target, 'extra_names', []))
        return reverse('targets:create') + '?' + urlencode(target_params)+'&'+urlencode(self.ex)

class GetCatalogsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            instance = catalogs.objects.all().values('filters')
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"Catalogs": instance}, status=status.HTTP_200_OK)
