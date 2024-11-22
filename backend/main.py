from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from bson import ObjectId
from bcrypt import hashpw, gensalt, checkpw
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from typing import List, Optional

##########################
# FOR TESTING REMOVE LATER!!
from time import sleep
##########################

# Initialize FastAPI app
app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["image_upload_db"]  # Replace with your database name
users_collection = db["Users"]  # Replace with your collection name
cases_collection = db["Cases"]  # Replace with your collection name for cases
images_collection = db["Images"]  # Collection for storing images

# Secret key and algorithm for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency for OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: Optional[List[str]] = None

# Helper function to create JWT tokens
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper function to decode JWT and get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles")
        if username is None or roles is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "roles": roles}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin role checker
def admin_required(current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Access denied: Admins only")
    return current_user

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
        "created_at": datetime.utcnow(),
        "last_login": None
    }

    # Insert the user document into the database
    result = users_collection.insert_one(user_document)

    return {"success": True, "message": "User registered successfully", "user_id": str(result.inserted_id)}

@app.post("/token", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find the user in the database by username
    user = users_collection.find_one({"username": form_data.username})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Validate password using bcrypt
    if not checkpw(form_data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate a JWT token
    access_token = create_access_token(
        data={"sub": user["username"], "roles": user["roles"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/cases")
async def create_case(case_data: CaseData, admin: dict = Depends(admin_required)):
    # Prepare the case document
    case_document = {
        "caseName": case_data.caseName,
        "imageIds": [],  # Initialize as empty
        "createdAt": datetime.utcnow()
    }

    # Insert the case into the MongoDB collection
    result = cases_collection.insert_one(case_document)

    return {
        "success": True,
        "message": "Case created successfully",
        "case_id": str(result.inserted_id)
    }

@app.post("/cases/{case_name}/upload-image")
async def upload_image(
    case_name: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload an image and associate it with a case based on the unique case name.
    If the case doesn't exist, it is created.
    Only users with 'admin' or 'macro_pathologist' roles can upload.
    """
    # Role validation
    allowed_roles = {"admin", "macro_pathologist"}
    user_roles = set(current_user["roles"])
    if not allowed_roles.intersection(user_roles):
        raise HTTPException(
            status_code=403, detail="Access denied: Only admins or macro pathologists can upload images"
        )

    # Check if the case exists
    case = cases_collection.find_one({"caseName": case_name})

    # If the case doesn't exist, create it
    if not case:
        case_document = {
            "caseName": case_name,
            "imageIds": [],
            "createdAt": datetime.utcnow()
        }
        result = cases_collection.insert_one(case_document)
        case_id = result.inserted_id
        case = cases_collection.find_one({"_id": case_id})
    else:
        case_id = case["_id"]

    # Read the file content
    file_content = await file.read()

    # Save the image to the database
    image_document = {
        "filename": file.filename,
        "content_type": file.content_type,
        "data": file_content,
        "uploaded_at": datetime.utcnow(),
        "uploaded_by": current_user["username"]
    }
    image_result = images_collection.insert_one(image_document)

    # Update the case document with the new image ID
    cases_collection.update_one(
        {"_id": case_id},
        {"$push": {"imageIds": str(image_result.inserted_id)}}
    )

    return {
        "success": True,
        "message": f"Image uploaded and associated with case '{case_name}'",
        "case_id": str(case_id),
        "image_id": str(image_result.inserted_id)
    }

@app.post("/logout")
async def logout():
    """
    Logs out the user by signaling the client to remove the token.
    """
    return {"message": "Successfully logged out. Please remove the token on the client side."}

@app.get("/")
async def root():
    return {"message": "Hello World"}
