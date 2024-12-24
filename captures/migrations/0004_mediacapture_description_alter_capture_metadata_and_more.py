# Generated by Django 5.1.4 on 2024-12-15 01:15

import tinymce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('captures', '0003_alter_mediacapture_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediacapture',
            name='description',
            field=tinymce.models.HTMLField(blank=True),
        ),
        migrations.AlterField(
            model_name='capture',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='mediacapture',
            name='file_size',
            field=models.BigIntegerField(null=True),
        ),
    ]
