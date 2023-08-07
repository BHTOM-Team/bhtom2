from django.utils import timezone

from rest_framework import serializers

from bhtom2.bhtom_targets.utils import check_duplicate_source_names, check_for_existing_alias, coords_to_degrees, \
    check_for_existing_coords
from bhtom_base.bhtom_targets.models import Target


class TargetsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ('name', 'ra', 'dec', 'epoch')
        extra_kwargs = {'raMin': {'read_only': True},
                        'raMax': {'read_only': True},
                        'decMin': {'read_only': True},
                        'decMax': {'read_only': True}}

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        if data.ra < 0 or data.ra > 360 or data.dec < -90 or data.dec > 90:
            raise serializers.ValidationError("Coordinates beyond range")
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.ra = validated_data.get('ra', instance.ra)
        instance.dec = validated_data.get('dec', instance.dec)
        instance.epoch = validated_data.get('epoch', instance.altitude)
        instance.created = timezone.now()
        instance.save()
        return instance

    def create(self, validated_data):
        duplicate_names = check_duplicate_source_names(validated_data.name)
        existing_names = check_for_existing_alias(validated_data.name)
        validated_data.ra = coords_to_degrees(validated_data.ra, 'ra')
        validated_data.dec = coords_to_degrees(validated_data.dec, 'dec')
        stored = Target.objects.all()
        coords_names = check_for_existing_coords(validated_data.ra, validated_data.dec, 3. / 3600., stored)

        if len(coords_names) != 0:
            raise serializers.ValidationError("Source found already at these coordinates (rad 3 arcsec)")
        if duplicate_names or existing_names:
            raise serializers.ValidationError("Duplicate names.")

        validated_data.sace()