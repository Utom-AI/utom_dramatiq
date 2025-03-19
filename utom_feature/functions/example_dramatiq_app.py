import dramatiq
import warnings
import asyncio
import time
import random
warnings.filterwarnings("ignore")
# Suppress specific warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="cassandra.cluster")
warnings.filterwarnings("ignore", category=UserWarning, module="cassandra.cluster")
warnings.filterwarnings("ignore", category=FutureWarning, module="cassandra.cluster")

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

import atexit
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import CurrentMessage
from driptok_utils.functions import general as gen
from driptok_utils.functions import env_utils
from driptok_utils.functions import dramatiq_task_funcs as dram_task
from driptok_databases.functions import rabbitmq_utils as rabbit_mq
from driptok_databases.functions import mongo_utils as mongo
from driptok_recommender.functions import content_recommender_funcs as cont_rec

"""
Server Side Setup
"""
# Make sure that the env variables are loaded in
env_utils.load_in_env_vars()

# Setup the rabbitmq broker
rabbitmq_server_ip_address = os.environ.get('rabbitmq_server_ip_address')
rabbitmq_server_username = os.environ.get('rabbitmq_server_username')
rabbitmq_server_password = os.environ.get('rabbitmq_server_password')
broker = RabbitmqBroker(url="amqp://%s:%s@%s:5672" % (rabbitmq_server_username, rabbitmq_server_password, rabbitmq_server_ip_address))

# Initialise rabbitmq and mongo connections
mongo_client = mongo.initialise_mongo_cloud_db_client()
channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()

# Function to be called at application shutdown
def close_mongo_connection():
    # print('Calling the at exit function to close the mongo client')
    mongo_client.close()
    # print('closed the mongo server')
    # print('Closing the rabbitmq channel')
    channel.close()
    # print('close the rabbitmq channel')

# Register the function to be called at exit
atexit.register(close_mongo_connection)

# Set the dramatiq broker and add messaging
dramatiq.set_broker(broker)
dramatiq.get_broker().add_middleware(CurrentMessage())

from driptok_databases.functions import cassandra_utils as cass_utils
from driptok_utils.functions import env_utils
from driptok_utils.functions import general as gen

env_utils.load_in_env_vars()

# Define your task
@dramatiq.actor(queue_name="generate_content_recommendations_for_driptok_user_task_queue", max_retries=1, time_limit=120000) # timeout defaulted to 2 minutes
def generate_content_recommendations_for_driptok_user_task(data):
    """
    Get the task worker and message details
    """
    worker_id = os.getpid()
    local_machine_public_ip = os.environ.get('local_machine_public_ip')
    
    msg = CurrentMessage.get_current_message()
    args_tuple = msg.args
    task_message_dict = json.loads(args_tuple[0])

    # - Get task details
    mongo_client = mongo.initialise_mongo_cloud_db_client()
    task_id_str = task_message_dict['task_id']
    task_log_service_mongo_db_name = os.environ.get('task_log_service_mongo_db_name')
    task_logs_collection_name = os.environ.get('task_logs_collection_name')
    filter_criteria = {
        'task_id' : task_id_str
    }
    db_task_message_dict = mongo.get_documents_by_filter_criteria(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, filter_criteria)[0]
    db_task_status = db_task_message_dict['task_status']
    if db_task_status == 'sent':
        # print('The task hasnt been started by another worker and we can start it')
        can_process_task = True
    else:
        # print('It seems the task has already been started by another process so we will not process it')
        can_process_task = False

    if can_process_task:
        print('It seems no other worker has picked up this task so we can start it')
        """
        Calculate initial time params on the task
        """
        # Get send time
        task_send_time = int(task_message_dict['task_send_time'])
        
        # Get params at the start of the task
        task_pickup_time = gen.get_current_utc0_unix_timestamp()
        task_time_to_pickup = int(task_pickup_time - task_send_time)

        """  
        Get the current task status to determine if we can start the task or if its already been started
        """
        """   
        Update the task logs that the task has been picked up
        """
        # Generate a dict of the things that need to be updated
        task_status = 'started'
        updated_task_json = {
            'task_status': task_status,
            'task_pickup_time' : task_pickup_time,
            'task_time_to_pickup' : task_time_to_pickup,
            'task_pickup_local_machine_public_ip' : local_machine_public_ip,
            'task_pickup_worker_id' : worker_id,
        }
        # Query to find the document you want to update (e.g., based on task_id)
        task_id_key_name = 'task_id'
        task_log_service_mongo_db_name = os.environ.get('task_log_service_mongo_db_name')
        task_logs_collection_name = os.environ.get('task_logs_collection_name')
        task_started_count_collection_name = os.environ.get('task_started_count_collection_name')
        mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)

        # Update the task started count
        dram_task.update_task_started_count(mongo_client, task_log_service_mongo_db_name, task_started_count_collection_name, task_id_str)

        """
        Execute on the task
        TODO:
        - later add a custom task message that would allow us to know the actual result of the task being run
        """
        try:
            cont_rec.process_generate_content_recommendations_for_driptok_user_task(data)
            task_message = 'Task ran end to end successfully'
            task_status = 'completed'
        except Exception as e:
            task_message = 'There was an error: %s' % e
            print(task_message)
            task_message_dict['task_message'] = task_message
            print('The task failed and the task log has been updated accordingly')
            task_status = 'failed'
    
        """
        Calculate post process time params
        """
        task_end_time = gen.get_current_utc0_unix_timestamp()
        task_time_taken = int(task_end_time -  task_send_time)
        task_process_time = int(task_time_taken - task_time_to_pickup)

        # Generate a dict of the things that need to be updated
        updated_task_json = {
            'task_status': 'completed',
            'task_pickup_time' : task_pickup_time,
            'task_time_to_pickup' : task_time_to_pickup,
            'task_end_time' : task_end_time,
            'task_time_taken' : task_time_taken,
            'task_process_time' : task_process_time,
            'task_message' : task_message,
            'local_machine_public_ip' : local_machine_public_ip,
            'worker_id' : worker_id,
        }
    
        """
        Update the task logs
        ** once we get dynamoDB up and running we will want to add this part
        """
        # Query to find the document you want to update (e.g., based on task_id)
        task_id_key_name = 'task_id'
        task_log_service_mongo_db_name = os.environ.get('task_log_service_mongo_db_name')
        task_logs_collection_name = os.environ.get('task_logs_collection_name')
        
        try:
            # Given how long the content service processing takes, we reinitialize the mongo_client at this point
            mongo_client = mongo.initialise_mongo_cloud_db_client()
            mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)
        except:
            print('There was an error when we tried to save the updated task details')
            mongo_client = mongo.initialise_mongo_cloud_db_client()
            mongo.update_document_in_mongo_by_document_id_str(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_id_key_name, task_id_str, updated_task_json)
        # print('We were able to save the data to mongo without having to explicitly initialise the mongo connection inside, which means that we are lit for cassandra')
        # mongo_client.close()

    if can_process_task:
        print(f"Task ID: {task_id_str}, Worker ID: {worker_id} was able to be processed and completed successfully")
    else:
        print(f"Task ID: {task_id_str}, Worker ID: {worker_id} seems to be a duplicate as the task was already started by another worker")


"""
RUnning
dramatiq --processes 2 --threads 1 person_media_search_dramatiq_app 

The above will spin up 2 single threads processes (essentially just 2 workers)... adjust this as needed based on how many things you want running concurrently
"""