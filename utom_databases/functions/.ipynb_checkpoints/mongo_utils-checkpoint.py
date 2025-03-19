import os
import sys
import ssl
import pymongo
from pymongo import IndexModel
import random
from pymongo import MongoClient, ASCENDING, IndexModel
from bson.objectid import ObjectId

# Add the root path so modules can be easily imported
temp = os.path.dirname(os.path.abspath(__file__))
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR
sys.path.insert(0, BASE_DIR)

"""
This module contains all functions related to MongoDB
"""
def initialise_mongodb_atlas_cloud_db_client():
    """
    Initialize a MongoDB client for a cloud-based database.

    Args:
        storri_config_params_dict (dict): A dictionary containing configuration parameters.
        mongo_server_name (str): The name of the MongoDB server to connect to.

    Returns:
        MongoClient: A MongoDB client instance.
    """
    # Get params
    mongodb_server_name = os.environ.get('storri_mongodb_server_name')
    mongodb_username = os.environ.get('storri_mongodb_username')
    mongodb_password = os.environ.get('storri_mongodb_password') 

    # Generate the connection string based on the selected server name
    if mongodb_server_name == 'staging':
        CONNECTION_STRING = "mongodb+srv://%s:%s@cluster0.uekmf3f.mongodb.net/?retryWrites=true&w=majority" % (mongodb_username, mongodb_password)
    else:
        print('We dont have a relevant mongo server to connect to')

    client = MongoClient(CONNECTION_STRING)

    return client
    
def initialise_mongo_cloud_db_client():
    """
    Initializes a MongoDB client to connect to a MongoDB server in the cloud.

    This function reads environment variables to obtain the public IP address of the MongoDB server,
    the MongoDB server's username, and the MongoDB server's password. It then creates a connection
    string and establishes a connection to the MongoDB server using the PyMongo library.

    Returns:
        MongoClient: A connected MongoDB client.

    Raises:
        ValueError: If any of the required environment variables are not set.
    """

    # Read environment variables
    mongo_server_public_ip_address = os.environ.get('mongo_server_public_ip_address')
    mongodb_server_username = os.environ.get('mongodb_server_username')
    mongodb_server_password = os.environ.get('mongodb_server_password')

    # # Print the environment variables (optional)
    # print(f"MongoDB Server IP: {mongo_server_public_ip_address}")
    # print(f"MongoDB Username: {mongodb_server_username}")
    # print("MongoDB Password: [Hidden]")

    # Create the MongoDB connection string
    CONNECTION_STRING = "mongodb://%s:%s@%s:27017/" % (mongodb_server_username, mongodb_server_password, mongo_server_public_ip_address)

    # Establish a connection to the MongoDB server
    client = MongoClient(CONNECTION_STRING)

    return client

def get_mongo_server_stats():
    """
    Retrieve and display MongoDB server connection statistics.

    This function connects to a MongoDB server, retrieves server status information, and extracts connection statistics,
    including the number of current and available connections. It then prints the statistics and returns the full server status.

    Returns:
        dict: A dictionary containing the full server status information.

    Raises:
        Exception: If there is an error during the connection or status retrieval.
    """

    # Initialize the MongoDB client by connecting to the cloud database
    mongo_client = mongo.initialise_mongo_cloud_db_client()

    # Retrieve server status information using the "serverStatus" command
    stats = mongo_client.admin.command("serverStatus")

    # Extract connection statistics from the server status
    connections = stats["connections"]
    current_connections = connections["current"]
    available_connections = connections["available"]

    # Print the connection statistics
    print('Num current connections: %s' % current_connections)
    print('Num available connections: %s' % available_connections)

    return stats

def input_data_into_mongo_db_collection(client, db_name, collection_name, input_data_dict):
    """
    Insert a single document into a MongoDB collection.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        input_data_dict (dict): The document data to insert.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    # Add data to the collection
    collection.insert_one(input_data_dict)


def input_document_list_into_mongo_db_collection(client, db_name, collection_name, document_list):
    """
    Insert multiple documents into a MongoDB collection.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        document_list (list): A list of document data to insert.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    # Add data to the collection
    collection.insert_many(document_list)


