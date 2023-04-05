from django.urls import path
from bhtom2.views import TargetListView

from bhtom_base.bhtom_targets.api_views import TargetExtraViewSet, TargetNameViewSet, TargetViewSet
from bhtom_base.bhtom_targets.views import TargetAddRemoveGroupingView, TargetDeleteView, TargetDetailView, TargetExportView, TargetGroupingCreateView, TargetGroupingDeleteView, TargetGroupingView, TargetImportView, TargetNameSearchView

from .views import TargetCreateView, TargetUpdateView, TargetGenerateTargetDescriptionLatexView

from bhtom_base.bhtom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()
router.register(r'targets', TargetViewSet, 'targets')
router.register(r'targetextra', TargetExtraViewSet, 'targetextra')
router.register(r'targetname', TargetNameViewSet, 'targetname')

app_name = 'bhtom2.bhtom_targets'

urlpatterns = [
    path('', TargetListView.as_view(), name='list'),
    path('targetgrouping/', TargetGroupingView.as_view(), name='targetgrouping'),
    path('create/', TargetCreateView.as_view(), name='create'),
    path('import/', TargetImportView.as_view(), name='import'),
    path('export/', TargetExportView.as_view(), name='export'),
    path('add-remove-grouping/', TargetAddRemoveGroupingView.as_view(), name='add-remove-grouping'),
    path('name/<str:name>', TargetNameSearchView.as_view(), name='name-search'),
    path('<int:pk>/update/', TargetUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', TargetDeleteView.as_view(), name='delete'),
    path('<int:pk>/', TargetDetailView.as_view(), name='detail'),
    path('targetgrouping/<int:pk>/delete/', TargetGroupingDeleteView.as_view(), name='delete-group'),
    path('targetgrouping/create/', TargetGroupingCreateView.as_view(), name='create-group'),
    path('<int:pk>/generate-target-description-latex/', TargetGenerateTargetDescriptionLatexView.as_view(), name='generate_target_description_latex'),

]

