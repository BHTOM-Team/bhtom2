
# Generated by Django 4.0.4 on 2024-05-22 08:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bhtom_observatory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observatory',
            name='comment',
            field=models.TextField(blank=True, null=True, verbose_name='Comments (e.g. camera specifications, telescope info)'),
        ),
        migrations.AlterField(
            model_name='observatory',
            name='lon',
            field=models.FloatField(db_index=True, validators=[django.core.validators.MinValueValidator(-180.0, message='longitude must be greater than -180.'), django.core.validators.MaxValueValidator(180.0, message='longitude must be less than 180.')], verbose_name='Longitude (East is positive) [deg]'),
        ),
    ]