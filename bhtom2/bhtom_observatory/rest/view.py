from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import views
from django.core import serializers

import logging
from django.db.models import Q

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom2.bhtom_observatory.rest.serializers import ObservatorySerializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class GetObservatoryApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ObservatorySerializers

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'prefix': openapi.Schema(type=openapi.TYPE_STRING),
                'lon': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lat': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'active_flg': openapi.Schema(type=openapi.TYPE_BOOLEAN, format=openapi.FORMAT_INT32),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            },
            required=[]
        ),
    )
    def post(self, request):
        query = Q()

        name = self.request.data.get('name', None)
        prefix = self.request.data.get('prefix', None)
        lon = self.request.data.get('lon', None)
        lat = self.request.data.get('lat', None)
        active_flg = self.request.data.get('active_flg', None)
        created_start = self.request.data.get('created_start', None)
        created_end = self.request.data.get('created_end', None)

        if name is not None:
            query &= Q(name=name)
        if prefix is not None:
            query &= Q(prefix=prefix)
        if lon is not None:
            query &= Q(lon=lon)
        if lat is not None:
            query &= Q(lat=lat)
        if active_flg is not None:
            query &= Q(active_flg=active_flg)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = Observatory.objects.filter(query).order_by('created')
        serialized_queryset = serializers.serialize('json', queryset)
        return Response(serialized_queryset, status=200)


class CreateObservatoryApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'lon': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lat': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'calibration_flg': openapi.Schema(type=openapi.TYPE_BOOLEAN, format=openapi.FORMAT_INT32),
                'example_file': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'altitude': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'gain': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'readout_noise': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'binning': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'saturation_level': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'pixel_scale': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'readout_speed': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'pixel_size': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'approx_lim_mag': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'filters': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['name', 'lon', 'lat']
        )
    )
    def post(self, request, *args, **kwargs):
        serializer = ObservatorySerializers(data=request.data)
        if serializer.is_valid():

            calibration_flg = request.data.get('calibration_flg', False)
            name = request.data['name']

            if calibration_flg is True:
                prefix = name + "_CalibrationOnly"
            else:
                prefix = name

            instance = serializer.create(serializer.data)
            instance.user = request.user
            instance.prefix = prefix
            instance.save()
            return Response({'Status': 'created'}, status=201)
        return Response(serializer.errors, status=404)


class UpdateObservatoryApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'lon': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lat': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'calibration_flg': openapi.Schema(type=openapi.TYPE_BOOLEAN, format=openapi.FORMAT_INT32),
                'example_file': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'altitude': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'gain': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'readout_noise': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'binning': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'saturation_level': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'pixel_scale': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'readout_speed': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'pixel_size': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'approx_lim_mag': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'filters': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['name']
        )
    )
    def patch(self, request):

        name = request.data.get('name', None)
        instance = Observatory.objects.get(name=name)
        serializer = ObservatorySerializers(instance, data=request.data, partial=True)

        if instance is not None:
            if request.user == instance.user and serializer.is_valid():
                serializer.save()
                return Response({'Status': 'updated'}, status=201)
        return Response(serializer.errors, status=404)


class GetObservatoryMatrixApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_STRING),
                'active_flg': openapi.Schema(type=openapi.TYPE_BOOLEAN, format=openapi.FORMAT_INT32),
                'observatory': openapi.Schema(type=openapi.TYPE_STRING),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            },
            required=[]
        ),
    )
    def post(self, request):
        query = Q()

        user = self.request.data.get('user', None)
        active_flg = self.request.data.get('active_flg', None)
        observatory = self.request.data.get('observatory', None)
        created_end = self.request.data.get('created_end', None)
        created_start = self.request.data.get('created_start', None)

        if user is not None:
            query &= Q(user=user)
        if active_flg is not None:
            query &= Q(active_flg=active_flg)
        if observatory is not None:
            query &= Q(observatory=observatory)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = ObservatoryMatrix.objects.filter(query).order_by('created')
        serialized_queryset = serializers.serialize('json', queryset)
        return Response(serialized_queryset, status=200)


class CreateObservatoryMatrixApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'observatory': openapi.Schema(type=openapi.TYPE_STRING),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['observatory']
        ),
    )
    def post(self, request, *args, **kwargs):
        observatoryName = request.data.get('observatory', None)

        if observatoryName is None:
            return Response("Observatory is required", status=404)

        observatoryRow = Observatory.objects.get(name=observatoryName)

        if not observatoryRow.active_flg:
            return Response("Observatory is not active", status=404)

        try:
            observatory = ObservatoryMatrix(
                user=request.user,
                observatory=observatoryRow,
                active_flg=True
            )
            observatory.save()
        except Exception as e:
            logger.error("Error in create user observatory: " + str(e))

        return Response({"Status": "Created"}, status=201)


class DeleteObservatoryMatrixApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'observatory': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['observatory']
        ),
    )
    def delete(self, request):
        observatory = request.data.get('observatory', None)
        user = request.user
        observatory = Observatory.objects.get(name=observatory)

        if observatory is None:
            return Response("Observatory not found", status=404)

        observatoryMatrix = ObservatoryMatrix.objects.get(observatory=observatory.id, user=user)

        if observatoryMatrix is not None and user == observatoryMatrix.user:
            observatoryMatrix.delete()
            return Response({"Status": "deleted"}, status=200)
        return Response("Observatory not found", status=404)
