from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify
from tinymce.models import HTMLField
import json
import uuid
import os

def get_upload_path(instance, filename):
    """
    Generate a unique path for uploaded files.
    Format: captures/<capture_type>/<year>/<month>/<uuid>.<ext>
    """
    ext = filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    capture_type = instance.capture.capture_type.lower()
    date = instance.capture.created_at
    return os.path.join(
        'captures',
        capture_type,
        str(date.year),
        str(date.month),
        filename
    )

class Capture(models.Model):
    """Base model for all types of captures (text, audio, video)."""
    CAPTURE_TYPES = (
        ('TEXT', 'Text Note'),
        ('AUDIO', 'Audio Recording'),
        ('VIDEO', 'Video Recording'),
    )
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='captures'
    )
    title = models.CharField(max_length=200)
    capture_type = models.CharField(max_length=5, choices=CAPTURE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('tags.Tag', blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.metadata:
            self.metadata = {}
        super().save(*args, **kwargs)

class TextCapture(models.Model):
    """Model for text-based captures with HTML content."""
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    content = HTMLField()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update word count in metadata
        word_count = len(self.content.split())
        self.capture.metadata['word_count'] = word_count
        self.capture.save()

class MediaCapture(models.Model):
    """Model for media-based captures (audio/video)."""
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=get_upload_path,
        max_length=500,
        storage=getattr(settings, 'MEDIA_STORAGE', None)
    )
    description = HTMLField(blank=True)
    duration = models.DurationField(null=True)
    file_size = models.BigIntegerField(null=True)  # in bytes
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
        # Update file metadata
        if self.file_size:
            self.capture.metadata['file_size'] = self.file_size
        if self.duration:
            self.capture.metadata['duration_seconds'] = self.duration.total_seconds()
        self.capture.save()
    
    def get_presigned_url(self, expiration=3600):
        """Generate a pre-signed URL for the media file."""
        if hasattr(self.file.storage, 'bucket_name'):
            try:
                return self.file.storage.url(
                    self.file.name,
                    parameters={'ResponseContentDisposition': f'inline; filename="{os.path.basename(self.file.name)}"'},
                    expire=expiration
                )
            except Exception as e:
                print(f"Error generating pre-signed URL: {e}")
        return self.file.url
