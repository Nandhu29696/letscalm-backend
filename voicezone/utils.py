#Utill class

import boto3
from uuid import uuid4
from django.conf import settings
import os
import speech_recognition as sr
import audioread
import mimetypes
import wave
# import assemblyai as aai
import shutil
import soundfile as sf
from mutagen import File
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import download
from pydub import AudioSegment
import librosa
import io
import traceback


ALLOWED_EXTENSIONS_AUDIO = ['mp3', 'wav', 'aac']
ALLOWED_EXTENSIONS_VIDEO = ['mp4', 'mkv', 'avi']

# aai.settings.api_key = "17fd74a864f0411fa70c349b1ba66d8b" 

# Download VADER lexicon
download('vader_lexicon')

def is_allowed_file(file_name, allowed_extensions):
    extension = file_name.split('.')[-1].lower()
    return extension in allowed_extensions

# def transcribe_speech(audio_file):
#     transcriber = aai.Transcriber()
#     config = aai.TranscriptionConfig(speaker_labels=True)
#     transcript = transcriber.transcribe(audio_file, config)
#     if transcript.status == aai.TranscriptStatus.error:
#         print(f"Transcription failed: {transcript.error}")
#         exit(1)
#     return transcript.text

def convert_to_pcm_wav(file_path):
        try:
            audio_data = AudioSegment.from_file(file_path)
            audio_data = audio_data.set_frame_rate(16000).set_channels(1).set_sample_width(2)

            wav_io = io.BytesIO()
            audio_data.export(wav_io, format="wav")
            wav_io.seek(0)

            # Debug: Save the converted audio to check manually
            with open("converted_audio.wav", "wb") as f:
                f.write(wav_io.getvalue())
            print("✅ Converted audio saved as 'converted_audio.wav' for testing")

            return wav_io

        except Exception as e:
            print(f"❌ Error in audio conversion: {e}")
            return None

def recognize_audio(wav_io):
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(wav_io) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduce background noise
            audio = recognizer.record(source)

            print("🔍 Running Google Speech Recognition...")
            text = recognizer.recognize_google(audio)

            return text.strip() if text.strip() else "unrecognized"

    except sr.UnknownValueError:
        print("❌ Google Speech API could not understand the audio.")
        return "unrecognized"
    
    except sr.RequestError:
        print("❌ Google Speech API is unavailable or request failed.")
        return "Speech API unavailable"

    except Exception as e:
        print(f"❌ Error during speech recognition: {e}")
        return "recognition_error"

def analyze_sentiment(wav_io):
    analyzer = SentimentIntensityAnalyzer()
    text = recognize_audio(wav_io)
    # text = transcribe_speech(wav_io)
    if not text:
        return {"text": "", "sentiment": "unrecognized", "scores": {}}

    sentiment_scores = analyzer.polarity_scores(text)
    compound = sentiment_scores['compound']
    pos = sentiment_scores['pos']
    neg = sentiment_scores['neg']
    neu = sentiment_scores['neu']

    # Emotion Classification
    if compound >= 0.7:
        sentiment = 'very happy'
    elif 0.05 <= compound < 0.7:
        sentiment = 'happy'
    elif -0.05 < compound < 0.05:
        sentiment = 'neutral'
    elif -0.7 < compound <= -0.05:
        sentiment = 'sad'
    else:
        sentiment = 'very sad'

    # Additional Emotional States
    if neg > 0.6:
        sentiment = 'angry or frustrated'
    elif pos > 0.6:
        sentiment = 'joyful or elated'
    elif neu > 0.9:
        sentiment = 'calm or indifferent'
    elif 0.4 < neg < 0.6:
        sentiment = 'fearful or worried'
    elif 0.4 < pos < 0.6:
        sentiment = 'hopeful or optimistic'

    # Confusion or mixed emotions
    if 0.2 < neg < 0.4 and 0.2 < pos < 0.4:
        sentiment = 'confused or uncertain'

    return {
        'text': text,
        'sentiment': sentiment,
        'scores': sentiment_scores
    }
    
def upload_to_s3(file):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )
    bucket_name = os.environ.get('AWS_BUCKET_NAME')

    file_extension = file.name.split('.')[-1].lower()
    if file_extension in ['mp3', 'wav', 'aac']:  # Allowed audio extensions
        folder = 'audio'
    elif file_extension in ['mp4', 'avi', 'mov']:  # Allowed video extensions
        folder = 'video'
    else:
        raise ValueError("Unsupported file type")

    unique_file_name = f"{folder}/{uuid4()}.{file_extension}"

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            unique_file_name,
            ExtraArgs={
                'ContentType': file.content_type 
            }
        )

        file_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_file_name}"
        return file_url, unique_file_name

    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None, None

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

