from django.contrib import admin

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera


class CameraInline(admin.TabularInline):
    model = Camera
    extra = 0
    
    def get_queryset(self, request):
        """
        Return the queryset for the inline formset.
        """
        queryset = super().get_queryset(request)
        return queryset.order_by('prefix')  # Order cameras by 'name'

    def activate_observatory(self, request, queryset):
        queryset.update(active_flg=True)

    def disable_observatory(self, request, queryset):
        queryset.update(active_flg=False)

    actions = [activate_observatory, disable_observatory]




class ObservatoryAdmin(admin.ModelAdmin):
    model = Observatory
    inlines = [CameraInline]
    list_display = ['name', 'lon', 'lat','altitude']
    ordering = ['name']

class ObservatoryMatrixAdmin(admin.ModelAdmin):
    model = ObservatoryMatrix
    list_display = ['camera', 'user', 'active_flg']
    exclude = ['seeing']
    ordering = ['camera']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'camera':
            kwargs['queryset'] = Camera.objects.order_by('prefix')  # Adjust this field if needed
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def activate_observatory(self, request, queryset):
        queryset.update(active_flg=True)

    def disable_observatory(self, request, queryset):
        queryset.update(active_flg=False)

    actions = [activate_observatory, disable_observatory]

# class CameraAdmin(admin.ModelAdmin):
#     model = Camera
#     list_display = '__all__'


admin.site.register(Observatory, ObservatoryAdmin)

admin.site.register(ObservatoryMatrix, ObservatoryMatrixAdmin)

