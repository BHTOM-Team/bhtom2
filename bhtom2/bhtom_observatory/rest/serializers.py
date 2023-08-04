from django.utils import timezone

from rest_framework import serializers

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix


class ObservatorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Observatory
        fields = ('id', 'name', 'lon', 'lat', 'altitude', 'calibration_flg', 'prefix', 'example_file', 'comment',
                  'active_flg', 'gain', 'readout_noise', 'binning', 'saturation_level', 'pixel_scale', 'readout_speed',
                  'pixel_size', 'approx_lim_mag', 'filters', 'created', 'modified')
        read_only_fields = ['created', 'modified']
        extra_kwargs = {'created_start': {'read_only': True},
                        'created_end': {'read_only': True}}

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.lon = validated_data.get('lon', instance.lon)
        instance.lat = validated_data.get('lat', instance.lat)
        instance.altitude = validated_data.get('altitude', instance.altitude)
        instance.calibration_flg = validated_data.get('calibration_flg', instance.calibration_flg)
        instance.prefix = validated_data.get('prefix', instance.prefix)
        instance.example_file = validated_data.get('example_file', instance.example_file)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.active_flg = validated_data.get('active_flg', instance.active_flg)
        instance.gain = validated_data.get('gain', instance.gain)
        instance.readout_noise = validated_data.get('readout_noise', instance.readout_noise)
        instance.binning = validated_data.get('binning', instance.binning)
        instance.saturation_level = validated_data.get('saturation_level', instance.saturation_level)
        instance.pixel_scale = validated_data.get('pixel_scale', instance.pixel_scale)
        instance.readout_speed = validated_data.get('readout_speed', instance.readout_speed)
        instance.pixel_size = validated_data.get('pixel_size', instance.pixel_size)
        instance.approx_lim_mag = validated_data.get('approx_lim_mag', instance.approx_lim_mag)
        instance.filters = validated_data.get('filters', instance.filters)
        instance.modified = timezone.now()

        instance.save()
        return instance


class ObservatoryMatrixSerializers(serializers.ModelSerializer):
    observatory_field = ObservatorySerializers(source='observatory', read_only=True)

    class Meta:
        model = ObservatoryMatrix
        fields = ('id', 'user', 'observatory', 'observatory_field', 'active_flg', 'comment', 'created', 'modified')
        read_only_fields = ['created', 'modified']
        extra_kwargs = {'created_start': {'read_only': True},
                        'created_end': {'read_only': True}}

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return data

    def create(self, validated_data):
        observatoryId = validated_data.get('observatory', None)

        if observatoryId is None:
            raise serializers.ValidationError("Observatory is required")

        observatoryRow = Observatory.objects.get(id=observatoryId.id)
        if not observatoryRow.active_flg:
            raise serializers.ValidationError("Observatory is not active")

        observatoryMatrix = ObservatoryMatrix.objects.create(**validated_data)
        return observatoryMatrix

    def update(self, instance, validated_data):

        observatory_active_flg = instance.observatory.active_flg
        if not observatory_active_flg and instance.active_flg:
            raise serializers.ValidationError("Observatory is not active")

        instance.active_flg = validated_data.get('active_flg', instance.active_flg)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.modified = timezone.now()

        instance.save()
        return instance
