from django.urls import path
from bhtom2.bhtom_dataproducts.views import FitsUploadAPIView, DataProductUploadView, DataProductListAllView, \
    DataProductListUserView, \
    DataProductGroupListView, DataProductGroupCreateView, DataProductGroupDetailView, photometry_download, \
    DataDetailsView, CpcsArchiveData, CalibrationLogDownload

app_name = 'bhtom2.bhtom_dataproducts'
urlpatterns = [
    path('upload/', FitsUploadAPIView.as_view(), name='upload'),
    path("upload-data-ui/", DataProductUploadView.as_view(), name="upload_data_ui"),
    path('data-all/', DataProductListAllView.as_view(), name='list_all'),
    path('data-user/', DataProductListUserView.as_view(), name='list_user'),
    path('data/group/list/', DataProductGroupListView.as_view(), name='group-list'),
    path('data/group/create/', DataProductGroupCreateView.as_view(), name='group-create'),
    path('data/group/<str:name>/', DataProductGroupDetailView.as_view(), name='group-detail'),
    path('download/photometry/<int:id>/', photometry_download.as_view(), name='photometry_download'),
    path('data/<int:pk>/', DataDetailsView.as_view(), name='dataproduct-details'),
    path('cpcs_data', CpcsArchiveData.as_view(), name='list_cpcs'),
    path('download/calibrationLog/<int:id>', CalibrationLogDownload.as_view(), name='calibration_log_download')
]
