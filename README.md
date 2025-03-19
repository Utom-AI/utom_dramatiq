# Video Processing Service with OpenAI Whisper Integration

This service processes videos to extract transcriptions and action points using OpenAI's Whisper API.

## Features
- Video download and processing
- Audio extraction
- Speech-to-text transcription using OpenAI Whisper
- Action points extraction
- MongoDB for task logging
- RabbitMQ for task queuing

## Prerequisites
- Python 3.10 or higher
- Docker and Docker Compose
- AWS Account with S3 access
- OpenAI API key

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/video-processing-service.git
cd video-processing-service
```

2. Create a virtual environment:
```bash
python -m venv venv310
source venv310/bin/activate  # On Windows: venv310\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.template .env
```
Edit `.env` with your:
- OpenAI API key
- AWS credentials
- MongoDB URI
- RabbitMQ configuration

5. Start MongoDB using Docker:
```bash
docker-compose up -d
```

## Testing

1. Run the MongoDB integration test:
```bash
python test_mongodb_integration.py
```
This will:
- Create a test task in MongoDB
- Process a test video
- Store metadata in MongoDB
- Display the stored metadata

2. Run other tests:
```bash
pytest
```

## Metadata Structure

After processing a video, the following metadata is stored in MongoDB:

```json
{
  "task_id": "unique_task_identifier",
  "video_url": "url_of_processed_video",
  "status": "completed",
  "created_at": "task_creation_timestamp",
  "completed_at": "task_completion_timestamp",
  "results": {
    "transcription": "full_video_transcription",
    "action_points": [
      "list of extracted action points"
    ],
    "context_points": [
      "list of contextual information"
    ],
    "formatted_output": "formatted version of points"
  }
}
```

## Usage

1. Submit a video for processing:
```python
from video_processor import process_video_task

task_id = process_video_task("https://example.com/video.mp4")
```

2. Check task status and get results:
```python
from utom_utils import get_mongodb_client

client = get_mongodb_client()
db = client['utom_video_processing_db']
task = db['tasks'].find_one({"task_id": task_id})
print(json.dumps(task, indent=2))
```

## Environment Variables

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `AWS_BUCKET_NAME`: S3 bucket name
- `MONGODB_URI`: MongoDB connection URI
- `MONGODB_DB_NAME`: MongoDB database name
