from django.utils import timezone
from rest_framework import serializers
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera



class CameraSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request') and self.context['request'].method == 'POST':
            # Set required fields for POST requests
            self.fields['camera_name'].required = True
            self.fields['observatory'].required = True
            self.fields['user'].required = True

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
    cameras = serializers.SerializerMethodField()


    class Meta:
        model = Observatory
        fields = ('id', 'name', 'lon', 'lat', 'altitude', 'calibration_flg', 'comment',
                   'approx_lim_mag','origin', 'telescope', 'aperture','focal_length','seeing', 'filters', 'created', 'modified', 'cameras' )
        read_only_fields = ['created', 'modified']
        extra_kwargs = {'created_start': {'read_only': True},
                        'created_end': {'read_only': True}}
    
    def get_cameras(self, obj):
        cameras = Camera.objects.filter(observatory=obj)
        serializer = CameraSerializer(cameras, many=True)
        return serializer.data
    
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
        instance.origin = validated_data.get('origin', instance.origin)
        instance.telescope = validated_data.get('telescope', instance.telescope)
        instance.aperture = validated_data.get('aperture', instance.aperture)
        instance.focal_length = validated_data.get('focal_length', instance.focal_length)
        instance.seeing = validated_data.get('seeing', instance.seeing)
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
