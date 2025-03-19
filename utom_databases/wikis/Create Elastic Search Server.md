# ElasticSearch Setup on Hetzner Server with Remote Access using elasticsearch python library

This guide will walk you through the process of setting up an ElasticSearch instance on a Hetzner cloud server and accessing it remotely from a separate computer using the elasticsearch library for Python.

## Prerequisites
1. **Hetzner Cloud Server**: You should have a Hetzner cloud server instance up and running. You can follow this wiki [Create hetzner Server](https://github.com/utom-AI/utom_WIKIS/blob/main/Hetzner%20Wikis/Create%20New%20Server.md).

2. **Python and elasticsearch**: You need Python installed on your local computer and the elasticsearch library for Python. You can install elasticsearch using pip:

```bash
pip install elasticsearch
```

# High Level Steps 
We are using cloud-init config to setup the server via a single config file, but here I will list out all the steps

## Step 1: Install Docker on your server
You can check out this wiki [Install docker on ARM64 server](https://github.com/utom-AI/utom_WIKIS/blob/main/Docker/Installing%20Docker%20on%20ARM%20Server.md) for more in depth understanding of how its done. 

## Step 2: Create a mongo data folder
Create a folder where the elasticsearch data gets persisted to, for example we create a folder called 'esdata' in the path '/root/esdata'
```bash
mkdir /root/esdata
```

## Step 3: Create YAML file for docker compose to create mongo server
Create a YAML file for docker-compose and ensure that you replace the 'volumes' part with your desired path for where the mongo data is stored. An example yaml file is below:
```bash
  version: '3'
  services:
    elasticsearch:
      image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
      container_name: driptok-elastic-search-server
      restart: always
      ports:
        - 9200:9200
      environment:
        - discovery.type=single-node
        - "ES_JAVA_OPTS=-Xms512m -Xmx5g"
        - "xpack.security.enabled=true"
        - "xpack.security.authc.basic.enabled=true"
      volumes:
        - esdata:/usr/share/elasticsearch/data
      command: >
        bash -c '
        /usr/share/elasticsearch/bin/elasticsearch-users useradd my_user -p my_password -r superuser;
        /usr/local/bin/docker-entrypoint.sh'
  volumes:
    esdata:
```

## Step 4: Create exec script that will be run each time the server is rebooted to ensure that the docker container is always running.
You would swap 'utom-mongo-server' for the assigned name of your server
```bash
ExecStart=/usr/bin/docker start -a utom-elastic-search-server
```


# cloud-init Configuration
cloud-init is a framework that allows you to upload a script that gets started when a server is deployed. Below is the configuration script used to create a Mongo sever on a new server

## Creating the cloud-init file
``` bash
#cloud-config

# Here we have files that we want created at the startup of the server
write_files:
  # This creates a file with the exec script to fire up the Elasticsearch server upon rebooting of the server
  - path: /etc/systemd/system/docker-startup.service
    content: |
      [Unit]
      Description=Start Docker Containers on Boot

      [Service]
      Type=oneshot
      ExecStart=/usr/bin/docker start -a driptok-elastic-search-server
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target
  
  # This creates the Docker Compose file for firing up the server
  - path: /root/docker-compose.yaml
    content: |
      version: '3'
      services:
        elasticsearch:
            image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
            container_name: driptok-elastic-search-server
            restart: always
            ports:
            - 9200:9200
            environment:
              - discovery.type=single-node
              # Enable X-Pack security and set the username and password - what we have here is the staging password
              - xpack.security.enabled=true
              - ELASTIC_PASSWORD=driptok_staging_2024 
            volumes:
            - esdata:/usr/share/elasticsearch/data

      volumes:
        esdata:

package_update: true
packages:
  - curl

runcmd:
  # Install Docker
  - curl -fsSL https://get.docker.com -o get-docker.sh
  - sh get-docker.sh
  - systemctl start docker
  - systemctl enable docker
  - docker --version

  # Installing Docker Compose
  - curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  - chmod +x /usr/local/bin/docker-compose
  - docker-compose --version

  # Start the Elasticsearch container
  - docker-compose -f /root/docker-compose.yaml up -d

  # Restart the server after all the configuration is done
  - reboot
```

# Final
## Check that everything was installed as expected on your server
1. After waiting for about 10 minutes, the process should be done. Use SSH to access your Hetzner cloud server. Replace your_server_ip with your server's IP address:
```bash
ssh root@your_server_ip
```

2. Check the status of the cloud-init process
```bash
sudo cloud-init status
```

3. Check that the docker compose file and mongo_data folder were created (do this on the root folder)
```bash
ls 
```

3. Check that the docker container is running
```bash
docker ps
```

## Testing: Connect to elasticsearch from a local Computer Using elasticsearch python library
Now, you can connect to your elasticsearch server from a separate computer using the elasticsearch library for Python. Below a Python script to connect to elasticsearch and perform basic operations:
```python
from elasticsearch import Elasticsearch

def get_all_index_names(elasticsearch_host):
    """
    Get a list of all index names in the Elasticsearch cluster.

    Args:
        elasticsearch_host (str): The Elasticsearch cluster's hostname or IP address.

    Returns:
        list: A list of index names.
    """
    # Create an Elasticsearch client
    es = Elasticsearch([elasticsearch_host])

    # Use the cat.indices API to get a list of all indices
    indices_info = es.cat.indices(format="json")

    # Extract index names from the response
    index_names = [index["index"] for index in indices_info]

    return index_names

# Example usage:
elasticsearch_host = "http://<Your Host IP Address>:9200"  # Replace with your Elasticsearch cluster's host
index_names = get_all_index_names(elasticsearch_host)
print("Index Names:", index_names)
```

* Run this Python script on your local computer. It should connect to your Hetzner elasticsearch server and perform the specified operations.

That's it! You've successfully created a elasticsearch instance on your Hetzner server, configured it for remote access, and connected to it from a separate computer using elasticsearch. You can now read and write data to your elasticsearch instance from anywhere with internet access.


# To Do
* Work on functionality for logging performance of the elasticsearch and also monitoring.
* Work on automated backups of the server data to long term storage like AWS, or another server.
* Work on a pipeline to upgrade the server where you move the data onto a bigger server... its very critical that you are able to do this without affecting the app performance... a way to approach this is for all services to have their own DB, so that there's minimized wahala when you want to upgrade a particular server... plus this will actually make the app a lot faster... food for thought.