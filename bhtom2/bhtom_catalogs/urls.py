from django.urls import path

from .views import CatalogQueryView, GetCatalogsApiView

app_name = 'bhtom2.bhtom_catalogs'


urlpatterns = [
    path('query/', CatalogQueryView.as_view(), name='query'),
    path('get-catalogs/',GetCatalogsApiView.as_view()),
]
