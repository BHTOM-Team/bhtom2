from django.urls import path
from . import views

app_name = 'bhtom_mymodule'

urlpatterns = [
    path('list/', views.mymodule_list, name='list'),
    path('details/', views.mymodule_details, name='details'),
]
