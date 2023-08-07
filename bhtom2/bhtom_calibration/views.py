from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from bhtom2.bhtom_calibration.models import calibration_data
from django.core import serializers

class CalibrationResultsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        file_id = request.data['file_id']
        try:
            instance = calibration_data.objects.get(dataproduct_id=file_id)
            results = serializers.serialize('json', [ instance ])
        except calibration_data.DoesNotExist:
            return Response({"Error":'File does not exist in the database'},status=status.HTTP_400_BAD_REQUEST)

        return Response({"Result": results}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        return ret
