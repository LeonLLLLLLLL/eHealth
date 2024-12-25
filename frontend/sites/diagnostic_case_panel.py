import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import base64
import zlib
import json
import matplotlib.pyplot as plt
import numpy as np

diagnostic_case_panel = Blueprint('diagnostic_case_panel', __name__)

BACKEND_URL = "http://127.0.0.1:8000"

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

                    for metadata_with_rle in decompressed_data:
                        mask, metadata = decode_mask_with_metadata(metadata_with_rle, image["image_shape"])
                        grids.append(metadata["grid_segments"])  # Append the grid_segments to the list

                        # Visualize or process the mask if needed
                        # plt.figure(figsize=(8, 8))
                        # plt.imshow(mask, cmap='gray', interpolation='nearest')
                        # plt.title(f"Class: {metadata['class']}, Confidence: {metadata['confidence']}")
                        # plt.colorbar(label="Value")
                        # plt.axis('off')
                        # plt.show()

                    # Add the grids list to the image's dictionary for future use
                    image["grids"] = grids

                return render_template('diagnostic_case_panel.html', case_name=case_name, case_data=data)

            else:
                flash(f"Error: {response.json().get('detail', 'Unable to fetch data')}", "error")
        except requests.exceptions.RequestException as e:
            flash(f"Backend request failed: {str(e)}", "error")

    return render_template('diagnostic_case_panel.html')
