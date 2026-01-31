import time
import board
import busio
import adafruit_sht31d

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_sht31d.SHT31D(i2c)

print("Reading SHT-30 sensor...")

while True:
    temperature = sensor.temperature
    humidity = sensor.relative_humidity

    print(f"Temperature: {temperature:.2f} °C")
    print(f"Humidity: {humidity:.2f} %")
    print("-" * 30)

    time.sleep(2)
