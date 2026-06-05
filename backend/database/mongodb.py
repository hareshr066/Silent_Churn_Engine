"""
SilentChurn AI - MongoDB Database Layer
This module manages connection, configuration, initialization, and interactions
with MongoDB Atlas. It reads connection configuration from environment variables.
"""

import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
# Search in root directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=dotenv_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "silentchurn_db"

class MongoDBManager:
    """Manages the lifecycle of the MongoDB client connection and provides database collections."""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        """Establishes connection to MongoDB Atlas and verifies it via a ping."""
        if not MONGODB_URI:
            logger.error("MONGODB_URI is not set in environment variables. Check .env file.")
            raise ValueError("MONGODB_URI environment variable is missing.")
            
        try:
            logger.info("Connecting to MongoDB Atlas...")
            # Set a 5 second server selection timeout
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Trigger a ping to confirm connection
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            logger.info(f"Connected to MongoDB database: '{DB_NAME}' successfully.")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB Atlas: {e}", exc_info=True)
            self.client = None
            self.db = None
            raise e
            
    def get_database(self):
        """Returns the database instance, connecting if not already established."""
        if self.db is None:
            self.connect()
        return self.db
        
    def get_collection(self, collection_name: str):
        """Returns a collection reference."""
        db = self.get_database()
        return db[collection_name]
        
    def close(self):
        """Closes the current database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB client connection closed.")
            self.client = None
            self.db = None

# Global instance for project-wide import and reuse
db_manager = MongoDBManager()

def init_db():
    """Verifies connection and creates collections with indexing if they do not exist."""
    try:
        db = db_manager.get_database()
        existing_collections = db.list_collection_names()
        logger.info(f"Existing collections: {existing_collections}")
        
        required_collections = ["raw_dataset", "cleaned_dataset", "model_metrics", "predictions", "recommendations"]
        
        for col_name in required_collections:
            if col_name not in existing_collections:
                db.create_collection(col_name)
                logger.info(f"Created collection: {col_name}")
            else:
                logger.info(f"Collection '{col_name}' already exists.")
                
            # Create indexes for optimized queries
            col = db[col_name]
            if col_name in ["predictions", "recommendations"]:
                col.create_index([("user_id", 1)])
                col.create_index([("created_at", -1)])
            elif col_name == "model_metrics":
                col.create_index([("created_at", -1)])
                col.create_index([("model_name", 1)])
                
        logger.info("MongoDB SilentChurn collections and indices initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    # Test connection and initialize
    print("Testing connection string and initializing database...")
    init_db()
