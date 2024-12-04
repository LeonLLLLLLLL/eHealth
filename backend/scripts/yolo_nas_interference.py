from super_gradients.training import models

def load_yolo_model(model_type, num_classes, checkpoint_path):
    """
    Loads a YOLO model.

    @param model_type: The type of YOLO model to load.
    @param num_classes: Number of classes for the model.
    @param checkpoint_path: Path to the checkpoint file.
    @return: Model object if loaded successfully, None otherwise.
    """
    try:
        model = models.get(
            model_type,
            num_classes=num_classes,
            checkpoint_path=checkpoint_path
        )
        return model
    except Exception as e:
        return None

def yolo_prediction(input_directory, model, conf=0.5, output_directory="", save=False):
    """
    Predicts using the YOLO model.

    @param input_directory: Path to the input images.
    @param model: The YOLO model for prediction.
    @param conf: Confidence threshold for predictions. Defaults to 0.5.
    @param output_directory: Directory to save prediction results. Defaults to "".
    @param save: Flag to save prediction results. Defaults to False.
    @return: Prediction results if successful, None otherwise.
    """
    try:
        result = model.predict(input_directory, conf=conf)
        if save:
            result.save(output_directory, box_thickness=1)
        return result
    except Exception as e:
        return None
