# Generated by Django 5.1.4 on 2024-12-13 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.CharField(default='staff', max_length=255),
            preserve_default=False,
        ),
    ]