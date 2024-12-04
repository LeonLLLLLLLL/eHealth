import logging
import cv2
import numpy as np
import onnxruntime
import time
from super_gradients.training.utils.media.image import load_image

# Initialize logger
logger = logging.getLogger(__name__)

def load_onnx_model(onnx_path):
    """
    Loads an ONNX model.

    @param onnx_path: Path to the ONNX model file.
    @return: ONNX inference session if loaded successfully, None otherwise.
    """
    logger.info(f"Loading ONNX model from path: {onnx_path}")
    try:
        session = onnxruntime.InferenceSession(
            onnx_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        logger.info(f"ONNX model loaded successfully: {onnx_path}")
        return session
    except Exception as e:
        logger.error(f"Failed to load ONNX model from {onnx_path}: {str(e)}")
        return None

def onnx_prediction(input_image_path, session):
    """
    Predicts using the ONNX model and returns scaled bounding boxes with confidence scores grouped by class.

    @param input_image_path: Path to the input image.
    @param session: The ONNX inference session for prediction.
    @return: A dictionary where keys are class IDs and values are lists of tuples (bounding box, confidence score).
    """
    try:
        logger.info(f"Predicting Image: {input_image_path}")
        class_bboxes = {}

        # Load the original image
        image = load_image(input_image_path)
        original_height, original_width = image.shape[:2]

        # Resize image to 640x640 for the model
        resized_image = cv2.resize(image, (640, 640))
        image_bchw = np.transpose(np.expand_dims(resized_image, 0), (0, 3, 1, 2))

        inputs = [o.name for o in session.get_inputs()]
        outputs = [o.name for o in session.get_outputs()]

        start = time.perf_counter()
        result = session.run(outputs, {inputs[0]: image_bchw})
        end = time.perf_counter()
        logger.info(f"Prediction time: {end-start} ms")

        flat_predictions = result[0]

        # Scaling factors
        scale_x = original_width / 640
        scale_y = original_height / 640

        # Post-process predictions and scale bbox coordinates
        for _, x_min, y_min, x_max, y_max, confidence, class_id in flat_predictions:
            class_id = int(class_id)
            logger.info(f"Detected object with class_id={class_id}, confidence={confidence}, "
                        f"x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")

            # Scale the coordinates back to the original image size
            x_min_scaled = x_min * scale_x
            y_min_scaled = y_min * scale_y
            x_max_scaled = x_max * scale_x
            y_max_scaled = y_max * scale_y

            bbox = (x_min_scaled, y_min_scaled, x_max_scaled, y_max_scaled)
            bbox_with_confidence = (bbox, confidence)

            # Initialize the class in the dictionary if not already present
            if class_id not in class_bboxes:
                class_bboxes[class_id] = []

            # Append the bounding box with confidence score to the corresponding class
            class_bboxes[class_id].append(bbox_with_confidence)

        return class_bboxes

    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        return {}

def draw_bboxes(image_path, class_predictions, output_path, class_labels=None):
    """
    Draws bounding boxes and optional labels on the image and saves it.

    @param image_path: Path to the input image.
    @param class_predictions: Dictionary with class IDs as keys and lists of (bbox, confidence) tuples as values.
    @param output_path: The path to save the output image with bounding boxes.
    @param class_labels: Optional dictionary with class IDs as keys and class names as values.
    @return: Image with drawn bounding boxes and labels.
    """
    # Load the original image
    image = load_image(image_path)

    # Make the image writable by creating a copy
    image = np.copy(image)

    # Define colors for each class in BGR format
    colors = {
        class_id: (np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256))
        for class_id in class_predictions
    }

    for class_id, bboxes in class_predictions.items():
        label = class_labels.get(class_id, f"Class {class_id}") if class_labels else f"Class {class_id}"
        color = colors[class_id]  # Color in BGR format

        for (bbox, confidence) in bboxes:
            x_min, y_min, x_max, y_max = map(int, bbox)

            # Draw the rectangle
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)

            # Draw the label with confidence score
            label_text = f"{label}: {confidence:.2f}"
            text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            text_x = x_min
            text_y = y_min - 10 if y_min - 10 > 10 else y_min + 10

            cv2.rectangle(
                image,
                (text_x, text_y - text_size[1] - 2),
                (text_x + text_size[0], text_y + 2),
                color,
                -1
            )
            cv2.putText(image, label_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Save the image with bounding boxes
    cv2.imwrite(output_path, image)
    logger.info(f"Image saved to {output_path}")

    return image


