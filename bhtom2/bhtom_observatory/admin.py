from django.contrib import admin

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix


class ObservatoryAdmin(admin.ModelAdmin):
    model = Observatory
    list_display = ['name', 'lon', 'lat', 'example_file', 'active_flg']

    def activate_observatory(self, request, queryset):
        queryset.update(active_flg=True)

    def disable_observatory(self, request, queryset):
        queryset.update(active_flg=False)

    actions = [activate_observatory, disable_observatory]


class ObservatoryMatrixAdmin(admin.ModelAdmin):
    model = ObservatoryMatrix
    list_display = ['observatory', 'user', 'active_flg']

    def activate_observatory(self, request, queryset):
        queryset.update(active_flg=True)

    def disable_observatory(self, request, queryset):
        queryset.update(active_flg=False)

    actions = [activate_observatory, disable_observatory]


admin.site.register(Observatory, ObservatoryAdmin)

admin.site.register(ObservatoryMatrix, ObservatoryMatrixAdmin)
