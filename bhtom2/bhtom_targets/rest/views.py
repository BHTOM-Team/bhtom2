from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bhtom2.bhtom_targets.rest.serializers import TargetsSerializers
from bhtom2.bhtom_targets.utils import update_targetList_cache, update_targetDetails_cache
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_targets.models import Target

from django.core import serializers

logger: BHTOMLogger = BHTOMLogger(__name__, '[bhtom_targets: rest-view]')


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
            },
            required=[]
        ),
    )
    def post(self, request):
        query = Q()

        name = request.data.get('name', None)
        raMin = request.data.get('raMin', None)
        raMax = request.data.get('raMax', None)
        decMin = request.data.get('decMin', None)
        decMax = request.data.get('decMax', None)

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
        except ValueError as e:
            logger.error("Value error in targetList " + str(e))
            return Response("Wrong format", status=404)

        queryset = Target.objects.filter(query).order_by('created')
        serialized_queryset = serializers.serialize('json', queryset)
        return Response(serialized_queryset, status=200)


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
                'epoch': openapi.Schema(type=openapi.TYPE_STRING),
                'classification': openapi.Schema(type=openapi.TYPE_STRING),
                'discovery_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cadence': openapi.Schema(type=openapi.TYPE_NUMBER),
            },
            required=['name', 'ra', 'dec']
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = TargetsSerializers(data=request.data)
        if serializer.is_valid():
            target = serializer.save()
            run_hook('target_post_save', target=target, created=True)
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
                'epoch': openapi.Schema(type=openapi.TYPE_STRING),
                'classification': openapi.Schema(type=openapi.TYPE_STRING),
                'discovery_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'importance': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cadence': openapi.Schema(type=openapi.TYPE_NUMBER),
            },
            required=[]
        ),
    )
    def patch(self, request, name):
        instance = Target.objects.get(name=name)
        serializer = TargetsSerializers(instance, data=request.data, partial=True)

        if instance is not None:
            if serializer.is_valid():
                serializer.save()
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
    )
    def delete(self, request):
        name = request.data.get('name', None)
        target = Target.objects.get(name=name)

        if target is None:
            return Response("Target not found", status=404)

        target.delete()
        return Response({"status": "deleted"}, status=200)


class CleanTargetListCache(views.APIView): #TODO add token
    def post(self, request):
        try:
            logger.info("Start clean target list cache")
            update_targetList_cache()
        except Exception as e:
            logger.error("Clean cache error: " + str(e))
            return Response("ERROR", status=500)
        return Response("OK", status=200)


class CleanTargetDetailsCache(views.APIView):
    def post(self, request):
        try:
            logger.error("Start clean target details cache")
            update_targetDetails_cache()
        except Exception as e:
            logger.error("Clean cache error: " + str(e))
            return Response("ERROR", status=500)
        return Response("OK", status=200)
