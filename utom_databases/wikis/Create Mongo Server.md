# MongoDB Setup on Hetzner Server with Remote Access using PyMongo

This guide will walk you through the process of setting up a MongoDB instance on a Hetzner cloud server and accessing it remotely from a separate computer using the PyMongo library for Python.

## Prerequisites
1. **Hetzner Cloud Server**: You should have a Hetzner cloud server instance up and running. You can follow this wiki [Create hetzner Server](https://github.com/utom-AI/utom_WIKIS/blob/main/Hetzner%20Wikis/Create%20New%20Server.md).

2. **Python and PyMongo**: You need Python installed on your local computer and the PyMongo library for Python. You can install PyMongo using pip:

```bash
pip install pymongo
```

# High Level Steps 
We are using cloud-init config to setup the server via a single config file, but here I will list out all the steps

## Step 1: Install Docker on your server
You can check out this wiki [Install docker on ARM64 server](https://github.com/utom-AI/utom_WIKIS/blob/main/Docker/Installing%20Docker%20on%20ARM%20Server.md) for more in depth understanding of how its done. 

## Step 2: Create a mongo data folder
Create a folder where the mongo data gets persisted to, for example we create a folder called 'mongo_data' in the path '/root/mongo_data'
```bash
mkdir /root/mongo_data
```

## Step 3: Create YAML file for docker compose to create mongo server
Create a YAML file for docker-compose and ensure that you replace the 'volumes' part with your desired path for where the mongo data is stored. An example yaml file is below:
```bash
version: '3'

services:
  mongodb:
    image: mongo
    container_name: utom-mongo-server
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - /mongo_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin
      MONGO_INITDB_DATABASE: admin
    networks:
      - utom-mongo-server-network

networks:
  utom-mongo-server-network:
    driver: bridge

volumes:
  mongodb-data:  # Define a named volume for MongoDB data
```

## Step 4: Create exec script that will be run each time the server is rebooted to ensure that the docker container is always running.
You would swap 'utom-mongo-server' for the assigned name of your server
```bash
ExecStart=/usr/bin/docker start -a utom-mongo-server
```


# cloud-init Configuration
cloud-init is a framework that allows you to upload a script that gets started when a server is deployed. Below is the configuration script used to create a Mongo sever on a new server

## Creating the cloud-init file
``` bash
#cloud-config

write_files:
  - path: /etc/systemd/system/docker-startup.service
    content: |
      [Unit]
      Description=Start Docker Containers on Boot

      [Service]
      Type=oneshot
      ExecStart=/usr/bin/docker start -a utom-mongo-server
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target

  - path: /root/docker-compose.yaml
    content: |
      version: "3"
      services:
        mongodb:
          image: mongo
          container_name: utom-mongo-server
          restart: always
          ports:
            - "27017:27017"
          volumes:
            - mongodb-data:/data/db  # Use the named volume
          environment:
            MONGO_INITDB_ROOT_USERNAME: utom
            MONGO_INITDB_ROOT_PASSWORD: utom2024
            MONGO_INITDB_DATABASE: admin
          networks:
            - utom-mongo-server-network

      networks:
        utom-mongo-server-network:
          driver: bridge

      volumes:
        mongodb-data:

package_update: true
packages:
  - curl

runcmd:
  - curl -fsSL https://get.docker.com -o get-docker.sh
  - sh get-docker.sh
  - systemctl start docker
  - systemctl enable docker
  - docker --version
  - curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  - chmod +x /usr/local/bin/docker-compose
  - docker-compose --version

  # Create the Docker volume directly
  - docker volume create --name mongodb-data

  # Start the MongoDB container
  - docker-compose -f /root/docker-compose.yaml up -d

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

## Testing: Connect to MongoDB from a local Computer Using PyMongo
Now, you can connect to your MongoDB server from a separate computer using the PyMongo library for Python. Below a Python script to connect to MongoDB and perform basic operations:
```python
import pymongo

# Replace with your MongoDB server's IP address and credentials
mongo_uri = "mongodb://admin_username:admin_password@your_server_ip:27017/"

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)

# Select a database (create one if it doesn't exist)
db = client["your_database_name"]

# Select a collection
collection = db["your_collection_name"]

# Insert a document
data = {"key": "value"}
collection.insert_one(data)

# Find documents
results = collection.find()
for result in results:
    print(result)

# Close the MongoDB connection
client.close()
```

* Replace the placeholders (admin_username, admin_password, your_server_ip, your_database_name, and your_collection_name) with your actual values.
* Run this Python script on your local computer. It should connect to your Hetzner MongoDB server and perform the specified operations.

That's it! You've successfully created a MongoDB instance on your Hetzner server, configured it for remote access, and connected to it from a separate computer using PyMongo. You can now read and write data to your MongoDB instance from anywhere with internet access.


# To Do
* Work on improving the deployment via docker to also include the creation of users.
* Work on functionality for logging performance of the mongo server and also monitoring.
* Work on automated backups of the server data to long term storage like AWS, or another server.
* Work on a pipeline to upgrade the server where you move the data onto a bigger server... its very critical that you are able to do this without affecting the app performance... a way to approach this is for all services to have their own DB, so that there's minimized wahala when you want to upgrade a particular server... plus this will actually make the app a lot faster... food for thought.