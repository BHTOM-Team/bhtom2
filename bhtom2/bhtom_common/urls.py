from django.urls import path

from bhtom2.bhtom_common.views import GetDataProductApi, DataListView, ReloadFits, ReloadPhotometry, \
     DeletePointAndRestartProcess, UpdateFits, ReloadPhotometryWithFits, NewsletterView, DataListCompletedView, CommentAPIView,DataListCCDPHOTErrorView, \
     DataListInProgressView, DataListInCalibView, DataListCPCSErrorView, DataListCPCSLimitView, GetReducedDataApi  ,DeleteReduceDatumApiView, \
          DeactivateReduceDatumApiView, DeleteDataProductApiView

from bhtom_base.bhtom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()


app_name = 'common'

urlpatterns = [
     path('', DataListView.as_view(), name='list'),
     path('fitsCompleted/', DataListCompletedView.as_view(), name='list_completed'),
     path('ccdphotError/', DataListCCDPHOTErrorView.as_view(), name='list_ccdphot_error'),
     path('inProgress/', DataListInProgressView.as_view(), name='list_in_progress'),
     path('inCalibration/', DataListInCalibView.as_view(), name='list_in_calibration'),
     path('cpcsError/', DataListCPCSErrorView.as_view(), name='list_cpcs_error'),
     path('cpcsLimit/', DataListCPCSLimitView.as_view(), name='list_cpcs_limit'),
     path('reloadFits/', ReloadFits.as_view(), name='reload_fits'),
     path('updateFits/', UpdateFits.as_view(), name='update_fits'),
     path('deletePointAndRestertFits/', DeletePointAndRestartProcess.as_view(), name='reload_s_fits'),
     path('reloadPhotometry/', ReloadPhotometry.as_view(), name='reload_photometry'),
     path('reloadPhotometryWithFits/', ReloadPhotometryWithFits.as_view(), name='reload_photometry_fits'),
     path('api/data/', GetDataProductApi.as_view(), name='data_api'),
     path('api/deleteDataProduct/', DeleteDataProductApiView.as_view()),
     path('api/reducedDatum/', GetReducedDataApi.as_view(), name='reduced_datum'),
     path('api/deleteReducedDatum/', DeleteReduceDatumApiView.as_view()),
     path('api/deactivateReducedDatum/',DeactivateReduceDatumApiView.as_view()),
     path('newsletter/', NewsletterView.as_view(), name='newsletter'),
     path('api/comments/', CommentAPIView.as_view()),
]
