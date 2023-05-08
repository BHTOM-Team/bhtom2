"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from bhtom2.bhtom_targets.views import TargetCreateView, TargetUpdateView, TargetGenerateTargetDescriptionLatexView

from bhtom_base.bhtom_targets.views import TargetDetailView

from bhtom2.views import BrokerQueryListView, TargetDownloadPhotometryDataView, TargetDownloadRadioDataView, TargetListImagesView, TargetListView

urlpatterns = [
    path('images/', TargetListImagesView.as_view(), name='images'),
    path('', include('bhtom_custom_registration.bhtom_registration.registration_flows.approval_required.urls', namespace='registration')),
    path('alerts/query/list/', BrokerQueryListView.as_view(template_name='bhtom_alerts/brokerquery_list.html'), name='alerts:list'),
    path('targets/', TargetListView.as_view(), name='targets'),
    path('targets/<str:name>/', TargetDetailView.as_view(template_name='bhtom_targets/target_detail.html'), name='detail'),
    path('targets/create/', TargetCreateView.as_view(template_name='bhtom_targets/target_form.html'), name='create'),
    path('targets/<int:pk>/update/', TargetUpdateView.as_view(template_name='bhtom_targets/target_form.html'), name='update'),
    path('targets/<int:pk>/download-photometry', TargetDownloadPhotometryDataView.as_view(), name='download_photometry_data'),
    path('targets/<int:pk>/download-radio', TargetDownloadRadioDataView.as_view(), name='download_radio_data'),
    path('targets/<int:pk>/generate-target-description-latex/',
         TargetGenerateTargetDescriptionLatexView.as_view(template_name='bhtom_targets/target_generate_latex_form.html'),
         name='generate_target_description_latex'),
    path('catalogs/', include('bhtom2.bhtom_catalogs.urls')),
    path('proposals/', include('bhtom2.bhtom_observations.urls', namespace='proposals')),
    path('targets/', include('bhtom2.bhtom_targets.urls', namespace='targets')),
    path('', include('bhtom_base.bhtom_common.urls')),
]
