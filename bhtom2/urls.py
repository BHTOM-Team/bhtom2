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
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.conf.urls.static import static

from bhtom2 import settings
from bhtom2.views import BrokerQueryListView

schema_view = get_schema_view(
    openapi.Info(
        title="BhTom",
        default_version='v2',
        description="Black Hole Tom",
        contact=openapi.Contact(email="akrawczyk@akond.com"),
    ),
    public=True,
)
urlpatterns = [
    path('swagger/', schema_view.with_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('targets/', include('bhtom2.bhtom_targets.urls', namespace='bhtom_targets')),
    path('calibration/', include('bhtom2.bhtom_calibration.urls', namespace='bhtom_calibration')),
    path('catalogs/', include('bhtom2.bhtom_catalogs.urls', namespace='bhtom_catalogs')),
    path('proposals/', include('bhtom2.bhtom_observations.urls', namespace='bhtom_proposals')),
    path('observatory/', include('bhtom2.bhtom_observatory.urls', namespace='bhtom_observatory')),
    path('dataproducts/', include('bhtom2.bhtom_dataproducts.urls', namespace='bhtom_dataproducts')),
    path('', include('bhtom_base.bhtom_common.urls')),
    path('', include('bhtom_custom_registration.bhtom_registration.registration_flows.approval_required.urls',
                     namespace='registration')),
    path('alerts/query/list/', BrokerQueryListView.as_view(template_name='bhtom_alerts/brokerquery_list.html'),
         name='alerts:list'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

