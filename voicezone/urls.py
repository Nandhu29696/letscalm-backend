from django.urls import path
from .views import AudioFileUploadView, PlayAudioView, EditAudioView, GetAllAudioFilesView, DeleteAudioView

urlpatterns = [
    path('upload-audio', AudioFileUploadView.as_view(), name='upload-audio'),
    path('audio/play', PlayAudioView.as_view(), name='audio-play'),
    path('audio/edit/<audio_id>', EditAudioView.as_view(), name='audio-edit'),
    path('audio/all/<user_id>', GetAllAudioFilesView.as_view(), name='get_all_audio_files'),
    path('audio/delete/<audio_id>', DeleteAudioView.as_view(), name='get_all_audio_files'),
]
