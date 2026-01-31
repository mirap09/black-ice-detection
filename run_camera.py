from ultralytics import YOLO
import cv2
import time

model = YOLO("yolov8s.pt")

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
time.sleep(1)

if not cap.isOpened():
    print("ERROR: Camera not accessible")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    results = model(frame, imgsz=416)
    annotated = results[0].plot()

    cv2.imshow("Black Ice Detection (NIR)", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

