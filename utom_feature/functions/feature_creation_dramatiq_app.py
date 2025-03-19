import dramatiq
import warnings
import time
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
import atexit
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from utom_utils.functions import general as gen
from utom_utils.functions import env_utils
from utom_utils.functions import dramatiq_task_funcs as dram_task
from utom_databases.functions import rabbitmq_utils as rabbit_mq
from utom_databases.functions import mongo_utils as mongo
from utom_feature.functions import feature_creation

"""
Server Side Setup
"""
# Make sure that the env variables are loaded in
env_utils.load_in_env_vars()

# Setup the rabbitmq broker
rabbitmq_server_ip_address = '95.216.155.137'
rabbitmq_server_username = 'utom'
rabbitmq_server_password = 'utom2024'
broker = RabbitmqBroker(url="amqp://%s:%s@%s:5672" % (rabbitmq_server_username, rabbitmq_server_password, rabbitmq_server_ip_address))

# Initialise rabbitmq and mongo connections
mongo_client = mongo.initialise_mongo_cloud_db_client()
channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
print('Initialised rabbitmq and mongo connections')
rabbit_mq.check_if_rabbitmq_server_is_active()
# Function to be called at application shutdown
def close_connections():
    mongo_client.close()
    channel.close()

# Register the function to be called at exit
atexit.register(close_connections)

# Set the dramatiq broker and add messaging
dramatiq.set_broker(broker)
dramatiq.get_broker().add_middleware(CurrentMessage())

# Define your task
@dramatiq.actor(queue_name="generate_feature_details_e2e_one_shot_task_queue", max_retries=1, time_limit=900000) # 15 minutes timeout
def generate_feature_details_e2e_one_shot_task(data):
    """
    Get the task worker and message details
    """
    worker_id = '111'
    local_machine_public_ip = '127.0.0.1'  # Use localhost for local testing
    
    msg = CurrentMessage.get_current_message()
    args_tuple = msg.args
    task_message_dict = json.loads(args_tuple[0])

    # - Get task details
    try:
        mongo_client = mongo.initialise_mongo_cloud_db_client()
        task_id_str = task_message_dict['task_id']
        task_log_service_mongo_db_name = 'utom_task_log_service'  # Hardcoded for testing
        task_logs_collection_name = 'task_logs'  # Hardcoded for testing
        
        # Try to get task from MongoDB
        try:
            filter_criteria = {
                'task_id': task_id_str
            }
            db_task_message_dict = mongo.get_documents_by_filter_criteria(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, filter_criteria)[0]
            db_task_status = db_task_message_dict['task_status']
            
            if db_task_status == 'sent':
                can_process_task = True
            else:
                can_process_task = False
        except Exception as e:
            print(f"Warning: Could not get task from MongoDB: {str(e)}")
            # Assume we can process the task if we can't check MongoDB
            can_process_task = True
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {str(e)}")
        # Assume we can process the task if we can't connect to MongoDB
        can_process_task = True
        mongo_client = None

    if can_process_task:
        """
        Calculate initial time params on the task
        """
        # Get send time
        task_send_time = int(task_message_dict['task_send_time'])
        
        # Get params at the start of the task
        task_pickup_time = int(time.time())
        task_time_to_pickup = int(task_pickup_time - task_send_time)

        """   
        Update the task logs that the task has been picked up
        """
        if mongo_client:
            task_status = 'started'
            updated_task_json = {
                'task_status': task_status,
                'task_pickup_time': task_pickup_time,
                'task_time_to_pickup': task_time_to_pickup,
                'task_pickup_local_machine_public_ip': local_machine_public_ip,
                'task_pickup_worker_id': worker_id,
            }
            
            task_id_key_name = 'task_id'
            task_log_service_mongo_db_name = 'utom_task_log_service'  # Hardcoded for testing
            task_logs_collection_name = 'task_logs'  # Hardcoded for testing
            task_started_count_collection_name = 'task_started_count'  # Hardcoded for testing
            
            try:
                mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)
                
                # Update the task started count
                dram_task.update_task_started_count(mongo_client, task_log_service_mongo_db_name, task_started_count_collection_name, task_id_str)
            except Exception as e:
                print(f"Warning: Could not update task status in MongoDB: {str(e)}")

        """
        Execute on the task
        """
        try:
            print(f"Starting task execution for task ID: {task_id_str}")
            
            # Use the process function from feature_creation
            feature_metadata = feature_creation.process_generate_feature_details_e2e_one_shot_task(data)
            
            task_message = 'Task ran end to end successfully'
            task_status = 'completed'
            print(f"Task completed successfully for task ID: {task_id_str}")
        except Exception as e:
            task_message = f'There was an error: {str(e)}'
            print(task_message)
            task_status = 'failed'
    
        """
        Calculate post process time params
        """
        task_end_time = int(time.time())
        task_time_taken = int(task_end_time - task_send_time)
        task_process_time = int(task_time_taken - task_time_to_pickup)

        # Generate a dict of the things that need to be updated
        updated_task_json = {
            'task_status': task_status,
            'task_pickup_time': task_pickup_time,
            'task_time_to_pickup': task_time_to_pickup,
            'task_end_time': task_end_time,
            'task_time_taken': task_time_taken,
            'task_process_time': task_process_time,
            'task_message': task_message,
            'local_machine_public_ip': local_machine_public_ip,
            'worker_id': worker_id,
        }
    
        """
        Update the task logs
        """
        if mongo_client:
            try:
                # Given how long the processing takes, we reinitialize the mongo_client at this point
                mongo_client = mongo.initialise_mongo_cloud_db_client()
                mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)
            except Exception as e:
                print(f"Warning: Could not update task status in MongoDB: {str(e)}")
                try:
                    mongo_client = mongo.initialise_mongo_cloud_db_client()
                    mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)
                except Exception as e:
                    print(f"Warning: Could not update task status in MongoDB after retry: {str(e)}")

    if can_process_task:
        print(f"Task ID: {task_id_str}, Worker ID: {worker_id} was able to be processed and completed successfully")
    else:
        print(f"Task ID: {task_id_str}, Worker ID: {worker_id} seems to be a duplicate as the task was already started by another worker") 