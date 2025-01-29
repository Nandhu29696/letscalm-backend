#View

from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import AudioFileUploadSerializer, PlayAudioSerializer, EditAudioSerializer, AudioFileSerializer, VideoFileUploadSerializer
from django.shortcuts import get_object_or_404
from .models import AudioFile, VideoFile, VoiceToText, SentimentAnalysisResult
from django.db.models import Q
import requests
from django.http import StreamingHttpResponse
from rest_framework import status, permissions
import os
from .utils import speech_to_text, analyze_sentiment
import speech_recognition as sr
from django.core.files.storage import default_storage

# Manage Audio files 
class AudioFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AudioFileUploadSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            audio_file = serializer.save()  # The file is uploaded and metadata is saved here
            return Response({
                'msg': 'Audio file uploaded successfully',
                'data': {
                    'title': audio_file.title,
                    'description': audio_file.description,
                    'audio_type': audio_file.audio_type,
                    'file_url': audio_file.file_url,
                    'file_name': audio_file.file_name,
                 }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlayAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PlayAudioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_path = serializer.validated_data['file_path']
        # lambda_url =  os.environ.get('AWS_LAMBDA_URL_DOWNLOAD_FILE')
        base_dir = os.path.join(os.getcwd(), "local_storage")
        full_file_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_file_path):
            return Response({"error": "Audio file not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            def file_iterator(file_name, chunk_size=8192):
                with open(file_name, "rb") as file:
                    while chunk := file.read(chunk_size):
                        yield chunk

            response = StreamingHttpResponse(
                file_iterator(full_file_path),
                content_type="audio/mpeg"  # You can adjust this based on the file type
            )
            response["Content-Disposition"] = f"inline; filename={os.path.basename(file_path)}"
            return response
        
            # Play audio from s3 bucket using lambda_url
            # lambda_response = requests.post(lambda_url, json={"file_path": file_path})
            # if lambda_response.status_code != 200 or "download_url" not in lambda_response.json():
            #     return Response({"error": "Failed to fetch presigned URL."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # presigned_url = lambda_response.json()["download_url"]

            # # Step 2: Stream the audio from the presigned URL
            # audio_response = requests.get(presigned_url, stream=True)

            # if audio_response.status_code != 200:
            #     return Response({"error": "Failed to fetch audio file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            # # Step 3: Stream the audio file in the response
            # response = StreamingHttpResponse(
            #     audio_response.iter_content(chunk_size=8192),
            #     content_type=audio_response.headers.get("Content-Type", "audio/mpeg")
            # )
            # response["Content-Disposition"] = f"inline; filename={file_path.split('/')[-1]}"
            # return response

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, audio_id, *args, **kwargs):
        try:
            # Fetch the audio file by ID
            audio_file = AudioFile.objects.get(id=audio_id, created_by=request.user)

            # Validate and update using the serializer
            serializer = EditAudioSerializer(audio_file, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AudioFile.DoesNotExist:
            return Response({"error": "Audio file not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetAllAudioFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user_id = request.user.id
            audio_files = AudioFile.objects.filter(created_by_id=user_id)
            if not audio_files.exists():
                return Response({"message": "No audio files found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = AudioFileSerializer(audio_files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteAudioView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, audio_id, *args, **kwargs):
        try:
            audio_file = AudioFile.objects.get(id=audio_id, created_by=request.user)
            audio_file.is_active = False
            audio_file.save()
            return Response({"message": "Audio file deleted successfully."}, status=status.HTTP_200_OK)

        except AudioFile.DoesNotExist:
            return Response({"error": "Audio file not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TranscriptionAPIView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.user.id
        file = request.FILES['file']
        audio_file = VoiceToText.objects.create(file=file, file_status="file saved")
        
        try:
            file_path = audio_file.file.path
            transcription = analyze_sentiment(file_path)
            
            sentiment_analysis_result = SentimentAnalysisResult.objects.create(
                user_id=user_id,
                file_id=audio_file.id,
                scores=transcription['scores'],
                converted_text=transcription['text'],
                sentiment=transcription['sentiment'],
            )
            
            if sentiment_analysis_result.sentiment == 'neutral':
                audio_files = AudioFile.objects.filter(created_by_id=user_id).first()
                
                if not audio_files:
                    return Response({"message": "No audio files found."}, status=status.HTTP_404_NOT_FOUND)
                audio_files = AudioFile.objects.filter(created_by_id=user_id)
                serialized_audio_files = AudioFileSerializer(audio_files, many=True).data
                response_data = {
                    "data": serialized_audio_files,
                    "sentimentStatus": sentiment_analysis_result.sentiment
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "The sentiment is not happy."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Mange Video Files

class VidepFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = VideoFileUploadSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            video_file = serializer.save()
            return Response({
                'msg': 'Video file uploaded successfully',
                'data': {
                    'title': video_file.title,
                    'description': video_file.description,
                    'video_type': video_file.video_type,
                    'file_url': video_file.file_url,
                    'file_name': video_file.file_name,
                 }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)