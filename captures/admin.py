from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import Capture, TextCapture, MediaCapture

class MetadataListFilter(admin.SimpleListFilter):
    """Custom filter for metadata fields."""
    title = 'metadata field'
    parameter_name = 'metadata_field'

    def lookups(self, request, model_admin):
        return (
            ('has_source_device', 'Has Source Device'),
            ('has_language', 'Has Language'),
            ('high_bitrate', 'High Bitrate (>128kbps)'),
            ('hd_resolution', 'HD Resolution'),
            ('s3_stored', 'Stored in S3'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'has_source_device':
            return queryset.filter(metadata__has_key='source_device')
        if self.value() == 'has_language':
            return queryset.filter(metadata__has_key='language')
        if self.value() == 'high_bitrate':
            return queryset.filter(metadata__bit_rate__gt=128000)
        if self.value() == 'hd_resolution':
            return queryset.filter(metadata__resolution__contains='1920')
        if self.value() == 's3_stored':
            return queryset.filter(metadata__has_key='storage_bucket')
        return queryset

class BaseMetadataForm(forms.ModelForm):
    """Base form for common metadata fields."""
    language = forms.ChoiceField(
        choices=[
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('it', 'Italian'),
            ('pt', 'Portuguese'),
            ('ru', 'Russian'),
            ('zh', 'Chinese'),
            ('ja', 'Japanese'),
            ('ko', 'Korean'),
        ],
        initial='en',
        help_text='Select the language of the content'
    )
    source_device = forms.ChoiceField(
        choices=[
            ('web', 'Web Browser'),
            ('mobile', 'Mobile App'),
            ('desktop', 'Desktop App'),
            ('api', 'API'),
            ('other', 'Other'),
        ],
        initial='web',
        help_text='Select the device or platform where this was captured'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate metadata fields from existing instance
            self.fields['language'].initial = self.instance.capture.metadata.get('language', 'en')
            self.fields['source_device'].initial = self.instance.capture.metadata.get('source_device', 'web')

class TextCaptureAdminForm(BaseMetadataForm):
    """Custom form for TextCapture admin to handle metadata fields."""
    class Meta:
        model = TextCapture
        fields = ['capture', 'content', 'language', 'source_device']

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Update metadata
        metadata = instance.capture.metadata
        metadata.update({
            'language': self.cleaned_data['language'],
            'source_device': self.cleaned_data['source_device'],
        })
        
        # Calculate word count and reading time
        word_count = len(instance.content.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        metadata.update({
            'word_count': word_count,
            'reading_time': reading_time,
        })
        
        instance.capture.metadata = metadata
        
        if commit:
            instance.save()
            instance.capture.save()
        
        return instance

class MediaCaptureAdminForm(BaseMetadataForm):
    """Custom form for MediaCapture admin to handle metadata fields."""
    # Audio fields
    sample_rate = forms.ChoiceField(
        choices=[
            (44100, '44.1 kHz'),
            (48000, '48 kHz'),
            (96000, '96 kHz'),
        ],
        initial=44100,
        required=False,
        help_text='Audio sample rate'
    )
    channels = forms.ChoiceField(
        choices=[
            (1, 'Mono'),
            (2, 'Stereo'),
            (6, '5.1 Surround'),
        ],
        initial=2,
        required=False,
        help_text='Audio channels'
    )
    audio_codec = forms.ChoiceField(
        choices=[
            ('mp3', 'MP3'),
            ('aac', 'AAC'),
            ('wav', 'WAV'),
            ('ogg', 'OGG Vorbis'),
        ],
        initial='mp3',
        required=False,
        help_text='Audio codec'
    )
    audio_bitrate = forms.ChoiceField(
        choices=[
            (96000, '96 kbps'),
            (128000, '128 kbps'),
            (192000, '192 kbps'),
            (256000, '256 kbps'),
            (320000, '320 kbps'),
        ],
        initial=128000,
        required=False,
        help_text='Audio bitrate'
    )
    
    # Video fields
    resolution = forms.ChoiceField(
        choices=[
            ('1280x720', 'HD (720p)'),
            ('1920x1080', 'Full HD (1080p)'),
            ('2560x1440', 'QHD (1440p)'),
            ('3840x2160', '4K (2160p)'),
        ],
        initial='1280x720',
        required=False,
        help_text='Video resolution'
    )
    frame_rate = forms.ChoiceField(
        choices=[
            (24.0, '24 fps'),
            (25.0, '25 fps'),
            (29.97, '29.97 fps'),
            (30.0, '30 fps'),
            (50.0, '50 fps'),
            (60.0, '60 fps'),
        ],
        initial=30.0,
        required=False,
        help_text='Video frame rate'
    )
    video_codec = forms.ChoiceField(
        choices=[
            ('h264', 'H.264/AVC'),
            ('h265', 'H.265/HEVC'),
            ('vp9', 'VP9'),
            ('av1', 'AV1'),
        ],
        initial='h264',
        required=False,
        help_text='Video codec'
    )
    video_bitrate = forms.ChoiceField(
        choices=[
            (1000000, '1 Mbps'),
            (2000000, '2 Mbps'),
            (4000000, '4 Mbps'),
            (8000000, '8 Mbps'),
            (16000000, '16 Mbps'),
        ],
        initial=2000000,
        required=False,
        help_text='Video bitrate'
    )

    class Meta:
        model = MediaCapture
        fields = ['capture', 'file', 'duration', 'file_size']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            metadata = self.instance.capture.metadata
            capture_type = self.instance.capture.capture_type

            if capture_type == 'AUDIO':
                self.fields['sample_rate'].initial = metadata.get('sample_rate', 44100)
                self.fields['channels'].initial = metadata.get('channels', 2)
                self.fields['audio_codec'].initial = metadata.get('codec', 'mp3')
                self.fields['audio_bitrate'].initial = metadata.get('bit_rate', 128000)
                
                # Hide video fields
                del self.fields['resolution']
                del self.fields['frame_rate']
                del self.fields['video_codec']
                del self.fields['video_bitrate']
            
            elif capture_type == 'VIDEO':
                self.fields['resolution'].initial = metadata.get('resolution', '1280x720')
                self.fields['frame_rate'].initial = metadata.get('frame_rate', 30.0)
                self.fields['video_codec'].initial = metadata.get('codec', 'h264')
                self.fields['video_bitrate'].initial = metadata.get('bit_rate', 2000000)
                
                # Hide audio fields
                del self.fields['sample_rate']
                del self.fields['channels']
                del self.fields['audio_codec']
                del self.fields['audio_bitrate']

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Update metadata
        metadata = instance.capture.metadata
        metadata.update({
            'language': self.cleaned_data['language'],
            'source_device': self.cleaned_data['source_device'],
        })
        
        # Update type-specific metadata
        if instance.capture.capture_type == 'AUDIO':
            metadata.update({
                'sample_rate': int(self.cleaned_data['sample_rate']),
                'channels': int(self.cleaned_data['channels']),
                'codec': self.cleaned_data['audio_codec'],
                'bit_rate': int(self.cleaned_data['audio_bitrate']),
            })
        elif instance.capture.capture_type == 'VIDEO':
            metadata.update({
                'resolution': self.cleaned_data['resolution'],
                'frame_rate': float(self.cleaned_data['frame_rate']),
                'codec': self.cleaned_data['video_codec'],
                'bit_rate': int(self.cleaned_data['video_bitrate']),
            })
        
        instance.capture.metadata = metadata
        
        if commit:
            instance.save()
            instance.capture.save()
        
        return instance

@admin.register(Capture)
class CaptureAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'capture_type', 'created_at', 'updated_at', 'display_metadata')
    search_fields = ('title', 'user__username', 'capture_type', 'metadata__storage_bucket', 'metadata__storage_key')
    list_filter = ('capture_type', 'created_at', 'updated_at', MetadataListFilter)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'formatted_metadata')

    def display_metadata(self, obj):
        """Format metadata for list display."""
        if not obj.metadata:
            return "No metadata"
        
        # Show key metadata fields based on capture type
        if obj.capture_type == 'TEXT':
            return f"Language: {obj.metadata.get('language', 'en')} | Words: {obj.metadata.get('word_count', 0)}"
        elif obj.capture_type == 'AUDIO':
            info = [
                f"Language: {obj.metadata.get('language', 'en')}",
                f"Codec: {obj.metadata.get('codec', 'Unknown')}",
                f"Bitrate: {obj.metadata.get('bit_rate', 0)/1000}kbps"
            ]
            return " | ".join(info)
        elif obj.capture_type == 'VIDEO':
            info = [
                f"Language: {obj.metadata.get('language', 'en')}",
                f"Resolution: {obj.metadata.get('resolution', 'Unknown')}",
                f"FPS: {obj.metadata.get('frame_rate', 0)}"
            ]
            return " | ".join(info)
        return str(obj.metadata)
    display_metadata.short_description = 'Metadata'

    def formatted_metadata(self, obj):
        """Format metadata as HTML for detail view."""
        if not obj.metadata:
            return "No metadata"
        
        html = ['<table style="width: 100%; border-collapse: collapse;">']
        html.append('<tr><th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Field</th><th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Value</th></tr>')
        
        # Group metadata fields
        storage_fields = ['storage_bucket', 'storage_key', 'etag']
        media_fields = ['codec', 'bit_rate', 'duration_seconds', 'file_size']
        basic_fields = [k for k in sorted(obj.metadata.keys()) if k not in storage_fields + media_fields]
        
        # Basic fields
        for key in basic_fields:
            html.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{key}</td><td style="padding: 8px; border: 1px solid #ddd;">{obj.metadata[key]}</td></tr>')
        
        # Storage fields if present
        if any(field in obj.metadata for field in storage_fields):
            html.append('<tr><td colspan="2" style="padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5;"><strong>Storage Information</strong></td></tr>')
            for key in storage_fields:
                if key in obj.metadata:
                    html.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{key}</td><td style="padding: 8px; border: 1px solid #ddd;">{obj.metadata[key]}</td></tr>')
        
        # Media fields if present
        if any(field in obj.metadata for field in media_fields):
            html.append('<tr><td colspan="2" style="padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5;"><strong>Media Information</strong></td></tr>')
            for key in media_fields:
                if key in obj.metadata:
                    value = obj.metadata[key]
                    if key == 'file_size':
                        value = f"{value / (1024 * 1024):.1f}MB"
                    elif key == 'bit_rate':
                        value = f"{value / 1000}kbps"
                    html.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{key}</td><td style="padding: 8px; border: 1px solid #ddd;">{value}</td></tr>')
        
        html.append('</table>')
        return format_html(''.join(html))
    formatted_metadata.short_description = 'Formatted Metadata'

@admin.register(TextCapture)
class TextCaptureAdmin(admin.ModelAdmin):
    form = TextCaptureAdminForm
    list_display = ('capture', 'preview_content', 'word_count', 'language', 'source_device')
    search_fields = ('capture__title', 'content')
    
    def preview_content(self, obj):
        """Show a preview of the content."""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    preview_content.short_description = 'Content Preview'
    
    def word_count(self, obj):
        """Display word count from metadata."""
        return obj.capture.metadata.get('word_count', 0)
    word_count.short_description = 'Word Count'
    
    def language(self, obj):
        """Display language from metadata."""
        return obj.capture.metadata.get('language', 'en')
    language.short_description = 'Language'
    
    def source_device(self, obj):
        """Display source device from metadata."""
        return obj.capture.metadata.get('source_device', 'web')
    source_device.short_description = 'Source Device'

@admin.register(MediaCapture)
class MediaCaptureAdmin(admin.ModelAdmin):
    form = MediaCaptureAdminForm
    list_display = ('capture', 'file_link', 'duration', 'file_size', 'media_info', 'language', 'source_device')
    search_fields = ('capture__title', 'file', 'capture__metadata__storage_bucket', 'capture__metadata__storage_key')
    list_filter = ('duration', 'file_size')
    readonly_fields = ('presigned_url', 'storage_info')
    
    def file_link(self, obj):
        """Display file with link to pre-signed URL."""
        try:
            url = obj.get_presigned_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.file.name)
        except Exception:
            return obj.file.name
    file_link.short_description = 'File'
    
    def presigned_url(self, obj):
        """Display pre-signed URL with different expiration options."""
        try:
            urls = [
                ('1 hour', obj.get_presigned_url(3600)),
                ('24 hours', obj.get_presigned_url(86400)),
                ('7 days', obj.get_presigned_url(604800)),
            ]
            html = ['<div style="margin-bottom: 10px;">Pre-signed URLs:</div>']
            for label, url in urls:
                html.append(f'<div style="margin-bottom: 5px;"><strong>{label}:</strong> ')
                html.append(f'<a href="{url}" target="_blank">{url}</a></div>')
            return mark_safe(''.join(html))
        except Exception as e:
            return f"Error generating pre-signed URLs: {str(e)}"
    presigned_url.short_description = 'Pre-signed URLs'
    
    def storage_info(self, obj):
        """Display detailed storage information."""
        if not hasattr(obj.file.storage, 'bucket_name'):
            return "Not using S3 storage"
            
        info = [
            ('Bucket', obj.capture.metadata.get('storage_bucket', 'N/A')),
            ('Storage Key', obj.capture.metadata.get('storage_key', 'N/A')),
            ('ETag', obj.capture.metadata.get('etag', 'N/A')),
            ('Content Type', obj.capture.metadata.get('content_type', 'N/A')),
        ]
        
        html = ['<table style="width: 100%; border-collapse: collapse;">']
        for label, value in info:
            html.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>{label}:</strong></td>')
            html.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{value}</td></tr>')
        html.append('</table>')
        
        return mark_safe(''.join(html))
    storage_info.short_description = 'Storage Information'
    
    def media_info(self, obj):
        """Display key media information from metadata."""
        if obj.capture.capture_type == 'AUDIO':
            return f"{obj.capture.metadata.get('codec', 'Unknown')} @ {obj.capture.metadata.get('bit_rate', 0)/1000}kbps"
        elif obj.capture.capture_type == 'VIDEO':
            return f"{obj.capture.metadata.get('resolution', 'Unknown')} @ {obj.capture.metadata.get('frame_rate', 0)}fps"
        return "N/A"
    media_info.short_description = 'Media Info'
    
    def language(self, obj):
        """Display language from metadata."""
        return obj.capture.metadata.get('language', 'en')
    language.short_description = 'Language'
    
    def source_device(self, obj):
        """Display source device from metadata."""
        return obj.capture.metadata.get('source_device', 'web')
    source_device.short_description = 'Source Device'
