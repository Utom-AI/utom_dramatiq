import os
from typing import Dict, Any
from pymongo import MongoClient
import pika

def get_mongodb_client() -> MongoClient:
    """Get MongoDB client using environment variables"""
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return MongoClient(mongo_uri)

def get_rabbitmq_channel():
    """Get RabbitMQ channel using environment variables"""
    credentials = pika.PlainCredentials(
        username=os.getenv("RABBITMQ_USER", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest")
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    return connection.channel() 