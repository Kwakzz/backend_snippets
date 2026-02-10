from datetime import timedelta
import json
import os
from pathlib import Path
import requests
from urllib.parse import urlparse

from app.core.exceptions import InternalServerError, ValidationError
from app.core.logging import logger
from app.core.config import settings
from google.cloud import storage
from google.oauth2 import service_account

from app.utils.file import FileExtension, generate_unique_filename, get_file_content_type, validate_file_extension
    

GCS_PUBLIC_OBJECT_BASE_URL = "https://storage.googleapis.com/"

storage_admin_sa_key_json_str = settings.STORAGE_ADMIN_SERVICE_ACCOUNT_KEY
storage_admin_sa_info = json.loads(storage_admin_sa_key_json_str)
storage_admin_sa_credentials = service_account.Credentials.from_service_account_info(storage_admin_sa_info)
project = storage_admin_sa_credentials.project_id

    

def delete_blob_from_gcs(blob_public_url: str) -> None:
    """Delete from blob from GCS by getting the blob and bucket names from its public GCS URL.

    Args:
        blob_public_url (str): Blob's public URL

    Raises:
        ValueError: GCS public URL format is invalid. Appropriate format is "https://storage.googleapis.com/{bucket_name}/{folder}/{filename}"
    """
    
    try:
        storage_client = storage.Client(
            credentials=storage_admin_sa_credentials,
            project=project
        )
        parsed_url = urlparse(blob_public_url)
        
        # Extract bucket name & blob path
        path_parts = parsed_url.path.lstrip("/").split("/", 1)
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GCS URL format: {blob_public_url}")

        bucket_name, blob_name = path_parts
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        logger.info(f"Deleting: {bucket_name}/{blob_name}")

        if blob.exists():
            blob.delete()
            logger.info(f"File {blob_name} deleted from {bucket_name}.")
        else:
            logger.info(f"File {blob_name} not found in {bucket_name}.")

    except Exception as e:
        logger.error(f"Error deleting blob: {e}")
        raise 


def get_file_metadata_from_gcs_public_url(gcs_public_url: str)-> dict:
    
    """Retrieves file metadata (name, extension, size) from a public GCS URL.

    Args:
        gcs_url (str): The public GCS URL of the file

    Raises:
        ValueError: If GCS URL format is invalid.
        FileNotFoundError: If GCS object not found.

    Returns:
        dict: Contains the following keys: name, extension and size
    """

    try:
        storage_client = storage.Client(
            credentials=storage_admin_sa_credentials,
            project=project
        )
        parsed_url = urlparse(gcs_public_url)
        # Extract bucket name & blob path
        path_parts = parsed_url.path.lstrip("/").split("/", 1)
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GCS URL format: {gcs_public_url}")

        bucket_name, blob_name = path_parts
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise FileNotFoundError(f"GCS object not found: {gcs_public_url}")
        
        blob.reload()

        file_name = os.path.basename(blob_name)
        file_extension = os.path.splitext(file_name)[1].lstrip(".").lower()
        file_size = blob.size

        return {
            "name": file_name,
            "extension": file_extension,
            "size": file_size,
        }

    except ValueError as e:
        logger.error(f"Invalid GCS URL: {e}")
        raise
    
    except FileNotFoundError as e:
        logger.error(e)
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving GCS metadata: {str(e)}")
        raise


def download_file_from_gcs(
    public_gcs_url: str, 
    local_path: str
)-> str:
    
    """Downloads a file from a public GCS URL to local storage (synchronous).

    Args:
        public_gcs_url (str): File's public GCS URL
        local_path (str): Path the downloaded file should be stored in.

    Returns:
        str: Path the downloaded file is stored in.
    """

    try:
        response = requests.get(public_gcs_url, stream=True, timeout=600) 
        response.raise_for_status()  

        # Create necessary directories
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as f:  
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)

        return local_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading from GCS: {str(e)}", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Error downloading from GCS: {str(e)}", exc_info=True)
        raise

    
