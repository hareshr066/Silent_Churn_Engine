"""
SilentChurn AI - MongoDB Database Layer
This module manages connection, configuration, initialization, and interactions
with MongoDB Atlas. It reads connection configuration from environment variables.
Includes a transparent local JSON database fallback if Atlas connection is unavailable.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=dotenv_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "silentchurn_db"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- Local JSON Mock Database Classes ---

class MockCursor:
    """Mock MongoDB cursor supporting sorting, limits, and iteration."""
    def __init__(self, data):
        self.data = data
        
    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            key, dir_val = key_or_list[0]
            reverse = (dir_val == -1)
        else:
            key = key_or_list
            reverse = (direction == -1)
            
        try:
            # Sort with secondary sorting on ID if keys are equal
            self.data.sort(key=lambda x: (x.get(key) is None, x.get(key, "")), reverse=reverse)
        except Exception as e:
            logger.debug(f"Mock sorting error: {e}")
        return self
        
    def limit(self, count):
        self.data = self.data[:count]
        return self
        
    def __iter__(self):
        return iter(self.data)
        
    def __getitem__(self, index):
        return self.data[index]
        
    def __len__(self):
        return len(self.data)

class MockCollection:
    """Mock MongoDB collection storing documents in a local JSON file."""
    def __init__(self, db_path, name):
        self.name = name
        self.file_path = os.path.join(db_path, f"{name}.json")
        os.makedirs(db_path, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)
                
    def _read(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
            
    def _write(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, default=str, indent=2)
            
    def insert_one(self, doc):
        data = self._read()
        import uuid
        doc_copy = doc.copy()
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(uuid.uuid4())
        # Convert datetimes to strings
        for k, v in doc_copy.items():
            if isinstance(v, datetime):
                doc_copy[k] = v.isoformat()
        data.append(doc_copy)
        self._write(data)
        return type('InsertOneResult', (), {'inserted_id': doc_copy["_id"]})
        
    def insert_many(self, docs):
        data = self._read()
        inserted_ids = []
        import uuid
        for doc in docs:
            doc_copy = doc.copy()
            if "_id" not in doc_copy:
                doc_copy["_id"] = str(uuid.uuid4())
            for k, v in doc_copy.items():
                if isinstance(v, datetime):
                    doc_copy[k] = v.isoformat()
            data.append(doc_copy)
            inserted_ids.append(doc_copy["_id"])
        self._write(data)
        return type('InsertManyResult', (), {'inserted_ids': inserted_ids})
        
    def delete_many(self, filter_query=None):
        if not filter_query:
            self._write([])
            return type('DeleteResult', (), {'deleted_count': 0})
        
        data = self._read()
        filtered = []
        deleted = 0
        for d in data:
            match = True
            for k, v in filter_query.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                deleted += 1
            else:
                filtered.append(d)
        self._write(filtered)
        return type('DeleteResult', (), {'deleted_count': deleted})
        
    def find(self, filter_query=None, projection=None):
        data = self._read()
        if not filter_query:
            return MockCursor(data)
            
        filtered = []
        for d in data:
            match = True
            for k, v in filter_query.items():
                # Simple dictionary attribute matching
                if d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return MockCursor(filtered)
        
    def find_one(self, filter_query=None):
        res = self.find(filter_query)
        if len(res.data) > 0:
            return res.data[0]
        return None
        
    def count_documents(self, filter_query=None):
        return len(self.find(filter_query).data)
        
    def create_index(self, keys, **kwargs):
        pass

class MockDatabase:
    """Mock MongoDB database containing local collections."""
    def __init__(self, db_path):
        self.db_path = db_path
        
    def list_collection_names(self):
        if not os.path.exists(self.db_path):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.db_path) if f.endswith(".json")]
        
    def create_collection(self, name):
        file_path = os.path.join(self.db_path, f"{name}.json")
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump([], f)
                
    def __getitem__(self, name):
        return MockCollection(self.db_path, name)

# --- Primary Connection Manager ---

class MongoDBManager:
    """Manages connection to MongoDB Atlas, falling back to local files on failure."""
    def __init__(self):
        self.client = None
        self.db = None
        self.is_fallback = False
        
    def connect(self):
        self.is_fallback = False
        if not MONGODB_URI:
            logger.warning("MONGODB_URI is empty. Falling back to local JSON database.")
            self.db = MockDatabase(os.path.join(BASE_DIR, "datasets", "mock_db"))
            self.is_fallback = True
            return
            
        try:
            logger.info("Connecting to MongoDB Atlas...")
            # Configure short timeout (2s) for fast response during local network checks
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000, tlsAllowInvalidCertificates=True)
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            logger.info(f"Connected to MongoDB database: '{DB_NAME}' successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB Atlas ({e}). Falling back to local JSON database.")
            self.client = None
            self.db = MockDatabase(os.path.join(BASE_DIR, "datasets", "mock_db"))
            self.is_fallback = True
            
    def get_database(self):
        if self.db is None:
            self.connect()
        return self.db
        
    def get_collection(self, collection_name: str):
        db = self.get_database()
        return db[collection_name]
        
    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB client connection closed.")
            self.client = None
            self.db = None

# Global manager instance
db_manager = MongoDBManager()

def init_db():
    try:
        db = db_manager.get_database()
        existing_collections = db.list_collection_names()
        logger.info(f"Existing collections: {existing_collections}")
        
        required_collections = ["raw_dataset", "cleaned_dataset", "model_metrics", "predictions", "recommendations"]
        for col_name in required_collections:
            if col_name not in existing_collections:
                db.create_collection(col_name)
                logger.info(f"Created collection: {col_name}")
                
        logger.info("Database collections initialized.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    init_db()
