from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['image_upload_db']  # Connect to the database
fs = GridFS(db)  # Create a GridFS instance

def retrieve_image(file_id, output_path):
    try:
        # Retrieve the file from GridFS
        file_data = fs.get(ObjectId(file_id))
        with open(output_path, "wb") as file:
            file.write(file_data.read())
        print(f"Image successfully retrieved and saved to {output_path}")
    except Exception as e:
        print(f"Error retrieving image: {e}")

if __name__ == "__main__":
    # Replace with the file ID of the uploaded image
    file_id = "6737373c23ec4eb6e0c21021"  # Example: "64b51c46dce64b6a7f0a2d9f6"
    output_path = "./retrieved_test.jpg"  # File path where the retrieved image will be saved
    retrieve_image(file_id, output_path)
