# Environment Variable and AWS Secrets Management Script

## Overview
This script is designed to manage environment variables and AWS secrets for an application. It performs several tasks:
- Configures the Python path to include the project's root directory.
- Loads environment variables from a `.env` file using the `python-dotenv` library.
- Retrieves the local machine's public IP address and adds it to the `.env` file.
- Updates AWS secrets with new key-value pairs.
- Ensures the environment variables are refreshed after AWS secrets updates.

## Installation & Dependencies
Before running the script, ensure you have the following dependencies installed:

- Python 3.x
- [requests](https://pypi.org/project/requests/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- A custom module `utom_aws` with its submodule `functions.aws_secrets`

You can install the required packages via pip:
```
pip install requests python-dotenv
```
Make sure that the custom module `utom_aws` is available in your project path.

## Usage
1. **Ensure the .env file is available**  
   Place the `.env` file at the base directory of your project (two levels up from this script's location).
   
2. **Run the script**  
   Execute the script directly using Python:
   ```
   python <script_name>.py
   ```
   Adjust `<script_name>.py` to the actual file name.

3. **Update AWS secrets**  
   To update AWS secrets with new parameters, call the function `update_aws_secrets_with_input_dict` from your code or integrate it into your workflow.

## Function / Class Documentation

### get_env_keys(env_var_path)
- **Purpose:**  
  Reads a `.env` file and returns a list of all environment variable keys contained in it.
- **Parameters:**
  - `env_var_path` (str): Path to the `.env` file.
- **Returns:**
  - `list`: A list of strings representing the environment variable keys.

### add_local_machine_public_ip_to_env(env_var_path)
- **Purpose:**  
  Retrieves the local machine's public IP address using an HTTP GET request and updates the `.env` file with the key `local_machine_public_ip`.
- **Parameters:**
  - `env_var_path` (str): Path to the `.env` file.
- **Returns:**  
  - None  
  (The function updates the `.env` file in place.)

### load_in_env_vars()
- **Purpose:**  
  Loads environment variables from the specified `.env` file. If the file exists, it loads the variables using `python-dotenv` and attempts to update the `local_machine_public_ip`. If it does not exist, the user is informed that proceeding may fail.
- **Parameters:**  
  - None.
- **Returns:**  
  - None.

### update_aws_secrets_with_input_dict(aws_secret_name, latest_aws_secret_params_dict)
- **Purpose:**  
  Updates the AWS secrets with new key-value pairs provided in the input dictionary.
- **Parameters:**
  - `aws_secret_name` (str): The name of the AWS secret to be updated.
  - `latest_aws_secret_params_dict` (dict): A dictionary of key-value pairs that should be added or updated in the AWS secret.
- **Returns:**  
  - None  
  (It updates the AWS secret, reloads the `.env` file, and prints the last 10 keys of the updated environment variables.)

## Code Walkthrough

1. **Setting Up the PYTHONPATH:**
   - The script calculates the base directory. It determines the script's directory using `os.path.dirname(os.path.abspath(__file__))`, splits the path, removes the last two directories, and reconstructs the base path.
   - The base directory is then inserted at the start of the system path (`sys.path`) to allow for easy module imports.

2. **Importing Dependencies:**
   - Standard libraries: `os` and `sys`
   - Third-party libraries: `requests`, `dotenv` functions such as `load_dotenv`, `dotenv_values`, and `set_key`
   - A custom module: `aws_secrets` from `utom_aws.functions`

3. **Function Definitions:**
   - `get_env_keys`: Loads environment variables from the specified `.env` file and returns a list of keys.
   - `add_local_machine_public_ip_to_env`: Retrieves the local machine’s public IP address by making an HTTP GET request to `httpbin.org/ip`, updates the `.env` file with this IP.
   - `load_in_env_vars`: Checks for the existence of the `.env` file. If present, loads the env vars and attempts to update the local IP; if not, it notifies the user of the missing file.
   - `update_aws_secrets_with_input_dict`: Uses the AWS secrets management functions to update and download AWS secrets into the `.env` file. After updating, it prints the last 10 keys from the environment variables for confirmation.

4. **Workflow Summary:**
   - The script first ensures the environment is properly configured by adjusting the PYTHONPATH.
   - It then loads or updates the environment variables from the `.env` file.
   - If necessary, it communicates with AWS Secrets Manager to update the secrets based on new input parameters.
   - Finally, it prints the most recent environment variables loaded.

## Example Output
If the script runs successfully and the `.env` file is updated, you might see an output similar to the following in the console:
```
The env vars have been loaded in and these are the last 10 keys
['KEY7', 'KEY8', 'KEY9', 'KEY10', 'local_machine_public_ip', ...]
```
This output indicates that the local machine’s public IP has been successfully added to the environment variables and that the AWS secrets update process completed.

## Error Handling
- **Environment File Check:**  
  The `load_in_env_vars` function first checks whether the `.env` file exists. If not, it warns the user that the file is missing, which is critical for the rest of the process.
  
- **Try-Except Block:**  
  In `load_in_env_vars`, when attempting to update the local machine's public IP with `add_local_machine_public_ip_to_env`, any exceptions are caught by a bare `except` clause. While this prevents the script from crashing, it might hide specific errors. In practice, consider catching specific exceptions to provide meaningful error messages.

---

This documentation should serve as a comprehensive guide to understanding, setting up, and using the script for environment variable and AWS secrets management.