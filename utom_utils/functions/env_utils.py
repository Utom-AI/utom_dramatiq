## Add the root path so modules can be easily imported
import os
import sys
temp = os.path.dirname(os.path.abspath(__file__))
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR

# Add the root path to our python paths
sys.path.insert(0, BASE_DIR)

import requests
from dotenv import load_dotenv, dotenv_values, set_key

from utom_aws.functions import aws_secrets

def get_env_keys(env_var_path):
    """
    Get a list of all keys (variables) in the .env file.

    Args:
        env_file_path (str): The path to the .env file.

    Returns:
        list: A list of all keys (variable names) in the .env file.
    """
    # Load the .env file
    load_dotenv(env_var_path)

    # Get all keys (variables) from the loaded environment
    keys = os.environ.keys()

    return list(keys)
    
def add_local_machine_public_ip_to_env(env_var_path):
    try:
        # Make an HTTP GET request to httpbin to get your public IP address
        response = requests.get("https://httpbin.org/ip")
        local_machine_public_ip = response.json()["origin"]
        
        # Load the current variables from the .env file
        env = dotenv_values(env_var_path)
        
        # Add or update a variable
        env["local_machine_public_ip"] = local_machine_public_ip
        
        # Write the updated variables back to the .env file
        set_key(env_var_path, "local_machine_public_ip", local_machine_public_ip)
    except Exception as e:
        print(f"Warning: Could not add local machine public IP: {str(e)}")

def load_in_env_vars():
    """
    Loads in the env vars from .env file
    """
    # Get the project root directory (2 levels up from this file)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Load environment variables from .env file
    env_var_path = os.path.join(project_root, '.env')
    
    if os.path.isfile(env_var_path):
        # Load the .env file
        load_dotenv(env_var_path)
        
        try:
            add_local_machine_public_ip_to_env(env_var_path)
        except Exception as e:
            print(f"Warning: Could not add local machine public IP: {str(e)}")
    else:
        print('Warning: The .env file does not exist at:', env_var_path)

def update_aws_secrets_with_input_dict(aws_secret_name, latest_aws_secret_params_dict):
    """
    This takes an input dict of key-value pairs that we want to add to
    the aws secrets 
    """
    # - First load in the current .env so we can make sure we have the aws params
    load_in_env_vars()

    # - Update the aws secrets with the input key-value pairs
    aws_secrets.create_or_update_aws_secret(aws_secret_name, latest_aws_secret_params_dict)
    
    # - reload the .env with the latest stuff
    env_var_path = os.path.join(BASE_DIR, '.env')
    aws_secrets.download_secret_to_env_file(aws_secret_name, env_var_path)

    # load in the env vars again after the update
    load_in_env_vars()
    
    # Get keys
    keys = get_env_keys(env_var_path)
    print('The env vars have been loaded in and these are the last 10 keys')
    print(keys[-10:])

