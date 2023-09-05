from django.urls import path

from bhtom2.bhtom_observatory.rest.view import GetObservatory,GetObservatoryMatrix, CreateObservatoryMatrix, \
    UpdateObservatoryMatrix, DeleteObservatoryMatrix
from bhtom2.bhtom_observatory.views import CreateObservatory, UpdateObservatory, DeleteObservatory, ObservatoryList, \
    ObservatoryDetailView, DeleteUserObservatory, UpdateUserObservatory, CreateUserObservatory

app_name = 'bhtom2.bhtom_observatory'

urlpatterns = [
    # path('getObservatory/', GetObservatory.as_view()),
    # path('createObservatory/', CreateObservatory.as_view()),
    # path('updateObservatory/<int:pk>/', UpdateObservatory.as_view()),
    # path('deleteObservatory/<int:pk>/', DeleteObservatory.as_view()),
    # path('getUserObservatory/', GetObservatoryMatrix.as_view()),
    # path('createUserObservatory/', CreateObservatoryMatrix.as_view()),
    # path('updateUserObservatory/<int:pk>/', UpdateObservatoryMatrix.as_view()),
    # path('deleteUserObservatory/<int:pk>/', DeleteObservatoryMatrix.as_view()),

    path('create/', CreateObservatory.as_view(), name='create'),
    path('<int:pk>/update/', UpdateObservatory.as_view(), name='update'),
    path('<int:pk>/delete/', DeleteObservatory.as_view(), name='delete'),
    path('<int:pk>/', ObservatoryDetailView.as_view(), name='detail'),
    path('', ObservatoryList.as_view(), name='list'),
    path('instrument/create/', CreateUserObservatory.as_view(), name='userObservatory_create'),
    path('user/<int:pk>/delete/', DeleteUserObservatory.as_view(), name='userObservatory_delete'),
    path('user/<int:pk>/update/', UpdateUserObservatory.as_view(), name='userObservatory_update'),
]
