from google.cloud import run_v2
from app.core.config import settings
from app.core.logging import logger
import json
from google.oauth2 import service_account


async def execute_video_processing_job(video_id: str, video_url: str):
    """Execute the Cloud Run Job for video processing."""
    
    try:

        # Instantiate the client
        client = run_v2.JobsClient()
        
        # The job name follows the format: projects/{project}/locations/{location}/jobs/{job_name}
        job_name = "job_name"
        
        # Create the container override object
        container_override = run_v2.RunJobRequest.Overrides.ContainerOverride(
            args=[
                "--video_id", video_id,
                "--temp_video_url", video_url
            ]
        )

        # Create the execution request with the override object
        request = run_v2.RunJobRequest(
            name=job_name,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[container_override]
            )
        )
        
        # Start the job
        operation = client.run_job(request=request)
        return operation.operation.name
    
    except Exception as e:
        logger.error("Error executing video processing job: {}", str(e), exc_info=True)
        raise
        