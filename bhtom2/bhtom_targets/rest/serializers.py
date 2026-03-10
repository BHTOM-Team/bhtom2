import re

from django.utils import timezone

from rest_framework import serializers

from bhtom2.bhtom_targets.utils import check_duplicate_source_names, check_for_existing_alias, coords_to_degrees, \
    check_for_existing_coords
from bhtom_base.bhtom_targets.models import Target, DownloadedTarget,TargetList

FORBIDDEN_TARGET_NAME_CHARS_RE = re.compile(r'[()/\\:]')
URL_LIKE_TARGET_NAME_RE = re.compile(
    r'(?i)\b(?:https?://|ftp://|www\.|javascript:|data:|file:|vbscript:|[a-z0-9-]+(?:\.[a-z0-9-]+)+)\b'
)
QUERY_LIKE_TARGET_NAME_RE = re.compile(r'(?i)(?:\?|&)[^=\s]{1,100}=')
ENCODED_URL_OR_QUERY_RE = re.compile(r'(?i)(?:%2f|%5c|%3a|%3f|%26|%3d|%28|%29)')


class TargetsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = (
            'name', 'ra', 'dec', 'epoch', 'description', 'classification', 'discovery_date', 'importance', 'cadence',
            'has_optical', 'has_infrared', 'has_radio', 'has_xray', 'has_gamma', 'has_polarimetry'
        )

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        ra = dec = 0

        # Apply stricter target name validation for create endpoint payloads.
        name = data.get('name')
        if name is not None:
            if FORBIDDEN_TARGET_NAME_CHARS_RE.search(name):
                raise serializers.ValidationError({'name': [r'Target name cannot contain any of: ( ) / \ :']})
            if (
                URL_LIKE_TARGET_NAME_RE.search(name)
                or QUERY_LIKE_TARGET_NAME_RE.search(name)
                or ENCODED_URL_OR_QUERY_RE.search(name)
            ):
                raise serializers.ValidationError({'name': ['Target name cannot contain web addresses or query strings.']})

        if 'ra' in data:
            ra = data['ra']
        if 'dec' in data:
            dec = data['dec']

        # Apply API defaults only for create. For partial update, omitted fields must stay unchanged.
        if self.instance is None:
            data.setdefault('epoch', 2000.0)
            data.setdefault('classification', 'Unknown')
            data.setdefault('importance', 9.98)
            data.setdefault('cadence', 1.0)

        if unknown:
            raise serializers.ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        if ra < 0 or ra > 360 or dec < -90 or dec > 90:
            raise serializers.ValidationError("Coordinates beyond range")
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.ra = validated_data.get('ra', instance.ra)
        instance.dec = validated_data.get('dec', instance.dec)
        instance.epoch = validated_data.get('epoch', instance.epoch)
        instance.classification = validated_data.get('classification', instance.classification)
        instance.discovery_date = validated_data.get('discovery_date', instance.discovery_date)
        instance.importance = validated_data.get('importance', instance.importance)
        instance.cadence = validated_data.get('cadence', instance.cadence)
        instance.has_optical = validated_data.get('has_optical', instance.has_optical)
        instance.has_infrared = validated_data.get('has_infrared', instance.has_infrared)
        instance.has_radio = validated_data.get('has_radio', instance.has_radio)
        instance.has_xray = validated_data.get('has_xray', instance.has_xray)
        instance.has_gamma = validated_data.get('has_gamma', instance.has_gamma)
        instance.has_polarimetry = validated_data.get('has_polarimetry', instance.has_polarimetry)
        instance.modified = timezone.now()
        instance.save()
        return instance

    def create(self, validated_data): #TODO add target name
        #duplicate_names = check_duplicate_source_names(validated_data['name'])
        #existing_names = check_for_existing_alias(validated_data['name'])
        validated_data['ra'] = coords_to_degrees(validated_data['ra'], 'ra')
        validated_data['dec'] = coords_to_degrees(validated_data['dec'], 'dec')
        validated_data['type'] = "SIDEREAL"
        stored = Target.objects.all()
        coords_names = check_for_existing_coords(validated_data['ra'], validated_data['dec'], 3. / 3600., stored)

        if len(coords_names) != 0:
            raise serializers.ValidationError("Source found already at these coordinates (rad 3 arcsec)")
        #if duplicate_names or existing_names:
          #  raise serializers.ValidationError("Duplicate names.")

        return Target.objects.create(**validated_data)


class TargetDownloadDataSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)



class DownloadedTargetSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    
    class Meta:
        model = DownloadedTarget
        fields = ('id', 'user', 'user_name', 'target', 'target_name', 'created', 'modified', 'download_type', 'ip_address')

    def get_user_name(self, obj):
        # Assuming `obj.user` is a foreign key to `User`
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return None
    
    def get_user(self, obj):
        # Return the username
        return obj.user.username if obj.user else None
    
    def get_target_name(self, obj):
        # Return the name of the target
        return obj.target.name if obj.target else None
    
    def get_target(self, obj):
        # Return the id of the target
        return obj.target.id if obj.target else None
    


class TargetsGroupsSerializer(serializers.ModelSerializer):

    class Meta:
            model = TargetList
            fields = ('id', 'name', 'created')
