# RabbitMQ Setup on Hetzner Server with Remote Access using pika

This guide will walk you through the process of setting up a RabbitMQ instance on a Hetzner cloud server and accessing it remotely from a separate computer using the pika library for Python.

## Prerequisites
1. **Hetzner Cloud Server**: You should have a Hetzner cloud server instance up and running. You can follow this wiki [Create hetzner Server](https://github.com/utom-AI/utom_WIKIS/blob/main/Hetzner%20Wikis/Create%20New%20Server.md).

2. **Python and pika**: You need Python installed on your local computer and the pika library for Python. You can install pika using pip:

```bash
pip install pika
```

# High Level Steps 
We are using cloud-init config to setup the server via a single config file, but here I will list out all the steps

## Step 1: Install Docker on your server
You can check out this wiki [Install docker on ARM64 server](https://github.com/utom-AI/utom_WIKIS/blob/main/Docker/Installing%20Docker%20on%20ARM%20Server.md) for more in depth understanding of how its done. 

## Step 2: Create a RabbitMQ data folder
Create a folder where the rabbitmq data gets persisted to, for example we create a folder called 'rabbitmqdata' in the path '/root/rabbitmqdata'
```bash
mkdir /root/rabbitmqdata
```

## Step 3: Create YAML file for docker compose to create RabbitMQ server
Create a YAML file for docker-compose and ensure that you replace the 'volumes' part with your desired path for where the rabbitmq data is stored. An example yaml file is below:
```bash
  version: '3'
  services:
    rabbitmq:
        image: rabbitmq:3-management
        container_name: utom-rabbitmq-server
        restart: always
        ports:
          - 5672:5672
          - 15672:15672
        environment:
          RABBITMQ_DEFAULT_USER: guest  # Use the default guest user
          RABBITMQ_DEFAULT_PASS: guest  # Use the default guest password
          RABBITMQ_DEFAULT_VHOST: /
        volumes:
          - rabbitmqdata:/var/lib/rabbitmq

  volumes:
    rabbitmqdata:
```

## Step 4: Create exec script that will be run each time the server is rebooted to ensure that the docker container is always running.
You would swap 'utom-rabbitmq-server' for the assigned name of your docker container
```bash
ExecStart=/usr/bin/docker start -a utom-rabbitmq-server
```
# cloud-init Configuration
cloud-init is a framework that allows you to upload a script that gets started when a server is deployed. Below is the configuration script used to create a Mongo sever on a new server

## Creating the cloud-init file
```bash
#cloud-config

write_files:
  - path: /etc/systemd/system/docker-startup.service
    content: |
      [Unit]
      Description=Start Docker Containers on Boot

      [Service]
      Type=oneshot
      ExecStart=/usr/bin/docker start -a utom-rabbitmq-server
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target

  - path: /root/docker-compose.yaml
    content: |
      version: '3'
      services:
        rabbitmq:
            image: rabbitmq:3-management
            container_name: utom-rabbitmq-server
            restart: always
            ports:
              - 5672:5672
              - 15672:15672
            environment:
              RABBITMQ_DEFAULT_USER: utom  # Use the default guest user
              RABBITMQ_DEFAULT_PASS: utom2024  # Use the default guest password
              RABBITMQ_DEFAULT_VHOST: /
            volumes:
              - rabbitmqdata:/var/lib/rabbitmq

      volumes:
        rabbitmqdata:

package_update: true
packages:
  - curl

runcmd:
  - curl -fsSL https://get.docker.com -o get-docker.sh
  - sh get-docker.sh
  - systemctl start docker
  - systemctl enable docker

  - curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  - chmod +x /usr/local/bin/docker-compose

  - docker-compose -f /root/docker-compose.yaml up -d

  - systemctl enable docker-startup

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

3. Check that the docker container is running
```bash
docker ps
```

## Testing: Connect to RabbitMQ server from a local Computer Using pika
Now, you can connect to your RabbitMQ server from a separate computer using the pika library for Python. 

That's it! You've successfully created a RabbitMQ instance on your Hetzner server, configured it for remote access, and connected to it from a separate computer using pika. You can now read and write data to your RabbitMQ instance from anywhere with internet access.


# To Do
* Work on implementing the dramatiq app to use rabbitMQ instead of Redis