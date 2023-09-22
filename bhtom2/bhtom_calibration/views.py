from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from bhtom2.bhtom_calibration.models import Calibration_data
from django.core import serializers
from bhtom2.bhtom_calibration.models import Catalogs as calibration_catalog
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_calibration.views')


class CalibrationResultsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        file_id = request.data['file_id']
        try:
            instance = Calibration_data.objects.get(dataproduct_id=file_id)
            results = serializers.serialize('json', [instance])
        except Calibration_data.DoesNotExist:
            return Response({"Error": 'File does not exist in the database'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"Result": results}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        return ret


class GetCatalogsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            instance = calibration_catalog.objects.all().values('filters')
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"Catalogs": instance}, status=status.HTTP_200_OK)
