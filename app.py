from flask import Flask, request, jsonify
from flask_cors import CORS
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from workers import process_video
from database import SessionLocal, init_db
from models import ProcessingJob
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Redis broker
redis_broker = RedisBroker(host="localhost", port=6379, db=0)
dramatiq.set_broker(redis_broker)

# Initialize database
init_db()

@app.route('/api/process', methods=['POST'])
def create_job():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        webhook_url = data.get('webhook_url')
        
        if not video_url:
            return jsonify({"error": "video_url is required"}), 400
            
        # Create job in database
        db = SessionLocal()
        job = ProcessingJob(video_url=video_url, webhook_url=webhook_url)
        db.add(job)
        db.commit()
        job_id = job.id
        db.close()
        
        # Send job to queue
        process_video.send(job_id, video_url, webhook_url)
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Video processing job created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<int:job_id>', methods=['GET'])
def get_status(job_id):
    try:
        db = SessionLocal()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        db.close()
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
            
        return jsonify({
            "job_id": job.id,
            "status": job.status,
            "error": job.error_message
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/results/<int:job_id>', methods=['GET'])
def get_results(job_id):
    try:
        db = SessionLocal()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        db.close()
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
            
        if job.status != "completed":
            return jsonify({"error": "Job not completed"}), 400
            
        return jsonify({
            "job_id": job.id,
            "transcription": job.transcription,
            "action_points": job.action_points
        })
        
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 