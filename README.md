# utom_dramatiq

A video processing service that uses OpenAI's Whisper API for transcription and GPT-4 for action point extraction.

## Features

- Video upload and processing
- Audio extraction from videos
- Transcription using OpenAI's Whisper API
- Action point extraction using GPT-4
- Task queue management with Dramatiq
- S3 storage integration
- MongoDB for task logging
- Modern React frontend with TypeScript

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
cd frontend
npm install
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=your_aws_region
MONGODB_URI=your_mongodb_uri
RABBITMQ_URL=your_rabbitmq_url
```

3. Initialize the database:
```bash
python init_db.py
```

4. Start the workers:
```bash
dramatiq workers.py
```

5. Run the application:
```bash
python video_processor.py
```

6. Start the frontend development server:
```bash
cd frontend
npm run dev
```

## Testing

Run the tests with:
```bash
python test_core_functionality.py
```

## License

MIT License
