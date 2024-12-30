from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from bson import ObjectId
from bcrypt import hashpw, gensalt, checkpw
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from typing import List, Optional
from backend.scripts.logging_config import logger
from backend.scripts.process_tissue import process_capsule, process_tissue, segment_bbox
from backend.scripts.onnx_interference import load_onnx_model
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import os
import numpy as np
from PIL import Image
import io
from backend.scripts.grid import generate_grid_segments, save_grid_segments, load_grid_segments, visualize_grid_segments_opencv
import json
import matplotlib.pyplot as plt
import base64
import zlib

##########################
# FOR TESTING REMOVE LATER!!
from time import sleep
import sys
import zipfile
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
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# Dependency for OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#AI Stuff
ort_session_capsule = load_onnx_model(os.path.join("backend", "models", "capsules.onnx"))
ort_session_tissue = load_onnx_model(os.path.join("backend", "models", "tissue.onnx"))
sam = "./backend/sam2/checkpoints/sam2.1_hiera_tiny.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
sam2 = build_sam2(model_cfg, sam, device ='cpu', apply_postprocessing=False)
predictor = SAM2ImagePredictor(sam2)

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

def convert_numpy(obj):
    """Convert numpy types to Python native types."""
    if isinstance(obj, (np.ndarray, list)):
        return [convert_numpy(el) for el in obj]
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    else:
        return obj

