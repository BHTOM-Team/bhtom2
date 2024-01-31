from django.db.models import Q
from django.http import Http404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from django.contrib.auth.models import User
from bhtom2.bhtom_targets.rest.serializers import TargetsSerializers, TargetDownloadDataSerializer
from bhtom2.bhtom_targets.utils import update_targetList_cache, update_targetDetails_cache
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_targets.models import Target
from rest_framework import status
import json
from django.conf import settings
from django.core import serializers
import os
from django.http import FileResponse
from bhtom2.utils.reduced_data_utils import save_photometry_data_for_target_to_csv_file, \
    save_radio_data_for_target_to_csv_file
from abc import ABC, abstractmethod

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.rest-view')

class GetTargetListApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'raMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'raMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'decMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'decMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'priority': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lastMag': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'sunDistance': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLat': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLon': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=[]
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request):
        query = Q()

        name = request.data.get('name', None)
        raMin = request.data.get('raMin', None)
        raMax = request.data.get('raMax', None)
        decMin = request.data.get('decMin', None)
        decMax = request.data.get('decMax', None)
        importance = request.data.get('importance', None)
        priority = request.data.get('priority', None)
        lastMag = request.data.get('lastMag', None)
        sunDistance = request.data.get('sunDistance', None)
        galacticLat = request.data.get('galacticLat', None)
        galacticLon = request.data.get('galacticLon', None)
        description = request.data.get('description', None)
        

        try:
            if name is not None:
                query &= Q(name=name)
            if raMin is not None:
                raMin = float(raMin)
                query &= Q(ra__gte=raMin)
            if raMax is not None:
                raMax = float(raMax)
                query &= Q(ra__lte=raMax)
            if decMin is not None:
                decMin = float(decMin)
                query &= Q(dec__gte=decMin)
            if decMax is not None:
                decMax = float(decMax)
                query &= Q(dec__lte=decMax)
            if importance is not None:
                importance = float(importance)
                query &= Q(importance=importance)
            if priority is not None:
                priority = float(priority)
                query &= Q(priority=priority)
            if lastMag is not None:
                lastMag = float(lastMag)
                query &= Q(mag_last=lastMag)
            if sunDistance is not None:
                sunDistance = float(sunDistance)
                query &= Q(sun_separation=sunDistance)
            if galacticLat is not None:
                galacticLat = float(galacticLat)
                query &= Q(galactic_lat=galacticLat)
            if galacticLon is not None:
                galacticLon = float(galacticLon)
                query &= Q(galactic_lng=galacticLon)
            if description is not None:
                query &= Q(description=description) 
        except ValueError as e:
            logger.error("Value error in targetList " + str(e))
            return Response("Wrong format", status=400)

        queryset = Target.objects.filter(query).order_by('created')
        serialized_queryset = serializers.serialize('json', queryset)
        return Response(serialized_queryset, status=200)


