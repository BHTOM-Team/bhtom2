from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status
from django_guid import get_guid
from bhtom2.bhtom_calibration.models import Calibration_data
from django.core import serializers
from bhtom2.bhtom_calibration.models import Catalogs as calibration_catalog
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum
from bhtom_base.bhtom_targets.models import Target
from bhtom2.utils.bhtom_logger import BHTOMLogger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import json
import requests
import re
from django.conf import settings
logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_calibration.views')


class CalibrationResultsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'files': openapi.Schema(type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),),
                'getPlot': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
            required=['fileId', 'getPlot']
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
        files = request.data['files']
        getPlot = request.data['getPlot']
        results = {}
        base_path = settings.DATA_PLOTS_PATH
        try:
            user = Token.objects.get(key=request.auth.key).user
            for file in files:
                if isinstance(file, str):
                    instance = Calibration_data.objects.get(dataproduct__data__contains= file)
                    dp = DataProduct.objects.get(data__contains=file)   
                elif isinstance(file, int):
                    instance = Calibration_data.objects.get(dataproduct_id=file)
                    dp = DataProduct.objects.get(id=file)
                if(instance.dataproduct.user_id == user.id or user.is_superuser):
                    serialized_data = serializers.serialize('json', [instance])
                    data = json.loads(serialized_data)[0] 
                    results[instance.id] = data["fields"]
                    if getPlot:
                        target = dp.target
                        if target.photometry_plot:
                            with open(base_path + str(target.photometry_plot), 'r') as json_file:
                                plot = json.load(json_file)
                                results[instance.id] = {"calib-res":  data["fields"] ,"plot": plot}
                    else:
                        results[instance.id] ={"calib-res":  data["fields"] ,"plot": None}
                else:
                        results[instance.id] ={"calib-res":  "It's not yours data","plot": None}
        except Calibration_data.DoesNotExist:
            return Response({"Error": 'File does not exist in the database'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Error": 'something went wrong' + str(e)}, status=status.HTTP_400_BAD_REQUEST)

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


class GetCpcsArchiveDataApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        radius = request.data['radius']
        ra = request.data['ra']
        dec = request.data['dec']
        if ra == None or dec == None:
             return Response({"Error": "ra and dec can't be None"}, status=status.HTTP_400_BAD_REQUEST)
        cpcs_archive_data = {}
        post_data = {
            'radius': radius,
            'ra': ra,
            'dec': dec,
        }
        header = {
            "Correlation-ID" : get_guid(),
        }
        try:
            cpcs_archive_data = requests.post(settings.CPCS_URL + '/getArchiveData/', data=post_data,
                      headers=header)    
        except Exception as e:
            return Response({"Error": 'Oops.. something went wrong ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Result": cpcs_archive_data}, status=status.HTTP_200_OK)

class GetAlertLCDataView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='alert_name',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='Name of the alert.'
            ),
        ],
    )
    def get(self, request):
        alert_name = request.query_params.get('alert_name', None)

        if not alert_name:
            return Response("You need to provide alert_name", status=status.HTTP_400_BAD_REQUEST)

        try:
            target = Target.objects.get(name=alert_name)
        except Target.DoesNotExist:
            logger.error(f"Target does not exist with name: {alert_name}")
            return Response(f"You need to provide correct alert_name, target does not exist in db", status=status.HTTP_400_BAD_REQUEST)

        try:
            # Define a regular expression pattern to match the format
            pattern = re.compile(r'(\w+)\((\w+)\)')

            data = ReducedDatum.objects.filter(target=target, value_unit="MAG").values_list(
                'id', 'mjd', 'value', 'error', 'filter', 'data_product__observatory__id',
                'data_product__observatory__observatory__name', 'data_product', 'source_location'
            )

            test = ReducedDatum.objects.filter(target=target, value_unit="MAG").values_list(
                'id', 'mjd', 'value', 'error', 'filter', 'data_product__observatory__id',
                'data_product__observatory__observatory__name', 'data_product', 'source_location'
            )
        
            caliberrs = [self.get_caliberr(reduce_datum) for reduce_datum in data]
            try:
                ids, mjds, mags, magerrs, bhtom_filters, obsids, obsnames, dp, source = zip(*data)
            except Exception as e:
                logger.error("No data for this alert!") 
                return Response('No data for this alert!', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Parse filters and catalogs
            filters, catalogs = self.parse_filters(bhtom_filters, pattern)

            lc_hash = {
                'alert_name': alert_name,
                'mjd': list(mjds),
                'mag': list(mags),
                'magerr': list(magerrs),
                'caliberr': caliberrs,
                'filter': filters,
                'catalog': catalogs,
                'observatory_id': list(obsids),
                'observatory': list(obsnames),
                'id': list(ids),
            }

        except Exception as e:
            logger.error(f"Error while getting reduced data: {str(e)}")
            return Response('Oops something went wrong: ' + str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(lc_hash, status=status.HTTP_200_OK)

    def get_caliberr(self, reduce_datum):
        caliberr = None
        if reduce_datum[-1] == 'cpcs':
            try:
                caliberr = Calibration_data.objects.get(dataproduct=reduce_datum[-2]).scatter
            except Calibration_data.DoesNotExist as e:
                logger.error(f"There is no Calibration_data for DataProduct: {reduce_datum.data_product.id}, {str(e)}")
        return caliberr

    def parse_filters(self, bhtom_filters, pattern):
        filters = []
        catalogs = []

        for filter_value in bhtom_filters:
            match = pattern.match(filter_value)
            if match:
                filter_name = match.group(1)
                catalog_name = match.group(2)
                filters.append(filter_name)
                catalogs.append(catalog_name)
            else:
                filters.append(filter_value)
                catalogs.append(None)

        return filters, catalogs
