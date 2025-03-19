# Environment Variable and AWS Secrets Manager

## Overview

This Python script is designed to manage environment variables stored in a `.env` file and integrate with AWS Secrets Manager. It performs the following tasks:

- Adds the root path to the Python module search path.
- Loads environment variables from a specified `.env` file.
- Automatically fetches the local machine's public IP address and updates the `.env` file with this information.
- Provides a function to update AWS Secrets with a new set of key-value pairs and subsequently refresh the local `.env` file with the latest secrets.
- Offers utility to retrieve all keys from the `.env` file.

## Installation & Dependencies

Before using this script, ensure that the following dependencies are installed:

- Python 3.x
- [requests](https://pypi.org/project/requests/): For making HTTP requests.
- [python-dotenv](https://pypi.org/project/python-dotenv/): For loading and updating environment variables in a `.env` file.
- A custom module from `utom_aws.functions` providing AWS Secrets operations. Ensure this module is available and properly configured in your project.

Install the Python packages using pip if needed:

```bash
pip install requests python-dotenv
```

## Usage

To run the script, ensure the `.env` file is present in the expected base directory. The script is intended to be imported as a module, but you can also call its functions directly. Below are examples of how to use the key functions:

### Example: Get Environment Keys

```python
from your_script_name import get_env_keys

env_file_path = '/path/to/your/.env'
keys = get_env_keys(env_file_path)
print("Env keys:", keys)
```

### Example: Update AWS Secrets

```python
from your_script_name import update_aws_secrets_with_input_dict

aws_secret_name = 'your_aws_secret_name'
params_to_update = {
    "key1": "value1",
    "key2": "value2"
}
update_aws_secrets_with_input_dict(aws_secret_name, params_to_update)
```

## Function Documentation

### get_env_keys(env_var_path)

- **Purpose**:  
  Retrieves all keys from a specified `.env` file.

- **Input Parameters**:  
  - `env_var_path` (str): The path to the `.env` file.

- **Return Value**:  
  - `list`: A list of strings representing the keys (environment variable names) contained in the `.env` file.

### add_local_machine_public_ip_to_env(env_var_path)

- **Purpose**:  
  Fetches the public IP address of the local machine using an HTTP request to httpbin.org and updates the `.env` file with this IP under the key `local_machine_public_ip`.

- **Input Parameters**:  
  - `env_var_path` (str): The path to the `.env` file.

- **Return Value**:  
  - None

### load_in_env_vars()

- **Purpose**:  
  Loads environment variables from the `.env` file stored at the base directory. If the `.env` file exists, it attempts to update it with the local machine’s public IP. If not, it prints an error message indicating that the file is missing.

- **Input Parameters**:  
  - None

- **Return Value**:  
  - None

### update_aws_secrets_with_input_dict(aws_secret_name, latest_aws_secret_params_dict)

- **Purpose**:  
  Updates an AWS Secret identified by its name with a dictionary of key-value pairs. After updating the secret, it downloads the latest secret configuration to the `.env` file and reloads the environment variables.

- **Input Parameters**:  
  - `aws_secret_name` (str): The name of the AWS secret to update.
  - `latest_aws_secret_params_dict` (dict): A dictionary containing the key-value pairs to be added or updated in the AWS secret.

- **Return Value**:  
  - None

## Code Walkthrough

1. **Setting Up the Module Path**:  
   - The script begins by determining the base directory of the project by splitting the current file's absolute path.
   - It then adds this base directory to the system path (`sys.path`) to ensure that modules within the project can be easily imported.

2. **Module Imports**:  
   - Standard libraries such as `os` and `sys` are imported.
   - Third-party libraries `requests` and functions from `dotenv` (`load_dotenv`, `dotenv_values`, `set_key`) are imported.
   - A custom module `utom_aws.functions.aws_secrets` is imported to interact with AWS Secrets Manager.

3. **Retrieving Environment Keys (`get_env_keys`)**:  
   - This function loads the specified `.env` file into the environment using `load_dotenv`.
   - It then retrieves and returns all environment variable keys as a list.

4. **Adding Local Machine Public IP (`add_local_machine_public_ip_to_env`)**:  
   - Makes an HTTP GET request to "https://httpbin.org/ip" to determine the machine’s public IP address.
   - Loads the current environment variables from the `.env` file using `dotenv_values`.
   - Updates the `.env` file with the new key `local_machine_public_ip` using `set_key`.

5. **Loading Environment Variables (`load_in_env_vars`)**:  
   - Constructs the path to the `.env` file (expected at the base directory).
   - Checks if the `.env` file exists.
     - If it does, it loads the environment and attempts to update it with the local machine's public IP.
     - If there is an error during the update, it is silently ignored using a generic try/except.
     - If the file does not exist, an error message is printed.

6. **Updating AWS Secrets (`update_aws_secrets_with_input_dict`)**:  
   - Initiates a loading of the current environment variables.
   - Calls a function from the custom AWS secrets module to create or update the secret with the provided dictionary.
   - Downloads the updated secret into the `.env` file.
   - Reloads the environment variables.
   - Retrieves and prints the last 10 keys from the environment variables to confirm the update.

## Example Output

When invoking the `update_aws_secrets_with_input_dict` function successfully, you might see an output similar to:

```
The env vars have been loaded in and these are the last 10 keys
['AWS_KEY_1', 'AWS_KEY_2', 'local_machine_public_ip', ...]
```

*(The actual keys will vary depending on the contents of your `.env` file.)*

## Error Handling

- In the `load_in_env_vars` function, the call to `add_local_machine_public_ip_to_env` is wrapped in a try/except block. This prevents the program from crashing if an exception occurs while updating the public IP (e.g., network issues or file permission errors).
- The script also prints error messages when the expected `.env` file is not found, ensuring that the user is aware of possible issues with the environment configuration.

---

This documentation should help you understand the purpose and functionality of the script as well as how to integrate it into your environment for managing secrets and environment variables.