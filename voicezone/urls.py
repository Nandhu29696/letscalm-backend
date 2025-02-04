from django.urls import path
from .views import AudioFileUploadView, PlayAudioView, EditAudioView, GetAllAudioFilesView, DeleteAudioView, TranscriptionAPIView, VidepFileUploadView, GetAllVideoFilesView, PlayVideoView

urlpatterns = [
    path('upload-audio', AudioFileUploadView.as_view(), name='upload-audio'),
    path('audio/play', PlayAudioView.as_view(), name='audio-play'),
    path('audio/edit/<audio_id>', EditAudioView.as_view(), name='audio-edit'),
    path('audio/all/<user_id>', GetAllAudioFilesView.as_view(), name='get_all_audio_files'),
    path('audio/delete/<audio_id>', DeleteAudioView.as_view(), name='get_all_audio_files'),
    path('transcribe', TranscriptionAPIView.as_view(), name='transcribe'),
    
    path('upload-video', VidepFileUploadView.as_view(), name='upload-video'),
    path('video/all/<user_id>', GetAllVideoFilesView.as_view(), name='get_all_video_files'),
    path('video/play', PlayVideoView.as_view(), name='video-play'),

]
