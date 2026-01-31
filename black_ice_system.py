from ultralytics import YOLO
import cv2
import board
import adafruit_sht31d
import lgpio
import time

# ---------------- LED SETUP (Pi 5 compatible) ----------------
LED_PIN = 17  # BCM numbering
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, LED_PIN, 0)

# ---------------- SENSOR SETUP ----------------
i2c = board.I2C()
sensor = adafruit_sht31d.SHT31D(i2c)

# ---------------- YOLO SETUP ----------------
model = YOLO("yolov8s.pt")
cap = cv2.VideoCapture(0)

CONF_THRESHOLD = 0.4

print("Black Ice Detection System Running (press Q to quit)")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Camera not accessible")
            break

        # YOLO inference
        results = model(frame, conf=CONF_THRESHOLD, verbose=False)
        detections = len(results[0].boxes)

        # Sensor readings
        temp_c = sensor.temperature
        humidity = sensor.relative_humidity

        # -------- BLACK ICE DECISION LOGIC --------
        black_ice_risk = (
            temp_c <= 3.0 and
            humidity >= 80.0 and
            detections > 0
        )

        # LED control
        lgpio.gpio_write(h, LED_PIN, 1 if black_ice_risk else 0)

        # Console output (for testing + logging)
        print(
            f"Detections: {detections} | "
            f"Temp: {temp_c:.2f} °C | "
            f"Humidity: {humidity:.2f} % | "
            f"RISK: {black_ice_risk}"
        )

        # Display annotated frame
        annotated = results[0].plot()
        cv2.imshow("Black Ice Detection", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.05)

finally:
    cap.release()
    cv2.destroyAllWindows()
    lgpio.gpiochip_close(h)

