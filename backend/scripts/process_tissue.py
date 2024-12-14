from backend.scripts.onnx_interference import onnx_prediction, draw_bboxes
import os
import torch
#from sam2.build_sam import build_sam2
import cv2
from PIL import Image
import numpy as np
import supervision as sv
#from sam2.sam2_image_predictor import SAM2ImagePredictor
import matplotlib.pyplot as plt

########## TESTING REMOVE LATER ############

############################################

def show_mask(mask, ax, random_color=False, borders = True):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30/255, 144/255, 255/255, 0.6])
    h, w = mask.shape[-2:]
    mask = mask.astype(np.uint8)
    mask_image =  mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    if borders:
        contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # Try to smooth contours
        contours = [cv2.approxPolyDP(contour, epsilon=0.01, closed=True) for contour in contours]
        mask_image = cv2.drawContours(mask_image, contours, -1, (1, 1, 1, 0.5), thickness=2)
    ax.imshow(mask_image)

def show_masks(image, masks, scores, point_coords=None, box_coords=None, input_labels=None, borders=True):
    for i, (mask, score) in enumerate(zip(masks, scores)):
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        show_mask(mask, plt.gca(), borders=borders)
        if point_coords is not None:
            assert input_labels is not None
            show_points(point_coords, input_labels, plt.gca())
        if box_coords is not None:
            # boxes
            show_box(box_coords, plt.gca())
        if len(scores) > 1:
            plt.title(f"Mask {i+1}, Score: {score:.3f}", fontsize=18)
        plt.axis('off')
        plt.show()

def calculate_pixels_per_cm(highest_score_mask, class_id):
    reference_length_cm = 8 if class_id == 0 else 4
    rows = np.any(highest_score_mask, axis=1)
    cols = np.any(highest_score_mask, axis=0)
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]

    width = x_max - x_min + 1
    height = y_max - y_min + 1

    if(width > height):
        _1cm = width / reference_length_cm
    else:
        _1cm = height / reference_length_cm

    return _1cm

def get_highest_conf_bbox(results):
    max_confidence = -1
    best_bbox = None
    best_class = None

    for cls, bboxes in results.items():
        for bbox, confidence in bboxes:
            if confidence > max_confidence:
                max_confidence = confidence
                best_bbox = bbox
                best_class = cls

    return best_class, best_bbox, max_confidence

def process_capsule(predictor, ort_session, image):
    result = onnx_prediction(image, ort_session)
    best_class, best_bbox, max_confidence = get_highest_conf_bbox(result)
    best_bbox = np.array(best_bbox)
    masks, scores, logits = segment_bbox(predictor, image, best_bbox)
    highest_score_mask = max(zip(masks, scores), key=lambda x: x[1])[0]
    _1cm = calculate_pixels_per_cm(highest_score_mask, best_class)
    return _1cm

def process_tissue(ort_session, image):
    result = onnx_prediction(image, ort_session)
    return result

def segment_bbox(predictor, image, bbox):
    predictor.set_image(image)
    masks, scores, logits = predictor.predict(box=bbox, multimask_output=True)
    return masks, scores, logits

if __name__ == "__main__":
    ort_session_capsule = load_onnx_model(os.path.join("models", "capsules.onnx"))
    ort_session_tissue = load_onnx_model(os.path.join("models", "tissue.onnx"))
    image_path = os.path.join("scripts", "test.jpg")
    sam = "./sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
    sam2 = build_sam2(model_cfg, sam, device ='cpu', apply_postprocessing=False)
    predictor = SAM2ImagePredictor(sam2)

    _1cm = process_capsule(predictor, ort_session_capsule, image_path)
    results = process_tissue(ort_session_tissue, image_path)
    image_cv = cv2.imread(image_path)
    index = 0
    for cls, bboxes in results.items():
        for bbox, confidence in bboxes:
            # Convert bbox (np.float32) values to Python floats
            bbox = tuple(map(float, bbox))
            grid_segments = generate_grid_segments(bbox, _1cm, (1,1))
            visualize_grid_segments_opencv(grid_segments, image_cv, f"tmp/out_{index}.jpg")
            index += 1


    #########

    #mask_generator = SAM2AutomaticMaskGenerator(sam2)

    #original_width, original_height = image.size
    #new_width = original_width // 2
    #new_height = original_height // 2
    #scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    #image_array = np.array(scaled_image)

    #bounding_box = np.array([10, 20, 80, 90])

    #show_masks(image, masks, scores)
    #masks = mask_generator.generate(image_array)
    #mask_annotator = sv.MaskAnnotator()
    #detections = sv.Detections.from_sam(masks)
    #detections.class_id = [i for i in range(len(detections))]
    #annotated_image = mask_annotator.annotate(image_array, detections)
    #annotated_pil_image = Image.fromarray(annotated_image)
    #annotated_pil_image.save("./tmp/test.jpg")
    #########









































