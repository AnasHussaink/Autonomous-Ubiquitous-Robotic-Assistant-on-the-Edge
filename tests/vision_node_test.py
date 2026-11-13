import logging
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import pytest

from src.vision.camera import capture_and_save, detect_face_and_save

logger = logging.getLogger(__name__)


def test_camera_record_and_save_jpg(tmp_path):
  """
  
  """
  
  test_filename = "test_hardware_camera.jpg"
  
  if os.path.exists(test_filename):
    os.remove(test_filename)
    
  photo = capture_and_save(filename=test_filename)
  
  assert photo is not None
  

@patch('src.vision.camera.cv2.VideoCapture')
def test_face_detection_model(mock_video_capture, tmp_path):
  """
  Test the TF-Lite model's ability to detect faces using a static image.
  """
  
  model_name = "face_detection_front.tflite"
  model_path =  Path("models")  / model_name  
  assert model_path.exists(), f"Model not found at {model_path}"
  
  output_filename = "test_detected_output.jpg"
  
  test_image_name = "images/test_data/two_faces_test.jpg"
  test_frame = cv2.imread(test_image_name)
  assert test_frame is not None, f"Could not load test image from {test_image_name}"

  mock_cap = MagicMock()
  mock_cap.isOpened.return_value = True
  mock_cap.read.return_value = (True, test_frame)
  mock_video_capture.return_value = mock_cap
  
  frame, boxes = detect_face_and_save(
    model_path=str(model_path),
    filename=output_filename,
    output_folder=tmp_path
    )
  
  assert len(boxes) > 0, "Expected model to return bounding boxes"
  assert len(boxes) == 2, f"Expected exactly 2 faces, but model returned {len(boxes)}"

  expected_saved_file = tmp_path / output_filename
  assert expected_saved_file.exists()
