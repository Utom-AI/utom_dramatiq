import pymongo
import datetime
from pymongo import MongoClient

def test_mongodb_connection():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    
    try:
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("✓ MongoDB connection successful!")
        return True
    except Exception as e:
        print("✗ MongoDB connection failed:", str(e))
        return False

def test_video_metadata_operations():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['video_processor']
    collection = db['video_metadata']
    
    try:
        # Test document
        test_metadata = {
            "video_id": "test_video_001",
            "filename": "sample_video.mp4",
            "upload_date": datetime.datetime.utcnow(),
            "duration": 120.5,
            "processed": False,
            "features": {
                "transcription": None,
                "action_points": []
            }
        }
        
        # Insert test document
        result = collection.insert_one(test_metadata)
        print("✓ Inserted test document with ID:", result.inserted_id)
        
        # Retrieve the document
        retrieved = collection.find_one({"video_id": "test_video_001"})
        if retrieved:
            print("✓ Successfully retrieved test document")
        
        # Update the document
        update_result = collection.update_one(
            {"video_id": "test_video_001"},
            {"$set": {"processed": True}}
        )
        print("✓ Updated document:", update_result.modified_count, "document(s) modified")
        
        # Clean up - delete test document
        delete_result = collection.delete_one({"video_id": "test_video_001"})
        print("✓ Cleaned up test document")
        
        return True
    except Exception as e:
        print("✗ Database operations failed:", str(e))
        return False

if __name__ == "__main__":
    print("Testing MongoDB Integration...")
    print("-" * 30)
    
    if test_mongodb_connection():
        print("\nTesting database operations...")
        print("-" * 30)
        test_video_metadata_operations()
    else:
        print("Skipping database operations due to connection failure") 