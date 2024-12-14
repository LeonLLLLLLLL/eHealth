import uuid
import json
import cv2
import numpy as np
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Generate Grid Segments
def generate_grid_segments(bounding_box, cm_to_pixels, grid_size_cm):
    logger.info("Generating grid segments.")
    logger.info(f"Bounding box: {bounding_box}, cm_to_pixels: {cm_to_pixels}, grid_size_cm: {grid_size_cm}")

    x_min, y_min, x_max, y_max = bounding_box
    cell_width = cm_to_pixels * grid_size_cm[0]
    cell_height = cm_to_pixels * grid_size_cm[1]

    horizontal_segments = []
    vertical_segments = []

    current_y = y_min
    while current_y < y_max:
        current_x = x_min
        while current_x < x_max:
            horizontal_segments.append({
                "id": str(uuid.uuid4()),
                "x_start": current_x,
                "y_start": current_y,
                "x_end": min(current_x + cell_width, x_max),
                "y_end": current_y
            })
            vertical_segments.append({
                "id": str(uuid.uuid4()),
                "x_start": current_x,
                "y_start": current_y,
                "x_end": current_x,
                "y_end": min(current_y + cell_height, y_max)
            })
            logger.info(f"Created horizontal segment: {horizontal_segments[-1]}")
            logger.info(f"Created vertical segment: {vertical_segments[-1]}")
            current_x += cell_width
        current_y += cell_height

    current_x = x_min
    while current_x < x_max:
        horizontal_segments.append({
            "id": str(uuid.uuid4()),
            "x_start": current_x,
            "y_start": current_y,
            "x_end": min(current_x + cell_width, x_max),
            "y_end": current_y
        })
        logger.info(f"Created horizontal segment: {horizontal_segments[-1]}")
        current_x += cell_width

    current_y = y_min
    while current_y < y_max:
        vertical_segments.append({
            "id": str(uuid.uuid4()),
            "x_start": x_max,
            "y_start": current_y,
            "x_end": x_max,
            "y_end": min(current_y + cell_height, y_max)
        })
        logger.info(f"Created vertical segment: {vertical_segments[-1]}")
        current_y += cell_height

    metadata = {
        "bounding_box": bounding_box,
        "cm_to_pixels": cm_to_pixels,
        "grid_size_cm": grid_size_cm
    }
    logger.info("Grid segments generation complete.")
    return {"horizontal_segments": horizontal_segments, "vertical_segments": vertical_segments, "metadata": metadata}

# Save and Load Grid Segments
def save_grid_segments(grid_segments, filepath="grid_segments.json"):
    logger.info(f"Saving grid segments to {filepath}.")
    try:
        with open(filepath, 'w') as f:
            json.dump(grid_segments, f, indent=4)
        logger.info(f"Grid segments successfully saved to {filepath}.")
    except Exception as e:
        logger.error(f"Failed to save grid segments to {filepath}: {str(e)}")

def load_grid_segments(filepath="grid_segments.json"):
    logger.info(f"Loading grid segments from {filepath}.")
    try:
        with open(filepath, 'r') as f:
            grid_segments = json.load(f)
        logger.info("Grid segments loaded successfully.")
        return grid_segments
    except Exception as e:
        logger.error(f"Failed to load grid segments from {filepath}: {str(e)}")
        return None

def visualize_grid_segments_opencv(grid_segments, image, save_path=None, max_display_size=(900, 700)):
    logger.info("Visualizing grid segments on the image.")
    try:
        output_image = image.copy()

        # Draw horizontal segments
        for segment in grid_segments["horizontal_segments"]:
            start = (int(segment["x_start"]), int(segment["y_start"]))
            end = (int(segment["x_end"]), int(segment["y_end"]))
            cv2.line(output_image, start, end, (0, 0, 255), 1)

        # Draw vertical segments
        for segment in grid_segments["vertical_segments"]:
            start = (int(segment["x_start"]), int(segment["y_start"]))
            end = (int(segment["x_end"]), int(segment["y_end"]))
            cv2.line(output_image, start, end, (0, 0, 255), 1)

        # Save the original image with the grid if save_path is provided
        if save_path:
            cv2.imwrite(save_path, output_image)
            logger.info(f"Image with grid saved to {save_path}")
    except Exception as e:
        logger.error(f"Error during grid visualization: {str(e)}")
