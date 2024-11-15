from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bcrypt import checkpw
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["patholink"]  # Replace with your database name
users_collection = db["users"]  # Replace with your collection name

# Define the Pydantic model for login data
class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
async def validate_login(login_data: LoginData):
    # Find the user in the database by username
    user = users_collection.find_one({"username": login_data.username})

    if not user:
        # User not found
        return {"success": False, "message": "Invalid username or password"}

    # Validate password
    #if checkpw(login_data.password.encode(), user["password"].encode()):
    if(login_data.password == user["password"]):
        return {"success": True, "message": "Login successful"}

    # Invalid password
    return {"success": False, "message": "Invalid username or password"}

@app.get("/")
async def root():
    return {"message": "Hello World"}
