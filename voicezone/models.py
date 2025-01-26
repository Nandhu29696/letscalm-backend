# Model.py


from django.db import models
from django.conf import settings

class AudioFile(models.Model):
    AUDIO_TYPES = [
        ("mp3", "MP3"),
        ("wav", "WAV"),
        ("aac", "AAC"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    audio_type = models.CharField(max_length=10, choices=AUDIO_TYPES)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    is_generic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Audio: {self.title} - {self.audio_type}"

class VideoFile(models.Model):
    VIDEO_TYPES = [
        ("mp4", "MP4"),
        ("mkv", "MKV"),
        ("avi", "AVI"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_type = models.CharField(max_length=10, choices=VIDEO_TYPES)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    is_generic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Video: {self.title} - {self.video_type}"
    

class VoiceToText(models.Model):
    file = models.FileField(upload_to='audio_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
