#serializers

from rest_framework import serializers
from .models import AudioFile, VideoFile, SentimentTypes, SentimentAnalysisResult
from voicezone.utils import upload_to_s3, upload_to_local  
import os

def handle_file_upload(file):
    upload_type = os.environ.get('STORAGE_TYPE')
    if upload_type == 's3':
        file_url, file_name = upload_to_s3(file)
    else:
        file_url, file_name = upload_to_local(file)

    return file_url, file_name

class AudioFileUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    sentiment_type = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    audio_type = serializers.ChoiceField(choices=AudioFile.AUDIO_TYPES)
    file = serializers.FileField()

    def create(self, validated_data):
        title = validated_data['title']
        sentiment_type = validated_data['sentiment_type']
        description = validated_data['description']
        audio_type = validated_data['audio_type']
        file = validated_data['file']
        created_by = self.context['request'].user
        # Upload file to S3 and get the file URL and name
        file_url, file_name = handle_file_upload(file)

        if file_url is None:
            raise serializers.ValidationError("Failed to upload file to S3")

        # Save the metadata to the database
        audio_file = AudioFile.objects.create(
            title=title,
            description=description,
            audio_type=audio_type,
            file_name=file_name,
            file_url=file_url,
            sentiment_type=sentiment_type,
            created_by=created_by 
        )
        return audio_file
    
    def update(self, instance, validated_data):
        if 'created_by' in validated_data:
            validated_data.pop('created_by')  # Prevent changes to the owner
        return super().update(instance, validated_data)

class PlayAudioSerializer(serializers.Serializer):
    file_path = serializers.CharField(required=True)

    def validate_file_path(self, value):
        if not value:
            raise serializers.ValidationError("File path is required.")
        return value
     
class EditAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = ['title', 'description', 'audio_type', 'is_generic','sentiment_type']

    def validate_audio_type(self, value):
        if value not in dict(AudioFile.AUDIO_TYPES):
            raise serializers.ValidationError("Invalid audio type.")
        return value
    
class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = ['id', 'title', 'description', 'audio_type', 'file_name', 'file_url', 'is_generic', 'sentiment_type','created_at', 'modified_at']
        
class VideoFileUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    video_type = serializers.ChoiceField(choices=VideoFile.VIDEO_TYPES)
    sentiment_type = serializers.CharField(max_length=255)
    file = serializers.FileField()

    def create(self, validated_data):
        title = validated_data['title']
        sentiment_type = validated_data['sentiment_type']
        description = validated_data['description']
        video_type = validated_data['video_type']
        file = validated_data['file']
        created_by = self.context['request'].user
        file_url, file_name = upload_to_s3(file)

        if file_url is None:
            raise serializers.ValidationError("Failed to upload file to S3")

        video_file = VideoFile.objects.create(
            title=title,
            description=description,
            video_type=video_type,
            file_name=file_name,
            file_url=file_url,
            sentiment_type=sentiment_type,
            created_by=created_by 
        )
        return video_file
    
    def update(self, instance, validated_data):
        if 'created_by' in validated_data:
            validated_data.pop('created_by') 
        return super().update(instance, validated_data)

class VideoFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFile
        fields = ['id', 'title', 'description', 'video_type','sentiment_type', 'file_name', 'file_url', 'is_generic', 'created_at', 'modified_at']
        
class PlayVideoSerializer(serializers.Serializer):
    file_path = serializers.CharField(required=True)

    def validate_file_path(self, value):
        if not value:
            raise serializers.ValidationError("File path is required.")
        return value
    
class SentimentTypeSerializer(serializers.Serializer):
    sentiment_type = serializers.CharField(max_length=255)
    
    def create(self, validated_data):
        sentiment_type = validated_data['sentiment_type']
        user = self.context['request'].user
        
        # Save the metadata to the database
        sentiment_data = SentimentTypes.objects.create(
            sentiment_type=sentiment_type,
            user=user 
        )
        return sentiment_data
    
class SentimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentTypes
        fields = ['id', 'sentiment_type', 'is_active', 'created_at']

class SentimentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentAnalysisResult
        fields = ['id', 'file_id', 'scores', 'converted_text', 'sentiment','created_at']
        
        