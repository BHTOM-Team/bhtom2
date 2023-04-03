from django.urls import path

from .views import CatalogQueryView

app_name = 'bhtom2.bhtom_catalogs'

urlpatterns = [
    path('query/', CatalogQueryView.as_view(), name='query'),
]
