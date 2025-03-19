import os
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

import os
from elasticsearch import Elasticsearch


def initialize_elasticsearch_client():
    """
    Initialize an Elasticsearch client based on configuration parameters.

    Returns:
        Elasticsearch: An Elasticsearch client instance.
    """
    
    # Extract the Elasticsearch host IP address from the configuration dictionary
    elasticsearch_host_ip_address = os.environ.get('elastic_search_server_public_ip_address')
    # print(elasticsearch_host_ip_address)
    elasticsearch_host_ip_address = 'http://%s:9200' % elasticsearch_host_ip_address
    # print(elasticsearch_host_ip_address)
    
    # Extract the Elasticsearch username and password from environment variables
    username = 'elastic'  # Assuming the default username
    password = os.environ.get('elastic_search_server_password')

    # Initialize an Elasticsearch client with the specified host IP address and authentication
    es_client = Elasticsearch(
        [elasticsearch_host_ip_address],
        http_auth=(username, password)  # Provide username and password for authentication
    )

    # Return the Elasticsearch client instance
    return es_client

def is_elasticsearch_client_active(es_client):
    """
    Check if the Elasticsearch client is active.

    Args:
        es_client (Elasticsearch): An Elasticsearch client instance.

    Returns:
        bool: True if the client is active, False otherwise.
    """
    try:
        # Perform a simple health check by sending a request to the cluster
        return es_client.ping()
    except ConnectionError:
        return False
    
def list_indices(es_client):
    """
    List all indices in the Elasticsearch cluster.

    Args:
        es_client (Elasticsearch): The Elasticsearch client.

    Returns:
        list: A list of index names.
    """
    # Get a list of index names using the Elasticsearch client
    indices_info = es_client.cat.indices(format="json", h="index")
    indices_list = [index["index"] for index in indices_info]
    return indices_list

def create_index(es_client, index_name, settings=None, mappings=None):
    """
    Create a new index in Elasticsearch with optional settings and mappings.

    Args:
        es_client (Elasticsearch): The Elasticsearch client.
        index_name (str): The name of the new index.
        settings (dict, optional): Index settings.
        mappings (dict, optional): Index mappings.

    Returns:
        bool: True if the index creation was successful, False otherwise.
    """
    # Check if the index already exists
    if not es_client.indices.exists(index_name):
        # Define the index body, including optional settings and mappings
        body = {}
        if settings:
            body['settings'] = settings
        if mappings:
            body['mappings'] = mappings

        # Attempt to create the index
        response = es_client.indices.create(index=index_name, body=body)
        
        # Check if the index creation was acknowledged
        return response.get('acknowledged', False)
    else:
        # Index already exists, return False
        return False

def create_index_without_mappings(es_client, index_name):
    es_client.indices.create(index=index_name)

def delete_index(es_client, index_name):
    es_client.indices.delete(index=index_name, ignore=[400, 404])

def clear_out_es_index(es_client, index_name):
    """   
    This function clear out the index and then reinitializes so that the index exists
    """
    # - Delete the index
    delete_index(es_client, index_name)

    # - Recreate the index
    create_index_without_mappings(es_client, index_name)
    
# def send_single_document_to_es_index(es_client, index_name, document):
#     try:
#         response = es_client.index(index=index_name, body=document)
#         print(f"Document indexed successfully. Index: {index_name}, Document ID: {response['_id']}")
#         print(document)
#     except Exception as e:
#         print(f"Error indexing document: {e}")

def send_single_document_to_es_index(es_client, index_name, document):
    try:
        es_client.indices.refresh()

        response = es_client.index(index=index_name, id='your_specific_id', body=document)
        
        es_client.indices.refresh()
        print(f"Document indexed successfully. Index: {index_name}, Document ID: {response['_id']}")
        print("Full response:", response)
    except Exception as e:
        print(f"Error indexing document: {e}")

def send_multiple_documents_to_es_index(es_client, index_name, documents):
    actions = [
        {
            "_index": index_name,
            "_source": document
        }
        for document in documents
    ]
    success, failed = bulk(es_client, actions=actions)
    print(f"Indexed {success} documents successfully, failed to index {failed} documents.")

def delete_documents_from_es_index(es_client, index_name, document_ids):
    try:
        for doc_id in document_ids:
            es_client.delete(index=index_name, id=doc_id)
        # print("Documents deleted successfully.")
    except Exception as e:
        print(f"Error deleting documents: {e}")
        
