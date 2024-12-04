import uuid
import json
import cv2
import numpy as np

# Generate Grid Segments
def generate_grid_segments(bounding_box, cm_to_pixels, grid_size_cm):
    x_min, y_min, x_max, y_max = bounding_box
    cell_width = cm_to_pixels * grid_size_cm[0]
    cell_height = cm_to_pixels * grid_size_cm[1]

    horizontal_segments = []
    vertical_segments = []

    current_y = y_min
    while current_y < y_max:
        current_x = x_min
        while current_x < x_max:
            # Add the top horizontal line
            horizontal_segments.append({
                "id": str(uuid.uuid4()),
                "x_start": current_x,
                "y_start": current_y,
                "x_end": min(current_x + cell_width, x_max),
                "y_end": current_y
            })

            # Add the left vertical line
            vertical_segments.append({
                "id": str(uuid.uuid4()),
                "x_start": current_x,
                "y_start": current_y,
                "x_end": current_x,
                "y_end": min(current_y + cell_height, y_max)
            })

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
        current_y += cell_height

    metadata = {
        "bounding_box": bounding_box,
        "cm_to_pixels": cm_to_pixels,
        "grid_size_cm": grid_size_cm
    }
    return {"horizontal_segments": horizontal_segments, "vertical_segments": vertical_segments, "metadata": metadata}

# Save and Load Grid Segments
def save_grid_segments(grid_segments, filepath="grid_segments.json"):
    with open(filepath, 'w') as f:
        json.dump(grid_segments, f, indent=4)

def load_grid_segments(filepath="grid_segments.json"):
    with open(filepath, 'r') as f:
        return json.load(f)

# Visualize the Segmented Grid
def visualize_grid_segments_opencv(grid_segments, bounding_box, image_shape=(900, 700)):
    canvas = np.ones((image_shape[1], image_shape[0], 3), dtype=np.uint8) * 255

    #x_min, y_min, x_max, y_max = bounding_box
    #cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)

    for segment in grid_segments["horizontal_segments"]:
        start = (int(segment["x_start"]), int(segment["y_start"]))
        end = (int(segment["x_end"]), int(segment["y_end"]))
        cv2.line(canvas, start, end, (0, 0, 0), 1)

    for segment in grid_segments["vertical_segments"]:
        start = (int(segment["x_start"]), int(segment["y_start"]))
        end = (int(segment["x_end"]), int(segment["y_end"]))
        cv2.line(canvas, start, end, (0, 0, 0), 1)

    cv2.imshow("Grid Visualization", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Modifier Functions
def move_line(grid_segments, segment_id, segment_type, offset):
    segments = grid_segments[f"{segment_type}_segments"]
    for segment in segments:
        if segment["id"] == segment_id:
            if segment_type == "horizontal":
                segment["y_start"] += offset
                segment["y_end"] += offset
            elif segment_type == "vertical":
                segment["x_start"] += offset
                segment["x_end"] += offset
            break
    return grid_segments

def resize_line(grid_segments, segment_id, segment_type, new_length, direction):
    segments = grid_segments[f"{segment_type}_segments"]
    for segment in segments:
        if segment["id"] == segment_id:
            if segment_type == "horizontal":
                if direction == "right":
                    segment["x_end"] = segment["x_start"] + new_length
                elif direction == "left":
                    segment["x_start"] = segment["x_end"] - new_length
            elif segment_type == "vertical":
                if direction == "down":
                    segment["y_end"] = segment["y_start"] + new_length
                elif direction == "up":
                    segment["y_start"] = segment["y_end"] - new_length
            break
    return grid_segments

# Example Usage
if __name__ == "__main__":
    bounding_box = (100, 100, 800, 600)
    cm_to_pixels = 100
    grid_size_cm = (1, 1)

    grid_segments = generate_grid_segments(bounding_box, cm_to_pixels, grid_size_cm)
    visualize_grid_segments_opencv(grid_segments, bounding_box)

    first_horizontal_id = grid_segments["horizontal_segments"][0]["id"]
    grid_segments = resize_line(grid_segments, first_horizontal_id, "horizontal", 200, "left")

    first_vertical_id = grid_segments["vertical_segments"][0]["id"]
    grid_segments = resize_line(grid_segments, first_vertical_id, "vertical", 300, "up")



    visualize_grid_segments_opencv(grid_segments, bounding_box)
