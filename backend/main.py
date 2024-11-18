from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from pydantic import BaseModel, EmailStr
from typing import List

# Initialize FastAPI app
app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["image_upload_db"]  # Replace with your database name
users_collection = db["Users"]  # Replace with your collection name
cases_collection = db["Cases"]  # Replace with your collection name for cases

# Define the Pydantic model for user data
class UserData(BaseModel):
    username: str
    email: EmailStr
    password: str
    roles: List[str] = ["user"]

class LoginData(BaseModel):
    username: str
    password: str

class CaseData(BaseModel):
    caseName: str
    description: str

@app.post("/register")
async def register_user(user_data: UserData):
    # Check if username or email already exists
    if users_collection.find_one({"username": user_data.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password
    hashed_password = hashpw(user_data.password.encode(), gensalt()).decode()

    # Create the user document
    user_document = {
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_password,
        "roles": user_data.roles,
        "created_at": None,
        "last_login": None
    }

    # Insert the user document into the database
    result = users_collection.insert_one(user_document)

    return {"success": True, "message": "User registered successfully", "user_id": str(result.inserted_id)}

@app.post("/login")
async def validate_login(login_data: LoginData):
    # Find the user in the database by username
    user = users_collection.find_one({"username": login_data.username})

    if not user:
        # User not found
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Validate password using bcrypt
    if not checkpw(login_data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "success": True,
        "message": "Login successful",
        "username": user["username"],
        "roles": user["roles"],  # Return roles explicitly
    }

@app.post("/cases")
async def create_case(case_data: CaseData):
    # Prepare the case document with empty imageIds and current creation time
    case_document = {
        "caseName": case_data.caseName,
        "description": case_data.description,
        "imageIds": [],  # Initialize as empty
        "createdAt": datetime.utcnow()
    }

    # Insert the case into the MongoDB collection
    result = cases_collection.insert_one(case_document)

    # Return a success response with the inserted case's ID
    return {
        "success": True,
        "message": "Case created successfully",
        "case_id": str(result.inserted_id)
    }

@app.get("/")
async def root():
    return {"message": "Hello World"}
