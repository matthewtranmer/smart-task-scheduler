import io
import numpy as np
from PIL import Image
from tflite_runtime.interpreter import Interpreter
import multiprocessing as mp
import os, sys
from contextlib import contextmanager

@contextmanager
def suppress_stderr_fd():
    """
    Temporarily redirect the OS-level stderr (fd 2) to /dev/null.
    This catches C/C++ library prints like TFLite's XNNPACK info.
    """
    stderr_fd = sys.stderr.fileno()

    # Save a copy of the current stderr fd
    saved_stderr_fd = os.dup(stderr_fd)

    try:
        # Open /dev/null and dup it over stderr
        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), stderr_fd)
        yield
    finally:
        # Restore original stderr
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(saved_stderr_fd)

class PersonDetector:
    def __init__(
            self,
            model_path,
            labels_path,
            score_threshold=0.4
        ):
        self.score_threshold = score_threshold

        # Load labels (one per line, first should be "person")
        with open(labels_path, "r") as f:
            self.labels = [l.strip() for l in f.readlines()]

        # Typically, label 0 == "person" for COCO TFLite models
        self.person_class_id = self.labels.index("person")

        with suppress_stderr_fd():
            self.interpreter = Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        in_shape = self.input_details[0]["shape"]  # [1, H, W, 3]
        self.height, self.width = int(in_shape[1]), int(in_shape[2])

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((self.width, self.height))

        # For uint8 model: values must be 0-255, dtype=uint8
        x = np.asarray(img, dtype=np.uint8)
        x = np.expand_dims(x, axis=0)  # [1, H, W, 3]
        return x

    def image_has_person(self, image_bytes: bytes) -> bool:
        input_tensor = self._preprocess(image_bytes)

        self.interpreter.set_tensor(self.input_details[0]["index"], input_tensor)
        self.interpreter.invoke()

        classes = self.interpreter.get_tensor(self.output_details[1]["index"])[0]    # [N]
        scores = self.interpreter.get_tensor(self.output_details[2]["index"])[0]     # [N]

        for cls_id, score in zip(classes, scores):
            if score < self.score_threshold:
                continue

            # Some models return float class IDs, so cast to int
            cls_id = int(cls_id)

            if cls_id == self.person_class_id:
                return True

        return False
    
def main(image_bytes: bytes) -> bool:
    detector = PersonDetector(
        model_path="/app/src/tasks/detect_human/efficientdet_lite0.tflite",
        labels_path="/app/src/tasks/detect_human/labelmap.txt",
        score_threshold=0.4,
    )

    return detector.image_has_person(image_bytes)
    
def detectHuman(image_bytes: bytes):
    with mp.Pool(1) as pool:
        response = pool.apply(main, args=(image_bytes,))

    return response