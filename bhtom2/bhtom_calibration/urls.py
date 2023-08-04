from django.urls import path
from bhtom2.bhtom_calibration.views import ResultFitsApiView

app_name = 'bhtom2.bhtom_calibration'
urlpatterns = [
    path("get-calibration-res/", ResultFitsApiView.as_view()),
]