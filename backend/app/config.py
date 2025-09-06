import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from google.cloud import firestore, storage, pubsub_v1
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    # GCP Configuration
    google_cloud_project: str = Field(default="playgroundai-470111", env="GOOGLE_CLOUD_PROJECT")
    
    # Service Configuration
    port: int = Field(default=8080, env="PORT")
    node_env: str = Field(default="production", env="NODE_ENV")
    
    # GCP Resource Names
    firestore_database_id: str = Field(default="(default)", env="FIRESTORE_DATABASE_ID")
    gcs_bucket_name: str = Field(default="playgroundai-470111-data", env="GCS_BUCKET_NAME")
    pubsub_topic_name: str = Field(default="train-jobs", env="PUBSUB_TOPIC_NAME")
    
    # Performance optimizations
    firestore_batch_size: int = Field(default=500, env="FIRESTORE_BATCH_SIZE")
    gcs_chunk_size: int = Field(default=8 * 1024 * 1024, env="GCS_CHUNK_SIZE")  # 8MB chunks
    
    # CORS Configuration
    cors_origin: str = Field(default="https://playground.theneural.in", env="CORS_ORIGIN")
    
    # Security
    jwt_secret: str = Field(default="your-super-secret-jwt-key-here", env="JWT_SECRET")
    
    class Config:
        env_file = ".env"


# Initialize settings
settings = Settings()


class GCPClients:
    """GCP client initialization using Application Default Credentials"""
    
    def __init__(self):
        self.project_id = settings.google_cloud_project
        
        # Initialize Firestore client
        self.firestore_client = firestore.Client(project=self.project_id)
        self.projects_collection = self.firestore_client.collection('projects')
        
        # Initialize Storage client
        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self.storage_client.bucket(settings.gcs_bucket_name)
        
        # Initialize Pub/Sub clients
        self.pubsub_client = pubsub_v1.PublisherClient()
        self.subscriber_client = pubsub_v1.SubscriberClient()  # Added SubscriberClient
        self.topic_path = self.pubsub_client.topic_path(
            self.project_id, 
            settings.pubsub_topic_name
        )
    
    def get_firestore_client(self):
        return self.firestore_client
    
    def get_storage_client(self):
        return self.storage_client
    
    def get_pubsub_client(self):
        return self.pubsub_client
    
    def get_subscriber_client(self):  # Added method
        return self.subscriber_client
    
    def get_projects_collection(self):
        return self.projects_collection
    
    def get_bucket(self):
        return self.bucket
    
    def get_topic_path(self):
        return self.topic_path
    
    def get_project_id(self):
        return self.project_id
    
    def get_topic_name(self):
        return settings.pubsub_topic_name
    
    def get_subscription_path(self):
        return self.subscriber_client.subscription_path(
            self.project_id, 
            "trainer-sub"
        )


# Global GCP clients instance
gcp_clients = GCPClients()
