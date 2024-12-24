from django.contrib import admin
from django.utils.html import format_html
from django import forms
from tinymce.widgets import TinyMCE
from .models import Capture, TextCapture, MediaCapture

class CaptureAdminForm(forms.ModelForm):
    """Base form for creating captures with type selection."""
    class Meta:
        model = Capture
        fields = ['title', 'capture_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'capture_type' in self.fields:
            self.fields['capture_type'].widget = forms.RadioSelect(choices=Capture.CAPTURE_TYPES)

class TextCaptureInline(admin.StackedInline):
    model = TextCapture
    extra = 1
    max_num = 1
    fields = ['content']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'content':
            kwargs['widget'] = TinyMCE()
        return super().formfield_for_dbfield(db_field, **kwargs)

class MediaCaptureInline(admin.StackedInline):
    model = MediaCapture
    extra = 1
    max_num = 1
    fields = ['file', 'description']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = TinyMCE()
        return super().formfield_for_dbfield(db_field, **kwargs)

@admin.register(Capture)
class CaptureAdmin(admin.ModelAdmin):
    form = CaptureAdminForm
    list_display = ('title', 'user', 'capture_type', 'created_at')
    list_filter = ('capture_type', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TextCaptureInline, MediaCaptureInline]  # Always include both inlines

    def get_formsets_with_inlines(self, request, obj=None):
        """Override to ensure proper inline initialization."""
        for inline in self.get_inline_instances(request, obj):
            # For new objects, yield all inlines (they'll be shown/hidden by JS)
            # For existing objects, only yield the appropriate inline
            if obj is None or (
                isinstance(inline, TextCaptureInline) and obj.capture_type == 'TEXT'
            ) or (
                isinstance(inline, MediaCaptureInline) and obj.capture_type in ['AUDIO', 'VIDEO']
            ):
                yield inline.get_formset(request, obj), inline

    def save_model(self, request, obj, form, change):
        """Set user when creating new capture."""
        if not change:  # Only set user on creation
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """Make capture_type readonly after creation."""
        if obj:  # Editing existing object
            return self.readonly_fields + ('capture_type',)
        return self.readonly_fields

    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }
        js = (
            'admin/js/jquery.init.js',
            'admin/js/inlines.js',
            'captures/admin/js/dynamic-inlines.js',  # Updated path to our custom JS
        )
