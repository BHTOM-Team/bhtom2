from django.urls import path
from bhtom2.bhtom_calibration.views import CalibrationResultsApiView, GetCatalogsApiView, GetCpcsArchiveDataApiView,GetAlertLCDataView, RestartCalibrationApiView

app_name = 'bhtom2.bhtom_calibration'
urlpatterns = [
    path("get-calibration-res/", CalibrationResultsApiView.as_view()),
    path("restart-calib/", RestartCalibrationApiView.as_view()),
    path('get-catalogs/',GetCatalogsApiView.as_view()),
    path('get-cpcs-archive/', GetCpcsArchiveDataApiView.as_view()),
    path('get_alert_lc_data/',GetAlertLCDataView.as_view()),
]