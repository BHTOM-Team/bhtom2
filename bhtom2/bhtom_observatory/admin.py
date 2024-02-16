from django.contrib import admin

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera


class CameraInline(admin.TabularInline):
    model = Camera
    extra = 0


class ObservatoryAdmin(admin.ModelAdmin):
    model = Observatory
    inlines = [CameraInline]
    list_display = ['name', 'lon', 'lat','active_flg']

    def activate_observatory(self, request, queryset):
        queryset.update(active_flg=True)

    def disable_observatory(self, request, queryset):
        queryset.update(active_flg=False)

    actions = [activate_observatory, disable_observatory]


class ObservatoryMatrixAdmin(admin.ModelAdmin):
    model = ObservatoryMatrix
    list_display = ['observatory', 'camera', 'user', 'active_flg']

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

