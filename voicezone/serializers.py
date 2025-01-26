#serializers

from rest_framework import serializers
from .models import AudioFile
from voicezone.utils import upload_to_local  # Import the utility function

class AudioFileUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    audio_type = serializers.ChoiceField(choices=AudioFile.AUDIO_TYPES)
    file = serializers.FileField()

    def create(self, validated_data):
        title = validated_data['title']
        description = validated_data['description']
        audio_type = validated_data['audio_type']
        file = validated_data['file']
        created_by = self.context['request'].user
        # Upload file to S3 and get the file URL and name
        file_url, file_name = upload_to_local(file)

        if file_url is None:
            raise serializers.ValidationError("Failed to upload file to S3")

        # Save the metadata to the database
        audio_file = AudioFile.objects.create(
            title=title,
            description=description,
            audio_type=audio_type,
            file_name=file_name,
            file_url=file_url,
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
        fields = ['title', 'description', 'audio_type', 'is_generic']

    def validate_audio_type(self, value):
        if value not in dict(AudioFile.AUDIO_TYPES):
            raise serializers.ValidationError("Invalid audio type.")
        return value
    
class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = ['id', 'title', 'description', 'audio_type', 'file_name', 'file_url', 'is_generic', 'created_at', 'modified_at']