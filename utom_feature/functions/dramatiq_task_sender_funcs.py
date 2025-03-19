import warnings
warnings.filterwarnings("ignore")

## Derive the BASE_DIR based on the current file location
import os
import sys
temp = os.path.dirname(os.path.abspath(__file__))
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR
sys.path.insert(0, BASE_DIR)

import time
import json
from bson import ObjectId
from datetime import datetime
from utom_databases.functions import mongo_utils as mongo
from utom_databases.functions import rabbitmq_utils as rabbit_mq
from utom_utils.functions import general as gen
from utom_utils.functions import dramatiq_task_funcs as dram_task
from utom_feature.functions.feature_creation_dramatiq_app import generate_feature_details_e2e_one_shot_task
from utom_project.functions import project_management
class CustomEncoder(json.JSONEncoder):
    """     
    This helps us deal with ObjectID and datetime objects that are causing issues, we simply convert them to string
    """
    def default(self, o):
        if isinstance(o, (ObjectId, datetime)):
            return str(o)
        return super().default(o)
    
def generate_feature_details_e2e_one_shot_task_dict(combined_data):
    """
    Generate a task dictionary for the feature details generation.

    Parameters:
    - combined_data (dict): A dictionary containing feature_creation_input_metadata and project_metadata.

    Returns:
    dict: A dictionary representing a task with specific parameters.
    """
    
    # Task specific parameters
    task_service_name = 'Feature Service'
    task_name = 'generate_feature_details_e2e_one_shot'
    task_id = str(ObjectId())
    task_status = 'sent'
    task_send_time = int(time.time())
    task_pickup_time = 0
    task_end_time = 0
    task_time_to_pickup = 0
    task_time_taken = 0
    task_message = 'NA'
    local_machine_public_ip = 'NA'
    worker_id = 'NA'
    
    # Create task dictionary
    task_dict = {
        'task_id': task_id,
        'task_service_name': task_service_name,
        'task_name': task_name,
        'task_status': task_status,
        'task_message_dict': combined_data,
        'task_send_time': task_send_time,
        'task_pickup_time': task_pickup_time,
        'task_end_time': task_end_time,
        'task_time_to_pickup': task_time_to_pickup,
        'task_time_taken': task_time_taken,
        'task_message': task_message,
        'local_machine_public_ip': local_machine_public_ip,
        'worker_id': worker_id
    }

    return task_dict

def send_generate_feature_details_e2e_one_shot_task(feature_creation_input_metadata):
    """
    Send a task to generate feature details end-to-end in one shot.
    
    Args:
        feature_creation_input_metadata (dict): Metadata required for feature creation
        project_metadata (dict): Metadata of the project
        
    Returns:
        str: The task_id of the sent task
    """
    project_id = feature_creation_input_metadata['project_id']
    project_metadata = project_management.get_project_by_id(project_id)
    del project_metadata['_id']

    task_log_service_mongo_db_name = 'utom_task_log_service'
    task_logs_collection_name = 'task_logs'
    
    channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
    mongo_client = mongo.initialise_mongo_cloud_db_client()

    # Combine the input metadata into a single dictionary
    combined_data = {
        'feature_creation_input_metadata': feature_creation_input_metadata,
        'project_metadata': project_metadata
    }
    
    task_dict = generate_feature_details_e2e_one_shot_task_dict(combined_data)
    task_json = json.dumps(task_dict)
    dram_task.save_task_log_to_mongo(task_dict, mongo_client, task_log_service_mongo_db_name, task_logs_collection_name)

    try:
        generate_feature_details_e2e_one_shot_task.send(task_json)
    except:
        print('Error sending task, retrying with new connection')
        channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
        generate_feature_details_e2e_one_shot_task.send(task_json)
    
    print(f'Task has been sent to dramatiq with task_id: {task_dict["task_id"]}')
    
    return task_dict["task_id"] 