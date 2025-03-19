import os
import sys
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv, dotenv_values, set_key

def get_env_keys(env_var_path: str) -> List[str]:
    """Get all environment variable keys from .env file"""
    if os.path.exists(env_var_path):
        return list(dotenv_values(env_var_path).keys())
    return []

def add_local_machine_public_ip_to_env(env_var_path: str) -> None:
    """Add local machine's public IP to .env file"""
    try:
        response = requests.get('http://httpbin.org/ip')
        if response.status_code == 200:
            public_ip = response.json()['origin']
            set_key(env_var_path, 'local_machine_public_ip', public_ip)
    except Exception as e:
        print(f"Warning: Could not get public IP: {str(e)}")

def load_in_env_vars() -> None:
    """Load environment variables from .env file"""
    # Get the base directory (two levels up from this file)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_var_path = os.path.join(base_dir, '.env')
    
    if os.path.exists(env_var_path):
        load_dotenv(env_var_path)
        add_local_machine_public_ip_to_env(env_var_path)
    else:
        print("Warning: .env file not found. Proceeding may fail.")

def update_env_vars(env_vars: Dict[str, Any]) -> None:
    """Update environment variables in .env file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_var_path = os.path.join(base_dir, '.env')
    
    for key, value in env_vars.items():
        set_key(env_var_path, key, str(value))
    
    # Reload environment variables
    load_in_env_vars() 