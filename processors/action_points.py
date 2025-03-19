from openai import OpenAI
import os
from typing import List, Dict
import logging
from dotenv import load_dotenv
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

def extract_action_points(transcription: str) -> List[Dict]:
    """Extract action points from transcription using OpenAI"""
    try:
        logger.info("Extracting action points from transcription")
        
        system_prompt = """
        You are an expert at analyzing transcripts and extracting clear, actionable points.
        You must respond with ONLY a valid JSON object in this exact format:
        {
            "action_points": [
                {
                    "action": "The specific action to be taken",
                    "context": "Brief context from the transcription",
                    "priority": "High/Medium/Low based on urgency"
                }
            ]
        }
        
        Guidelines:
        1. Actions should be clear, specific, and actionable
        2. Context should be a brief quote or reference from the transcription
        3. Priority should reflect urgency and importance
        4. Return ONLY the JSON object, no additional text or explanations
        5. Ensure the response is valid JSON that can be parsed
        """

        user_prompt = f"""
        Analyze this transcription and return action points as a JSON object:

        {transcription}
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse and validate the JSON response
        try:
            content = response.choices[0].message.content.strip()
            logger.info(f"Received GPT response: {content[:200]}...")  # Log first 200 chars
            
            # Parse JSON response
            parsed = json.loads(content)
            
            # Extract action points array
            if isinstance(parsed, dict) and 'action_points' in parsed:
                action_points = parsed['action_points']
            elif isinstance(parsed, list):
                action_points = parsed
            else:
                raise ValueError("Unexpected response format")
            
            # Validate and format each action point
            formatted_points = []
            for point in action_points:
                if isinstance(point, dict):
                    formatted_point = {
                        'action': str(point.get('action', '')).strip(),
                        'context': str(point.get('context', '')).strip(),
                        'priority': str(point.get('priority', 'Medium')).strip()
                    }
                    
                    # Validate required fields
                    if not formatted_point['action']:
                        continue
                        
                    # Normalize priority
                    priority = formatted_point['priority'].lower()
                    if 'high' in priority or 'urgent' in priority:
                        formatted_point['priority'] = 'High'
                    elif 'low' in priority:
                        formatted_point['priority'] = 'Low'
                    else:
                        formatted_point['priority'] = 'Medium'
                        
                    formatted_points.append(formatted_point)
            
            if not formatted_points:
                raise ValueError("No valid action points extracted")
                
            logger.info(f"Successfully extracted {len(formatted_points)} action points")
            return formatted_points
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
            # Create a fallback action point
            return [{
                'action': 'Review transcription manually',
                'context': f'Failed to parse GPT response: {str(e)}',
                'priority': 'High'
            }]
            
    except Exception as e:
        logger.error(f"Error extracting action points: {str(e)}")
        # Return a minimal valid response rather than raising
        return [{
            'action': 'System encountered an error',
            'context': f'Error during action point extraction: {str(e)}',
            'priority': 'High'
        }] 