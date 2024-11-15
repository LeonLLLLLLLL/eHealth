from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId
import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['image_upload_db']  # Use the database
fs = GridFS(db)  # GridFS instance for image storage

# Function to upload an image
def upload_image(file_path):
    with open(file_path, "rb") as file:
        file_id = fs.put(file, filename=file_path.split("/")[-1])  # Store file with its name
    print(f"Image uploaded with ID: {file_id}")
    return file_id

# Function to create a case
def create_case(case_name, description, image_ids):
    case_data = {
        "caseName": case_name,
        "description": description,
        "imageIds": [ObjectId(image_id) for image_id in image_ids],  # List of image IDs
        "createdAt": datetime.datetime.utcnow()
    }
    result = db.Cases.insert_one(case_data)
    print(f"Case created with ID: {result.inserted_id}")
    return result.inserted_id

# Function to retrieve and print case details
def get_case_with_images(case_id):
    try:
        # Retrieve the case
        case = db.Cases.find_one({"_id": ObjectId(case_id)})
        if not case:
            print("Case not found!")
            return

        print(f"Case: {case['caseName']}")
        print(f"Description: {case['description']}")
        print("Images:")

        # Retrieve and display associated images
        for image_id in case["imageIds"]:
            image_file = fs.get(image_id)
            print(f"- {image_file.filename} (ID: {image_id})")

    except Exception as e:
        print(f"Error retrieving case: {e}")

if __name__ == "__main__":
    # Test data: Upload images for Case 1
    image_path1 = "./test.jpg"  # Replace with actual image path
    image_path2 = "./test.jpg"  # Replace with actual image path
    image_id1 = upload_image(image_path1)
    image_id2 = upload_image(image_path2)

    # Create Case 1
    case_name1 = "Case 1"
    description1 = "This is the first test case with two images."
    case_id1 = create_case(case_name1, description1, [image_id1, image_id2])

    # Test data: Upload images for Case 2
    image_path3 = "./test.jpg"  # Replace with actual image path
    image_path4 = "./test.jpg"  # Replace with actual image path
    image_id3 = upload_image(image_path3)
    image_id4 = upload_image(image_path4)

    # Create Case 2
    case_name2 = "Case 2"
    description2 = "This is the second test case with two images."
    case_id2 = create_case(case_name2, description2, [image_id3, image_id4])

    # Retrieve and print Case 1 details
    print("\nDetails for Case 1:")
    get_case_with_images(case_id1)

    # Retrieve and print Case 2 details
    print("\nDetails for Case 2:")
    get_case_with_images(case_id2)
