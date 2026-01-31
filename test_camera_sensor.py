from ultralytics import YOLO
import cv2
import board
import adafruit_sht31d
import time

i2c = board.I2C()
sensor = adafruit_sht31d.SHT31D(i2c)
 
model = YOLO("yolov8s.pt")
cap = cv2.VideoCapture(0)

print("Testing camera + sensor (press Q to quit)")

while True:
	ret, frame = cap.read()
	if not ret:
		print("error:Camera not accessible")
		break
	results = model(frame, conf=0.4, verbose=False)
	detections = len(results[0].boxes)
	temp_c = sensor.temperature
	humidity = sensor.relative_humidity

	print(
		f"Detection: {detections} | "
		f"Temp: {temp_c:.2f} degrees C | "
		f"Humidity: {humidity:.2f} %"
	)

	annotated = results[0].plot()
	cv2.imshow("Camera + Sensor Test", annotated)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

	time.sleep(0.1)

cap.release()
cv2.destroyAllWindows()
