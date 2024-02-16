from django.urls import path

from bhtom2.bhtom_observatory.rest.view import GetObservatoryApi, CreateObservatoryApi, UpdateObservatoryApi, \
    GetObservatoryMatrixApi, CreateObservatoryMatrixApi, DeleteObservatoryMatrixApi
from bhtom2.bhtom_observatory.views import CreateObservatory, UpdateObservatory, DeleteObservatory, ObservatoryList, \
    ObservatoryDetailView, DeleteUserObservatory, UpdateUserObservatory, CreateUserObservatory, CameraDetailView

app_name = 'bhtom2.bhtom_observatory'

urlpatterns = [
    path('getObservatoryList/', GetObservatoryApi.as_view()),
    path('createObservatory/', CreateObservatoryApi.as_view()),
    path('updateObservatory/', UpdateObservatoryApi.as_view()),
    path('getFavouriteObservatory/', GetObservatoryMatrixApi.as_view()),
    path('addFavouriteObservatory/', CreateObservatoryMatrixApi.as_view()),
    path('deleteFavouriteObservatory/', DeleteObservatoryMatrixApi.as_view()),

    path('create/', CreateObservatory.as_view(), name='create'),
    path('<int:pk>/update/', UpdateObservatory.as_view(), name='update'),
    path('<int:pk>/delete/', DeleteObservatory.as_view(), name='delete'),
    path('<int:pk>/', CameraDetailView.as_view(), name='detail'),
    path('', ObservatoryList.as_view(), name='list'),
    path('instrument/create/', CreateUserObservatory.as_view(), name='userObservatory_create'),
    path('user/<int:pk>/delete/', DeleteUserObservatory.as_view(), name='userObservatory_delete'),
    path('user/<int:pk>/update/', UpdateUserObservatory.as_view(), name='userObservatory_update'),
]
