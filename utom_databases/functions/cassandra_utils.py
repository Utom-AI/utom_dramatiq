"""    
These are utility functions related to getting a cassandra env up and running
"""
import os
from cassandra.cluster import Cluster

"""
ENVS to add

cassandra_server_public_ip_address = os.environ.get('cassandra_server_public_ip_address')

"""
def create_cassandra_session_connection():
    """
    This function creates a cassandra session connection (however note that it isnt connected to any keyspaces)

    Parameters:
    - contact_points: List of Cassandra node addresses e.g ['65.108.247.177']

    Returns:
    - None
    """
    try:
        cassandra_server_public_ip_address = os.environ.get('cassandra_server_public_ip_address')
        # print('server public address: %s' % cassandra_server_public_ip_address)
        contact_points = [cassandra_server_public_ip_address]
        cluster = Cluster(contact_points)
        cassandra_session = cluster.connect()

        # print("Successfully connected to the Cassandra cluster!")

    except Exception as e:
        print(f"Error connecting to the Cassandra cluster: {e}")
        cassandra_session = None

    return cassandra_session

def test_cassandra_connection(contact_points):
    """
    Test connection to a Cassandra cluster.

    Parameters:
    - contact_points: List of Cassandra node addresses e.g ['65.108.247.177']

    Returns:
    - None
    """
    try:
        cluster = Cluster(contact_points)
        session = cluster.connect()

        print("Successfully connected to the Cassandra cluster!")

        # Close the session and cluster connection
        session.shutdown()
        cluster.shutdown()

    except Exception as e:
        print(f"Error connecting to the Cassandra cluster: {e}")


def create_keyspace(session, keyspace_name):
    """
    Create a keyspace in Cassandra.

    Parameters:
    - cluster: Cassandra cluster object.
    - keyspace_name: Name of the keyspace to be created.

    Returns:
    - None
    """  
    # Define the replication strategy and factor
    replication_strategy = "SimpleStrategy"
    replication_factor = 1

    # Create keyspace
    create_keyspace_query = f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace_name}
        WITH replication = {{
            'class': '{replication_strategy}',
            'replication_factor': {replication_factor}
        }};
    """
    
    session.execute(create_keyspace_query)
    
    # Switch to the created keyspace
    session.set_keyspace(keyspace_name)
    
    # Close the session
    session.shutdown()

def create_cassandra_keyspace_session_for_keyspace(keyspace_name):
    """       
    This function takes in the keyspace name and then connects to cassandra and creates a session 
    connection to the input keyspace 
    """
    for i in range(5):
        try:
            cassandra_server_public_ip_address = os.environ.get('cassandra_server_public_ip_address')
            cluster = Cluster([cassandra_server_public_ip_address])
            cassandra_keyspace_session = cluster.connect(keyspace_name)
        except Exception as e:
            print('Unable to create cassandra session')
            print(e)
            cassandra_keyspace_session = None
        
        if cassandra_keyspace_session is not None:
            break

    return cassandra_keyspace_session

def get_available_keyspaces(contact_points):
    """
    Get the list of available keyspaces in a Cassandra cluster.

    Parameters:
    - contact_points: List of Cassandra node addresses e.g ['65.108.247.177']

    Returns:
    - List of keyspace names.
    """
    try:
        cluster = Cluster(contact_points)
        session = cluster.connect()

        # Query to get available keyspaces
        query = "SELECT keyspace_name FROM system_schema.keyspaces"
        result = session.execute(query)

        # Extract keyspace names from the result
        keyspaces = [row.keyspace_name for row in result]

        # Print the available keyspaces
        print("Available keyspaces:")
        for keyspace in keyspaces:
            print(f"- {keyspace}")

        return keyspaces

    except Exception as e:
        print(f"Error getting available keyspaces: {e}")
        return []

    finally:
        # Close the session and cluster connection
        session.shutdown()
        cluster.shutdown()

def get_list_of_keyspace_table_names(session, keyspace_name):
    """     
    In this case we have initiated a cassandra session with a key
    """
    rows = session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", (keyspace_name,))
    table_name_list = [row.table_name for row in rows]
    return table_name_list

def get_total_table_entries(cassandra_keyspace_session, table_name):

    # Prepare and execute the query to get the total number of entries
    query = f"SELECT COUNT(*) FROM {table_name};"
    result = cassandra_keyspace_session.execute(query)

    # Extract the count from the result
    total_entries = result.one()[0]

    return total_entries

def delete_cassandra_table(cassandra_keyspace_session, table_name):
    """Delete the specified Cassandra table if it exists."""
    cassandra_keyspace_session.execute(f"DROP TABLE IF EXISTS {table_name}")








