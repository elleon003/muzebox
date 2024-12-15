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
    """
    Base model for all types of captures (text, audio, video).
    Handles common fields and metadata validation.
    """
    CAPTURE_TYPES = (
        ('TEXT', 'Text Note'),
        ('AUDIO', 'Audio Recording'),
        ('VIDEO', 'Video Recording'),
    )
    
    # Core fields
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
    
    # Metadata with validation
    metadata = models.JSONField(
        default=dict,
        help_text="Format-specific metadata. Structure varies by capture_type."
    )
    
    class Meta:
        ordering = ['-created_at']
        
    def clean(self):
        """Validate metadata structure based on capture_type."""
        super().clean()
        
        if not self.metadata:
            self.metadata = self.get_default_metadata()
            return
            
        required_fields = self.get_metadata_schema()
        
        # Validate required fields exist
        for field, field_type in required_fields.items():
            if field not in self.metadata:
                raise ValidationError(f"Missing required metadata field: {field}")
            if not isinstance(self.metadata[field], field_type):
                raise ValidationError(f"Invalid type for metadata field {field}. Expected {field_type.__name__}")
    
    def get_metadata_schema(self):
        """Define required metadata fields and their types based on capture_type."""
        base_schema = {
            'language': str,
            'source_device': str,
        }
        
        type_specific_schema = {
            'TEXT': {
                'word_count': int,
                'reading_time': int,  # in seconds
            },
            'AUDIO': {
                'sample_rate': int,
                'channels': int,
                'codec': str,
                'bit_rate': int,
            },
            'VIDEO': {
                'resolution': str,
                'frame_rate': float,
                'codec': str,
                'bit_rate': int,
            }
        }
        
        # Add storage-specific fields for media types
        if self.capture_type in ['AUDIO', 'VIDEO']:
            base_schema.update({
                'storage_bucket': str,
                'storage_key': str,
                'content_type': str,
                'etag': str,
            })
        
        return {**base_schema, **type_specific_schema.get(self.capture_type, {})}
    
    def get_default_metadata(self):
        """Provide default metadata values based on capture_type."""
        base_defaults = {
            'language': 'en',
            'source_device': 'web',
        }
        
        type_specific_defaults = {
            'TEXT': {
                'word_count': 0,
                'reading_time': 0,
            },
            'AUDIO': {
                'sample_rate': 44100,
                'channels': 2,
                'codec': 'mp3',
                'bit_rate': 128000,
                'storage_bucket': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''),
                'storage_key': '',
                'content_type': 'audio/mpeg',
                'etag': '',
            },
            'VIDEO': {
                'resolution': '1280x720',
                'frame_rate': 30.0,
                'codec': 'h264',
                'bit_rate': 2000000,
                'storage_bucket': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''),
                'storage_key': '',
                'content_type': 'video/mp4',
                'etag': '',
            }
        }
        
        return {**base_defaults, **type_specific_defaults.get(self.capture_type, {})}
    
    def save(self, *args, **kwargs):
        if not self.metadata:
            self.metadata = self.get_default_metadata()
        self.full_clean()
        super().save(*args, **kwargs)

class TextCapture(models.Model):
    """Model for text-based captures with HTML content."""
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    content = HTMLField()
    
    def save(self, *args, **kwargs):
        """Update metadata when saving text content."""
        super().save(*args, **kwargs)
        
        # Update word count and reading time
        word_count = len(self.content.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        self.capture.metadata.update({
            'word_count': word_count,
            'reading_time': reading_time,
        })
        self.capture.save()

class MediaCapture(models.Model):
    """Model for media-based captures (audio/video)."""
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=get_upload_path,
        max_length=500,  # Increased for S3 keys
        storage=getattr(settings, 'MEDIA_STORAGE', None)  # Use custom storage if configured
    )
    duration = models.DurationField(null=True)
    file_size = models.BigIntegerField()  # in bytes
    
    def save(self, *args, **kwargs):
        """Update metadata when saving media file."""
        super().save(*args, **kwargs)
        
        # Update file-related metadata
        storage_metadata = {
            'file_size': self.file_size,
            'duration_seconds': self.duration.total_seconds() if self.duration else None,
        }
        
        # Add storage-specific metadata if using S3
        if hasattr(self.file.storage, 'bucket_name'):
            storage_metadata.update({
                'storage_bucket': self.file.storage.bucket_name,
                'storage_key': self.file.name,
                'etag': getattr(self.file, 'etag', ''),
            })
        
        self.capture.metadata.update(storage_metadata)
        self.capture.save()
    
    def get_presigned_url(self, expiration=3600):
        """
        Generate a pre-signed URL for the media file.
        Only works with S3-compatible storage backends.
        
        Args:
            expiration (int): URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Pre-signed URL or regular URL if not using S3
        """
        if hasattr(self.file.storage, 'bucket_name'):
            try:
                return self.file.storage.url(
                    self.file.name,
                    parameters={'ResponseContentDisposition': f'inline; filename="{os.path.basename(self.file.name)}"'},
                    expire=expiration
                )
            except Exception as e:
                # Log the error and fall back to regular URL
                print(f"Error generating pre-signed URL: {e}")
        
        return self.file.url
