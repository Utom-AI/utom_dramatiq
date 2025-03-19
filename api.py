from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import ProcessingJob
from workers import process_video, fetch_metadata_and_process
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Processing API")

@app.post("/process")
async def process_video_endpoint(video_url: str, db: Session = Depends(get_db)):
    """
    Submit a video URL for processing.
    Returns a job ID that can be used to check the status and retrieve results.
    """
    try:
        # Create new job
        job = ProcessingJob(video_url=video_url, status="pending")
        db.add(job)
        db.commit()
        db.refresh(job)

        # Enqueue processing task
        process_video.send(job.id)

        return {"job_id": job.id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a processing job"""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"job_id": job.id, "status": job.status}

@app.get("/results/{job_id}")
async def get_job_results(job_id: int, db: Session = Depends(get_db)):
    """Get the results of a completed processing job"""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error_message or "Job failed")
    
    if job.status != "completed":
        raise HTTPException(status_code=202, detail="Job still processing")
    
    return {
        "job_id": job.id,
        "video_url": job.video_url,
        "transcription": job.transcription,
        "action_points": job.action_points
    }

@app.post("/fetch-and-process")
async def fetch_and_process_endpoint():
    """
    Fetch metadata from configured API endpoint and process the video URL found in it.
    This endpoint triggers the metadata fetching process.
    """
    try:
        # Enqueue metadata fetching task
        fetch_metadata_and_process.send()
        return {"status": "Task enqueued successfully"}
    except Exception as e:
        logger.error(f"Error enqueueing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 