from google.cloud import run_v2
from app.core.config import settings
from app.core.logging import logger
import json
from google.oauth2 import service_account


async def execute_video_processing_job(video_id: str, video_url: str):
    """Execute the Cloud Run Job for video processing."""
    
    try:
        
        jobs_sa_key_json_str = settings.JOBS_SERVICE_ACCOUNT_KEY
        jobs_sa_info = json.loads(jobs_sa_key_json_str)
        jobs_sa_credentials = service_account.Credentials.from_service_account_info(jobs_sa_info)
        
        # Instantiate the client
        client = run_v2.JobsClient(credentials=jobs_sa_credentials)
        
        # The job name follows the format: projects/{project}/locations/{location}/jobs/{job_name}
        job_name = f"projects/wonderspaced-450711/locations/us-central1/jobs/video-processing-job-{settings.ENV.lower()}"
        
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
        