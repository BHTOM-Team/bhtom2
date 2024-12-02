from rest_framework import serializers
from bhtom_base.bhtom_dataproducts.models import DataProduct, CCDPhotJob
from bhtom2.bhtom_calibration.models import Calibration_data
from bhtom_base.bhtom_targets.models import Target
from django_comments.models import Comment

class DataProductSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    camera = serializers.SerializerMethodField()
    observatory_name = serializers.SerializerMethodField()
    observatory = serializers.SerializerMethodField()
    calibration_data = serializers.SerializerMethodField()

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
     
        if obj.status == "E":
            return  [{"status": "Error"}]
        elif obj.status == "P":
             return  [{"status": "In progress"}]
        else:
            calibration_data = Calibration_data.objects.filter(dataproduct=obj)

            return [
                {
                    'id': cal.id,
                    'time_photometry': cal.modified,
                    'mjd': cal.mjd,
                    'calib_survey_filter': f"{cal.use_catalog.survey}/{cal.use_catalog.filters}",
                    'standardised_to': f"{cal.survey}/{cal.best_filter}" if cal.survey and cal.best_filter else None,
                    'magnitude': cal.mag,
                    'zp': cal.zeropoint,
                    'scatter': cal.scatter,
                    'number of datapoints used for calibration': cal.npoints,
                    'outlier fraction': cal.outlier_fraction,
                    'matching radius[arcsec]': cal.match_distans
                }
                for cal in calibration_data
            ]



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