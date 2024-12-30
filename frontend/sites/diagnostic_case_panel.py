import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import base64
import zlib
import json
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from PIL import Image, ImageOps
import cv2

diagnostic_case_panel = Blueprint('diagnostic_case_panel', __name__)

BACKEND_URL = "http://127.0.0.1:8000"

def numpy_to_base64(np_array):
    img = Image.fromarray(np_array)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_str

def mask_to_polygons(mask):
    """
    Convert a binary mask to a list of polygons (vectorized contours).
    """
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polygons = [contour.flatten().tolist() for contour in contours]
    return polygons

def overlay_masks_on_image(base64_image: str, masks: list) -> str:
    """
    Overlays binary masks onto a base64 image in transparent red.

    Args:
        base64_image (str): Base64-encoded input image.
        masks (list): List of binary masks as NumPy arrays (same size as the image).

    Returns:
        str: Base64-encoded image with masks overlayed.
    """
    # Decode the base64 image
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data)).convert("RGBA")
    image_width, image_height = image.size

    # Create a transparent overlay
    overlay = Image.new("RGBA", image.size, (255, 0, 0, 0))

    for mask in masks:
        if mask.shape != (image_height, image_width):
            raise ValueError("Mask size must match the image size")

        # Convert binary mask to RGBA image
        mask_image = Image.fromarray((mask * 255).astype(np.uint8))
        red_overlay = Image.new("RGBA", mask_image.size, (255, 0, 0, 128))  # Transparent red
        overlay = Image.alpha_composite(overlay, Image.composite(red_overlay, Image.new("RGBA", mask_image.size), mask_image))

    # Combine the overlay with the original image
    final_image = Image.alpha_composite(image, overlay)

    # Display for debugging
    #plt.imshow(final_image)
    #plt.axis("off")
    #plt.show()

    # Convert final image to base64
    buffered = BytesIO()
    #final_image.save(buffered, format="PNG")
    final_base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return final_base64_image

def decode_rle(rle, shape):
    """Decodes a run-length encoded mask back to a binary mask."""
    flat = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for start, length in zip(rle[0::2], rle[1::2]):
        flat[start:start + length] = 1
    return flat.reshape(shape)

def decompress_metadata_with_masks(compressed_data):
    """Decompresses RLE masks and metadata from a compressed format."""
    # Decode the base64 encoded string
    compressed = base64.b64decode(compressed_data)
    # Decompress the zlib-compressed data
    decompressed = zlib.decompress(compressed).decode('utf-8')
    # Deserialize the JSON string into a Python object
    metadata_with_rle_list = json.loads(decompressed)
    return metadata_with_rle_list

def decode_mask_with_metadata(metadata_with_rle, shape):
    """Decodes an RLE mask along with its metadata."""
    rle = metadata_with_rle["rle"]
    metadata = metadata_with_rle["metadata"]
    mask = decode_rle(rle, shape)  # Use existing RLE decoding function
    return mask, metadata

@diagnostic_case_panel.route('/', methods=['GET', 'POST'])
def diagnostic_page():
    return render_template('diagnostic_case_panel.html')

@diagnostic_case_panel.route('/get_case', methods=['GET', 'POST'])
def diagnostic_panel():
    """
    Diagnostic case panel route, protected by user authentication.
    """
    if request.method == 'POST':
        case_name = request.form.get('case_input')
        user_token = session['access_token']  # Retrieve the token from session
        headers = {"Authorization": f"Bearer {user_token}"}

        try:
            # Fetch case images and analysis results from the backend
            response = requests.get(f"{BACKEND_URL}/cases/{case_name}/images", headers=headers)
            if response.status_code == 200:
                data = response.json()
                for image in data:
                    decompressed_data = decompress_metadata_with_masks(image["compressed_analysis_results"])
                    grids = []  # Initialize a list to store grids for the current image
                    masks = []
                    for metadata_with_rle in decompressed_data:
                        mask, metadata = decode_mask_with_metadata(metadata_with_rle, image["image_shape"])
                        grids.append(metadata["grid_segments"])  # Append the grid_segments to the list
                        masks.append(mask_to_polygons(mask))
                        # Visualize or process the mask if needed
                        # plt.figure(figsize=(8, 8))
                        # plt.imshow(mask, cmap='gray', interpolation='nearest')
                        # plt.title(f"Class: {metadata['class']}, Confidence: {metadata['confidence']}")
                        # plt.colorbar(label="Value")
                        # plt.axis('off')
                        # plt.show()

                    # Add the grids list to the image's dictionary for future use
                    image["grids"] = grids
                    image["masks"] = masks

                return render_template('diagnostic_case_panel.html', case_name=case_name, case_data=data)

            else:
                flash(f"Error: {response.json().get('detail', 'Unable to fetch data')}", "error")
        except requests.exceptions.RequestException as e:
            flash(f"Backend request failed: {str(e)}", "error")

    return render_template('diagnostic_case_panel.html')
