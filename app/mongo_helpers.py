import os
from dotenv import load_dotenv
load_dotenv()

MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')

from pymongo import MongoClient

from bson import ObjectId

def serialize_mongo_data(data):
    """
    Recursively convert MongoDB data to a JSON-serializable format.
    """
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, list):
        return [serialize_mongo_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_mongo_data(value) for key, value in data.items()}
    return data

class MongoDBHelper:
    def __init__(self, uri=MONGODB_CONNECTION_STRING, db_name="myDatabase"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def execute_user_query(self, query):
        """
        Execute a MongoDB query provided as a dictionary.
        """
        collection_name = query.get("collection")
        operation = query.get("operation")
        parameters = query.get("parameters", {})

        if not collection_name or not operation:
            raise ValueError("Both 'collection' and 'operation' must be provided.")

        collection = self.db[collection_name]


        # print(f"er")
        # Safely execute based on operation
        if operation == "find":
            result = collection.find(parameters.get("filter", {}))
            return serialize_mongo_data(list(result))  # Serialize data
        elif operation == "aggregate":
            result = collection.aggregate(parameters.get("pipeline", []))
            return serialize_mongo_data(list(result))  # Serialize data
        elif operation == "insert":
            result = collection.insert_many(parameters.get("documents", []))
            return serialize_mongo_data(result.inserted_ids)  # Serialize IDs
        elif operation == "update":
            result = collection.update_many(
                parameters.get("filter", {}),
                parameters.get("update", {})
            )
            return result.modified_count  # Count is JSON serializable
        elif operation == "delete":
            result = collection.delete_many(parameters.get("filter", {}))
            return result.deleted_count  # Count is JSON serializable
        else:
            raise ValueError(f"Unsupported operation: {operation}")
