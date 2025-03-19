import os
import json
import logging
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_action_points(transcription: str) -> dict:
    """Extract detailed action points and tasks from video transcription"""
    try:
        logger.info("Extracting action points from transcription...")
        
        prompt = f"""
        Analyze the following video transcription and extract detailed, specific, and actionable tasks.
        Break down each task into clear, executable steps with assigned responsibilities.

        For each task identified from the transcription:
        1. WHO: Identify the specific role/person who should be responsible
        2. WHAT: Define the exact task that needs to be done
        3. HOW: Break down the implementation steps
        4. WHEN: Set a realistic timeline and priority
        5. WHY: Explain the impact and benefits
        6. Define clear success criteria

        Transcription:
        {transcription}
        
        Format your response as a JSON with the following structure:
        {{
            "action_points": [
                {{
                    "task": "Clear task description from the transcription",
                    "owner": "Role/person who should handle this",
                    "steps": ["Step 1 with clear action", "Step 2 with clear action", ...],
                    "timeline": "Specific timeframe from now",
                    "priority": "High/Medium/Low based on urgency",
                    "impact": "Concrete benefit or outcome",
                    "success_criteria": ["Measurable outcome 1", "Measurable outcome 2", ...],
                    "dependencies": ["Required prerequisite 1", "Required prerequisite 2", ...],
                    "resources_needed": ["Specific resource 1", "Specific resource 2", ...]
                }},
                ...
            ],
            "key_points": [
                {{
                    "insight": "Key insight from transcription",
                    "implications": ["Business implication 1", "Business implication 2", ...],
                    "risks": ["Associated risk 1", "Associated risk 2", ...],
                    "monitoring_metrics": ["Metric to track 1", "Metric to track 2", ...]
                }},
                ...
            ],
            "context": "Brief summary of the video content",
            "summary": "Detailed summary of key messages",
            "risk_assessment": {{
                "market_risks": ["Market-related risk 1", "Market-related risk 2", ...],
                "technical_risks": ["Technical risk 1", "Technical risk 2", ...],
                "regulatory_risks": ["Regulatory risk 1", "Regulatory risk 2", ...],
                "mitigation_strategies": ["Strategy to address risk 1", "Strategy to address risk 2", ...]
            }}
        }}

        IMPORTANT:
        - Tasks MUST be SPECIFIC, MEASURABLE, ACHIEVABLE, RELEVANT, and TIME-BOUND (SMART)
        - Focus on CONCRETE ACTIONS derived from the transcription
        - Each step should be IMMEDIATELY ACTIONABLE
        - Timelines should be REALISTIC and SPECIFIC
        - Success criteria must be MEASURABLE
        """
        
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert project manager and business analyst, skilled at converting information into actionable tasks and strategic insights."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info("Successfully extracted action points and tasks")
        return {"success": True, "points": result}
        
    except Exception as e:
        logger.error(f"Error extracting action points: {str(e)}")
        return {"success": False, "error": str(e)}

def format_action_points(points: dict) -> dict:
    """Format action points into a structured report"""
    try:
        logger.info("Formatting action points into report...")
        
        # Extract tasks with priorities
        tasks = []
        for action in points["action_points"]:
            task = {
                "description": action["task"],
                "owner": action["owner"],
                "priority": action["priority"],
                "timeline": action["timeline"],
                "steps": action["steps"],
                "success_criteria": action["success_criteria"]
            }
            tasks.append(task)
        
        # Sort tasks by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        tasks.sort(key=lambda x: priority_order[x["priority"]])
        
        # Create summary
        summary = {
            "overview": points["summary"],
            "context": points["context"],
            "total_tasks": len(tasks),
            "high_priority": len([t for t in tasks if t["priority"] == "High"]),
            "key_risks": points["risk_assessment"]["market_risks"] + 
                        points["risk_assessment"]["technical_risks"] + 
                        points["risk_assessment"]["regulatory_risks"]
        }
        
        return {
            "success": True,
            "tasks": tasks,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error formatting action points: {str(e)}")
        return {"success": False, "error": str(e)}