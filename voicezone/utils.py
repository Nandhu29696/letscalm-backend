#Utill class

import boto3
from uuid import uuid4
from django.conf import settings
import os

# Allowed extensions
ALLOWED_EXTENSIONS_AUDIO = ['mp3', 'wav', 'aac']
ALLOWED_EXTENSIONS_VIDEO = ['mp4', 'mkv', 'avi']

def is_allowed_file(file_name, allowed_extensions):
    """Check if the file has an allowed extension."""
    extension = file_name.split('.')[-1].lower()
    return extension in allowed_extensions

def upload_to_s3(file):
    """Upload file to AWS S3 and return the file URL and file name."""
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

    # Create a unique file name (folder/sub-folder/unique-id.ext)
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
