from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status
from bhtom2.bhtom_calibration.models import Calibration_data
from django.core import serializers
from bhtom2.bhtom_calibration.models import Catalogs as calibration_catalog
from bhtom_base.bhtom_dataproducts.models import DataProduct
from bhtom_base.bhtom_targets.models import Target
from bhtom2.utils.bhtom_logger import BHTOMLogger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import json
from django.conf import settings
logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_calibration.views')


class CalibrationResultsApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # @swagger_auto_schema(
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         properties={
    #             'files': openapi.Schema(type=openapi.TYPE_ARRAY,
    #             items=openapi.Schema(type=openapi.TYPE_INTEGER),),
    #             'getPlot': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #         },
    #         required=['fileId', 'getPlot']
    #     ),
    #     manual_parameters=[
    #         openapi.Parameter(
    #         name='Authorization',
    #         in_=openapi.IN_HEADER,
    #         type=openapi.TYPE_STRING,
    #         required=True,
    #         description='Token <Your Token>'
    #     ),
    # ],
    # )

    def post(self, request):
        files = request.data['files']
        getPlot = request.data['getPlot']
        results = {}
        base_path = settings.DATA_PLOT_PATH
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
