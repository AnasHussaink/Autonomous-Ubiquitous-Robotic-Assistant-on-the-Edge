import os
import urllib.request
import logging
from pathlib import Path

import cv2
import numpy as np
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    tflite = None

logger = logging.getLogger("VisionNode")

# Set to True while streaming from laptop, False when camera is plugged into Pi
USE_NETWORK_CAMERA = True
NETWORK_CAMERA_URL = "http://10.175.217.103:8000/snapshot"
LOCAL_FRAME_PATH = "audio_files/current_frame.jpg"


def capture_frame(output_path: str = LOCAL_FRAME_PATH) -> str:
    """Captures a single frame from the network stream or local camera."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if USE_NETWORK_CAMERA:
        try:
            urllib.request.urlretrieve(NETWORK_CAMERA_URL, output_path)
            logger.info(f"Captured frame from network camera to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to capture network frame: {e}")
            return None
    else:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open local camera at index 0")
                return None
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                cv2.imwrite(output_path, frame)
                return output_path
            return None
        except Exception as e:
            logger.error(f"Local camera capture error: {e}")
            return None


def capture_and_save(n=1, filename="capture.jpg", output_folder="images", camera_index=0, warmup_frames=5):
    """
    Capture n frames from the camera, save to output_folder,
    and return a list of frames (BGR numpy arrays).
    """
    save_dir = Path(output_folder)
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / filename

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}. Check permissions or connection.")

    for _ in range(warmup_frames):
        cap.read()

    frames = []
    for i in range(n):
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            raise RuntimeError(f"Failed to grab frame {i+1}/{n} from camera.")
        frames.append(frame)

    cap.release()
    if frames:
        cv2.imwrite(str(filepath), frames[-1])
    return frames


def detect_face_and_save(model_path: str, filename: str, output_folder: str = "images", camera_index: int = 0):
    """Capture a frame, run TFLite BlazeFace detection, filter outputs, and save."""
    if tflite is None:
        raise RuntimeError("tflite_runtime is not installed in this environment.")

    save_dir = Path(output_folder)
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / filename

    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]['shape']
    model_height, model_width = input_shape[1], input_shape[2]

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}")

    for _ in range(5):
        cap.read()

    ret, image = cap.read()
    cap.release()

    if not ret or image is None:
        raise RuntimeError("Failed to grab a frame from the camera.")

    rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    resized_frame = cv2.resize(rgb_frame, (model_width, model_height))
    input_data = np.expand_dims(resized_frame, axis=0).astype(np.float32) / 255.0

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    out1 = interpreter.get_tensor(output_details[0]['index'])
    out2 = interpreter.get_tensor(output_details[1]['index'])

    if out1.shape[-1] == 1:
        scores_tensor = out1[0]
        boxes_tensor = out2[0]
    else:
        scores_tensor = out2[0]
        boxes_tensor = out1[0]

    clipped_scores = np.clip(scores_tensor.flatten(), -10, 10)
    probabilities = 1 / (1 + np.exp(-clipped_scores))

    confidence_threshold = 0.70
    valid_indices = np.where(probabilities > confidence_threshold)[0]

    filtered_boxes = boxes_tensor[valid_indices]
    filtered_scores = probabilities[valid_indices]

    nms_boxes = []
    for box in filtered_boxes:
        nms_boxes.append([float(box[0]), float(box[1]), float(box[2]), float(box[3])])

    iou_threshold = 0.3
    final_indices = cv2.dnn.NMSBoxes(
        bboxes=nms_boxes,
        scores=filtered_scores.tolist(),
        score_threshold=confidence_threshold,
        nms_threshold=iou_threshold
    )

    final_faces = final_indices.flatten().tolist() if len(final_indices) > 0 else []

    cv2.imwrite(str(filepath), image)
    logger.info(f"Saved inference image. Detected {len(final_faces)} faces.")

    return image, final_faces