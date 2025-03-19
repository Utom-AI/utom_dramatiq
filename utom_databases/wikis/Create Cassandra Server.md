# cassandra Setup on Hetzner Server with Remote Access using cassandra-driver python library

This guide will walk you through the process of setting up an cassandra instance on a Hetzner cloud server and accessing it remotely from a separate computer using the cassandra-driver library for Python.

## Prerequisites
1. **Hetzner Cloud Server**: You should have a Hetzner cloud server instance up and running. You can follow this wiki [Create hetzner Server](https://github.com/UTOM/UTOM_WIKIS/blob/main/Hetzner%20Wikis/Create%20New%20Server.md).

2. **Python and cassandra**: You need Python installed on your local computer and the cassandra library for Python. You can install cassandra using pip:

```bash
pip install cassandra
```

# High Level Steps 
We are using cloud-init config to setup the server via a single config file, but here I will list out all the steps

## Step 1: Install Docker on your server
You can check out this wiki [Install docker on ARM64 server](https://github.com/UTOM/UTOM_WIKIS/blob/main/Docker/Installing%20Docker%20on%20ARM%20Server.md) for more in depth understanding of how its done. 

## Step 3: Create YAML file for docker compose to create cassandra server
Create a YAML file for docker-compose and ensure that you replace the 'volumes' part with your desired path for where the mongo data is stored. An example yaml file is below:
```bash
    version: '3'
    services:
      cassandra:
        image: cassandra:latest
        container_name: utom-cassandra-server
        restart: always
        ports:
          - "9042:9042"
        volumes:
          - cassandra-data:/var/lib/cassandra

    volumes:
      cassandra-data:
```

## Step 4: Create exec script that will be run each time the server is rebooted to ensure that the docker container is always running.
You would swap 'utom-cassandra-server' for the assigned name of your server
```bash
ExecStart=/usr/bin/docker start -a utom-cassandra-server
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
      ExecStart=/usr/bin/docker start -a utom-cassandra-server
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target
  
  - path: /root/docker-compose.yaml
    content: |
      version: '3'
      services:
        cassandra:
          image: cassandra:latest
          container_name: utom-cassandra-server
          restart: always
          ports:
            - "9042:9042"
          volumes:
            - cassandra-data:/var/lib/cassandra

      volumes:
        cassandra-data:

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

