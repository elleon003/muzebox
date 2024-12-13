from django.db import models

class Capture(models.Model):
    CAPTURE_TYPES = (
        ('TEXT', 'Text Note'),
        ('AUDIO', 'Audio Recording'),
        ('VIDEO', 'Video Recording'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    capture_type = models.CharField(max_length=5, choices=CAPTURE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('tags.Tag', blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)  # For storing format-specific metadata
    
    class Meta:
        ordering = ['-created_at']

class TextCapture(models.Model):
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    content = models.TextField()

class MediaCapture(models.Model):
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE)
    file = models.FileField(upload_to='captures/')
    duration = models.DurationField(null=True)
    file_size = models.BigIntegerField()  # in bytes

