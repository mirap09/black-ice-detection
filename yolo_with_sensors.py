import cv2
import board
import busio
import adafruit_sht31d
from ultralytics import YOLO

# ==========================
# SENSOR SETUP (SHT-30)
# ==========================
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_sht31d.SHT31D(i2c)

# ==========================
# YOLO SETUP
# ==========================
model = YOLO("models/checkpoints/black_ice/weights/best.pt")

# ==========================
# CAMERA SETUP
# ==========================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera not accessible")
    exit()

print("YOLO + Temperature + Humidity system running")
print("Press 'q' to quit")

# ==========================
# MAIN LOOP
# ==========================
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- YOLO inference ---
        results = model(frame, verbose=False)
        detections = len(results[0].boxes) if results[0].boxes else 0

        # --- Sensor readings ---
        temperature = sensor.temperature
        humidity = sensor.relative_humidity

        # --- Print data with class info ---
        if results[0].boxes:
            classes = results[0].boxes.cls.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_info = ", ".join([f"Class {int(c)} ({conf:.2f})" for c, conf in zip(classes, confidences)])
            print(
                f"Detections: {detections} [{class_info}] | "
                f"Temp: {temperature:.2f} °C | "
                f"Humidity: {humidity:.2f} %"
            )
        else:
            print(
                f"Detections: {detections} | "
                f"Temp: {temperature:.2f} °C | "
                f"Humidity: {humidity:.2f} %"
            )

        # --- Display ---
        annotated = results[0].plot()
        cv2.imshow("YOLO + Environment", annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    print("Shutting down cleanly.")
    cap.release()
    cv2.destroyAllWindows()
