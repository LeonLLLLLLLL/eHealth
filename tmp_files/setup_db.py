from pymongo import MongoClient

# Connect to MongoDB server
client = MongoClient('mongodb://localhost:27017')

# Create or connect to the database 'test'
db = client['test']

# Function to create a collection with a validation schema
def create_collection_with_schema(collection_name, schema):
    db.create_collection(collection_name)
    db.command("collMod", collection_name, validator={"$jsonSchema": schema})
    print(f"Created collection '{collection_name}' with schema validation.")

# Define validation schemas for the collections
schemas = {
    "Users": {
        "bsonType": "object",
        "required": ["username", "passwordHash", "email", "role"],
        "properties": {
            "username": {"bsonType": "string"},
            "passwordHash": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "role": {"enum": ["Pathologist", "Patient"]},
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"}
        }
    },
    "Images": {
        "bsonType": "object",
        "required": ["uploadedBy", "filePath", "metadata"],
        "properties": {
            "uploadedBy": {"bsonType": "objectId"},
            "filePath": {"bsonType": "string"},
            "metadata": {
                "bsonType": "object",
                "properties": {
                    "resolution": {"bsonType": "string"},
                    "fileSize": {"bsonType": "string"},
                    "uploadedAt": {"bsonType": "date"}
                }
            }
        }
    },
    "ObjectDetections": {
        "bsonType": "object",
        "required": ["imageId", "detectedObjects"],
        "properties": {
            "imageId": {"bsonType": "objectId"},
            "detectedObjects": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["objectId", "boundingBox", "confidence"],
                    "properties": {
                        "objectId": {"bsonType": "string"},
                        "boundingBox": {
                            "bsonType": "object",
                            "properties": {
                                "x": {"bsonType": "int"},
                                "y": {"bsonType": "int"},
                                "width": {"bsonType": "int"},
                                "height": {"bsonType": "int"}
                            }
                        },
                        "confidence": {"bsonType": "double"}
                    }
                }
            }
        }
    },
    "Segmentations": {
        "bsonType": "object",
        "required": ["detectionId", "segmentationData"],
        "properties": {
            "detectionId": {"bsonType": "objectId"},
            "segmentationData": {
                "bsonType": "object",
                "additionalProperties": True
            },
            "createdAt": {"bsonType": "date"}
        }
    },
    "Grids": {
        "bsonType": "object",
        "required": ["segmentationId", "gridProperties"],
        "properties": {
            "segmentationId": {"bsonType": "objectId"},
            "gridProperties": {
                "bsonType": "object",
                "additionalProperties": True
            },
            "createdAt": {"bsonType": "date"}
        }
    },
    "Reports": {
        "bsonType": "object",
        "required": ["authorId", "gridId", "findings"],
        "properties": {
            "authorId": {"bsonType": "objectId"},
            "gridId": {"bsonType": "objectId"},
            "findings": {"bsonType": "string"},
            "createdAt": {"bsonType": "date"}
        }
    },
    "AccessLogs": {
        "bsonType": "object",
        "required": ["userId", "action", "timestamp"],
        "properties": {
            "userId": {"bsonType": "objectId"},
            "action": {"bsonType": "string"},
            "timestamp": {"bsonType": "date"}
        }
    },
    "AuditTrails": {
        "bsonType": "object",
        "required": ["action", "details", "performedAt"],
        "properties": {
            "action": {"bsonType": "string"},
            "details": {"bsonType": "object"},
            "performedAt": {"bsonType": "date"}
        }
    }
}

# Create collections with schemas
for collection_name, schema in schemas.items():
    try:
        create_collection_with_schema(collection_name, schema)
    except Exception as e:
        print(f"Collection '{collection_name}' already exists or an error occurred: {e}")

print("Database setup complete!")
