from django.db import models
from django.contrib.auth import get_user_model


class Integration(models.Model):
    INTEGRATION_TYPES = (
        ('NOTION', 'Notion'),
        ('AIRTABLE', 'Airtable'),
        ('ASANA', 'Asana'),
        # Add more as needed
    )
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    is_active = models.BooleanField(default=True)
    credentials = models.JSONField(default=dict)  # Store OAuth tokens etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CaptureSync(models.Model):
    capture = models.ForeignKey('captures.Capture', on_delete=models.CASCADE)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255)  # ID in external system
    last_synced = models.DateTimeField()
    sync_status = models.CharField(max_length=20)  # SUCCESS, FAILED, PENDING