from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from rest_framework.authtoken.models import Token
from rest_framework import status
import base64
from django.db.models import Q
from django_guid import get_guid
from bhtom2.bhtom_calibration.models import Calibration_data
from django.core import serializers
from bhtom2.bhtom_calibration.models import Catalogs as calibration_catalog
from bhtom_base.bhtom_dataproducts.models import DataProduct, ReducedDatum, CCDPhotJob
from bhtom_base.bhtom_targets.models import Target
from bhtom2.utils.api_pagination import StandardResultsSetPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'calibid': openapi.Schema(type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Array of calibration IDs"
                ),
                'filename': openapi.Schema(type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Array of calibration filenames"
                ),
                'getPlot': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number for pagination'),
            },
            required=['getPlot']
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
        calibid = request.data.get('calibid', [])
        filename = request.data.get('filename', [])
        getPlot = request.data.get('getPlot', False)
        page = request.data.get('page', 1)

        if not calibid and not filename:
            return Response({"Error": "'calibid' or 'filename' fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Token.objects.get(key=request.auth.key).user
            calibration_data_list = []

            # Process based on calibid (integer IDs)
            for file_id in calibid:
                try:
                    instance = Calibration_data.objects.get(dataproduct_id=file_id)
                    if instance.dataproduct.user_id == user.id or user.is_superuser:
                        serialized_data = serializers.serialize('json', [instance])
                        data = json.loads(serialized_data)[0]
                        result = data["fields"]
                        file_url = f"https://{request.get_host()}/dataproducts/download/photometry/{instance.dataproduct.id}/"
                        result["file_download_link"] = file_url
                        if getPlot:
                            if instance.calibration_plot:
                                plot_path = settings.DATA_PLOTS_PATH + str(instance.calibration_plot)
                                with open(plot_path, 'rb') as image_file:
                                    plot_data = base64.b64encode(image_file.read()).decode('utf-8')
                                    result["plot"] = f"data:image/png;base64,{plot_data}"
                            else:
                                result["plot"] = None
                        else:
                            result["plot"] = None
                        if instance.dataproduct.data_product_type == "fits_file":
                            ccdphot_instance = CCDPhotJob.objects.get(dataProduct_id=instance.dataproduct.id)
                            serialized_ccdphot_data = serializers.serialize('json', [ccdphot_instance])
                            ccdphot_data = json.loads(serialized_ccdphot_data)[0]
                            result["ccdphot_results"] = ccdphot_data["fields"]
                        calibration_data_list.append(result)
                    else:
                        calibration_data_list.append({"calib-res": "It's not your data", "plot": None})

                except Calibration_data.DoesNotExist:
                    calibration_data_list.append({"Error": f"File with id {file_id} does not exist"})

            # Process based on filename (string filenames)
            for file_name in filename:
                try:
                    instance = Calibration_data.objects.get(dataproduct__data__contains=file_name)

                    if instance.dataproduct.user_id == user.id or user.is_superuser:
                        serialized_data = serializers.serialize('json', [instance])
                        data = json.loads(serialized_data)[0]
                        result = data["fields"]
                        file_url = request.build_absolute_uri(settings.DATA_MEDIA_PATH + str(instance.dataproduct.photometry_data))
                        result["file_download_link"] = file_url
                        if getPlot:
                            if instance.calibration_plot:
                                plot_path = settings.DATA_PLOTS_PATH + str(instance.calibration_plot)
                                with open(plot_path, 'rb') as image_file:
                                    plot_data = base64.b64encode(image_file.read()).decode('utf-8')
                                    result["plot"] = f"data:image/png;base64,{plot_data}"
                            else:
                                result["plot"] = None
                        else:
                            result["plot"] = None
                        if instance.dataproduct.data_product_type == "fits_file":
                            ccdphot_instance = CCDPhotJob.objects.get(dataProduct_id=instance.dataproduct.id)
                            serialized_ccdphot_data = serializers.serialize('json', [ccdphot_instance])
                            ccdphot_data = json.loads(serialized_ccdphot_data)[0]
                            result["ccdphot_results"] = ccdphot_data["fields"]
                        calibration_data_list.append(result)
                    else:
                        calibration_data_list.append({"calib-res": "It's not your data", "plot": None})

                except Calibration_data.DoesNotExist:
                    calibration_data_list.append({"Error": f"File with name {file_name} does not exist"})

            # Pagination logic remains the same
            paginator = Paginator(calibration_data_list, self.pagination_class.max_page_size)
            try:
                paginated_data = paginator.page(page)
            except PageNotAnInteger:
                paginated_data = paginator.page(1)
            except EmptyPage:
                paginated_data = paginator.page(paginator.num_pages)

            response_data = {
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': paginated_data.number,
                'data': list(paginated_data)
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Error": 'Something went wrong: ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        return ret


class GetCatalogsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        page_number = request.query_params.get('page', 1)

        try:
            queryset = calibration_catalog.objects.all().values('filters')

            paginator = Paginator(queryset, self.pagination_class.max_page_size)

            try:
                paginated_data = paginator.page(page_number)
            except PageNotAnInteger:
              
                paginated_data = paginator.page(1)
            except EmptyPage:
                paginated_data = paginator.page(paginator.num_pages)

            response_data = {
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': paginated_data.number,
                'data': list(paginated_data)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class RestartCalibrationByTargetApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='target_name',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_STRING,description='Target name.'),
            openapi.Parameter(name='target_id',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Target ID.'),
            openapi.Parameter(name='mjd_max',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='MJD max.'),
            openapi.Parameter(name='mjd_min',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='MJD min.'),
            openapi.Parameter(name='filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='New Filter.'),
            openapi.Parameter(name='old_filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Old Filter.'),
            openapi.Parameter(name='match_dist',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Filter.'),
            openapi.Parameter(name='oname',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='ONAME.'),
            openapi.Parameter(name='comment',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Comment.'),
            openapi.Parameter(name='status',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status'),
            openapi.Parameter(name='status_message',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status Message'),
        ],
    )
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")

        header = {
            "Correlation-ID": get_guid(),
        }

        try:
            response = requests.post(
                url=f"{settings.CPCS_URL}/calib/restartCalibByTarget/",
                data=request.data,
                headers=header
                )

            if response.status_code != 200:
                try:
                    error_details = response.json()
                except ValueError:
                    error_details = response.text 

                return Response(
                    {"Error": f"Oops.. something went wrong. Error: {error_details}"},
                    status=response.status_code
                )
            else:
                response_data = response.json()  
                return Response(
                    {"Success": response_data},
                    status=status.HTTP_200_OK
                )
        except requests.exceptions.RequestException as e:
            return Response(
                {"Error": f"Oops.. something went wrong. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RestartCalibrationByDataProductApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='data_product_id',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Data Product ID.'),
            openapi.Parameter(name='filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='New Filter.'),
            openapi.Parameter(name='old_filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Old Filter.'),
            openapi.Parameter(name='match_dist',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Filter.'),
            openapi.Parameter(name='oname',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='ONAME.'),
            openapi.Parameter(name='comment',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Comment.'),
            openapi.Parameter(name='status',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status'),
            openapi.Parameter(name='status_message',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status Message'),
        ],
    )
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")

        header = {
            "Correlation-ID": get_guid(),
        }

        try:
            response = requests.post(
                url=f"{settings.CPCS_URL}/calib/restartCalibByDataProduct/",
                data=request.data,
                headers=header
                )

            if response.status_code != 200:
                try:
                    error_details = response.json()
                except ValueError:
                    error_details = response.text 

                return Response(
                    {"Error": f"Oops.. something went wrong. Error: {error_details}"},
                    status=response.status_code
                )
            else:
                response_data = response.json()  
                return Response(
                    {"Success": response_data},
                    status=status.HTTP_200_OK
                )
        except requests.exceptions.RequestException as e:
            return Response(
                {"Error": f"Oops.. something went wrong. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RestartCalibrationApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='id_from',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Id from.'),
            openapi.Parameter(name='id_to',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Id to.'),
            openapi.Parameter(name='filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='New Filter.'),
            openapi.Parameter(name='old_filter',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Old Filter.'),
            openapi.Parameter(name='match_dist',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Filter.'),
            openapi.Parameter(name='oname',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='ONAME.'),
            openapi.Parameter(name='comment',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Comment.'),
            openapi.Parameter(name='status',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status'),
            openapi.Parameter(name='status_message',in_=openapi.IN_QUERY,required=False,type=openapi.TYPE_INTEGER,description='Status Message'),
        ],
    )
    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied(detail="Access denied. You must be an admin.")

        header = {
            "Correlation-ID": get_guid(),
        }

        try:
            response = requests.post(
                url=f"{settings.CPCS_URL}/calib/restartCalib/",
                data=request.data,
                headers=header
                )

            if response.status_code != 200:
                try:
                    error_details = response.json()
                except ValueError:
                    error_details = response.text 

                return Response(
                    {"Error": f"Oops.. something went wrong. Error: {error_details}"},
                    status=response.status_code
                )
            else:
                response_data = response.json()  
                return Response(
                    {"Success": response_data},
                    status=status.HTTP_200_OK
                )
        except requests.exceptions.RequestException as e:
            return Response(
                {"Error": f"Oops.. something went wrong. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
