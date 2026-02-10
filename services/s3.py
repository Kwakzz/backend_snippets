from app.core.logging import logger
from app.core.config import settings
import boto3


s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.S3_USER_SECRET_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_USER_SECRET_ACCESS_KEY,
)


def delete_s3_folder_contents(
    bucket: str, 
    url_or_prefix: str, 
) -> None:
    
    """
    Delete all objects under a given S3 prefix. The prefix is extracted from a full URL or provided directly.
    """
    try:
        prefix = url_or_prefix
        if ".amazonaws.com/" in url_or_prefix:
            prefix = url_or_prefix.split(".amazonaws.com/")[1]
            prefix = "/".join(prefix.split("/")[:-1]) + "/"

        logger.info(f"Deleting all S3 files under prefix: {prefix}")

        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" in response:
            keys = [{"Key": obj["Key"]} for obj in response["Contents"]]
            s3_client.delete_objects(Bucket=bucket, Delete={"Objects": keys})
            for obj in keys:
                logger.info(f"Deleted from S3: {obj['Key']}")
                
    except Exception as e:
        logger.error(f"Error deleting files from S3: {str(e)}")
        raise
    
    
def delete_s3_file(
    bucket: str, 
    url_or_key: str, 
) -> None:
    """
    Delete a single file from S3. Accepts either a full S3 URL or a raw key.
    """
    try:
        key = url_or_key
        if url_or_key.startswith("https://"):
            # Example: https://my-bucket.s3.amazonaws.com/uploads/videos/12345.mp4
            key = url_or_key.split(".amazonaws.com/")[1]
        
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Deleted from S3: {key}")
    except Exception as e:
        logger.error(f"Error deleting file from S3: {str(e)}")
        raise
