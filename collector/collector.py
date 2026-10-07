"""Collector: Subscribe MQTT -> validate -> write InfluxDB raw bucket."""
import json
import time
import logging
from pathlib import Path

import yaml
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Load config ---
ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("collector")

# --- InfluxDB ---
influx = InfluxDBClient(
    url=cfg["influxdb"]["url"],
    token=cfg["influxdb"]["token"],
    org=cfg["influxdb"]["org"],
)
write_api = influx.write_api(write_options=SYNCHRONOUS)


def validate(data: dict):
    v = cfg["validation"]
    required = ["device_id", "ts", "temperature", "humidity", "light"]
    for k in required:
        if k not in data:
            return False, f"thieu field {k}"
    try:
        t = float(data["temperature"])
        h = float(data["humidity"])
        l = float(data["light"])
        ts = float(data["ts"])
    except (TypeError, ValueError):
        return False, "kieu du lieu sai"
    if not (v["temp_min"] <= t <= v["temp_max"]):
        return False, f"temperature ngoai khoang: {t}"
    if not (v["humidity_min"] <= h <= v["humidity_max"]):
        return False, f"humidity ngoai khoang: {h}"
    if l < v["light_min"]:
        return False, f"light am: {l}"
    if abs(time.time() - ts) > v["max_clock_skew_sec"]:
        return False, f"clock skew qua lon: {abs(time.time() - ts):.1f}s"
    return True, ""


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("Da ket noi MQTT broker")
        client.subscribe(cfg["mqtt"]["topic"], qos=1)
        log.info(f"Subscribe topic: {cfg['mqtt']['topic']}")
    else:
        log.error(f"Ket noi MQTT that bai, rc={rc}")


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8")
        data = json.loads(raw)
    except Exception as e:
        log.warning(f"Payload khong phai JSON hop le: {e} | raw={msg.payload[:80]}")
        return

    ok, reason = validate(data)
    if not ok:
        log.warning(f"Du lieu khong hop le: {reason} | data={data}")
        return

    receive_ts = time.time()
    latency = receive_ts - float(data["ts"])

    try:
        point = (
            Point("raw_sensor")
            .tag("device_id", str(data["device_id"]))
            .field("temperature", float(data["temperature"]))
            .field("humidity", float(data["humidity"]))
            .field("light", float(data["light"]))
            .field("latency_sec", float(latency))
            .time(int(receive_ts * 1e9))
        )
        write_api.write(bucket=cfg["influxdb"]["bucket_raw"], record=point)
        log.info(
            f"OK | device={data['device_id']} | T={data['temperature']} "
            f"H={data['humidity']} L={data['light']} | latency={latency:.3f}s"
        )
    except Exception as e:
        log.error(f"Ghi InfluxDB that bai: {e}")


def main():
    client = mqtt.Client(
        client_id=cfg["mqtt"]["client_id"],
        protocol=mqtt.MQTTv5,
    )
    client.on_connect = on_connect
    client.on_message = on_message

    log.info(f"Dang ket noi toi MQTT {cfg['mqtt']['broker']}:{cfg['mqtt']['port']}...")
    client.connect(cfg["mqtt"]["broker"], cfg["mqtt"]["port"], 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
