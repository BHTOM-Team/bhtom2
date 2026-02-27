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
from bhtom2.bhtom_targets.rest.serializers import TargetsSerializers, TargetDownloadDataSerializer, DownloadedTargetSerializer,TargetsGroupsSerializer
from bhtom2.bhtom_targets.utils import update_targetList_cache, update_targetDetails_cache, get_client_ip
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_targets.utils import cone_search_filter
from bhtom_base.bhtom_targets.models import Target, DownloadedTarget, TargetList, TargetName
from rest_framework import status
import json
from django.conf import settings
from django.core import serializers
import os
import math
from django.http import FileResponse
from bhtom2.utils.reduced_data_utils import save_high_energy_data_for_target_to_csv_file, save_photometry_data_for_target_to_csv_file, \
    save_radio_data_for_target_to_csv_file
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bhtom2.utils.api_pagination import StandardResultsSetPagination

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.rest-view')

def _parse_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ('true', '1', 'yes', 'y', 't'):
            return True
        if normalized in ('false', '0', 'no', 'n', 'f'):
            return False
    raise ValueError(f'Invalid boolean value: {value}')


def clean_floats_for_json(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: clean_floats_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_floats_for_json(v) for v in obj]
        else:
            return obj
        
class GetTargetListApi(views.APIView):


    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'type': openapi.Schema(type=openapi.TYPE_STRING),  
                'raMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'raMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'decMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'decMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'importanceMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'importanceMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'classification': openapi.Schema(type=openapi.TYPE_STRING),
                'targetGroup': openapi.Schema(type=openapi.TYPE_STRING),
                'coneSearchTarget':  openapi.Schema(type=openapi.TYPE_STRING),
                'coneSearchRaDecRadius':  openapi.Schema(type=openapi.TYPE_STRING),
                'priority': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLatMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLatMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLonMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'galacticLonMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'sunSeparationMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'sunSeparationMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lastMagMin': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'lastMagMax': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'hasOptical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'hasInfrared': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'hasRadio': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'hasXray': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'hasGamma': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'hasPolarimetry': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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

        name = request.data.get('name', None)
        targetType = request.data.get('type', None)
        raMin = request.data.get('raMin', None)
        raMax = request.data.get('raMax', None)
        decMin = request.data.get('decMin', None)
        decMax = request.data.get('decMax', None)
        importanceMin = request.data.get('importanceMin', None)
        importanceMax = request.data.get('importanceMax', None)
        classification = request.data.get('classification', None)
        targetGroup = request.data.get('targetGroup', None)
        coneSearchTarget = request.data.get('coneSearchTarget', None)
        coneSearchRaDecRadius = request.data.get('coneSearchRaDecRadius', None)
        priority = request.data.get('priority', None)
        lastMagMin = request.data.get('lastMagMin', None)
        lastMagMax = request.data.get('lastMagMax', None)
        sunSeparationMin = request.data.get('sunSeparationMin', None)
        sunSeparationMax = request.data.get('sunSeparationMax', None)
        galacticLatMin = request.data.get('galacticLatMin', None)
        galacticLatMax = request.data.get('galacticLatMax', None)
        galacticLonMin = request.data.get('galacticLonMin', None)
        galacticLonMax = request.data.get('galacticLonMax', None)
        description = request.data.get('description', None)
        hasOptical = request.data.get('hasOptical', None)
        hasInfrared = request.data.get('hasInfrared', None)
        hasRadio = request.data.get('hasRadio', None)
        hasXray = request.data.get('hasXray', None)
        hasGamma = request.data.get('hasGamma', None)
        hasPolarimetry = request.data.get('hasPolarimetry', None)
        page = request.data.get('page', 1)
      
        

        try:
            if name is not None:
                query &= Q(name=name)
            if targetType is not None:
                query &= Q(type=targetType)
            if raMin is not None:
                query &= Q(ra__gte=float(raMin))
            if raMax is not None:
                query &= Q(ra__lte=float(raMax))
            if decMin is not None:
                query &= Q(dec__gte=float(decMin))
            if decMax is not None:
                query &= Q(dec__lte=float(decMax))
            if importanceMin is not None:
                query &= Q(importance__gte=float(importanceMin))
            if importanceMax is not None:
                query &= Q(importance__lte=float(importanceMax))
            if priority is not None:
                query &= Q(priority=float(priority))
            if lastMagMin is not None:
                query &= Q(mag_last__gte=float(lastMagMin))
            if lastMagMax is not None:
                query &= Q(mag_last__lte=float(lastMagMax))
            if sunSeparationMin is not None:
                query &= Q(sun_separation__gte=float(sunSeparationMin))
            if sunSeparationMax is not None:
                query &= Q(sun_separation__lte=float(sunSeparationMax))
            if galacticLatMin is not None:
                query &= Q(galactic_lat__gte=float(galacticLatMin))
            if galacticLatMax is not None:
                query &= Q(galactic_lat__lte=float(galacticLatMax))
            if galacticLonMin is not None:
                query &= Q(galactic_lng__gte=float(galacticLonMin))
            if galacticLonMax is not None:
                query &= Q(galactic_lng__lte=float(galacticLonMax))
            if description is not None:
                query &= Q(description=description)
            if classification is not None:
                query &= Q(classification=classification)
            if targetGroup is not None:
                query &= Q(targetlist__name=targetGroup)
            if hasOptical is not None:
                query &= Q(has_optical=_parse_bool(hasOptical))
            if hasInfrared is not None:
                query &= Q(has_infrared=_parse_bool(hasInfrared))
            if hasRadio is not None:
                query &= Q(has_radio=_parse_bool(hasRadio))
            if hasXray is not None:
                query &= Q(has_xray=_parse_bool(hasXray))
            if hasGamma is not None:
                query &= Q(has_gamma=_parse_bool(hasGamma))
            if hasPolarimetry is not None:
                query &= Q(has_polarimetry=_parse_bool(hasPolarimetry))

        except ValueError as e:
            logger.error("Value error in targetList " + str(e))
            return Response("Wrong format: " + str(e), status=400)

        queryset = Target.objects.filter(query).order_by('created')
 
        # Obsługa coneSearchRaDecRadius: "RA,DEC,RADIUS"
        if coneSearchRaDecRadius:
            try:
                ra_dec_radius = [float(x.strip()) for x in coneSearchRaDecRadius.split(',')]
                if len(ra_dec_radius) == 3:
                    ra, dec, radius = ra_dec_radius
                    queryset = cone_search_filter(queryset, ra, dec, radius)
            except Exception as e:
                logger.error(f"Cone search by RA/Dec error: {e}")

        # Obsługa coneSearchTarget: "TargetName,RADIUS"
        if coneSearchTarget:
            try:
                target_name, radius = [x.strip() for x in coneSearchTarget.split(',')]
                radius = float(radius)
                target_obj = Target.objects.filter(
                    Q(name__icontains=target_name) | Q(aliases__name__icontains=target_name)
                ).distinct().first()
                if target_obj:
                    ra = target_obj.ra
                    dec = target_obj.dec
                    queryset = cone_search_filter(queryset, ra, dec, radius)
            except Exception as e:
                logger.error(f"Cone search by target name error: {e}")


        paginator = Paginator(queryset, self.pagination_class.max_page_size)

        try:
            paginated_queryset = paginator.page(page)
        except PageNotAnInteger:
            paginated_queryset = paginator.page(1)
        except EmptyPage:
            paginated_queryset = paginator.page(paginator.num_pages)

        serialized_queryset = serializers.serialize('json', paginated_queryset)

        serialized_data = json.loads(serialized_queryset)
        fields_only = [item['fields'] for item in serialized_data]

        for target in fields_only:
            aliases = []
            target_list_names = []
            
            try:
                temp = Target.objects.get(name=target['name'])
                aliases = TargetName.objects.filter(target_id=temp.id).values_list('source_name','name')
            except Exception as e:
                logger.error("Ops, something went wrong" + str(e))
                aliases = []
            try:
                temp = Target.objects.get(name=target['name'])
                target_lists = TargetList.objects.filter(targets=temp)
                target_list_names = target_lists.values_list('name', 'id')
            except Exception as e:
                logger.error("Ops, something went wrong" + str(e))
                target_list_names = []

            target['aliases'] = aliases
            target['groups'] = target_list_names

        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'data': clean_floats_for_json(fields_only)
        }
        return Response(response_data, status=200)


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
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'discovery_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cadence': openapi.Schema(type=openapi.TYPE_NUMBER),
                'has_optical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_infrared': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_radio': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_xray': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_gamma': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_polarimetry': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'has_optical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_infrared': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_radio': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_xray': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_gamma': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_polarimetry': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
            base_path = settings.DATA_PLOTS_PATH
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
            base_path = settings.DATA_PLOTS_PATH
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

        name = serializer.validated_data['name']
        target_id = Target.objects.get(name=name).id

        logger.info(f'API Generating radio data in CSV file for target with id={target_id}...')

        tmp = None
        try:
            tmp, filename = save_radio_data_for_target_to_csv_file(name)
            ip_address = get_client_ip(request)
            DownloadedTarget.objects.create(
                user=request.user,
                target_id=target_id,
                download_type='R',
                ip_address=ip_address
            )
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating radio data to CSV file for target with id={target_id}: {e}')
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp:
                os.remove(tmp.name)

