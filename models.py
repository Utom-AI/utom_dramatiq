from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import json
from database import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, nullable=False)
    webhook_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    transcription = Column(Text, nullable=True)
    action_points = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        result = {
            "id": self.id,
            "video_url": self.video_url,
            "webhook_url": self.webhook_url,
            "status": self.status,
            "transcription": self.transcription,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
        
        if self.action_points:
            try:
                result["action_points"] = json.loads(self.action_points)
            except json.JSONDecodeError:
                result["action_points"] = None
        else:
            result["action_points"] = None
            
        return result 