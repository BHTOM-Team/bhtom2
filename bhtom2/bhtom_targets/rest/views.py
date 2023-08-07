from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response

from bhtom2.bhtom_targets.rest.serializers import TargetsSerializers
from bhtom_base.bhtom_common.hooks import run_hook
from bhtom_base.bhtom_targets.models import Target


class GetTargetList(generics.ListCreateAPIView):
    serializer_class = TargetsSerializers

    def get_queryset(self):
        query = Q()

        name = self.request.data.get('name', None)
        raMin = self.request.data.get('raMin', None)
        raMax = self.request.data.get('raMax', None)
        decMin = self.request.data.get('decMin', None)
        decMax = self.request.data.get('decMax', None)

        if name is not None:
            query &= Q(name=name)
        if raMin is not None:
            query &= Q(ra__gte=raMin)
        if raMax is not None:
            query &= Q(ra__lte=raMax)
        if decMin is not None:
            query &= Q(dec__gte=decMin)
        if decMax is not None:
            query &= Q(dec__lte=decMax)

        queryset = Target.objects.filter(query).order_by('created')

        return queryset


class TargetCreate(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        serializer = TargetsSerializers(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            run_hook('target_post_save', target=serializer.data, created=True)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class TargetUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Target.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TargetsSerializers(instance, data=request.data)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=404)


class DeleteObservatory(generics.RetrieveUpdateDestroyAPIView):
    queryset = Target.objects.all()
    serializer_class = TargetsSerializers

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response("OK", status=202)
