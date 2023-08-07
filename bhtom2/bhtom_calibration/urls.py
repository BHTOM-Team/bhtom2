from django.urls import path
from bhtom2.bhtom_calibration.views import CalibrationResultsApiView

app_name = 'bhtom2.bhtom_calibration'
urlpatterns = [
    path("get-calibration-res/", CalibrationResultsApiView.as_view()),
]