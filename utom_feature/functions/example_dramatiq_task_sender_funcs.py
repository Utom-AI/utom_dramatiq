import dramatiq
import warnings
import asyncio
import time
import random
warnings.filterwarnings("ignore")

## Add the root path so modules can be easily imported
import os
import sys
import json
temp = os.path.dirname(os.path.abspath(__file__))
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR

# Add the root path to our python paths
sys.path.insert(0, BASE_DIR)

from bson import ObjectId
from datetime import datetime
from driptok_databases.functions import mongo_utils as mongo
from driptok_databases.functions import rabbitmq_utils as rabbit_mq
from driptok_utils.functions import general as gen
from driptok_utils.functions import dramatiq_task_funcs as dram_task
from driptok_recommender.functions.content_recommendation_dramatiq_app import generate_content_recommendations_for_driptok_user_task

from bson import ObjectId

class CustomCDDEncoder(json.JSONEncoder):
    """     
    This helps us deal with ObjectID and datetime objects that are causing issues, we simply convert them to string
    """
    def default(self, o):
        if isinstance(o, (ObjectId, datetime)):
            return str(o)
        return super().default(o)
    
def generate_content_recommendations_for_driptok_user_task_dict(user_recc_params_dict):
    """
    Generate a Celery task dictionary for the recommendation dictionary.

    Parameters:
    - user_recommendation_id (str): A dictionary containing RSS publication data.

    Returns:
    dict: A dictionary representing a Celery task with specific parameters.
    """
    
    # Task specific parameters
    task_service_name = 'Recommender Service'
    task_name = 'generate_content_recommendations_for_driptok_user'
    task_id = str(ObjectId())
    task_status = 'sent'
    task_send_time = int(gen.get_current_utc0_unix_timestamp())
    task_pickup_time = 0
    task_end_time = 0
    task_time_to_pickup = 0
    task_time_taken = 0
    task_message = 'NA'
    local_machine_public_ip = 'NA'
    worker_id = 'NA'
    
    # Create Celery task dictionary
    task_dict = {
        'task_id' : task_id,
        'task_service_name' : task_service_name,
        'task_name' : task_name,
        'task_status' : task_status,
        'task_message_dict' : user_recc_params_dict,
        'task_send_time' : task_send_time,
        'task_pickup_time' : task_pickup_time,
        'task_end_time' : task_end_time,
        'task_time_to_pickup' : task_time_to_pickup,
        'task_time_taken' : task_time_taken,
        'task_message' : task_message,
        'local_machine_public_ip' : local_machine_public_ip,
        'worker_id' : worker_id
    }

    return task_dict

def send_generate_content_recommendations_for_driptok_user_task(user_recc_params_dict):

    task_log_service_mongo_db_name = os.environ.get('task_log_service_mongo_db_name')
    task_logs_collection_name = os.environ.get('task_logs_collection_name')
    
    channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
    mongo_client = mongo.initialise_mongo_cloud_db_client()

    task_dict = generate_content_recommendations_for_driptok_user_task_dict(user_recc_params_dict)
    task_json = json.dumps(task_dict)
    dram_task.save_task_log_to_mongo(task_dict, mongo_client, task_log_service_mongo_db_name, task_logs_collection_name)

    try:
        generate_content_recommendations_for_driptok_user_task.send(task_json)
    except:
        print('wahala')
        channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
        generate_content_recommendations_for_driptok_user_task.send(task_json)
    print('Task has been sent to dramatiq')
