from django.contrib import admin
from .models import AudioFile, VideoFile

class AudioFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'audio_type', 'file_name', 'file_url', 'is_generic', 'is_active', 'created_by', 'created_at', 'modified_at')
    list_filter = ('audio_type', 'is_generic', 'created_by')
    search_fields = ('title', 'file_name', 'file_url', 'description')
    ordering = ('-created_at',)
    list_per_page = 20

class VideoFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_type', 'file_name', 'file_url', 'is_generic', 'is_active', 'created_by', 'created_at', 'modified_at')
    list_filter = ('video_type', 'is_generic', 'created_by')
    search_fields = ('title', 'file_name', 'file_url', 'description')
    ordering = ('-created_at',)
    list_per_page = 20

# Register the models with the admin site
admin.site.register(AudioFile, AudioFileAdmin)
admin.site.register(VideoFile, VideoFileAdmin)
