import pymongo
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# # Replace the placeholder data with your Atlas connection string. Be sure it includes
# # a valid username and password! Note that in a production environment,
# # you should not store your password in plain-text here.
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')
# class MongoDBHelper:
#     def __init__(self):
#         try:
#             client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
        
#         # return a friendly error if a URI error is thrown 
#         except pymongo.errors.ConfigurationError:
#             print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
#             sys.exit(1)
        
#         # self
#         # use a database named "myDatabase"
#         self.db = client.myDatabase

#     def get_all_collections(self):
#         """
#         Get all collection names and their documents.
#         """
#         try:
#             collections = {}
#             for collection_name in self.db.list_collection_names():
#                 collections[collection_name] = list(self.db[collection_name].find())
#             return collections
#         except Exception as e:
#             print(f"Error fetching collections: {e}")
#             return {"error": str(e)}
    
#     # def execute_user_query(self, query):
#     #     return self.db.command(query)


#     def execute_user_query(self, query):
#         """
#         Process a dynamic MongoDB query string.
#         Query should be in the format:
#         - find: {"action": "find", "collection": "myCollection", "filter": {...}}
#         - insertOne: {"action": "insertOne", "collection": "myCollection", "document": {...}}
#         - updateOne: {"action": "updateOne", "collection": "myCollection", "filter": {...}, "update": {...}}
#         - deleteOne: {"action": "deleteOne", "collection": "myCollection", "filter": {...}}
#         """
#         try:
#             if not isinstance(query, dict):
#                 raise ValueError("Query must be a valid JSON object.")

#             action = query.get("action")
#             collection_name = query.get("collection")
#             if not collection_name or collection_name not in self.db.list_collection_names():
#                 raise ValueError(f"Collection '{collection_name}' does not exist.")

#             collection = self.db[collection_name]

#             if action == "find":
#                 filter_query = query.get("filter", {})
#                 return list(collection.find(filter_query))
            
#             elif action == "insertOne":
#                 document = query.get("document")
#                 if not document:
#                     raise ValueError("Document to insert cannot be empty.")
#                 return collection.insert_one(document).inserted_id
            
#             elif action == "updateOne":
#                 filter_query = query.get("filter", {})
#                 update_data = query.get("update")
#                 if not update_data:
#                     raise ValueError("Update data cannot be empty.")
#                 return collection.update_one(filter_query, {"$set": update_data}).modified_count
            
#             elif action == "deleteOne":
#                 filter_query = query.get("filter", {})
#                 return collection.delete_one(filter_query).deleted_count
            
#             else:
#                 raise ValueError(f"Unsupported action: {action}. Supported actions: find, insertOne, updateOne, deleteOne.")
        
#         except Exception as e:
#             print(f"Error executing query: {e}")
#             return {"error": str(e)}



from pymongo import MongoClient

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

        # Safely execute based on operation
        if operation == "find":
            return list(collection.find(parameters.get("filter", {})))
        elif operation == "aggregate":
            return list(collection.aggregate(parameters.get("pipeline", [])))
        elif operation == "insert":
            return collection.insert_many(parameters.get("documents", [])).inserted_ids
        elif operation == "update":
            return collection.update_many(
                parameters.get("filter", {}),
                parameters.get("update", {}),
            ).modified_count
        elif operation == "delete":
            return collection.delete_many(parameters.get("filter", {})).deleted_count
        else:
            raise ValueError(f"Unsupported operation: {operation}")
