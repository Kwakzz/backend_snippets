from firebase_admin import messaging
from app.core.logging import logger
from app.schemas.response import SuccessResponse
from enum import Enum
from app.services import firebase_init


class NotificationTopic(Enum):
    ALL_USERS = "all_users"
    

async def notify_all_users(
    title: str,
    body: str,
    topic: NotificationTopic = NotificationTopic.ALL_USERS
):
    """Send a notification to all users subscribed to a topic using Firebase Cloud Messaging

    Args:
        title (str): Notification title
        body (str): Notification body
        topic (NotificationTopic): Topic name to send notification to. Defaults to NotificationTopic.ALL_USERS
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic.value
        )

        response = messaging.send(message)
        logger.info(f"Notification sent to topic '{topic.value}': {response}")
        return SuccessResponse(
            message=f"Notification sent to topic {topic.value}",
            data=response
        )
    
    except Exception as e:
        logger.error("Error sending topic notification: {}", str(e), exc_info=True)
        raise


async def notify_user(
    device_token: str, 
    title: str, 
    body: str
):
    """Send a notification to a device using Firebase Cloud Messaging(FCM)

    Args:
        device_token (str): token of device
        title (str): title of notification
        body (str): body of notification

    Returns:
        SuccessResponse: Contains a message saying "Notification sent to {device token}" and a data value equal to a message ID from Firebase.
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=device_token,
    )

    try:
        response = messaging.send(message)
        return SuccessResponse(
            message=f"Notification sent to {device_token}",
            data=response
        )
    
    except Exception as e:
        logger.error("Error sending notification to device: {}", str(e), exc_info=True)
        raise