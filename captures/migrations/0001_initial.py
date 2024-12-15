# Generated by Django 5.1.4 on 2024-12-14 23:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from tinymce.models import HTMLField



class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tags', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Capture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('capture_type', models.CharField(choices=[('TEXT', 'Text Note'), ('AUDIO', 'Audio Recording'), ('VIDEO', 'Video Recording')], max_length=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('metadata', models.JSONField(default=dict)),
                ('tags', models.ManyToManyField(blank=True, to='tags.tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='captures', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MediaCapture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='captures/')),
                ('duration', models.DurationField(null=True)),
                ('file_size', models.BigIntegerField()),
                ('capture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='captures.capture')),
            ],
        ),
        migrations.CreateModel(
            name='TextCapture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', HTMLField()),
                ('capture', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='captures.capture')),
            ],
        ),
    ]