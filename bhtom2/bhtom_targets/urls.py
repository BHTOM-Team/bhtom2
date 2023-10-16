from django.urls import path

from bhtom_base.bhtom_targets.api_views import TargetExtraViewSet, TargetNameViewSet, TargetViewSet
from bhtom_base.bhtom_targets.views import TargetAddRemoveGroupingView, TargetDeleteView, \
    TargetExportView, TargetGroupingCreateView, TargetGroupingDeleteView, TargetGroupingView, TargetNameSearchView, \
    TargetDetailView
from .rest.views import CleanTargetListCache, GetTargetListApi, CleanTargetDetailsCache, TargetCreateApi, \
    TargetUpdateApi, TargetDeleteApi, GetPlotsApiView, TargetDownloadRadioDataApiView, TargetDownloadPhotometryDataApiView

from .views import TargetCreateView, TargetUpdateView, TargetGenerateTargetDescriptionLatexView, TargetImportView, \
    TargetDownloadPhotometryStatsLatexTableView, TargetListImagesView, TargetDownloadPhotometryDataView, \
    TargetDownloadRadioDataView, TargetMicrolensingView, TargetListView

from bhtom_base.bhtom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()
router.register(r'targets', TargetViewSet, 'targets')
router.register(r'targetextra', TargetExtraViewSet, 'targetextra')
router.register(r'targetname', TargetNameViewSet, 'targetname')

app_name = 'targets'

urlpatterns = [
     path('cleanTargetListCache/', CleanTargetListCache.as_view()),
     path('cleanTargetDetailCache/', CleanTargetDetailsCache.as_view()),
     path('getTargetList/', GetTargetListApi.as_view()),
     path('createTarget/', TargetCreateApi.as_view()),
     path('updateTarget/<str:name>/', TargetUpdateApi.as_view()),
     path('deleteTarget/', TargetDeleteApi.as_view()),
     path('get-plots/', GetPlotsApiView.as_view()),
     path('download-radio/', TargetDownloadRadioDataApiView.as_view()),
     path('download-photometry/', TargetDownloadPhotometryDataApiView.as_view()),
     path('', TargetListView.as_view(), name='list'),
     path('', TargetListView.as_view(), name='targets'),
     path('create/', TargetCreateView.as_view(), name='create'),
     path('<int:pk>/update/', TargetUpdateView.as_view(), name='update'),
     path('<str:name>/update/', TargetUpdateView.as_view(), name='update'),
     path('<int:pk>/delete/', TargetDeleteView.as_view(), name='delete'),
     path('import/', TargetImportView.as_view(), name='import'),
     path('export/', TargetExportView.as_view(), name='export'),
     path('targetgrouping/', TargetGroupingView.as_view(), name='targetgrouping'),
     path('targetgrouping/<int:pk>/delete/', TargetGroupingDeleteView.as_view(), name='delete-group'),
     path('targetgrouping/create/', TargetGroupingCreateView.as_view(), name='create-group'),
     path('add-remove-grouping/', TargetAddRemoveGroupingView.as_view(), name='add-remove-grouping'),
     path('name/<str:name>', TargetNameSearchView.as_view(), name='name-search'),
     path('<int:pk>/generate-target-description-latex/', TargetGenerateTargetDescriptionLatexView.as_view(),
         name='generate_target_description_latex'),
     path('<str:name>/generate-target-description-latex/', TargetGenerateTargetDescriptionLatexView.as_view(),
         name='generate_target_description_latex'),
     path('<int:pk>/download-photometry-stats-latex', TargetDownloadPhotometryStatsLatexTableView.as_view(),
         name='download_photometry_stats_latex'),
     path('import/', TargetImportView.as_view(), name='import'),
     path('images/', TargetListImagesView.as_view(), name='images'),
     path('<int:pk>/download-photometry', TargetDownloadPhotometryDataView.as_view(), name='download_photometry_data'),
     path('<str:name>/download-photometry', TargetDownloadPhotometryDataView.as_view(),
         name='download_photometry_data'),
     path('<int:pk>/download-radio', TargetDownloadRadioDataView.as_view(), name='download_radio_data'),
     path('<str:name>/download-radio', TargetDownloadRadioDataView.as_view(), name='download_radio_data'),
     path('<int:pk>/microlensing',
         TargetMicrolensingView.as_view(template_name='bhtom_targets/target_microlensing.html'),
         name="microlensing_model"),
     path('<int:pk>/microlensing_parallax',
         TargetMicrolensingView.as_view(template_name='bhtom_targets/target_microlensing_parallax.html'),
         name="microlensing_parallax_model"),

     path('<int:pk>/', TargetDetailView.as_view(template_name='bhtom_targets/target_detail.html'),
         name='detail'),
     path('<str:name>/', TargetDetailView.as_view(template_name='bhtom_targets/target_detail.html'),
         name='detail'),
]