def get_document_count_in_es_index(es_client, index_name):
    """
    Get the number of documents in the specified Elasticsearch index.

    Parameters:
    - elastic_search_client: An instance of the Elasticsearch client.
    - index_name: Name of the Elasticsearch index.

    Returns:
    - Number of documents in the index, or 0 if an error occurs.
    """
    try:
        # Use the count API to get the document count for the specified index
        result = es_client.count(index=index_name)
        
        # Extract and return the document count
        document_count = result.get('count', 0)
        return document_count
    except Exception as e:
        # Handle any exceptions, e.g., connection errors
        print(f"Error: {e}")
        return 0

def get_all_es_index_documents(es_client, index_name):
    """
    Retrieve all documents from an Elasticsearch index.

    Parameters:
    - es_client: Elasticsearch client instance.
    - index_name: Name of the Elasticsearch index.

    Returns:
    - List of documents.
    """
    try:
        # Using match_all query to retrieve all documents
        result = es_client.search(index=index_name, body={"query": {"match_all": {}}}, size=10000)

        # Extract documents from the search result
        documents = [hit["_source"] for hit in result["hits"]["hits"]]
        return documents

    except Exception as e:
        print(f"Error: {e}")
        return []

def get_random_es_index_document(es_client, index_name):
    """
    Retrieve a random document from an Elasticsearch index using aggregation.

    Parameters:
    - es_client: Elasticsearch client instance.
    - index_name: Name of the Elasticsearch index.

    Returns:
    - A random document.
    """
    try:
        # Define the aggregation to sample a random document
        aggregation_query = {
            "sample": {
                "shard_size": 1
            }
        }

        # Execute the aggregation query
        result = es_client.search(index=index_name, body={"aggs": aggregation_query}, size=0)

        # Extract the random document from the aggregation result
        random_document = result["aggregations"]["sample"]["hits"]["hits"][0]["_source"]

        return random_document

    except Exception as e:
        print(f"Error: {e}")
        return None
    
def search(es_client, index_name, query):
    """
    Perform a search query on an index in Elasticsearch.

    Args:
        es_client (Elasticsearch): The Elasticsearch client.
        index_name (str): The name of the index to search.
        query (dict): The Elasticsearch query.

    Returns:
        dict: Elasticsearch search response.
    """
    # Perform the search query on the specified index
    return es_client.search(index=index_name, body=query)

def enhanced_search(es_client, index_name, query, field_weights):
    """
    Perform an enhanced search across multiple fields in an index with field weights.

    Args:
        es_client (Elasticsearch): The Elasticsearch client.
        index_name (str): The name of the index to search.
        query (str): The search query string.
        field_weights (dict): A dictionary mapping field names to their importance weights.

    Returns:
        dict: Elasticsearch search response.
    """
    # Construct a list of "match" clauses for each field based on field_weights
    should_clauses = []
    functions = []

    for field_name, weight in field_weights.items():
        should_clauses.append({"match": {field_name: query}})
        functions.append({
            "filter": {"match": {field_name: query}},
            "weight": weight
        })

    # Build the query body with "should" clauses and functions
    query_body = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "should": should_clauses
                    }
                },
                "functions": functions,
                "score_mode": "sum",
                "boost_mode": "replace"
            }
        }
    }

    # Perform the enhanced search on the specified index
    return es_client.search(index=index_name, body=query_body)

def search_across_all_document_fields_in_index(es_client, index_name, search_string):
    """     
    In a case where we may not know which particular field to search within, this function
    takes in the search term and then searches across all fields in the documents of the es index
    """
    query = {
        "query": {
            "query_string": {
                "query": search_string,
                "fields": ["*"]
            }
        }
    }

    result = es_client.search(index=index_name, body=query)
    return result["hits"]["hits"]

# """     
# Useful Code Snippets
# """
# es_client = es_utils.initialize_elasticsearch_client()
# is_active = es_utils.is_elasticsearch_client_active(es_client)
# print(is_active)

# index_name_to_delete = "rss_articles"
# el_utils.create_index_without_mappings(es_client, index_name)

# index_name_to_delete = "rss_articles"
# el_utils.delete_index(es_client, index_name_to_delete)

# el_utils.list_indices(es_client)

# ## Searching
# # Example usage
# search_term = 'music'
# search_results = search_all_fields(es_client, index_name, search_term)

# # Display search results
# print(f"Search Results for '{search_term}':")
# for hit in search_results:
#     print(hit['_source'])
#     print(hit['_score'])
#     print(f"Content ID: {hit['_source']['content_id']}, Type: {hit['_source']['content_type']}, Categories: {hit['_source']['content_categories']}")
#     print()