from rest_framework import serializers
from bhtom_base.bhtom_dataproducts.models import DataProduct, CCDPhotJob
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
    fits_filter = serializers.SerializerMethodField()

    class Meta:
        model = DataProduct
        fields = '__all__'

    def get_user_name(self, obj):
        user_name = obj.user.first_name + " " + obj.user.last_name
        return user_name
    
    def get_user(self, obj):
        user = obj.user.username
        return user
    
    def get_camera(self, obj):
        camera = None
        try:
            camera = obj.observatory.camera.prefix
        except Exception as e:
            camera = None
        return camera
    
    def get_target_name(self, obj):
        target_name = obj.target.name if obj.target else None
        return target_name
    
    def get_target(self, obj):
        target = obj.target.id if obj.target else None
        return target
    
       
    def get_observatory_name(self, obj):
        observatory_name = None
        try:
            observatory_name  =  obj.observatory.camera.observatory.name
        except Exception as e:
            observatory_name = None
        return observatory_name
    
    def get_observatory(self, obj):
        observatory = None
        try:
            observatory  =  obj.observatory.camera.observatory.id
        except Exception as e:
            observatory = None
        return observatory
    
    def get_fits_filter(self, obj):
        try:
            ccdphotjob  =  CCDPhotJob.objects.get(dataProduct=obj.id)
            fits_filter = ccdphotjob.fits_filter
        except Exception as e:
            fits_filter = None
        return fits_filter
    



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