# this is API for SIDEREAL target creation, non-sidereal has to go to a different api
class TargetCreateApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'ra': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'dec': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'epoch': openapi.Schema(type=openapi.TYPE_NUMBER),
                'classification': openapi.Schema(type=openapi.TYPE_STRING),
                'discovery_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cadence': openapi.Schema(type=openapi.TYPE_NUMBER),
            },
            required=['name', 'ra', 'dec']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = TargetsSerializers(data=request.data)
        try:
            user_id = Token.objects.get(key=request.auth.key).user_id
            user = User.objects.get(id=user_id)
        except Exception as e:
            logger.error("Error while get user from token: " + str(e))
            user = None

        if serializer.is_valid():
            target = serializer.save()
            run_hook('target_post_save', target=target, created=True, user=user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class TargetUpdateApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'ra': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'dec': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'epoch': openapi.Schema(type=openapi.TYPE_NUMBER),
                'classification': openapi.Schema(type=openapi.TYPE_STRING),
                'discovery_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cadence': openapi.Schema(type=openapi.TYPE_NUMBER),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=[]
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def patch(self, request, name):
        instance = Target.objects.get(name=name)
        serializer = TargetsSerializers(instance, data=request.data, partial=True)

        if instance is not None:
            if serializer.is_valid():
                serializer.save()
                # run_hook('update_alias', target=target, created=True) TODO UPDATE TARGET NAME
                return Response({'Status': 'updated'}, status=201)
        return Response(serializer.errors, status=404)


class TargetDeleteApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['name']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def delete(self, request):
        name = request.data.get('name', None)
        target = Target.objects.get(name=name)

        if target is None:
            return Response("Target not found", status=404)

        target.delete()
        return Response({"status": "deleted"}, status=200)


class CleanTargetListCache(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.is_superuser:
                logger.info("Start clean target list cache")
                update_targetList_cache()
            else:
                raise Http404
        except Exception as e:
            logger.error("Clean cache error: " + str(e))
            return Response("ERROR", status=500)
        return Response("OK", status=200)


class CleanTargetDetailsCache(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.is_superuser:
                logger.info("Start clean target details cache")
                update_targetDetails_cache()
            else:
                raise Http404
        except Exception as e:
            logger.error("Clean cache error: " + str(e))
            return Response("ERROR", status=500)
        return Response("OK", status=200)


class GetPlotsApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'targetNames': openapi.Schema(type=openapi.TYPE_ARRAY,
                                              items=openapi.Schema(type=openapi.TYPE_STRING), ),
            },
            required=['targetNames']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request):
        targetNames = request.data['targetNames']
        results = {}
        try:
            base_path = settings.DATA_PLOT_PATH
            for target_name in targetNames:

                target = Target.objects.get(name=target_name)
                if target.photometry_plot:
                    with open(base_path + str(target.photometry_plot), 'r') as json_file:
                        plot = json.load(json_file)
                    results[target.name] = plot
                else:
                    results[target.name] = "None"

        except Target.DoesNotExist:
            return Response({"Error ": 'Target does not exist in the database '}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Plots": results}, status=status.HTTP_200_OK)


class GetPlotsObsApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'targetNames': openapi.Schema(type=openapi.TYPE_ARRAY,
                                              items=openapi.Schema(type=openapi.TYPE_STRING), ),
            },
            required=['targetNames']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request):
        targetNames = request.data['targetNames']
        results = {}
        try:
            base_path = settings.DATA_PLOT_PATH
            for target_name in targetNames:

                target = Target.objects.get(name=target_name)
                if target.photometry_plot_obs:
                    with open(base_path + str(target.photometry_plot_obs), 'r') as json_file:
                        plot = json.load(json_file)
                    results[target.name] = plot
                else:
                    results[target.name] = "None"

        except Target.DoesNotExist:
            return Response({"Error": 'Target does not exist in the database'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Plots": results}, status=status.HTTP_200_OK)


class TargetDownloadRadioDataApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['name']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request):
        serializer = TargetDownloadDataSerializer(data=request.data)
        if not serializer.is_valid():
            logger.info('Error bad request')
            return Response({"Error": 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)

        target_id = serializer.validated_data['name']
        logger.info(f'API Generating radio data in CSV file for target with id={target_id}...')

        tmp = None
        try:
            tmp, filename = save_radio_data_for_target_to_csv_file(target_id)
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating radio data to CSV file for target with id={target_id}: {e}')
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp:
                os.remove(tmp.name)


class TargetDownloadPhotometryDataApiView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['name']
        ),
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description='Token <Your Token>'
            ),
        ],
    )
    def post(self, request):
        serializer = TargetDownloadDataSerializer(data=request.data)
        if not serializer.is_valid():
            logger.info('Error bad request')
            return Response({"Error": 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)
        target_id = serializer.validated_data['name']
        logger.info(f'API Generating photometry CSV file for target with id={target_id}...')

        tmp = None
        try:
            tmp, filename = save_photometry_data_for_target_to_csv_file(target_id)
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating photometry CSV file for target with id={target_id}: {e}')
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp:
                os.remove(tmp.name)
