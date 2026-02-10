from google.cloud import tasks_v2
import json
from enum import Enum
from app.core.config import settings


class CloudTaskQueue(Enum):
    EBOOK_PROCESSING = "ebook-processing-queue"
    EBOOK_UPDATE = "ebook-update-queue"


class CloudTaskURL(Enum):
     # empty for security reasons
    EBOOK_PROCESSING = f""
    EBOOK_UPDATE = f""


client = tasks_v2.CloudTasksClient()

 # empty for security reasons
project = ""
location = ""

def create_cloud_task(queue_name: str, url: str, payload: dict):
    """Creates a Google Cloud Task to execute a background job"""
    
    parent = client.queue_path(project, location, queue_name)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    response = client.create_task(request={"parent": parent, "task": task})
    return response.name