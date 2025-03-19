import os
import json
from datetime import datetime
from utom_utils import get_mongodb_client
from utom_feature.processors.video import process_video
from utom_feature.processors.transcription import transcribe_audio
from utom_feature.processors.action_points import extract_action_points, format_action_points

def test_video_processing_with_mongodb():
    """Test video processing and MongoDB integration"""
    try:
        # Initialize MongoDB client
        mongodb_client = get_mongodb_client()
        db = mongodb_client['utom_video_processing_db']
        tasks_collection = db['tasks']

        # Create a test task
        task_id = f"test_task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short test video

        task = {
            "task_id": task_id,
            "video_url": test_video_url,
            "status": "pending",
            "created_at": datetime.utcnow()
        }

        # Insert task into MongoDB
        tasks_collection.insert_one(task)
        print(f"\nCreated task in MongoDB: {json.dumps(task, default=str, indent=2)}")

        # Process video
        print("\nProcessing video...")
        video_result = process_video(test_video_url)
        if not video_result.get("success"):
            raise Exception(video_result.get("error", "Failed to process video"))

        video_path = video_result["video_path"]
        audio_path = video_result["audio_path"]

        try:
            # Transcribe audio
            print("\nTranscribing audio...")
            transcription_result = transcribe_audio(audio_path)
            if not transcription_result.get("success"):
                raise Exception(transcription_result.get("error", "Failed to transcribe audio"))

            # Extract action points
            print("\nExtracting action points...")
            action_points_result = extract_action_points(transcription_result)
            if not action_points_result.get("success"):
                raise Exception(action_points_result.get("error", "Failed to extract action points"))

            # Format results
            formatted_points = format_action_points(action_points_result)

            # Update task with results
            result = {
                "status": "completed",
                "results": {
                    "transcription": transcription_result["text"],
                    "action_points": action_points_result["action_points"],
                    "context_points": action_points_result["context_points"],
                    "formatted_output": formatted_points
                },
                "completed_at": datetime.utcnow()
            }

            tasks_collection.update_one(
                {"task_id": task_id},
                {"$set": result}
            )

            # Retrieve and display the results
            updated_task = tasks_collection.find_one({"task_id": task_id})
            print("\nStored metadata in MongoDB:")
            print(json.dumps(updated_task, default=str, indent=2))

        finally:
            # Clean up temporary files
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)

    except Exception as e:
        print(f"\nError: {str(e)}")
        # Update task status to failed
        if 'tasks_collection' in locals() and 'task_id' in locals():
            tasks_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.utcnow()
                    }
                }
            )
    finally:
        if 'mongodb_client' in locals():
            mongodb_client.close()

if __name__ == "__main__":
    test_video_processing_with_mongodb() 