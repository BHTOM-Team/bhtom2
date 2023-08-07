from rest_framework.response import Response
from rest_framework import generics

import logging
from django.db.models import Q

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom2.bhtom_observatory.rest.serializers import ObservatorySerializers, ObservatoryMatrixSerializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
logger = logging.getLogger(__name__)


class GetObservatory(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
  
    serializer_class = ObservatorySerializers
  
    def get_queryset(self):
        query = Q()

        name = self.request.data.get('name', None)
        prefix = self.request.data.get('prefix', None)
        lon = self.request.data.get('lon', None)
        lat = self.request.data.get('lat', None)
        active_flg = self.request.data.get('active_flg', None)
        created_start = self.request.data.get('created_start', None)
        created_end = self.request.data.get('created_end', None)

        if name is not None:
            query &= Q(name=name)
        if prefix is not None:
            query &= Q(prefix=prefix)
        if lon is not None:
            query &= Q(lon=lon)
        if lat is not None:
            query &= Q(lat=lat)
        if active_flg is not None:
            query &= Q(active_flg=active_flg)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = Observatory.objects.filter(query).order_by('created')

        return queryset


class CreateObservatory(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ObservatorySerializers(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class UpdateObservatory(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Observatory.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ObservatorySerializers(instance, data=request.data)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class DeleteObservatory(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Observatory.objects.all()
    serializer_class = ObservatorySerializers

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response("OK", status=202)


class GetObservatoryMatrix(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    serializer_class = ObservatoryMatrixSerializers

    def get_queryset(self):
        query = Q()

        user = self.request.data.get('user', None)
        active_flg = self.request.data.get('active_flg', None)
        observatory = self.request.data.get('observatory', None)
        created_end = self.request.data.get('created_end', None)
        created_start = self.request.data.get('created_start', None)

        if user is not None:
            query &= Q(user=user)
        if active_flg is not None:
            query &= Q(active_flg=active_flg)
        if observatory is not None:
            query &= Q(observatory=observatory)
        if created_start is not None:
            query &= Q(created__gte=created_start)
        if created_end is not None:
            query &= Q(created__lte=created_end)

        queryset = ObservatoryMatrix.objects.filter(query).order_by('created')

        return queryset


class CreateObservatoryMatrix(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ObservatoryMatrixSerializers(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class UpdateObservatoryMatrix(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = ObservatoryMatrix.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ObservatoryMatrixSerializers(instance, data=request.data)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class DeleteObservatoryMatrix(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Observatory.objects.all()
    serializer_class = ObservatoryMatrixSerializers
    
    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response("OK", status=202)
