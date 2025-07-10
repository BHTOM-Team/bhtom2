from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import views
from django.core import serializers
from django.db import transaction

import logging
from django.db.models import Q
import json

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera
from bhtom2.bhtom_observatory.rest.serializers import ObservatorySerializers, CameraSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bhtom2.utils.api_pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


class GetObservatoryApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ObservatorySerializers
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'lon': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lat': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number for pagination'),
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

        name = self.request.data.get('name', None)
        lon = self.request.data.get('lon', None)
        lat = self.request.data.get('lat', None)
        created_start = self.request.data.get('created_start', None)
        created_end = self.request.data.get('created_end', None)
        page = self.request.data.get('page', 1)  
     

        if name is not None:
            query &= Q(name=name)
        if lon is not None:
            query &= Q(lon=lon)
        if lat is not None:
            query &= Q(lat=lat)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = Observatory.objects.filter(query).order_by('created')

        paginator = Paginator(queryset, self.pagination_class.max_page_size)
        
        try:
            paginated_queryset = paginator.page(page)
        except PageNotAnInteger:
            paginated_queryset = paginator.page(1)
        except EmptyPage:
            paginated_queryset = paginator.page(paginator.num_pages)


        serialized_queryset =  self.serializer_class(queryset,many=True).data
        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'data': serialized_queryset
        }

        return Response(response_data, status=200)


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
                'camera_name': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'example_file': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
                'authors': openapi.Schema(type=openapi.TYPE_STRING),
                'acknowledgements': openapi.Schema(type=openapi.TYPE_STRING),
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
            required=['name', 'lon', 'lat', 'camera_name']
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
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        obsData = { 'name': request.data.get('name'),
                    'lon':request.data.get('lon'),
                    'lat': request.data.get('lat'),
                    'calibration_flg': request.data.get('calibration_flg'),
                    'comment': request.data.get('comment'),
                    'altitude': request.data.get('altitude'),
                    'approx_lim_mag':request.data.get('approx_lim_mag'),
                    'filters': request.data.get('filters'),
                    'authors': request.data.get('authors'),
                    'acknowledgements': request.data.get('acknowledgements'),
        }
        camera_name= request.data.get('camera_name', None)
        example_file= request.data.get('example_file',None)
        gain= request.data.get('gain',None)
        readout_noise= request.data.get('readout_noise',None)
        binning= request.data.get('binning',None)
        saturation_level= request.data.get('saturation_level',None)
        pixel_scale= request.data.get('pixel_scale',None)
        readout_speed= request.data.get('readout_speed',None)
        pixel_size= request.data.get('pixel_size',None)
        
        if camera_name is None:
           return Response("camera name can not be None", status=404)

        serializer_obs = ObservatorySerializers(data=obsData)

        if serializer_obs.is_valid():
            instance_obs = serializer_obs.create(serializer_obs.data)
            instance_obs.user = request.user
            instance_obs.save()
            camera = Camera(camera_name=camera_name, 
                                example_file=example_file,
                                gain=gain,
                                readout_noise=readout_noise,
                                binning=binning,
                                saturation_level=saturation_level, 
                                pixel_scale=pixel_scale,
                                readout_speed=readout_speed,
                                pixel_size=pixel_size,
                                observatory=instance_obs,
                                user=request.user,
                                prefix=instance_obs.name + "_" + camera_name)
            camera.save()
            return Response({'Status': 'created'}, status=201)
  
        return Response(serializer_obs.errors, status=404)


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
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
                'authors': openapi.Schema(type=openapi.TYPE_STRING),
                'acknowledgements': openapi.Schema(type=openapi.TYPE_STRING),
                'altitude': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'approx_lim_mag': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'filters': openapi.Schema(type=openapi.TYPE_STRING),
                'origin': openapi.Schema(type=openapi.TYPE_STRING), 
                'telescope':openapi.Schema(type=openapi.TYPE_STRING),
                'aperture':openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'focal_length':openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'seeing':openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),

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
    pagination_class = StandardResultsSetPagination
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user': openapi.Schema(type=openapi.TYPE_STRING),
                'active_flg': openapi.Schema(type=openapi.TYPE_BOOLEAN, format=openapi.FORMAT_INT32),
                'camera': openapi.Schema(type=openapi.TYPE_STRING),
                'created_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number for pagination'),
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

        user = self.request.data.get('user', None)
        active_flg = self.request.data.get('active_flg', None)
        camera = self.request.data.get('camera', None)
        created_end = self.request.data.get('created_end', None)
        created_start = self.request.data.get('created_start', None)
        page = self.request.data.get('page', 1)  
        
        if user is not None:
            query &= Q(user=user)
        if active_flg is not None:
            query &= Q(active_flg=active_flg)
        if camera is not None:
            query &= Q(camera__camera_name=camera)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)
        try:
            queryset = ObservatoryMatrix.objects.filter(query).order_by('created')
            paginator = Paginator(queryset,self.pagination_class.max_page_size) 
            try:
                paginated_queryset = paginator.page(page)
            except PageNotAnInteger:
                paginated_queryset = paginator.page(1)
            except EmptyPage:
                paginated_queryset = paginator.page(paginator.num_pages)

            serialized_queryset = serializers.serialize('json', queryset)
            serialized_data = json.loads(serialized_queryset)
            fields_only = [item['fields'] for item in serialized_data]
            response_data = {
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': paginated_queryset.number,
                'data': fields_only
            }
            
            return Response(response_data, status=200)
        except Exception as e:
             return Response("Oops, somthing went wrong: " + str(e) , status=400)

class CreateObservatoryMatrixApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'observatory': openapi.Schema(type=openapi.TYPE_STRING),
                'camera': openapi.Schema(type=openapi.TYPE_STRING),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
                'oname': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['observatory', 'camera']
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
        observatoryName = request.data.get('observatory', None)
        cameraName = request.data.get('camera', None)
        oname = request.data.get('oname', None)

        if not (oname or (observatoryName and cameraName)):
            return Response("Either (Observatory and Camera) or ONAME is required", status=404)
        try:
            if oname:
                cameraRow = Camera.objects.get(prefix=oname)
            else:
                observatoryRow = Observatory.objects.get(name=observatoryName)
                cameraRow = Camera.objects.get(camera_name=cameraName, observatory=observatoryRow)
        except Observatory.DoesNotExist:
            return Response("Observatory with this name does not exist", status=404)
        except Camera.DoesNotExist:
            return Response("Camera with this name does not exist for this observatory", status=404)

        if not cameraRow.active_flg:
            return Response("Observatory is not active", status=404)

        try:
            if ObservatoryMatrix.objects.filter(user=request.user, camera=cameraRow, active_flg=True).exists():
                return Response("This observatory already exists in yours favourite list", status=404)
            obsMatrix = ObservatoryMatrix(
                user=request.user,
                camera=cameraRow,
                active_flg=True
            )
            obsMatrix.save()
        except Exception as e:
            logger.error("Error in creating user observatory/camera: " + str(e))
            return Response("Error in creating user observatory/camera: " + str(e), status=400)

        return Response({"Status": "Created"}, status=201)


class DeleteObservatoryMatrixApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'camera': openapi.Schema(type=openapi.TYPE_STRING),
                'observatory': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['camera', 'observatory']
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
        camera_name = request.data.get('camera', None)
        observatory_name = request.data.get('observatory', None)
        user = request.user

        if not user.is_staff:
            return Response("Only admin have access", status=404)
        
        observatory = Observatory.objects.get(name=observatory_name)

        if observatory is None:
            return Response("Observatory not found", status=404)
        
        camera = Camera.objects.get(camera_name=camera_name, observatory=observatory)
        if camera is None:
            return Response("Camera not found", status=404)
        
        observatoryMatrix = ObservatoryMatrix.objects.get(camera=camera.id, user=user)

        if observatoryMatrix is not None and user == observatoryMatrix.user:
            observatoryMatrix.delete()
            return Response({"Status": "deleted"}, status=200)
        return Response("ObservatoryMatrix not found", status=404)
