import sys
from ultralytics import YOLO

# Load a small but accurate model (downloaded on first use)
model = YOLO("./yolov8n.pt")  # you can use 'yolov8s.pt' for better accuracy but slower

def containsHuman(image_path: str, conf_threshold: float = 0.35) -> bool:
    # Run inference
    results = model.predict(image_path, conf=conf_threshold, verbose=False)

    # YOLO uses COCO class IDs; 0 = 'person'
    PERSON_CLASS_ID = 0

    for r in results:
        if r.boxes is None:
            continue

        for cls_id, score in zip(r.boxes.cls, r.boxes.conf):
            if int(cls_id.item()) == PERSON_CLASS_ID and float(score.item()) >= conf_threshold:
                return True
            
        return False



if __name__ == "__main__":
    # path = "/home/matthew/repos/smart-task-scheduler/local/tests/tasks/detect-human/tests/people2.jpg"
    # path = "/home/matthew/repos/smart-task-scheduler/local/tests/tasks/detect-human/without-human/5.jpg"
    path = "/home/matthew/repos/smart-task-scheduler/local/tests/tasks/detect-human/with-human/5.jpg"
    # path = "/home/matthew/repos/smart-task-scheduler/local/tests/tasks/detect-human/tests/people2.jpg"
    # path = "/home/matthew/repos/smart-task-scheduler/local/tests/tasks/detect-human/tests/people2.jpg"

    containsHuman(path)