class TargetDownloadHEDataApiView(views.APIView):
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
            return Response({"Error": 'Something went wrong, bad request in API '}, status=status.HTTP_400_BAD_REQUEST)

        name = serializer.validated_data['name']
        target_id = Target.objects.get(name=name).id

        logger.info(f'API Generating radio data in CSV file for target with id={target_id}...')

        tmp = None
        try:
            tmp, filename = save_high_energy_data_for_target_to_csv_file(name)
            ip_address = get_client_ip(request)
            DownloadedTarget.objects.create(
                user=request.user,
                target_id=target_id,
                download_type='H',
                ip_address=ip_address
            )
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating high energy data to CSV file for target with id={target_id}: {e}')
            return Response({"Error ": 'Something went wrong in high energy download' + str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
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
        name = serializer.validated_data['name']
        target_id = Target.objects.get(name=name).id

        logger.info(f'API Generating photometry CSV file for target with id={target_id}')

        tmp = None
        try:
            tmp, filename = save_photometry_data_for_target_to_csv_file(name)
            ip_address = get_client_ip(request)
            DownloadedTarget.objects.create(
                user=request.user,
                target_id=target_id,
                download_type='P',
                ip_address=ip_address
            )
            return FileResponse(open(tmp.name, 'rb'),
                                as_attachment=True,
                                filename=filename)
        except Exception as e:
            logger.error(f'Error while generating photometry CSV file for target with id={target_id}: {e}')
            return Response({"Error ": 'Something went wrong ' + str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp:
                os.remove(tmp.name)



class GetDownloadedTargetListApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'target': openapi.Schema(type=openapi.TYPE_STRING),
                'user': openapi.Schema(type=openapi.TYPE_STRING),
                'created_from': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'created_to': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'download_type': openapi.Schema(type=openapi.TYPE_STRING),
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

        target = request.data.get('target', None)
        user = request.data.get('user', None)
        created_from = request.data.get('created_from', None)
        created_to = request.data.get('created_to', None)
        download_type = request.data.get('download_type', None)
        page = request.data.get('page', 1)

        if not request.user.is_superuser:
             return Response("You have no permissions, Admin Only", status=404)

        try:
            if target is not None:
                query &= Q(target__name__icontains=target)
            if user is not None:
                query &= Q(user__username__icontains=user)
            if created_from is not None:
                query &= Q(created__gte=created_from)
            if created_to is not None:
                query &= Q(created__lte=created_to)
            if download_type is not None:
                query &= Q(download_type=download_type)
        except ValueError as e:
            logger.error("Value error in GetDownloadedTargetListApi " + str(e))
            return Response("Wrong format", status=400)

        queryset = DownloadedTarget.objects.filter(query).order_by('-created')
        paginator = Paginator(queryset, self.pagination_class.max_page_size)

        try:
            paginated_queryset = paginator.page(page)
        except PageNotAnInteger:
            paginated_queryset = paginator.page(1)
        except EmptyPage:
            paginated_queryset = paginator.page(paginator.num_pages)

        serialized_queryset = DownloadedTargetSerializer(paginated_queryset, many=True)

        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'data': serialized_queryset.data
        }
        
        return Response(response_data, status=200)
    


class GetTargetsGroups(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
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
        page = request.data.get('page', 1)

        
        try:
            queryset = TargetList.objects.order_by('-created')
            paginator = Paginator(queryset, self.pagination_class.max_page_size)

            try:
                paginated_queryset = paginator.page(page)
            except PageNotAnInteger:
                paginated_queryset = paginator.page(1)
            except EmptyPage:
                paginated_queryset = paginator.page(paginator.num_pages)

            serialized_queryset = TargetsGroupsSerializer(paginated_queryset, many=True)
        except Exception as e:
            logger.error("Oops, something went wrong: " + str(e))
            return Response("Oops, something went wrong " + str(e), status=400)
        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'data': serialized_queryset.data
        }
        
        return Response(response_data, status=200)
    
class GetTargetsFromGroup(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number for pagination'),
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The Target group id'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='The Target group name'),
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
        page = request.data.get('page', 1)
        group_id = request.data.get('id', None)
        group_name = request.data.get('name', None)
        
       
        
        if group_id is None and group_name is None:
            return Response({"detail": "Please provide either 'id' or 'name' of the target group."}, status=400)
        elif group_id and group_name:
            return Response({"detail": "Please provide only one parameter: either 'id' or 'name', not both."}, status=400)

        try:
         
            if group_name:
                target_list = TargetList.objects.get(name=group_name)
            else:
                target_list = TargetList.objects.get(id=group_id)

  
            targets = target_list.targets.all()

     
            paginator = Paginator(targets, self.pagination_class.max_page_size)

            try:
                paginated_queryset = paginator.page(page)
            except PageNotAnInteger:
                paginated_queryset = paginator.page(1)
            except EmptyPage:
                paginated_queryset = paginator.page(paginator.num_pages)

           
            serialized_queryset = TargetsSerializers(paginated_queryset, many=True)

        except TargetList.DoesNotExist:
            return Response({"detail": "Target group not found."}, status=404)
        except Exception as e:
            logger.error(f"Oops, something went wrong: {str(e)}")
            return Response({"detail": f"Oops, something went wrong: {str(e)}"}, status=400)

       
        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'group': group_name if group_name else group_id,
            'data': serialized_queryset.data
        }

        return Response(response_data, status=200)