def get_gcs_upload_signed_url(
    filename: str,
    folder: str,
    content_type: str,
    bucket_name: str
) -> dict:
    """
    Get the public and signed upload URLs for a file. Upon retrieving the signed URL, you must upload within the expiry time (set to 1 hour in this app), add a header with the key-value {"X-Goog-ACL": "public-read"} to ensure the object is accessible via a public URL, and upload the file using the content type/extension specified as a binary.

    Args:
        filename (str): Name of the file plus its extension.
        folder (str): folder to store the file in the specified GCS bucket.
        content_type (str): content type of the file
        bucket_name (str): GCS bucket to store the file in.

    Raises:
        InternalServerError: If there's a bug in the code, insufficient credentials or problem from GCS.

    Returns:
        dict: Contains the keys, "upload_url" and "public_url". Upload file to GCS via the upload URL, and access via the public URL once retrieved.
    """
    try:        
        storage_client = storage.Client(
            credentials=storage_admin_sa_credentials,
            project=project
        )
        
        bucket = storage_client.bucket(bucket_name) 
        blob = bucket.blob(f"{folder}/{filename}")

        upload_url = blob.generate_signed_url(
            
            version="v4",
            expiration=timedelta(hours=1),
            content_type=content_type,  # Correct content-type ensures object renders properly.
            method="PUT",  # Use PUT for uploads
            headers={"x-goog-acl": "public-read"} # When you make a request with the signed URL, include this param-key pair in the header
        )
                
        public_url = f"{GCS_PUBLIC_OBJECT_BASE_URL}{bucket_name}/{folder}/{filename}"
        
        return {
            "upload_url": upload_url, 
            "public_url": public_url
        }
    
    except Exception as e:
        logger.error("Error getting GCS signed URL: {}", str(e), exc_info=True)
        raise InternalServerError()


def get_avatar_signed_url(filename) -> dict:
    try:
        validate_file_extension(
            filename, 
            [FileExtension.JPG.value, FileExtension.JPEG.value, FileExtension.PNG.value]
        )        
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.AVATARS_FOLDER, 
            content_type, 
            settings.GCS_PERMANENT_FILES_BUCKET
        )
    except ValidationError as e:
        raise


def get_thumbnail_signed_url(filename: str) -> dict:
    try:
        validate_file_extension(
            filename, 
            [FileExtension.JPG.value, FileExtension.JPEG.value, FileExtension.PNG.value]
        )        
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.THUMBNAILS_FOLDER, 
            content_type, 
            settings.GCS_PERMANENT_FILES_BUCKET
        )
    except ValidationError as e:
        raise


def get_theme_icon_signed_url(filename: str) -> dict:
    try:
        validate_file_extension(
            filename, 
            [FileExtension.JPG.value, FileExtension.JPEG.value, FileExtension.PNG.value]
        )
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.THEME_ICONS_FOLDER, 
            content_type, 
            settings.GCS_PERMANENT_FILES_BUCKET
        )
    except ValidationError as e:
        raise
    

def get_video_signed_url(filename: str) -> dict:
    try:
        validate_file_extension(
            filename, 
            [FileExtension.MP4.value]
        )
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.VIDEOS_FOLDER, 
            content_type, 
            settings.GCS_TEMP_FILES_BUCKET
        )
    except ValidationError as e:
        logger.error("Video extension not allowed: {}", str(e), exc_info=True)
        raise


def get_ebook_signed_url(filename) -> dict:
    try:       
        validate_file_extension(
            filename, 
            [FileExtension.PDF.value]
        )
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.EBOOKS_FOLDER, 
            content_type, 
            settings.GCS_PERMANENT_FILES_BUCKET
        )
    except ValidationError as e:
        logger.error("eBook extension not allowed: {}", str(e), exc_info=True)
        raise
   
   
def get_quiz_signed_url(filename) -> dict:
    try:       
        validate_file_extension(
            filename, 
            [FileExtension.PDF.value, FileExtension.DOCX.value]
        )
        content_type = get_file_content_type(filename)
        filename = generate_unique_filename(filename)
        return get_gcs_upload_signed_url(
            filename, 
            settings.QUIZZES_FOLDER, 
            content_type, 
            settings.GCS_TEMP_FILES_BUCKET
        )
    except ValidationError as e:
        logger.error("Quiz extension not allowed: {}", str(e), exc_info=True)
        raise