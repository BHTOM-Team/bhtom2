from django.urls import path

from .views import ProposalListView, ProposalDetailView

app_name = 'bhtom2.bhtom_observations'

urlpatterns = [
    path('', ProposalListView.as_view(), name='list'),
    path('<int:pk>/', ProposalDetailView.as_view(), name='detail'),
]