def get_all_documents_from_mongo_collection(client, db_name, collection_name):
    """
    Retrieve all documents from a MongoDB collection.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.

    Returns:
        pymongo.cursor.Cursor: A cursor to iterate over the documents.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    all_docs_gen = collection.find({})

    return all_docs_gen


def get_document_dict_for_mongo_db_collection_by_object_id(client, db_name, collection_name, object_id):
    """
    Retrieve a document from a MongoDB collection by its ObjectID.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        object_id (str): The ObjectID of the document to retrieve.

    Returns:
        dict: The document as a dictionary.
    """
    # Initialise the db connection
    db = client[db_name]
    collection = db[collection_name]

    # Read in the document given the object id
    doc_dict = collection.find_one({"_id": ObjectId(object_id)})

    return doc_dict


def search_mongo_collection_by_key_and_search_term(client, db_name, collection_name, key_name, search_term,
                                                   match_type='full'):
    """
    Search for a document in a MongoDB collection by a specific key and search term.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        key_name (str): The name of the key to search.
        search_term (str): The search term to match.
        match_type (str, optional): The type of match ('full' or 'partial'). Defaults to 'full'.

    Returns:
        dict: The matching document as a dictionary.
    """
    db = client[db_name]
    collection = db[collection_name]

    if match_type == 'full':
        search_results_gen = collection.find_one({key_name: search_term},
                                                 sort=[('_id', pymongo.DESCENDING)])
    elif match_type == 'partial':
        search_results_gen = collection.find_one({key_name: {'$regex': search_term}},
                                                 sort=[('_id', pymongo.DESCENDING)])

    return search_results_gen


def search_mongo_collection_by_multiple_key_and_search_term(client, db_name, collection_name, key_list,
                                                            search_term_list):
    """
    Search for documents in a MongoDB collection by multiple keys and their corresponding search terms.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        key_list (list): A list of keys to search.
        search_term_list (list): A list of search terms corresponding to the keys.

    Returns:
        pymongo.cursor.Cursor: A cursor to iterate over the matching documents.
    """
    search_dict = {}

    for i in range(len(key_list)):
        key = key_list[i]
        search_term = search_term_list[i]
        s_dict = {key: search_term}
        search_dict.update(s_dict)

    db = client[db_name]
    collection = db[collection_name]
    search_results_gen = collection.find(search_dict)

    return search_results_gen


def update_mongo_collection_document(client, db_name, collection_name, content_id, input_data_dict):
    """
    Update a document in a MongoDB collection by its ObjectID.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        content_id (str): The ObjectID of the document to update.
        input_data_dict (dict): The updated document data.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    # Update the document
    query = {"_id": ObjectId(content_id)}
    result = collection.replace_one(query, input_data_dict)


