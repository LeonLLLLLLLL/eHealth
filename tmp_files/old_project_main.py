import os
from functools import wraps
from tqdm import tqdm
import numpy as np
import cv2
import traceback
from Scripts.mask_operations import (
    find_contours, calculate_circumference, calculate_xy_dimensions, calculate_area,
    normalize_px, crop_mask_from_img
)
from Scripts.sam_segment import segment, load_sam, convert_mask
from Scripts.yolo_nas_predict import pred, load_img_names, rename_img, load_yolo
from Scripts.logger import Logger
from Scripts.bounding_box import overlapping_boxes, raw_boxes_on_image, draw_grid_on_image
#from Scripts.create_folder_struct import create_folders

logger = Logger("logs/log.txt")

# Define constants for output directories
BASE_DIR = os.getcwd()  # Use the current working directory as the base directory
OUTPUT_DIR = os.path.join(BASE_DIR, "Images_out")
CAPSULE_DIR = os.path.join(OUTPUT_DIR, "Capsules")
TISSUE_DIR = os.path.join(OUTPUT_DIR, "Tissue")

def get_output_paths(subfolder, *args):
    return os.path.join(BASE_DIR, subfolder, *args)

def error_handler_and_logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in function '{func.__name__}': {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            return None

    return wrapper

@error_handler_and_logger
def process_image(file_path, dir_out, index, model, classes, conf, save):
    logger.info(f"Processing image: {file_path}")
    result = list(pred(file_path, model, classes, conf, dir_out, save))[0]
    boxes = result.prediction.bboxes_xyxy.tolist()
    confidences = result.prediction.confidence
    labels = result.prediction.labels.tolist()
    rename_img(dir_out, index + 1, "pred")
    return [boxes, confidences, labels]

@error_handler_and_logger
def handle_box(boxes, confidences, labels, index, file_path, out_dir, color, mask_out):
    results = []
    for count, (box, confidence, label) in enumerate(zip(boxes, confidences, labels)):
        logger.info(f"############## Image: {index + 1} | Box: {count + 1} ###############")
        logger.info(f"File Path: {file_path}")
        box = np.array([box[0], box[1], box[2], box[3]])
        mask = segment(file_path, index + 1, box, out_dir, color, count)
        binary_mask = convert_mask(mask)
        cv2.imwrite(get_output_paths(mask_out, f"binary_mask{index}_0.jpg"), binary_mask)
        rename_img(mask_out, count + 1, f"binary_mask{index}")
        contours = find_contours(binary_mask)
        circumference = calculate_circumference(contours)
        area = calculate_area(contours)
        dimensions = calculate_xy_dimensions(contours)

        if dimensions[0] < dimensions[1]:
            dimensions[0], dimensions[1] = dimensions[1], dimensions[0]

        results.append({
            "circumference": circumference,
            "area": area,
            "height": dimensions[0],
            "width": dimensions[1],
            "labelvalue": label,
            "confidencevalue": confidence,
            "box": box,
            "mask": binary_mask
        })
    return results

@error_handler_and_logger
def process_capsule(filename, index):
    dir_in = get_output_paths("Images_in")
    dir_out = get_output_paths(CAPSULE_DIR, "detected_capsules")
    detect_capsule_model = load_yolo("yolo_nas_l", 2, "model/detect_all_capsules.pth")
    length = 0

    file_path = os.path.join(dir_in, filename)
    boxes, confidences, labels = process_image(file_path, dir_out, index, detect_capsule_model, ["Capsule_opened", "Capsule_closed"], 0.7, True)

    if boxes is not None and boxes:
        best_box, best_confidence, best_label = None, None, None
        for count, (box, confidence, label) in enumerate(zip(boxes, confidences, labels)):
            if count <= 0:
                best_box, best_confidence, best_label = box, confidence, label
            elif best_confidence < confidence:
                best_box, best_confidence, best_label = box, confidence, label

        results = handle_box([best_box], [best_confidence], [best_label], index, file_path, get_output_paths(CAPSULE_DIR, "capsules_seg_out"), "blue", get_output_paths(CAPSULE_DIR, "capsule_binary_mask_out"))
        for count, result in enumerate(results):
            _1cm = calculate_1cm_in_pixels(result["labelvalue"], result["height"])
            logger.info(f"############## Image: {index + 1} | Box: {count + 1} ###############")
            logger.info(f"File Path: ${file_path}$")
            logger.info(f"Circumference: ${result['circumference']}$ pixels")
            logger.info(f"Area: ${result['area']}$ pixels^2")
            logger.info(f"Height: ${result['height']}$ pixels")
            logger.info(f"Width: ${result['width']}$ pixels")
            logger.info(f"Labelvalue: ${result['labelvalue']}$")
            logger.info(f"Confidencevalue: ${result['confidencevalue']}$")
            logger.info(f"Boxcoordinates: ${result['box']}$")
            logger.info(f"1cm: ${_1cm}$ pixels")
            length = _1cm
    else:
        logger.warning(f"No Bounding box found")
        logger.warning(f"Image: {file_path}")
    return length

@error_handler_and_logger
def fill_biggest_contour(array):
    contours, _ = cv2.findContours(array, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        largest_contour_mask = np.zeros_like(array)
        cv2.drawContours(largest_contour_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
        filled_mask = np.zeros_like(array)
        cv2.drawContours(filled_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    else:
        largest_contour_mask = np.zeros_like(array)
        filled_mask = np.zeros_like(array)
    return filled_mask

@error_handler_and_logger
def fill_non_overlapping_contours(array):
    contours, _ = cv2.findContours(array, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled_mask = np.zeros_like(array)

    for contour in contours:
        cv2.drawContours(filled_mask, [contour], -1, 255, thickness=cv2.FILLED)

    return filled_mask

@error_handler_and_logger
def process_tissue(filename, length, name_index, detect_tissue_model):
    dir_in = get_output_paths("Images_in")
    dir_out_pred = get_output_paths(TISSUE_DIR, "tissue_detected")
    dir_out_seg = get_output_paths(TISSUE_DIR, "tissue_seg_out")
    dir_out_mask = get_output_paths(TISSUE_DIR, "tissue_binary_mask_out")
    dir_out_cropped = get_output_paths(TISSUE_DIR, "tissue_cropped")
    dir_out_gray = get_output_paths(TISSUE_DIR, "tissue_gray_out")
    dir_out_box = get_output_paths(TISSUE_DIR, "tissue_fixed_box_out")
    dir_out_mask_combined = get_output_paths(TISSUE_DIR, "tissue_binary_mask_combined_out")
    dir_out_grid = get_output_paths(TISSUE_DIR, "tissue_grid_out")
    dir_out_cropped_combined = get_output_paths(TISSUE_DIR, "tissue_combined_cropped_out")
    dir_out_seg_gray = get_output_paths(TISSUE_DIR, "tissue_seg_gray_out")
    dir_out_gray_rgb_combined_cropped = get_output_paths(TISSUE_DIR, "tissue_gray_rgb_combined_crop_out")
    grayscale_image(dir_in, filename, get_output_paths(TISSUE_DIR, "tissue_gray_out"))

    file_path = os.path.join(dir_in, filename)
    file_path_gray = os.path.join(get_output_paths(TISSUE_DIR, "tissue_gray_out"), filename)
    boxes, confidences, labels = process_image(file_path, dir_out_pred, name_index, detect_tissue_model, ["Gewebe"], 0.65, True)

    if boxes is not None and boxes:
        box = overlapping_boxes(boxes)
        combined_box_img = raw_boxes_on_image(file_path, dir_out_box, f"fixed_box_{name_index}_{filename}", box[0], "blue")
        draw_grid_on_image(file_path, dir_out_grid, box[0], length, name_index, filename)
        results = handle_box(box[0], confidences, labels, name_index, file_path, dir_out_seg, "red", dir_out_mask)
        results2 = handle_box(box[0], confidences, labels, name_index, os.path.join(get_output_paths(TISSUE_DIR, "tissue_gray_out"), filename), dir_out_seg_gray, "red", dir_out_mask)
        combined_mask = np.zeros_like(results[0]["mask"][0])
        combined_mask2 = np.zeros_like(results2[0]["mask"][0])
        combined_mask3 = np.zeros_like(results2[0]["mask"][0])
        for count, (result, result2) in enumerate(zip(results, results2)):
            cropped = crop_mask_from_img(file_path, fill_non_overlapping_contours(result["mask"]))
            combined_mask = np.bitwise_or(combined_mask, result["mask"])
            combined_mask2 = np.bitwise_or(combined_mask2, result2["mask"])
            cv2.imwrite(get_output_paths(dir_out_cropped, f"{filename.replace('.jpg', '')}_{count}_cropped_{name_index+1}.jpg"), cropped)
        combined_mask3 = np.bitwise_or(combined_mask,combined_mask2)
        cropped_combined = crop_mask_from_img(file_path, combined_mask)
        gray_rgb_combined_crop = crop_mask_from_img(file_path, combined_mask3)
        cv2.imwrite(get_output_paths(dir_out_gray_rgb_combined_cropped, f"{filename.replace('.jpg', '')}_gray_rgb_combined_crop_{name_index+1}.jpg"), gray_rgb_combined_crop)
        cv2.imwrite(get_output_paths(dir_out_mask_combined, f"{filename.replace('.jpg', '')}_combined_mask_{name_index+1}.jpg"), combined_mask)
        cv2.imwrite(get_output_paths(dir_out_cropped_combined, f"{filename.replace('.jpg', '')}_combined_crop_{name_index+1}.jpg"), cropped_combined)
    else:
        logger.warning(f"No Bounding box found")
        logger.warning(f"Image: {file_path}")

@error_handler_and_logger
def grayscale_image(input_dir, filename, output_dir):
    file_path = os.path.join(input_dir, filename)
    image = cv2.imread(file_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.join(output_dir, filename), gray_image)

@error_handler_and_logger
def create_folders():
    # Define folder paths
    dir_out_pred = get_output_paths(TISSUE_DIR, "tissue_detected")
    dir_out_seg = get_output_paths(TISSUE_DIR, "tissue_seg_out")
    dir_out_mask = get_output_paths(TISSUE_DIR, "tissue_binary_mask_out")
    dir_out_cropped = get_output_paths(TISSUE_DIR, "tissue_cropped")
    dir_out_gray = get_output_paths(TISSUE_DIR, "tissue_gray_out")
    dir_out_box = get_output_paths(TISSUE_DIR, "tissue_fixed_box_out")
    dir_out_mask_combined = get_output_paths(TISSUE_DIR, "tissue_binary_mask_combined_out")
    dir_out_grid = get_output_paths(TISSUE_DIR, "tissue_grid_out")
    dir_out_cropped_combined = get_output_paths(TISSUE_DIR, "tissue_combined_cropped_out")
    dir_out_seg_gray = get_output_paths(TISSUE_DIR, "tissue_seg_gray_out")
    dir_out_gray_rgb_combined_cropped = get_output_paths(TISSUE_DIR, "tissue_gray_rgb_combined_crop_out")

    # Check if Images_out already exists
    if os.path.exists(OUTPUT_DIR):
        # If Images_out exists, find the highest numbered folder and increment
        existing_numbers = [int(folder.split("_")[-1]) for folder in os.listdir(BASE_DIR) if folder.startswith("Images_out_")]
        if existing_numbers:
            new_number = max(existing_numbers) + 1
        else:
            new_number = 1

        # Rename existing Images_out folder
        os.rename(OUTPUT_DIR, f"Images_out_{new_number}")

    # Create new Images_out folder
    os.makedirs(TISSUE_DIR, exist_ok=True)

    # Create subfolders
    os.makedirs(dir_out_pred, exist_ok=True)
    os.makedirs(dir_out_seg, exist_ok=True)
    os.makedirs(dir_out_mask, exist_ok=True)
    os.makedirs(dir_out_cropped, exist_ok=True)
    os.makedirs(dir_out_gray, exist_ok=True)
    os.makedirs(dir_out_box, exist_ok=True)
    os.makedirs(dir_out_mask_combined, exist_ok=True)
    os.makedirs(dir_out_grid, exist_ok=True)
    os.makedirs(dir_out_cropped_combined, exist_ok=True)
    os.makedirs(dir_out_seg_gray, exist_ok=True)
    os.makedirs(dir_out_gray_rgb_combined_cropped, exist_ok=True)

@error_handler_and_logger
def main():
    load_sam("model/sam_vit_h_4b8939.pth")
    model = load_yolo("yolo_nas_l", 1, "model/big_tissue.pth")
    dir_in = get_output_paths("Images_in")
    filenames = load_img_names(dir_in)
    name_index = 0
    create_folders()

    for filename in tqdm(filenames, desc="Processing images"):
        process_tissue(filename, 100, name_index, model)
        name_index += 1

@error_handler_and_logger
def calculate_1cm_in_pixels(label, height):
    if label == 1:
        return normalize_px(4, height)
    elif label == 0:
        return normalize_px(8, height)
    else:
        logger.error(f"Label can't be assigned correctly")
        logger.error(f"Labelvalue: {label}")
        return None

if __name__ == "__main__":
    logger.info("Script started.")
    try:
        main()
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"Script encountered an error: {str(e)}\n{traceback_str}")
    finally:
        logger.info("Script completed.")
        logger.set_logfile()
