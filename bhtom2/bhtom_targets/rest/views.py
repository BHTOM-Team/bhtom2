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
from bhtom_base.bhtom_targets.models import Target, DownloadedTarget, TargetList, TargetName
from rest_framework import status
import json
from django.conf import settings
from django.core import serializers
import os
from django.http import FileResponse
from bhtom2.utils.reduced_data_utils import save_photometry_data_for_target_to_csv_file, \
    save_radio_data_for_target_to_csv_file
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bhtom2.utils.api_pagination import StandardResultsSetPagination

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_targets.rest-view')

class GetTargetListApi(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

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
        page = request.data.get('page', 1)

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

        target_ids = [target.id for target in paginated_queryset]
        aliases_map = {}
        for tn in TargetName.objects.filter(target_id__in=target_ids):
            aliases_map.setdefault(tn.target_id, []).append((tn.source_name, tn.name))
        groups_map = {}
        for tl in TargetList.objects.filter(targets__id__in=target_ids):
            for target in tl.targets.filter(id__in=target_ids):
                groups_map.setdefault(target.id, []).append((tl.name, tl.id))

        # Przypisz aliasy i grupy bez dodatkowych zapytań
        for target, item in zip(paginated_queryset, fields_only):
            item['aliases'] = aliases_map.get(target.id, [])
            item['groups'] = groups_map.get(target.id, [])

        response_data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': paginated_queryset.number,
            'data': fields_only
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