def update_mongo_collection_document_by_obj_id(client, db_name, collection_name, content_id, input_data_dict):
    """
    Update a document in a MongoDB collection by its custom ObjectID.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        content_id (str): The custom ObjectID of the document to update.
        input_data_dict (dict): The updated document data.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    # Update the document
    query = {"_id": content_id}
    result = collection.replace_one(query, input_data_dict)

def delete_mongodb_collection(client, db_name, collection_name):
    """
    Delete a MongoDB collection.

    Args:
        client (MongoClient): The MongoDB client.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to delete.

    Returns:
        bool: True if the collection was deleted successfully, False otherwise.
    """
    try:
        # Access the specified database
        db = client[db_name]
        
        # Drop the specified collection
        db.drop_collection(collection_name)
        
        print(f"Collection '{collection_name}' deleted successfully.")
        return True
    except Exception as e:
        print(f"Error deleting collection '{collection_name}': {str(e)}")
        return False

def count_documents_in_collection(client, db_name, collection_name):
    """
    Get the number of documents in a MongoDB collection.

    Args:
        client (MongoClient): The MongoDB client.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to count documents in.

    Returns:
        int: The number of documents in the collection.
    """
    try:
        # Access the specified database
        db = client[db_name]

        # Access the specified collection
        collection = db[collection_name]

        # Use the count_documents method to count documents in the collection
        count = collection.count_documents({})

        return count
    except Exception as e:
        print(f"Error counting documents in collection '{collection_name}': {str(e)}")
        return -1  # Return -1 to indicate an error

def pick_random_document_from_collection(client, db_name, collection_name):
    """
    Pick a random document from a MongoDB collection.

    Args:
        client (MongoClient): The MongoDB client.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to pick a document from.

    Returns:
        dict: A random document from the collection, or None if the collection is empty.
    """
    try:
        # Access the specified database
        db = client[db_name]

        # Access the specified collection
        collection = db[collection_name]

        # Get the total number of documents in the collection
        total_documents = collection.count_documents({})

        if total_documents == 0:
            print(f"Collection '{collection_name}' is empty.")
            return None

        # Generate a random index within the range of the number of documents
        random_index = random.randint(0, total_documents - 1)

        # Find one document at the random index
        random_document = collection.find().skip(random_index).limit(1).next()

        return random_document
    except Exception as e:
        print(f"Error picking a random document from collection '{collection_name}': {str(e)}")
        return None


def remove_duplicate_documents_by_field(client, db_name, collection_name, field_name = 'article_url'):
    db = client[db_name]
    collection = db[collection_name]
    
    pipeline = [
        {
            "$group": {
                "_id": "$" + field_name,
                "unique_ids": {"$addToSet": "$_id"},
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        }
    ]
    
    duplicate_docs = list(collection.aggregate(pipeline))
    
    # Remove duplicate documents
    num_duplicates_deleted = 0
    for duplicate in duplicate_docs:
        # Keep the first document and delete the others
        ids_to_delete = duplicate['unique_ids'][1:]
        num_duplicates_deleted += len(ids_to_delete)
        collection.delete_many({"_id": {"$in": ids_to_delete}})
    print('%s duplicate documents have been deleted' % num_duplicates_deleted)


def update_document_in_mongo_by_document_id_str(mongo_client, db_name, collection_name, document_id_key_name, document_id_str, updated_document_json):
    """
    Updated Document JSON would only contain the specific keys that you want to update and doesnt need the entire document
    """
    try:
        # Select the database
        db = mongo_client[db_name]

        # Select the collection
        collection = db[collection_name]

        query = {document_id_key_name: document_id_str}
        
        # Update the document that matches the query with the updated task JSON
        update_result = collection.update_one(query, {"$set": updated_document_json})

        # if update_result.modified_count > 0:
        #     print(f"{update_result.modified_count} document(s) updated.")
        # else:
        #     print("No matching document found for the query.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def find_documents_by_id(mongo_client, db_name, collection_name, document_id_key_name, document_id_str):
    try:
        # Select the database
        db = mongo_client[db_name]

        # Select the collection
        collection = db[collection_name]

        # Define the query to find documents with the specified ID
        query = {document_id_key_name: document_id_str}

        # Find documents that match the query
        matching_documents = list(collection.find(query))

        return matching_documents
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def update_documents_in_db(db_name, collection_name, documents_to_update):
    """
    This would take a lis tof documents that we want to update, and the db and collection names and then do the update
    """
    # Connect to the MongoDB
    mongo_client = initialise_mongo_cloud_db_client()

    db = mongo_client[db_name]
    collection = db[collection_name]

    # Prepare the bulk update operations
    bulk_operations = []
    for doc in documents_to_update:
        query = {'_id': doc['_id']}  # Adjust this query based on your data structure
        update = {'$set': doc}
        bulk_operations.append(pymongo.UpdateOne(query, update))

    # Perform the bulk update
    if bulk_operations:
        result = collection.bulk_write(bulk_operations)

        # Check the result for any errors
        if result.matched_count != len(documents_to_update):
            print("Warning: Not all documents were updated!")

# def create_ttl_index(mongo_client, db_name, collection_name, ttl_field, ttl_seconds):
#     try:
#         # Select the database
#         db = mongo_client[db_name]

#         # Select the collection
#         collection = db[collection_name]

#         # Check if the TTL index already exists
#         index_names = [index['name'] for index in collection.list_indexes()]
#         if f"{ttl_field}_1" not in index_names:
#             # Define the TTL index
#             ttl_index = [(ttl_field, 1)]

#             # Create the TTL index
#             collection.create_index(ttl_index, expireAfterSeconds=ttl_seconds)

#             print(f"TTL index created for {collection_name} with {ttl_seconds} seconds.")
#         else:
#             print(f"TTL index for {collection_name} already exists.")

#     except Exception as e:
#         print(f"An error occurred: {str(e)}")


def create_ttl_unix_timestamp_index(client, db_name, collection_name, index_name):
    try:
        # Select the database
        db = client[db_name]

        # Select the collection
        collection = db[collection_name]

        # Create a TTL index with the specified index name
        index_spec = [(index_name, ASCENDING)]
        index_options = {"expireAfterSeconds": 0}  # Expire documents immediately (0 seconds)
        collection.create_index(index_spec, expireAfterSeconds=index_options["expireAfterSeconds"])

        print(f"TTL index '{index_name}' has been created in the '{collection_name}' collection.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
