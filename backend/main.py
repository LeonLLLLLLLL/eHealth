from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from bson import ObjectId
from bcrypt import hashpw, gensalt, checkpw
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from typing import List, Optional
from scripts.logging_config import logger

##########################
# FOR TESTING REMOVE LATER!!
from time import sleep
##########################

logger.info("Starting backend application")

# Initialize FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application is starting up.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application is shutting down.")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string
db = client["image_upload_db"]  # Replace with your database name
users_collection = db["Users"]  # Replace with your collection name
cases_collection = db["Cases"]  # Replace with your collection name for cases
images_collection = db["Images"]  # Collection for storing images

logger.info("Connected to MongoDB database")

# Secret key and algorithm for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency for OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def create_access_token(data: dict, expires_delta: timedelta = None):
    logger.debug(f"Creating access token for data: {data}")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created successfully for user: {data.get('sub')}")
    return token

def get_current_user(token: str = Depends(oauth2_scheme)):
    logger.debug(f"Decoding JWT token: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles")
        if username is None or roles is None:
            logger.warning("Token is invalid: missing 'sub' or 'roles'")
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.info(f"Authenticated user: {username}")
        return {"username": username, "roles": roles}
    except JWTError as e:
        logger.error(f"Token decoding failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(current_user: dict = Depends(get_current_user)):
    logger.debug(f"Checking admin privileges for user: {current_user}")
    if "admin" not in current_user["roles"]:
        logger.warning(f"Access denied for user: {current_user['username']}, insufficient privileges")
        raise HTTPException(status_code=403, detail="Access denied: Admins only")
    logger.info(f"User {current_user['username']} has admin access")
    return current_user

@app.post("/register")
async def register_user(user_data: UserData):
    logger.info(f"Registering user: {user_data.username}")
    if users_collection.find_one({"username": user_data.username}):
        logger.warning(f"Username already exists: {user_data.username}")
        raise HTTPException(status_code=400, detail="Username already exists")
    if users_collection.find_one({"email": user_data.email}):
        logger.warning(f"Email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hashpw(user_data.password.encode(), gensalt()).decode()
    user_document = {
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_password,
        "roles": user_data.roles,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    result = users_collection.insert_one(user_document)
    logger.info(f"User {user_data.username} registered successfully with ID: {result.inserted_id}")
    return {"success": True, "message": "User registered successfully", "user_id": str(result.inserted_id)}

@app.post("/token", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"User login attempt: {form_data.username}")
    user = users_collection.find_one({"username": form_data.username})
    if not user:
        logger.warning(f"Login failed for username: {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not checkpw(form_data.password.encode(), user["password"].encode()):
        logger.warning(f"Password validation failed for user: {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user["username"], "roles": user["roles"]})
    logger.info(f"User {user['username']} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/cases")
async def create_case(case_data: CaseData, admin: dict = Depends(admin_required)):
    logger.info(f"Creating new case: {case_data.caseName}")
    case_document = {
        "caseName": case_data.caseName,
        "imageIds": [],
        "createdAt": datetime.utcnow()
    }
    result = cases_collection.insert_one(case_document)
    logger.info(f"Case {case_data.caseName} created successfully with ID: {result.inserted_id}")
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
    logger.info(f"Uploading image for case: {case_name}, uploaded by: {current_user['username']}")
    allowed_roles = {"admin", "macro_pathologist"}
    user_roles = set(current_user["roles"])
    if not allowed_roles.intersection(user_roles):
        logger.warning(f"Access denied for user {current_user['username']} to upload image")
        raise HTTPException(
            status_code=403, detail="Access denied: Only admins or macro pathologists can upload images"
        )

    case = cases_collection.find_one({"caseName": case_name})
    if not case:
        logger.debug(f"Case '{case_name}' not found. Creating new case.")
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

    file_content = await file.read()
    logger.debug(f"File received: {file.filename}")

    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file_content)
    logger.debug(f"File saved temporarily at: {temp_file_path}")

    image_document = {
        "filename": file.filename,
        "content_type": file.content_type,
        "data": file_content,
        "analysis_result": None,
        "uploaded_at": datetime.utcnow(),
        "uploaded_by": current_user["username"]
    }
    image_result = images_collection.insert_one(image_document)

    cases_collection.update_one(
        {"_id": case_id},
        {"$push": {"imageIds": str(image_result.inserted_id)}}
    )
    logger.info(f"Image {file.filename} uploaded successfully and associated with case: {case_name}")
    return {
        "success": True,
        "message": f"Image uploaded and associated with case '{case_name}'",
        "case_id": str(case_id),
        "image_id": str(image_result.inserted_id)
    }

@app.post("/logout")
async def logout():
    logger.info("User logged out successfully")
    return {"message": "Successfully logged out. Please remove the token on the client side."}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}
