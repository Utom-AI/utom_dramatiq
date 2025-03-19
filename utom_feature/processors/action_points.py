import os
from openai import OpenAI
import logging
from typing import Dict, Any

# Configure logging to match organization's style
logger = logging.getLogger(__name__)

def extract_action_points(text: str) -> Dict[str, Any]:
    """
    Extract action points from transcribed text using OpenAI GPT
    
    Args:
        text: Transcribed text to analyze
        
    Returns:
        dict: Contains success status, action points and context points
    """
    try:
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Prepare prompt
        prompt = f"""
        Please analyze the following transcription and extract:
        1. Key action points (specific tasks that need to be done)
        2. Context points (important background information)
        
        Format each action point as a clear, actionable task with:
        - Who is responsible (if mentioned)
        - What needs to be done
        - When it needs to be done (if mentioned)
        - Any relevant details
        
        Transcription:
        {text}
        
        Format the response as JSON with the following structure:
        {{
            "action_points": [
                {{
                    "task": "Complete task description",
                    "assignee": "Person responsible (if mentioned)",
                    "deadline": "Deadline (if mentioned)",
                    "details": "Additional context"
                }}
            ],
            "context_points": ["point 1", "point 2", ...]
        }}
        """
        
        # Call GPT-4
        logger.info("Extracting action points using GPT-4")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts clear, actionable tasks and important context from meeting transcriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # Parse response
        result = response.choices[0].message.content
        import json
        points = json.loads(result)
        
        return {
            "success": True,
            "action_points": points["action_points"],
            "context_points": points["context_points"]
        }
        
    except Exception as e:
        logger.error(f"Error extracting action points: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def format_action_points(result: Dict[str, Any]) -> str:
    """
    Format action points and context points into a readable string
    
    Args:
        result (dict): Result from extract_action_points containing action_points and context_points
        
    Returns:
        str: Formatted string
    """
    try:
        output = []
        
        # Add action points
        output.append("Action Points:")
        for i, point in enumerate(result["action_points"], 1):
            task = point["task"]
            assignee = point.get("assignee", "Unassigned")
            deadline = point.get("deadline", "No deadline specified")
            details = point.get("details", "")
            
            output.append(f"{i}. Task: {task}")
            output.append(f"   Assignee: {assignee}")
            output.append(f"   Deadline: {deadline}")
            if details:
                output.append(f"   Details: {details}")
            output.append("")
            
        # Add context points
        output.append("\nContext Points:")
        for i, point in enumerate(result["context_points"], 1):
            output.append(f"{i}. {point}")
            
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Error formatting action points: {str(e)}")
        return f"Error formatting action points: {str(e)}"