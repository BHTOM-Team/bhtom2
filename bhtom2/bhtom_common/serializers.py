from rest_framework import serializers
from django.core import serializers as serial
from bhtom_base.bhtom_dataproducts.models import DataProduct, CCDPhotJob, ReducedDatum
from bhtom2.bhtom_calibration.models import Calibration_data
from bhtom_base.bhtom_targets.models import Target
from django_comments.models import Comment
from django.contrib.auth.models import User
from bhtom_custom_registration.bhtom_registration.models import LatexUser
import json

class CCDPhotJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CCDPhotJob
        fields = '__all__'

class DataProductSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    camera = serializers.SerializerMethodField()
    observatory_name = serializers.SerializerMethodField()
    observatory = serializers.SerializerMethodField()
    calibration_data = serializers.SerializerMethodField()
    ccdphot_result = serializers.SerializerMethodField()

    class Meta:
        model = DataProduct
        fields = '__all__'

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_user(self, obj):
        return obj.user.username

    def get_camera(self, obj):
        try:
            return obj.observatory.camera.prefix
        except AttributeError:
            return None

    def get_target_name(self, obj):
        return obj.target.name if obj.target else None

    def get_target(self, obj):
        return obj.target.id if obj.target else None

    def get_observatory_name(self, obj):
        try:
            return obj.observatory.camera.observatory.name
        except AttributeError:
            return None

    def get_observatory(self, obj):
        try:
            return obj.observatory.camera.observatory.id
        except AttributeError:
            return None


    def get_calibration_data(self, obj):
        
        cal = Calibration_data.objects.filter(dataproduct=obj).first()
        if not cal:
            return {
                'id': "",
                'time_photometry': "",
                'mjd': "",
                'calib_survey_filter': "",
                'standardised_to': "",
                'magnitude': "",
                'zp': "",
                'scatter': "",
                'number of datapoints used for calibration': "",
                'outlier fraction': "",
                'matching radius[arcsec]': "",
                'cpcs_results': {}
            }
        return {
            'id': cal.id or "",
            'time_photometry': cal.modified or "",
            'mjd': cal.mjd or "",
            'calib_survey_filter': f"{cal.use_catalog.survey or ''}/{cal.use_catalog.filters or ''}"  if cal.use_catalog else "",
            'standardised_to': f"{cal.survey or ''}/{cal.best_filter or ''}" if cal.survey and cal.best_filter else "",
            'magnitude': cal.mag or "",
            'mag_error': cal.mag_error or "",
            'zp': cal.zeropoint or "",
            'scatter': cal.scatter or "",
            'number of datapoints used for calibration': cal.npoints or "",
            'outlier fraction': cal.outlier_fraction or "",
            'matching radius[arcsec]': cal.match_distans or "",
            'cpcs_results': cal.cpcs_results if cal.cpcs_results is not None else {}
        }
    def get_ccdphot_result(self,obj):
        try:
            ccdphot = CCDPhotJob.objects.get(dataProduct_id = obj.id)
        except:
            ccdphot = None
        if not ccdphot:
            return {}
        serialized_ccdphot_data = serial.serialize('json', [ccdphot])
        ccdphot_data = json.loads(serialized_ccdphot_data)[0]
        return ccdphot_data["fields"]


class ReducedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReducedDatum
        fields = '__all__'

        

class CommentSerializer(serializers.ModelSerializer):
    target_name = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()

    def get_target_name(self, obj):
        target_name = Target.objects.get(id=obj.object_pk).name
        return target_name
    
    def get_target_id(self, obj):
        target_id = obj.object_pk
        return target_id
    
    class Meta:
        model = Comment
        fields = ['id','user_name','comment', 'submit_date','user_id','target_name','target_id'] 



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class AdminCreateUserSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=150, required=False)
    first_name = serializers.CharField(max_length=150, required=False)
    surname = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    affiliation = serializers.CharField(max_length=255, required=False, allow_blank=True)
    about = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        first_name = (attrs.get('firstname') or attrs.get('first_name') or '').strip()
        surname = attrs['surname'].strip()
        if not first_name:
            raise serializers.ValidationError({"firstname": "This field is required."})
        if not surname:
            raise serializers.ValidationError({"surname": "This field may not be blank."})

        attrs['first_name'] = first_name
        attrs['surname'] = surname
        username = f"{first_name.lower()}.{surname.lower()}"
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                "username": f"User with generated username '{username}' already exists."
            })
        attrs['username'] = username
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=password,
            first_name=validated_data['first_name'].strip(),
            last_name=validated_data['surname'].strip(),
            email=validated_data['email'].strip(),
            is_active=True,
        )
        LatexUser.objects.update_or_create(
            user=user,
            defaults={
                'latex_name': f"{user.first_name} {user.last_name}",
                'latex_affiliation': validated_data.get('affiliation', ''),
                'about_me': validated_data['about'],
            }
        )
        return user
