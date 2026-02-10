import boto3
from app.core.config import settings

ses_client = boto3.client(
    "ses",
    region_name=settings.AWS_S3_REGION_NAME,
    aws_access_key_id=settings.EMAIL_USER_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.EMAIL_USER_AWS_SECRET_ACCESS_KEY,
)

def send_email(
    to_email: str, 
    subject: str, 
    body_html: str, 
    body_text: str = ""
):
    response = ses_client.send_email(
        Source="no-reply@wonderspaced.com",  
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject},
            "Body": {
                "Text": {"Data": body_text},
                "Html": {"Data": body_html},
            },
        },
        ReplyToAddresses=["wonderspacedapp@gmail.com"]
    )
    return response
