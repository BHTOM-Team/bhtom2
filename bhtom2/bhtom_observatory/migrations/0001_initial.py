# Generated by Django 4.0.4 on 2024-03-08 15:49

import bhtom2.bhtom_observatory.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Observatory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Observatory name')),
                ('lon', models.FloatField(db_index=True, validators=[django.core.validators.MinValueValidator(-180.0, message='longitude must be greater than -180.'), django.core.validators.MaxValueValidator(180.0, message='longitude must be less than 180.')], verbose_name='Longitude (West is positive) [deg]')),
                ('lat', models.FloatField(db_index=True, validators=[django.core.validators.MinValueValidator(-180.0, message='latitude must be greater than -90.'), django.core.validators.MaxValueValidator(180.0, message='latitude must be less than 90.')], verbose_name='Latitude (North is positive) [deg]')),
                ('altitude', models.FloatField(default=0.0, null=True, verbose_name='Altitude [m]')),
                ('calibration_flg', models.BooleanField(db_index=True, default='False', verbose_name='Only instrumental photometry file')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comments (e.g. hyperlink to the observatory website, camera specifications, telescope info)')),
                ('approx_lim_mag', models.FloatField(default=18.0, null=True, verbose_name='Approximate limit magnitude [mag]')),
                ('filters', models.CharField(blank=True, default='V,R,I', max_length=100, null=True, verbose_name='Filters (comma-separated list, as they are visible in FITS)')),
                ('origin', models.CharField(blank=True, max_length=255, null=True, verbose_name='Origin')),
                ('telescope', models.CharField(blank=True, max_length=255, null=True, verbose_name='Telescope name')),
                ('aperture', models.FloatField(blank=True, default=0.0, null=True, verbose_name='Aperture [m]')),
                ('focal_length', models.FloatField(default=0.0, null=True, verbose_name='Focal length [mm]')),
                ('seeing', models.FloatField(blank=True, default=0.0, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'observatories',
                'unique_together': {('name', 'lon', 'lat')},
            },
        ),
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('camera_name', models.CharField(max_length=255, verbose_name='Camera name')),
                ('active_flg', models.BooleanField(db_index=True, default='False')),
                ('prefix', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('gain', models.FloatField(default=2, null=True, verbose_name='Gain [e/ADU]')),
                ('example_file', models.FileField(null=True, upload_to=bhtom2.bhtom_observatory.models.example_file_path, verbose_name='Sample fits')),
                ('readout_noise', models.FloatField(default=2, null=True, verbose_name='Readout Noise [e]')),
                ('binning', models.IntegerField(default=1, null=True)),
                ('saturation_level', models.FloatField(default=63000, null=True, verbose_name='Saturation Level [ADU]')),
                ('pixel_scale', models.FloatField(default=0.8, null=True, verbose_name='Pixel Scale [arcseconds/pixel]')),
                ('readout_speed', models.FloatField(default=9999.0, null=True, verbose_name='Readout Speed [microseconds/pixel]')),
                ('pixel_size', models.FloatField(default=13.5, null=True, verbose_name='Pixel size [micrometers]')),
                ('date_time_keyword', models.CharField(default='DATE-OBS', max_length=255, verbose_name='Date & Time keyword')),
                ('time_keyword', models.CharField(default='TIME-OBS', max_length=255, verbose_name='Time keyword')),
                ('exposure_time_keyword', models.CharField(default='EXPTIME', max_length=255, verbose_name='Exposure time keyword')),
                ('mode_recognition_keyword', models.CharField(blank=True, default='', max_length=255, null=True, verbose_name='Mode recognition keyword name')),
                ('additional_info', models.TextField(blank=True, default='', null=True, verbose_name='Additional info')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('observatory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bhtom_observatory.observatory')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'cameras',
                'unique_together': {('observatory', 'camera_name')},
            },
        ),
        migrations.CreateModel(
            name='ObservatoryMatrix',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active_flg', models.BooleanField(default='True')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comments (e.g. hyperlink to the observatory website, camera specifications, telescope info)')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now_add=True, null=True)),
                ('number_of_uploaded_file', models.IntegerField(default=0)),
                ('file_size', models.FloatField(default=0)),
                ('last_file_process', models.DateTimeField(blank=True, null=True)),
                ('camera', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bhtom_observatory.camera')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'observatory matrix',
                'unique_together': {('user', 'camera')},
            },
        ),
    ]