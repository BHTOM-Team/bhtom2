from django.urls import path
from bhtom2.bhtom_dataproducts.views import FitsUploadAPIView, DataProductUploadView

app_name = 'bhtom2.bhtom_dataproducts'
urlpatterns = [
    path('upload/', FitsUploadAPIView.as_view(), name='upload'),
    path("upload-data-ui/", DataProductUploadView.as_view(), name="upload_data_ui")
]