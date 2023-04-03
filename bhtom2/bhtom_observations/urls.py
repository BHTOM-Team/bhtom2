from django.urls import path

from .views import ProposalListView

app_name = 'bhtom2.bhtom_observations'

urlpatterns = [
    path('', ProposalListView.as_view(), name='list'),
]
