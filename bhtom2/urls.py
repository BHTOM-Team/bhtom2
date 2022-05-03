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
from bhtom_base.tom_targets.views import TargetDetailView

from bhtom2.views import BrokerQueryListView

urlpatterns = [
    path('', include('tom_registration.registration_flows.approval_required.urls', namespace='registration')),
    path('alerts/query/list/', BrokerQueryListView.as_view(template_name='tom_alerts/brokerquery_list.html'), name='alerts:list'),
    path('targets/<int:pk>/', TargetDetailView.as_view(template_name='tom_targets/target_detail.html'), name='detail'),
    path('', include('bhtom_base.tom_common.urls')),
]
