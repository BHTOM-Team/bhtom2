from django.urls import path

from bhtom2.bhtom_common.views import DataListView, ReloadFits, ReloadPhotometry, DeletePointAndRestartProcess, \
     UpdateFits
from bhtom_base.bhtom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()


app_name = 'common'

urlpatterns = [
     path('', DataListView.as_view(), name='list'),
     path('reloadFits/', ReloadFits.as_view(), name='reload_fits'),
     path('updateFits/', UpdateFits.as_view(), name='update_fits'),
     path('deletePointAndRestertFits/', DeletePointAndRestartProcess.as_view(), name='reload_s_fits'),
     path('reloadPhotometry/', ReloadPhotometry.as_view(), name='reload_photometry'),
]