#Utill class

import boto3
from uuid import uuid4
from django.conf import settings
import os
import speech_recognition as sr
import audioread
import wave
import assemblyai as aai
import shutil
import soundfile as sf
from mutagen import File
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import download


ALLOWED_EXTENSIONS_AUDIO = ['mp3', 'wav', 'aac']
ALLOWED_EXTENSIONS_VIDEO = ['mp4', 'mkv', 'avi']

aai.settings.api_key = "17fd74a864f0411fa70c349b1ba66d8b" 

# Download VADER lexicon
download('vader_lexicon')

def is_allowed_file(file_name, allowed_extensions):
    """Check if the file has an allowed extension."""
    extension = file_name.split('.')[-1].lower()
    return extension in allowed_extensions

def transcribe_speech(audio_file):
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcript = transcriber.transcribe(audio_file, config)
    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        exit(1)
    return transcript.text

def analyze_sentiment(audio_file):
    analyzer = SentimentIntensityAnalyzer()
    text = transcribe_speech(audio_file)
    sentiment_scores = analyzer.polarity_scores(text)

    if sentiment_scores['compound'] >= 0.05:
        sentiment = 'happy'
    elif sentiment_scores['compound'] <= -0.05:
        sentiment = 'sad'
    else:
        sentiment = 'neutral'

    return {
        'text': text,
        'sentiment': sentiment,
        'scores': sentiment_scores
    }
    
# def upload_to_s3(file):
#     s3_client = boto3.client(
#         's3',
#         aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
#         aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
#         region_name=os.environ.get('AWS_REGION')
#     )
#     bucket_name = os.environ.get('AWS_BUCKET_NAME')

#     file_extension = file.name.split('.')[-1].lower()
#     if file_extension in ['mp3', 'wav', 'aac']:  # Allowed audio extensions
#         folder = 'audio'
#     elif file_extension in ['mp4', 'avi', 'mov']:  # Allowed video extensions
#         folder = 'video'
#     else:
#         raise ValueError("Unsupported file type")

#     unique_file_name = f"{folder}/{uuid4()}.{file_extension}"

#     try:
#         s3_client.upload_fileobj(
#             file,
#             bucket_name,
#             unique_file_name,
#             ExtraArgs={
#                 'ContentType': file.content_type 
#             }
#         )

#         file_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
#         return file_url, unique_file_name

#     except Exception as e:
#         print(f"Error uploading to S3: {str(e)}")
#         return None, None

def upload_to_local(file):
    base_dir = os.path.join(os.getcwd(), "local_storage")
    os.makedirs(base_dir, exist_ok=True) 
    
    file_extension = file.name.split('.')[-1].lower()
    if file_extension in ['mp3', 'wav', 'aac']:  
        folder = 'audio'
    elif file_extension in ['mp4', 'avi', 'mov']:
        folder = 'video'
    else:
        raise ValueError("Unsupported file type")

    # Create a subfolder for the file type
    folder_path = os.path.join(base_dir, folder)
    os.makedirs(folder_path, exist_ok=True)

    # Generate a unique file name and save the file
    unique_file_name = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(folder_path, unique_file_name)

    try:
        with open(file_path, 'wb') as local_file:
            for chunk in file.chunks():
                local_file.write(chunk)

        return file_path, unique_file_name
    except Exception as e:
        print(f"Error saving file locally: {str(e)}")
        return None, None

def get_file_format(file_path: str) -> str:
    try:
        audio_file = File(file_path)
        if audio_file is None:
            raise ValueError("File format could not be determined.")
        return audio_file.mime[0].split("/")[-1]  # Example: 'wav', 'mp3'
    except Exception as e:
        print(f"Error detecting file format: {e}")
        raise
    
def convert_to_wav(file_path: str, output_path: str) -> str:
    try:
        data, samplerate = sf.read(file_path)
        sf.write(output_path, data, samplerate, format='WAV', subtype='PCM_16')
        return output_path
    except Exception as e:
        print(f"Error converting to WAV: {e}")
        raise ValueError("File conversion to WAV failed.")

def validate_wav_file(file_path: str) -> bool:
    try:
        with wave.open(file_path, 'rb') as wav_file:
            if wav_file.getsampwidth() != 2:  # 16-bit PCM
                raise ValueError("WAV file is not PCM-encoded.")
            return True
    except wave.Error as e:
        print(f"Wave Error: {e}")
        return False
    except Exception as e:
        print(f"Error validating WAV file: {e}")
        return False
    
def prepare_voice_file(file_path: str) -> str:
    try:
        # Detect file format
        file_format = get_file_format(file_path)
        print(f"Detected file format: {file_format}")

        # If already WAV, validate
        if file_format == 'wav' and validate_wav_file(file_path):
            return file_path
        
        # Otherwise, convert to WAV
        wav_path = os.path.splitext(file_path)[0] + '_converted.wav'
        return convert_to_wav(file_path, wav_path)
    except Exception as e:
        print(f"Error preparing audio file: {e}")
        raise ValueError("Failed to prepare the audio file.")


def transcribe_audio(audio_data, language: str) -> str:
    r = sr.Recognizer()
    text = r.recognize_google(audio_data, language=language)
    return text


def speech_to_text(file_path: str, language: str) -> str:
    try:
        print(f"Processing file: {file_path}")

        if not os.path.exists(file_path):
            print("Error: File does not exist.")
            return None

        wav_file = prepare_voice_file(file_path)
        print(f"Converted to WAV: {wav_file}")

        with sr.AudioFile(wav_file) as source:
            recognizer = sr.Recognizer()
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data, language=language)
        return transcription
    except Exception as e:
        print(f"Error in transcription: {e}")
        raise 