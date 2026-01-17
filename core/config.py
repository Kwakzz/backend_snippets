import os
from pydantic_settings import BaseSettings
from google.cloud import secretmanager
from app.core.logging import logger

client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_name: str, version: str = "latest") -> str:
    """Retrieves a secret from Secret Manager."""
    project_id = os.environ.get("GCP_PROJECT_NO") 
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"

    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8") # Decode from bytes to string
    except Exception as e:
        logger.error(f"Error accessing secret: {e}")
        return None  

class Settings(BaseSettings):
    
    ENV: str = os.environ.get("ENV", "dev")
    
    @property
    def GCP_PROJECT_ID(self):
        return get_secret("GCP_PROJECT_ID")
    
    @property
    def SECRET_KEY(self):
        return get_secret("SECRET_KEY")

    @property
    def DB_USER(self) -> str:
        return get_secret("DB_USER")
    
    @property
    def DB_PASSWORD(self) -> str:
        return get_secret("DB_PASSWORD")
    
    @property
    def DB_NAME(self) -> str:
        return get_secret("DB_NAME")
    
    @property
    def INSTANCE_CONNECTION_NAME(self) -> str:
        return get_secret(f"{self.ENV.upper()}_INSTANCE_CONNECTION_NAME")
    
    @property
    def EMAIL_USER_AWS_ACCESS_KEY_ID(self):
        return get_secret("EMAIL_USER_AWS_ACCESS_KEY_ID")

    @property
    def EMAIL_USER_AWS_SECRET_ACCESS_KEY(self):
        return get_secret("EMAIL_USER_AWS_SECRET_ACCESS_KEY")
    
    @property
    def ROOT_USER_AWS_ACCESS_KEY_ID(self):
        return get_secret("ROOT_USER_AWS_ACCESS_KEY_ID")

    @property
    def ROOT_USER_AWS_SECRET_ACCESS_KEY(self):
        return get_secret("ROOT_USER_AWS_SECRET_ACCESS_KEY")
    
    @property
    def S3_USER_SECRET_ACCESS_KEY(self):
        return get_secret("S3_USER_SECRET_ACCESS_KEY")
    
    @property
    def S3_USER_SECRET_ACCESS_KEY_ID(self):
        return get_secret("S3_USER_SECRET_ACCESS_KEY_ID")

    @property
    def AWS_STORAGE_BUCKET_NAME(self):
        return get_secret(f"AWS_STORAGE_BUCKET_NAME_{self.ENV.upper()}")
    
    @property
    def AWS_S3_REGION_NAME(self):
        return get_secret("AWS_S3_REGION_NAME")

    @property
    def AWS_S3_SIGNATURE_VERSION(self):
        return get_secret("AWS_S3_SIGNATURE_VERSION")

    @property
    def AWS_S3_FILE_OVERWRITE(self):
        value = get_secret("AWS_S3_FILE_OVERWRITE")
        return value == "True" if value is not None else False 

    @property
    def AWS_DEFAULT_ACL(self):
        return get_secret("AWS_DEFAULT_ACL")

    @property
    def FROM_EMAIL(self):
        return get_secret("FROM_EMAIL")

    @property
    def GEMINI_KEY(self):
        return get_secret("GEMINI_KEY")
    
    @property
    def ANDROID_GOOGLE_CLIENT_ID(self):
        return get_secret("ANDROID_GOOGLE_CLIENT_ID")
    
    @property
    def IOS_GOOGLE_CLIENT_ID(self):
        return get_secret("IOS_GOOGLE_CLIENT_ID")
    
    @property
    def GCS_TEMP_FILES_BUCKET(self):
        return get_secret("GCS_TEMP_FILES_BUCKET")
    
    @property
    def GCS_PERMANENT_FILES_BUCKET(self):
        return get_secret(f"GCS_PERMANENT_FILES_BUCKET_{self.ENV.upper()}")
    
    @property
    def STORAGE_ADMIN_SERVICE_ACCOUNT_KEY(self):
        return get_secret("STORAGE_ADMIN_SERVICE_ACCOUNT_KEY")
    
    @property
    def FIREBASE_SERVICE_ACCOUNT_KEY(self):
        return get_secret("FIREBASE_SERVICE_ACCOUNT_KEY")
    
    @property
    def VIDEO_PROCESSOR_TOKEN(self):
        return get_secret("VIDEO_PROCESSOR_TOKEN")
    
    @property
    def EBOOK_PROCESSOR_TOKEN(self):
        return get_secret("EBOOK_PROCESSOR_TOKEN")
    
    @property
    def VIDEO_PROCESSING_TOPIC_NAME(self):
        return f"video-processing-topic-{self.ENV.lower()}"
    
    @property
    def JOBS_SERVICE_ACCOUNT_KEY(self):
        return get_secret("JOBS_SERVICE_ACCOUNT_KEY")

    # Logging
    LOG_LEVEL: str = "INFO"


# Initialize settings globally
settings = Settings()