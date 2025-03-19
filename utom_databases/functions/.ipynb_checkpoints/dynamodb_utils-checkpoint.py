import os
import boto3
import botocore

def create_dynamodb_table(table_name, partition_key, ttl_key_name=None, ttl_seconds=None):
    """
    This checks if the table already exists and if it doesnt, it creates it
    """

    # - Get AWS params
    aws_default_region = os.environ.get('aws_default_region')
    aws_credentials = {
        'aws_access_key_id': os.environ.get('s3_access_key'),
        'aws_secret_access_key': os.environ.get('s3_secret_access_key')
    }

    # Create a DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)

    try:
        # Check if the table exists
        response = dynamodb.describe_table(TableName=table_name)
        print(f"The table {table_name} already exists.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table does not exist, so create it
            print(f"The table {table_name} does not exist. Creating it...")

            # Define the table's schema
            table_schema = [
                {
                    'AttributeName': partition_key,
                    'AttributeType': 'S'  # Assuming article_id is a string
                }
            ]

            # If TTL parameters are provided, add TTL specifications
            if ttl_key_name and ttl_seconds:
                table_schema.append({
                    'AttributeName': ttl_key_name,
                    'AttributeType': 'N'
                })

            # Create the table
            key_schema = [
                {
                    'AttributeName': partition_key,
                    'KeyType': 'HASH'  # HASH indicates the partition key
                }
            ]
            if ttl_key_name and ttl_seconds:
                key_schema.append({
                    'AttributeName': ttl_key_name,
                    'KeyType': 'RANGE'  # RANGE indicates the sort key (only if needed)
                })

            dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=table_schema,
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,  # Adjust these values as needed
                    'WriteCapacityUnits': 5
                }
            )

            # Wait for the table to be created
            dynamodb.get_waiter('table_exists').wait(TableName=table_name)
            print(f"The table {table_name} has been created.")
            # If TTL parameters are provided, enable TTL
            if ttl_key_name and ttl_seconds:
                dynamodb.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'AttributeName': ttl_key_name,
                        'Enabled': True
                    }
                )
        else:
            raise e  # Re-raise any other exceptions

def get_dynamo_table_table_description(table_name):
    """
    In cases where there may be some confusion / wahala, this functionality gets you the schema information for your table
    """
    # Get AWS parameters
    aws_default_region = os.environ.get('aws_default_region')
    aws_credentials = {
        'aws_access_key_id': os.environ.get('s3_access_key'),
        'aws_secret_access_key': os.environ.get('s3_secret_access_key')
    }
    
    # Create a DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)
    # table_name = 'YourTableName'  # Replace with the name of your table
    
    response = dynamodb.describe_table(TableName=table_name)
    table_description = response['Table']
    
    print("Table Name:", table_description['TableName'])
    print("Key Schema:", table_description['KeySchema'])
    print("Attribute Definitions:", table_description['AttributeDefinitions'])

    return table_description
    
def generate_dynamo_entry_from_dynamo_compatible_dict(input_dict):
    """
    This takes a dict that has been transformed to by dynamo compatible and then restructured it to prepare
    for input into dynamoDB
    """
    # Create an item to store in DynamoDB
    dynamodb_dict = {}

    # Iterate through the input dictionary and format the data for DynamoDB
    for key, value in input_dict.items():
        # Use 'S' for string values, 'N' for numeric values, and 'M' for maps (nested dictionaries)
        if isinstance(value, str):
            dynamodb_dict[key] = {'S': value}
        elif isinstance(value, int):
            dynamodb_dict[key] = {'N': str(value)}
        elif isinstance(value, dict):
            # Handle nested dictionaries
            nested_map = {}
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, str):
                    nested_map[nested_key] = {'S': nested_value}
                elif isinstance(nested_value, int):
                    nested_map[nested_key] = {'N': str(nested_value)}
            dynamodb_dict[key] = {'M': nested_map}

    return dynamodb_dict

def store_dynamodb_dict_in_dynamodb(table_name, dynamodb_dict):

    aws_default_region = os.environ.get('aws_default_region')
    aws_credentials = {
    'aws_access_key_id' : os.environ.get('s3_access_key'),
    'aws_secret_access_key' : os.environ.get('s3_secret_access_key'),
    }
    
    # Create a DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)
    
    # Store the item in DynamoDB
    response = dynamodb.put_item(
        TableName=table_name,
        Item=dynamodb_dict
    )

    return response

def dynamodb_item_to_dict(item):
    # Convert a DynamoDB item to a dictionary
    result = {}
    for key, value in item.items():
        result[key] = list(value.values())[0]
    return result
    
def get_list_of_dicts_of_all_items_in_dynamodb_table(table_name):
    # - Get AWS params
    aws_default_region = os.environ.get('aws_default_region')
    aws_credentials = {
        'aws_access_key_id': os.environ.get('s3_access_key'),
        'aws_secret_access_key': os.environ.get('s3_secret_access_key')
    }

    # Create a DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)

    # Initialize an empty list to store the items
    items = []

    # Use a DynamoDB paginator to scan the entire table
    paginator = dynamodb.get_paginator('scan')
    for page in paginator.paginate(TableName=table_name):
        items.extend(page['Items'])

    # Convert the DynamoDB items to dictionaries
    items_as_dicts = [dynamodb_item_to_dict(item) for item in items]

    return items_as_dicts

def get_item_count_in_dynamodb_table(table_name):
    try:
        # Get AWS parameters
        aws_default_region = os.environ.get('aws_default_region')
        aws_credentials = {
            'aws_access_key_id': os.environ.get('s3_access_key'),
            'aws_secret_access_key': os.environ.get('s3_secret_access_key')
        }

        # Create a DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)

        # Use a DynamoDB scan to count the items in the table
        response = dynamodb.scan(TableName=table_name, Select='COUNT')

        # Extract and return the item count
        item_count = response.get('Count', 0)

        return item_count
    except Exception as e:
        return str(e)

def get_dynamodb_table_item(table_name, primary_key):
    try:
        # Get AWS parameters
        aws_default_region = os.environ.get('aws_default_region')
        aws_credentials = {
            'aws_access_key_id': os.environ.get('s3_access_key'),
            'aws_secret_access_key': os.environ.get('s3_secret_access_key')
        }

        # Create a DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)

        # Get the item from DynamoDB
        response = dynamodb.get_item(
            TableName=table_name,
            Key=primary_key
        )

        item = response.get('Item')

        return item
    except Exception as e:
        return str(e)

def update_dynamodb_table_item(table_name, primary_key, update_data):
    try:
        # Get AWS parameters
        aws_default_region = os.environ.get('aws_default_region')
        aws_credentials = {
            'aws_access_key_id': os.environ.get('s3_access_key'),
            'aws_secret_access_key': os.environ.get('s3_secret_access_key')
        }

        # Create a DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=aws_default_region, **aws_credentials)

        # Generate UpdateExpression and ExpressionAttributeValues from update_data
        update_expression = 'SET '
        expression_attribute_values = {}

        for key, value in update_data.items():
            update_expression += f'{key} = :{key}, '
            expression_attribute_values[f':{key}'] = value

        # Remove the trailing comma and space from UpdateExpression
        update_expression = update_expression[:-2]

        # Update the item in DynamoDB
        response = dynamodb.update_item(
            TableName=table_name,
            Key=primary_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='UPDATED_NEW'
        )

        return response
    except Exception as e:
        return str(e)