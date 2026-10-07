"""Giả lập ESP32 publish dữ liệu cảm biến lên MQTT (dùng khi Wokwi không kết nối được)."""
import json
import time
import random
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "iot/class/lab2/esp32-01/data"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

temp = 28.0
hum = 65.0

print("Dang gia lap ESP32 publish du lieu... (Ctrl+C de dung)")
i = 0
while True:
    i += 1
    # dao dong nhe quanh gia tri trung binh
    temp += random.uniform(-0.3, 0.3)
    hum += random.uniform(-0.5, 0.5)
    light = random.randint(300, 600)

    # thinh thoang tao outlier de minh hoa phat hien bat thuong
    if i % 15 == 0:
        temp += random.choice([-8, 8])

    data = {
        "device_id": "esp32-01",
        "ts": time.time(),
        "temperature": round(temp, 1),
        "humidity": round(hum, 1),
        "light": light,
    }
    client.publish(TOPIC, json.dumps(data))
    print(f"Published: {data}")
    time.sleep(5)