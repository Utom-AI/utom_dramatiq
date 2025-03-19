"""
Driptok Redis 
"""
import os
import redis
import socket

"""
ENV to add

redis_server_ip_address = os.environ.get('redis_server_ip_address')
"""

def generate_redis_labs_server_url_from_host_name_port_number_etc(redis_host_name, redis_port_number, redis_user_password):
    """
    Generates a Redis server URL for connecting to a Redis Labs server with authentication.

    Args:
        redis_host_name (str): The hostname or IP address of the Redis server.
        redis_port_number (int): The port number of the Redis server.
        redis_user_password (str): The password for authentication.

    Returns:
        str: The Redis server URL with authentication.

    Example:
        redis_url = generate_redis_labs_server_url_from_host_name_port_number_etc(
            "redis-19383.c278.us-east-1-4.ec2.cloud.redislabs.com",
            19383,
            "SKGAjhd1od2827oT83nysJzmXGMPleET"
        )
    """
    # Construct the Redis server URL with authentication
    redis_server_url = f"redis://:{redis_user_password}@{redis_host_name}:{redis_port_number}"
    
    # Return the generated URL
    return redis_server_url
    
def initialise_redis_hetzner_cloud_db_client():
    """
    Initialize a Redis client to connect to a Redis server.

    Parameters:
    - redis_server_ip_address (str): The IP address or hostname of the Redis server.

    Returns:
    - redis.StrictRedis: A Redis client object connected to the specified Redis server.
    """
    
    # Create a Redis client object with the provided server address, port, and database.
    redis_server_ip_address = os.environ.get('redis_server_ip_address')
    redis_client = redis.StrictRedis(host=redis_server_ip_address, port=6379, db=0)

    # Return the Redis client object to the caller.
    return redis_client

def check_if_redis_is_running(redis_client):
    """
    Check if a Redis server is running by sending a PING command.

    Parameters:
    - redis_client (redis.StrictRedis): A Redis client object connected to the Redis server.

    Returns:
    None
    """

    # Send a PING command to the Redis server and store the response.
    response = redis_client.ping()

    # Check the response and print a message accordingly.
    if response:
        client_active = True
    else:
        client_active = False

    return client_active

def get_queue_ttl(redis_client, queue_name):
    """
    Get the remaining time to live (TTL) for a Redis key (queue).

    Args:
        redis_client (redis.client.StrictRedis): A Redis client instance.
        queue_name (str): The name of the Redis key (queue).

    Returns:
        int: The remaining TTL in seconds. Returns -2 if the key does not exist,
             -1 if the key exists but does not have an associated TTL, or 0 if the key has expired.
    """
    # Use the TTL command to get the remaining time to live for the key (queue)
    ttl = redis_client.ttl(queue_name)
    
    return ttl
    
def push_to_redis_queue(redis_client, queue_name, data):
    """
    Push data to a Redis queue using a pre-existing Redis client.

    Parameters:
    - redis_client (redis.StrictRedis): A Redis client object connected to the Redis server.
    - queue_name (str): The name of the Redis queue.
    - data (str): The data to be pushed into the queue.

    Returns:
    bool: True if the data was successfully pushed to the queue, False otherwise.
    """

    try:
        # Push the data to the Redis queue
        redis_client.lpush(queue_name, data)

        # Return True to indicate a successful push
        return True
    except Exception as e:
        # Print an error message if there's an exception and return False
        print(f"Error pushing data to Redis queue: {e}")
        return False

def get_all_queue_names_in_redis_db(redis_client):
    """
    Get a list of all queue names in a Redis database that match a specified pattern.

    Args:
        redis_client (redis.StrictRedis): A Redis client instance connected to the Redis database.

    Returns:
        list: A list of queue names that match the specified pattern.

    Example:
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        queue_names = get_all_queue_names_in_redis_db(redis_client)
        print(queue_names)
    """
    # Specify a pattern to match your queue names (e.g., all keys ending with "_queue")
    queue_pattern = "*_queue"  # Adjust the pattern as needed
    
    # Use the keys command to get a list of keys (queue names) that match the pattern
    queues = redis_client.keys(queue_pattern)
    
    # Initialize a list to store the queue names
    queue_names_list = []
    
    # Convert each queue name from bytes to a string and add it to the list
    for queue_name in queues:
        queue_names_list.append(queue_name.decode('utf-8'))  # Convert bytes to a string
        
    return queue_names_list
    
def get_queue_length(redis_client, queue_name):
    """
    Get the number of tasks in a Redis queue.

    Args:
        redis_client (redis.client.StrictRedis): A Redis client instance.
        queue_name (str): The name of the Redis queue.

    Returns:
        int: The number of tasks in the queue.
    """
    # Use the llen method of the Redis client to retrieve the length (number of items) in the queue
    queue_length = redis_client.llen(queue_name)
    
    # Return the length of the queue as an integer
    return queue_length

def get_all_elements_from_queue(redis_client, queue_name):
    """
    Retrieve all elements from a Redis queue (list).

    Args:
        redis_client (redis.client.StrictRedis): A Redis client instance.
        queue_name (str): The name of the Redis queue (list).

    Returns:
        list: A list of all elements in the queue.
    """
    # Use the LRANGE command to retrieve all elements from the queue
    elements = redis_client.lrange(queue_name, 0, -1)
    
    # Decode elements from bytes to strings (assuming they are strings)
    decoded_elements = [element.decode('utf-8') for element in elements]
    
    return decoded_elements

def clear_redis_queue(redis_client, queue_name):
    """
    Clear all items from a Redis queue.

    Args:
        redis_client (redis.StrictRedis): A Redis client instance connected to the Redis server.
        queue_name (str): The name of the Redis queue to clear.
    """
    try:
        # Set the queue's range to 0 elements, effectively clearing it
        redis_client.ltrim(queue_name, 1, 0)
        
        return True  # Successfully cleared the queue
    except Exception as e:
        return str(e)  # Return any error message if an exception occurs
