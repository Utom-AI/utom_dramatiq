import os
import pika
import json
import requests

"""   
ENVS to add

rabbitmq_server_ip_address = os.environ.get('rabbitmq_server_ip_address')
rabbitmq_server_username = os.environ.get('rabbitmq_server_username')
rabbitmq_server_password = os.environ.get('rabbitmq_server_password')
"""

def initialize_rabbitmq_client_and_create_channel():
    """
    Initialize a RabbitMQ client to connect to a RabbitMQ server using the default 'guest' user.

    Args:
        rabbitmq_server_ip (str): The IP address or hostname of the RabbitMQ server.

    Returns:
        pika.BlockingConnection: A connection object to the RabbitMQ server.
    """
    # Create a connection to the RabbitMQ server using the default 'guest' user and password
    rabbitmq_server_ip_address = os.environ.get('rabbitmq_server_ip_address')
    rabbitmq_server_username = os.environ.get('rabbitmq_server_username')
    rabbitmq_server_password = os.environ.get('rabbitmq_server_password')

    # Create a connection to the RabbitMQ server using the provided username and password
    credentials = pika.PlainCredentials(rabbitmq_server_username, rabbitmq_server_password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_server_ip_address, credentials=credentials))
    channel = connection.channel()
    
    return channel

def check_if_rabbitmq_server_is_active():

    channel = initialize_rabbitmq_client_and_create_channel()
    
    # Check if the channel is open
    if channel.is_open:
        print("RabbitMQ channel is active.")
        rabbit_mq_active = True
    else:
        print("RabbitMQ channel is not active.")
        rabbit_mq_active = False

    return rabbit_mq_active
    
def create_rabbitmq_channel(connection):
    """
    Create a channel for communication with RabbitMQ.

    Args:
        connection (pika.BlockingConnection): A connection object to the RabbitMQ server.

    Returns:
        pika.channel.Channel: A channel for communication.
    """
    # Create a channel
    channel = connection.channel()
    
    return channel


def declare_rabbitmq_queue(
    channel, 
    queue_name, 
    message_ttl=None, 
    queue_expires=None
):
    """
    Declare a RabbitMQ queue with optional message time-to-live and queue expiration.

    Args:
        channel (pika.channel.Channel): A channel for communication with RabbitMQ.
        queue_name (str): The name of the RabbitMQ queue to declare.
        message_ttl (int, optional): The time-to-live for messages in milliseconds. If not set, messages don't expire.
        queue_expires (int, optional): The queue expiration time in milliseconds. If not set, the queue doesn't expire.
    """
    arguments = {}

    # Set message time-to-live if provided
    if message_ttl is not None:
        arguments['x-message-ttl'] = message_ttl

    # Set queue expiration if provided
    if queue_expires is not None:
        arguments['x-expires'] = queue_expires

    # Declare the queue with optional arguments
    channel.queue_declare(queue=queue_name, arguments=arguments)

def publish_message_to_rabbitmq_queue(channel, queue_name, message_body):
    """
    Publish a message to a RabbitMQ queue.

    Args:
        channel (pika.channel.Channel): A channel for communication with RabbitMQ.
        queue_name (str): The name of the RabbitMQ queue to publish to.
        message_body (str): The message to publish.
    """
    # Publish a message to the specified queue
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=message_body)

def publish_dict_to_rabbitmq_queue(channel, queue_name, data_dict):
    """
    Publish a dictionary as a message to a RabbitMQ queue.

    Args:
        channel (pika.channel.Channel): A channel for communication with RabbitMQ.
        queue_name (str): The name of the RabbitMQ queue to publish to.
        data_dict (dict): The dictionary to publish as a message.
    """
    # Serialize the dictionary to JSON
    message_body = json.dumps(data_dict)

    # Publish the JSON message to the specified queue
    publish_message_to_rabbitmq_queue(channel, queue_name, message_body)

def consume_messages_from_rabbitmq_queue(connection, queue_name, callback):
    """
    Consume messages from a RabbitMQ queue.

    Args:
        connection (pika.BlockingConnection): A connection object to the RabbitMQ server.
        queue_name (str): The name of the RabbitMQ queue to consume messages from.
        callback (function): A callback function to process received messages.
    """
    # Create a channel
    channel = connection.channel()
    
    # Declare the queue to consume from
    channel.queue_declare(queue=queue_name)

    # Set up a message consumer with the provided callback function
    channel.basic_consume(queue=queue_name,
                          on_message_callback=callback,
                          auto_ack=True)

    # Start consuming messages
    channel.start_consuming()

