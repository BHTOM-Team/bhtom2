from django.utils import timezone

from rest_framework import serializers

from django.contrib.auth.models import User
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera

from bhtom_base.bhtom_dataproducts.models import DataProduct


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ('id', 'user', 'observatory', 'camera_name', 'active_flg', 'prefix', 'gain', 'example_file',
          'readout_noise', 'binning', 'saturation_level', 'pixel_scale', 'readout_speed', 'pixel_size',
          'date_time_keyword', 'time_keyword', 'exposure_time_keyword', 'mode_recognition_keyword',
          'additional_info', 'created', 'modified')
        
        read_only_fields = ['created', 'modified']
        extra_kwargs = {'created_start': {'read_only': True},
                        'created_end': {'read_only': True}}

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return data


class ObservatorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Observatory
        fields = ('id', 'name', 'lon', 'lat', 'altitude', 'calibration_flg', 'comment',
                   'approx_lim_mag', 'filters', 'created', 'modified')
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
        instance.comment = validated_data.get('comment', instance.comment)
        instance.approx_lim_mag = validated_data.get('approx_lim_mag', instance.approx_lim_mag)
        instance.filters = validated_data.get('filters', instance.filters)
        instance.modified = timezone.now()

        instance.save()
        return instance


class ObservatoryMatrixSerializers(serializers.ModelSerializer):
    camera_field = ObservatorySerializers(source='camera', read_only=True)

    class Meta:
        model = ObservatoryMatrix
        fields = ('id', 'user', 'camera', 'camera_field', 'active_flg', 'comment', 'created', 'modified')
        read_only_fields = ['created', 'modified']
        extra_kwargs = {'created_start': {'read_only': True},
                        'created_end': {'read_only': True}}

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return data

    def create(self, validated_data):
        cameraId = validated_data.get('camera', None)

        if cameraId is None:
            raise serializers.ValidationError("Camera is required")

        cameraRow = Camera.objects.get(id=cameraId.id)
        if not cameraRow.active_flg:
            raise serializers.ValidationError("Camera is not active")

        observatoryMatrix = ObservatoryMatrix.objects.create(**validated_data)
        return observatoryMatrix

    def update(self, instance, validated_data):

        camera_active_flg = instance.camera.active_flg
        if not camera_active_flg and instance.active_flg:
            raise serializers.ValidationError("Camera is not active")

        instance.active_flg = validated_data.get('active_flg', instance.active_flg)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.modified = timezone.now()

        instance.save()
        return instance

class DataProductSerializer(serializers.ModelSerializer):
    camera = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = DataProduct
        fields = '__all__'

    def get_user_name(self, obj):
        user_name = obj.camera.user.first_name + " " + obj.camera.user.last_name
        return user_name
    
    def get_user(self, obj):
        user = obj.camera.user.username
        return user
    
    def get_camera(self, obj):
        camera_name = obj.camera.camera_name
        return camera_name
    
    def get_target_name(self, obj):
        target_name = obj.target.name if obj.target else None
        return target_name
    
    def get_target(self, obj):
        target = obj.target.id if obj.target else None
        return target