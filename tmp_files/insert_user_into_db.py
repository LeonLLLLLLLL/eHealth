from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["image_upload_db"]  # Replace with your database name

# Define the new collection
collection = db["U´sers"]  # Replace with your collection name

# Example document
user_document = {
    "_id": "64b64c7e0d7d9e0001d0c7d1",
    "username": "mike",
    "email": "mike@example.com",
    "password": "test123",
    "roles": ["pathologist"],
    "last_login": datetime(2024, 11, 14, 10, 0, 0),
    "created_at": datetime(2024, 1, 1, 12, 0, 0)
}

# Insert the document into the collection
result = collection.insert_one(user_document)

print(f"Inserted document with ID: {result.inserted_id}")