def clear_rabbitmq_queue(channel, queue_name):
    """
    Clear all messages from a RabbitMQ queue.

    Args:
        channel (pika.channel.Channel): A channel for communication with RabbitMQ.
        queue_name (str): The name of the RabbitMQ queue to clear.
    """
    # Purge (delete) all messages from the specified queue
    channel.queue_purge(queue=queue_name)


def list_rabbitmq_queues(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password):
    """
    List all queues in RabbitMQ using the RabbitMQ Management HTTP API.

    Args:
        rabbitmq_management_api_url (str): The URL of the RabbitMQ Management API.
        username (str): Your RabbitMQ username.
        password (str): Your RabbitMQ password.

    Returns:
        list: A list of queue names in RabbitMQ.
    """
    # Create an HTTP Basic Authentication header with your RabbitMQ username and password
    rabbitmq_management_api_url = "http://%s:15672" % rabbitmq_server_ip_address
    auth = (rabbitmq_server_username, rabbitmq_server_password)

    # Make an HTTP GET request to the RabbitMQ Management API to get a list of queues
    response = requests.get(f"{rabbitmq_management_api_url}/api/queues", auth=auth)

    if response.status_code == 200:
        # Parse the JSON response and extract the queue names
        queues_data = response.json()
        queue_names = [queue["name"] for queue in queues_data]
        return queue_names
    else:
        print(f"Failed to retrieve queues. Status code: {response.status_code}")
        return []

def get_queue_message_count(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password, queue_name):
    """
    Get the number of messages in a specific RabbitMQ queue using the RabbitMQ Management HTTP API.

    Args:
        rabbitmq_server_ip_address (str): The IP address or hostname of the RabbitMQ server.
        rabbitmq_server_username (str): Your RabbitMQ username.
        rabbitmq_server_password (str): Your RabbitMQ password.
        queue_name (str): The name of the RabbitMQ queue to get the message count for.

    Returns:
        int: The number of messages in the specified queue.
    """
    # Create an HTTP Basic Authentication header with your RabbitMQ username and password
    rabbitmq_management_api_url = f"http://{rabbitmq_server_ip_address}:15672"
    auth = (rabbitmq_server_username, rabbitmq_server_password)

    # Make an HTTP GET request to the RabbitMQ Management API to get queue details
    response = requests.get(f"{rabbitmq_management_api_url}/api/queues/%2F/{queue_name}", auth=auth)

    if response.status_code == 200:
        # Parse the JSON response and extract the message count
        queue_data = response.json()
        message_count = queue_data["messages"]
        return message_count
    else:
        print(f"Failed to retrieve message count. Status code: {response.status_code}")
        return -1  # Return -1 to indicate an error
    
def print_rabbitmq_queues_and_num_messages():
    rabbitmq_server_ip_address = os.environ.get('rabbitmq_server_ip_address')
    rabbitmq_server_username = os.environ.get('rabbitmq_server_username')
    rabbitmq_server_password = os.environ.get('rabbitmq_server_password')
    current_queues = list_rabbitmq_queues(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password)

    channel = initialize_rabbitmq_client_and_create_channel()
    for queue_name in current_queues:
        print(queue_name)
        message_count = get_queue_message_count(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password, queue_name)
        print(message_count)

def clear_all_rabbitmq_queues():
    rabbitmq_server_ip_address = os.environ.get('rabbitmq_server_ip_address')
    rabbitmq_server_username = os.environ.get('rabbitmq_server_username')
    rabbitmq_server_password = os.environ.get('rabbitmq_server_password')
    current_queues = list_rabbitmq_queues(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password)

    channel = initialize_rabbitmq_client_and_create_channel()
    for queue_name in current_queues:
        print(queue_name)
        message_count = get_queue_message_count(rabbitmq_server_ip_address, rabbitmq_server_username, rabbitmq_server_password, queue_name)
        print(message_count)
        # print()
        clear_rabbitmq_queue(channel, queue_name)