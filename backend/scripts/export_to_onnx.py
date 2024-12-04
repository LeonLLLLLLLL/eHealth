from super_gradients.common.object_names import Models
from super_gradients.training import models
from super_gradients.conversion import DetectionOutputFormatMode
from super_gradients.conversion.conversion_enums import ExportQuantizationMode
from super_gradients.conversion import ExportTargetBackend
import os

def load_yolo_model(model_type, num_classes, checkpoint_path):
    model = models.get(
        model_type,
        num_classes=num_classes,
        checkpoint_path=checkpoint_path
    )
    return model

model = load_yolo_model("yolo_nas_l", 2, os.path.abspath("models/capsules.pth"))

export_result = model.export(
    "capsules.onnx",
    confidence_threshold = 0.5,
    nms_threshold = 0.5,
    num_pre_nms_predictions = 100,
    max_predictions_per_image = 100,
    output_predictions_format = DetectionOutputFormatMode.FLAT_FORMAT,
    #engine=ExportTargetBackend.TENSORRT
)


