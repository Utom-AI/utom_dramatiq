from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime

from env_utils import load_in_env_vars
from utom_feature.utils import send_task_to_queue, get_task_by_id, update_task_status

# Load environment variables
load_in_env_vars()

app = Flask(__name__)
CORS(app)

@app.route('/process_video', methods=['POST'])
def process_video():
    """Endpoint to submit a video for processing"""
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        webhook_url = data.get('webhook_url')
        
        if not video_url:
            return jsonify({
                'success': False,
                'error': 'No video URL provided'
            }), 400
            
        # Create task data
        task_data = {
            'task_id': f"video_task_{int(datetime.utcnow().timestamp())}",
            'video_url': video_url,
            'webhook_url': webhook_url,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Send task to queue
        send_task_to_queue('video_processing_queue', task_data)
        
        return jsonify({
            'success': True,
            'task_id': task_data['task_id'],
            'message': 'Video processing task submitted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Endpoint to check task status"""
    try:
        task = get_task_by_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
            
        return jsonify({
            'success': True,
            'task': task
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'True').lower() == 'true') 