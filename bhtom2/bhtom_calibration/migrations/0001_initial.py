# Generated by Django 4.0.4 on 2024-03-08 15:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bhtom_dataproducts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalogs',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('survey', models.TextField(editable=False)),
                ('filters', models.TextField(editable=False)),
                ('isActive', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Calibration_data',
            fields=[
                ('id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('C', 'TO DO'), ('P', 'IN PROGRESS'), ('S', 'SUCCESS'), ('E', 'ERROR')], db_index=True, default='C', max_length=1)),
                ('status_message', models.TextField(blank=True, null=True)),
                ('mjd', models.FloatField()),
                ('exp_time', models.FloatField(blank=True, null=True)),
                ('mag', models.FloatField(blank=True, null=True)),
                ('mag_error', models.FloatField(blank=True, null=True)),
                ('ra', models.FloatField(blank=True, null=True)),
                ('dec', models.FloatField(blank=True, null=True)),
                ('zeropoint', models.FloatField(blank=True, null=True)),
                ('outlier_fraction', models.FloatField(blank=True, null=True)),
                ('scatter', models.FloatField(blank=True, null=True)),
                ('npoints', models.IntegerField(blank=True, null=True)),
                ('processing_time', models.FloatField(blank=True, null=True)),
                ('created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('modified', models.DateTimeField(blank=True, null=True)),
                ('start_processing', models.DateTimeField(blank=True, null=True)),
                ('best_filter', models.CharField(blank=True, max_length=5, null=True)),
                ('survey', models.CharField(blank=True, max_length=32, null=True)),
                ('match_distans', models.FloatField(default=0.5)),
                ('no_plot', models.BooleanField(default=True)),
                ('calibration_plot', models.TextField(blank=True, null=True)),
                ('number_tries', models.IntegerField(default=0)),
                ('dataproduct', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bhtom_dataproducts.dataproduct')),
                ('use_catalog', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bhtom_calibration.catalogs')),
            ],
            options={
                'verbose_name': 'cpcs processing file',
                'verbose_name_plural': 'calibration_data',
            },
        ),
    ]