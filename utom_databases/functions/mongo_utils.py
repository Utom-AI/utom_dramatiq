import os
import sys
import ssl
import pymongo
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

    # Read environment variables *** later we will read from env variables
    mongo_server_public_ip_address = '95.217.233.18'
    mongodb_server_username = 'utom_admin'
    mongodb_server_password = 'utom_secure_2024'

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
    mongo_client = initialise_mongo_cloud_db_client()

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

def search_mongo_collection_for_all_docs_by_key_and_search_term(client, db_name, collection_name, key_name, search_term, match_type='full'):
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
        list: A list of matching documents as dictionaries.
    """
    db = client[db_name]
    collection = db[collection_name]

    if match_type == 'full':
        search_results = collection.find({key_name: search_term})
    elif match_type == 'partial':
        search_results = collection.find({key_name: {'$regex': search_term}})

    # Sorting results by '_id' in descending order
    search_results = search_results.sort('_id', pymongo.DESCENDING)

    # Converting the cursor to a list of dictionaries
    result_list = list(search_results)

    return result_list


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

def get_documents_by_filter_criteria(client, db_name, collection_name, filter_criteria):
    """
    Get documents from a MongoDB collection based on specified key-value pairs.

    Parameters:
    - collection: MongoDB collection object
    - key_value_pairs: Dictionary containing key-value pairs for filtering
    
    Example Filter Criteria:
    filter_criteria = {
        # "task_name": "process_dripshot",
        "task_name": "create_dripshot_video",
        "task_status": "completed"
    }
    Returns:
    - List of documents matching the specified key-value pairs
    """
    db = client[db_name]
    collection = db[collection_name]

    query = {key: value for key, value in filter_criteria.items()}
    result = collection.find(query)

    return list(result)

def remove_documents_by_ids(client, db_name, collection_name, to_delete_object_id_list):
    """
    Remove documents from a MongoDB collection based on a list of _id objects.

    Args:
    - collection: MongoDB collection object.
    - id_list: List of _id objects to be removed.

    Returns:
    - None
    """
    db = client[db_name]
    collection = db[collection_name]
    try:
        # Convert _id strings to ObjectId
        object_ids = [id for id in to_delete_object_id_list]

        # Delete documents using the _id field
        result = collection.delete_many({'_id': {'$in': object_ids}})

        print(f"{result.deleted_count} documents removed.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
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

def update_mongo_collection_document_by_key(client, db_name, collection_name, key, key_value, input_data_dict):
    """
    Update a document in a MongoDB collection by a specified key.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        key (str): The key to identify the document to update.
        key_value (str): The value of the key to identify the document to update.
        input_data_dict (dict): The updated document data.
    """
    # Connect to the specific collection
    db = client[db_name]
    collection = db[collection_name]

    # Update the document
    query = {key: key_value}
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


def remove_duplicate_documents_by_field(client, db_name, collection_name, field_name='article_url'):
    """
    Remove duplicate documents from a MongoDB collection based on a specified field.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection where duplicates should be removed.
        field_name (str, optional): The field by which to identify duplicates. Defaults to 'article_url'.

    This function identifies duplicate documents within the specified collection based on the provided field and retains the first occurrence of each unique document.

    It does so by creating an aggregation pipeline:
    1. The first stage groups documents by the specified field and creates a list of unique IDs and counts the number of documents in each group.
    2. The second stage filters groups with a count greater than 1, which indicates duplicates.

    After identifying duplicate groups, the function iterates through them, keeping the first document and deleting the others by their IDs. It then prints the number of duplicate documents deleted.
    """
    db = client[db_name]
    collection = db[collection_name]

    # Create an aggregation pipeline to identify duplicate documents
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

    # Execute the aggregation pipeline and store the results
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
    Update a document in a MongoDB collection based on a document's ID using a JSON object with specific keys.

    Args:
        mongo_client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection containing the document.
        document_id_key_name (str): The key name used for document identification (e.g., '_id').
        document_id_str (str): The document's ID as a string.
        updated_document_json (dict): A JSON object containing specific keys to update.

    This function updates a document within the specified collection using its unique ID. The provided JSON object contains specific keys and their updated values. It performs an update operation to modify the document accordingly.

    In case of a successful update, the function returns None. If no matching document is found, no update occurs.

    Returns:
        None

    Raises:
        Exception: If there is an error during the update operation.
    """
    try:
        # Select the database
        db = mongo_client[db_name]

        # Select the collection
        collection = db[collection_name]

        query = {document_id_key_name: document_id_str}
        
        # Update the document that matches the query with the updated JSON object
        update_result = collection.update_one(query, {"$set": updated_document_json})

        # Check if any document was modified
        # if update_result.modified_count > 0:
        #     print(f"{update_result.modified_count} document(s) updated.")
        # else:
        #     print("No matching document found for the query.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def find_documents_by_id(mongo_client, db_name, collection_name, document_id_key_name, document_id_str):
    """
    Find documents in a MongoDB collection by their unique IDs.

    Args:
        mongo_client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to search.
        document_id_key_name (str): The key used for document identification (e.g., '_id').
        document_id_str (str): The unique ID of the document to search for.

    This function searches for documents in the specified collection that match the provided unique ID. The document_id_key_name determines the field used for identification.

    Returns:
        list: A list of matching documents as dictionaries. If no documents match the query, an empty list is returned.

    Raises:
        Exception: If there is an error during the search operation.
    """
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
    Update multiple documents in a MongoDB collection.

    Args:
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to update.
        documents_to_update (list): A list of documents with changes to apply.

    This function allows the bulk update of multiple documents within the specified collection. It connects to the MongoDB and performs update operations based on the provided documents_to_update list.

    Each document in the list should contain the document's unique ID and the specific keys to update.

    Example:
        documents_to_update = [
            {"_id": ObjectId("..."), "key_to_update1": "new_value1"},
            {"_id": ObjectId("..."), "key_to_update2": "new_value2"},
            # Additional documents
        ]

    Raises:
        Exception: If there is an error during the update operation.
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

def create_ttl_unix_timestamp_index(client, db_name, collection_name, index_name):
    """
    Create a TTL (Time-to-Live) index with UNIX timestamps in a MongoDB collection.

    Args:
        client (MongoClient): A MongoDB client instance.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection in which to create the TTL index.
        index_name (str): The name for the TTL index.

    This function creates a TTL index in a MongoDB collection using UNIX timestamps. A TTL index is used for automatically removing documents that have exceeded a specified time-to-live.

    The index_name is the name of the field in the documents that stores UNIX timestamps. The index is set to expire documents immediately (0 seconds).

    Example:
        create_ttl_unix_timestamp_index(client, 'my_db', 'my_collection', 'expiration_time')

    Raises:
        Exception: If there is an error during the TTL index creation.
    """
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