def encode_rle(mask):
    """Encodes a binary mask using run-length encoding."""
    flat = mask.flatten()
    runs = np.where(flat[1:] != flat[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return runs.tolist()

def decode_rle(rle, shape):
    """Decodes a run-length encoded mask back to a binary mask."""
    flat = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for start, length in zip(rle[0::2], rle[1::2]):
        flat[start:start + length] = 1
    return flat.reshape(shape)

def encode_mask_with_metadata(mask, metadata):
    """Encodes a binary mask along with metadata using RLE."""
    rle = encode_rle(mask)  # Use existing RLE encoding function
    metadata_with_rle = {
        "rle": rle,
        "metadata": metadata
    }
    return metadata_with_rle

def decode_mask_with_metadata(metadata_with_rle, shape):
    """Decodes an RLE mask along with its metadata."""
    rle = metadata_with_rle["rle"]
    metadata = metadata_with_rle["metadata"]
    mask = decode_rle(rle, shape)  # Use existing RLE decoding function
    return mask, metadata

def compress_metadata_with_masks(metadata_with_rle_list):
    """Compresses RLE masks along with metadata."""
    # Serialize metadata and RLEs into a JSON string
    serialized_data = json.dumps(metadata_with_rle_list)
    # Compress using zlib and encode in base64
    compressed = zlib.compress(serialized_data.encode())
    return base64.b64encode(compressed).decode('utf-8')

def decompress_metadata_with_masks(compressed_data):
    """Decompresses RLE masks and metadata from a compressed format."""
    # Decode the base64 encoded string
    compressed = base64.b64decode(compressed_data)
    # Decompress the zlib-compressed data
    decompressed = zlib.decompress(compressed).decode('utf-8')
    # Deserialize the JSON string into a Python object
    metadata_with_rle_list = json.loads(decompressed)
    return metadata_with_rle_list

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

    # Check or create the case
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
    else:
        case_id = case["_id"]

    # Read the file and process the image
    file_content = await file.read()
    logger.debug(f"File received: {file.filename}")

    try:
        image = Image.open(io.BytesIO(file_content))
        image_array = np.array(image)

        # Process the image
        _1cm = process_capsule(predictor, ort_session_capsule, image_array)
        results_tissue = process_tissue(ort_session_tissue, image_array)

        # Save analysis results
        metadata_with_rle_list = []
        test = []
        for cls, bboxes in results_tissue.items():
            for bbox, confidence in bboxes:
                bbox = tuple(map(float, bbox))
                grid_segments = generate_grid_segments(bbox, _1cm, (1, 1))
                save_grid_segments(grid_segments)

                # Segmentation results
                tissue_masks, tissue_scores, _ = segment_bbox(predictor, image_array, bbox)
                highest_score_mask = max(zip(tissue_masks, tissue_scores), key=lambda x: x[1])[0]
                logger.info(highest_score_mask)

                # Metadata for the mask
                metadata = {
                    "class": cls,
                    "confidence": float(confidence),
                    "bbox": bbox,
                    "grid_segments": grid_segments
                }

                # Encode mask with metadata
                test.append((metadata, highest_score_mask))
                metadata_with_rle = encode_mask_with_metadata(highest_score_mask, metadata)
                metadata_with_rle_list.append(metadata_with_rle)

        # Compress metadata with RLE masks
        compressed_data = compress_metadata_with_masks(metadata_with_rle_list)

        # Decompress to verify integrity
        #decompressed_data = decompress_metadata_with_masks(compressed_data)
        #index = 0
        #for metadata_with_rle in decompressed_data:
            #mask, metadata = decode_mask_with_metadata(metadata_with_rle, image_array.shape[:2])
            #visualize_grid_segments_opencv(metadata["grid_segments"], image_array, f"{index}.jpg")
            #index += 1

            # Visualize or process the mask
        #    plt.figure(figsize=(8, 8))
        #    plt.imshow(mask, cmap='gray', interpolation='nearest')
        #    plt.title(f"Class: {metadata['class']}, Confidence: {metadata['confidence']}")
        #    plt.colorbar(label="Value")
        #    plt.axis('off')
        #    plt.show()

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=400, detail="Failed to process image. Please upload a valid image file."
        )

    # Save the image and analysis results to the database
    image_document = {
        "case_id": str(case_id),
        "filename": file.filename,
        "content_type": file.content_type,
        "image_shape": image_array.shape[:2],
        "data": file_content,
        "uploaded_at": datetime.utcnow(),
        "uploaded_by": current_user["username"],
        "compressed_analysis_results": compressed_data  # Store compressed data here
    }
    image_result = images_collection.insert_one(image_document)
    image_id = str(image_result.inserted_id)

    # Link the image to the case
    cases_collection.update_one(
        {"_id": case_id},
        {"$push": {"imageIds": image_id}}
    )

    logger.info(f"Image {file.filename} uploaded successfully and associated with case: {case_name}")
    return {
        "success": True,
        "message": f"Image uploaded and associated with case '{case_name}'",
        "case_id": str(case_id),
        "image_id": image_id
    }

@app.get("/cases/{case_name}/images", response_model=list)
async def get_case_images(case_name: str, current_user: dict = Depends(get_current_user)):
    logger.info(f"Fetching images for case: {case_name}, requested by: {current_user['username']}")

    allowed_roles = {"admin", "diagnostic_pathologist"}
    user_roles = set(current_user["roles"])

    if not allowed_roles.intersection(user_roles):
        logger.warning(f"Access denied for user {current_user['username']} to fetch images")
        raise HTTPException(
            status_code=403, detail="Access denied: Only admins or diagnostic pathologists can access case images"
        )

    # Fetch the case by name
    case = cases_collection.find_one({"caseName": case_name})
    if not case:
        logger.warning(f"Case '{case_name}' not found")
        raise HTTPException(status_code=404, detail=f"Case '{case_name}' not found")

    # Retrieve all images linked to the case
    image_ids = case.get("imageIds", [])
    if not image_ids:
        return []

    # Convert image IDs to ObjectId and fetch corresponding images
    try:
        object_ids = [ObjectId(image_id) for image_id in image_ids]
        images = list(images_collection.find({"_id": {"$in": object_ids}}))
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching images")

    # Serialize images and encode binary data
    serialized_images = []
    for image in images:
        serialized_image = {
            "_id": str(image["_id"]),
            "filename": image.get("filename", "unknown"),
            "image_shape": image.get("image_shape", {}),
            "compressed_analysis_results": image.get("compressed_analysis_results", "")
        }

        # Encode the binary 'data' field in Base64 if present
        if "data" in image and isinstance(image["data"], bytes):
            serialized_image["data"] = base64.b64encode(image["data"]).decode("utf-8")

        serialized_images.append(serialized_image)

    return serialized_images

    #analysis_result = []
    #for image in images:
    #    compressed_data = image.get('compressed_analysis_results')
    #    decompressed_data = decompress_metadata_with_masks(compressed_data)
    #    for metadata_with_rle in decompressed_data:
    #        mask, metadata = decode_mask_with_metadata(metadata_with_rle, image.get("image_shape"))
    #        analysis_result.append(mask, metadata)
    #        logger.info(metadata)


@app.post("/logout")
async def logout():
    logger.info("User logged out successfully")
    return {"message": "Successfully logged out. Please remove the token on the client side."}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}
