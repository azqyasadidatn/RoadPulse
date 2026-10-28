import json
import math
import ssl
import threading
from collections import defaultdict, deque

from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt


# =========================
# KONFIGURASI
# =========================
PROJECT_ID = "roadpulse_kelompok_01"
MQTT_HOST = "broker.hivemq.com"
MQTT_PORT = 8883
TOPIC_SUB = f"roadpulse/{PROJECT_ID}/edge/+/telemetry"

WINDOW_SIZE = 10

app = Flask(__name__)

road_reports = []
sample_windows = defaultdict(list)
data_lock = threading.Lock()


def classify_road(accel_rms, gyro_rms):
    # Tingkat keparahan accelerometer
    if accel_rms < 0.3:
        accel_level = 0
    elif accel_rms < 1.0:
        accel_level = 1
    elif accel_rms < 2.0:
        accel_level = 2
    else:
        accel_level = 3

    # Tingkat keparahan gyroscope
    # Ambang awal jika rotationRate dari browser menggunakan derajat/detik.
    if gyro_rms < 15:
        gyro_level = 0
    elif gyro_rms < 45:
        gyro_level = 1
    elif gyro_rms < 90:
        gyro_level = 2
    else:
        gyro_level = 3

    # Ambil tingkat keparahan tertinggi dari kedua sensor.
    severity = max(accel_level, gyro_level)

    conditions = ["Normal", "Bumpy", "Pothole", "Impact"]
    return conditions[severity]


# =========================
# MQTT CALLBACKS
# =========================
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Status koneksi: {reason_code}")

    if reason_code == 0:
        client.subscribe(TOPIC_SUB, qos=1)
        print(f"[MQTT] Subscribe: {TOPIC_SUB}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        acceleration = payload.get("acceleration", {})
        gyroscope = payload.get("gyroscope", {})
        location = payload.get("location", {})
        device_id = payload.get("device_id", "unknown")

        # Pastikan ketiga sumbu akselerometer tersedia.
        axes = [
            float(acceleration["x"]),
            float(acceleration["y"]),
            float(acceleration["z"]),
        ]

        if not all(math.isfinite(v) for v in axes):
            raise ValueError("Nilai accelerometer tidak valid")

        gyro_axes = [
            float(gyroscope.get("x", 0)),
            float(gyroscope.get("y", 0)),
            float(gyroscope.get("z", 0)),
        ]

        if not all(math.isfinite(v) for v in gyro_axes):
            raise ValueError("Nilai gyroscope tidak valid")

        lat = float(location["lat"])
        lng = float(location["lng"])

        if not (
            math.isfinite(lat)
            and math.isfinite(lng)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            raise ValueError("Koordinat GPS tidak valid")

        # Browser mengirim accelerationIncludingGravity dalam m/s².
        # Kurangi gravitasi dari besar vektor sebagai pendekatan awal.
        magnitude = math.sqrt(sum(v * v for v in axes))
        gravity_error = magnitude - 9.80665

        sample = {
            "timestamp": payload.get("timestamp"),
            "gravity_error": gravity_error,
            "gyro_magnitude": math.sqrt(
                sum(v * v for v in gyro_axes)
            ),
            "lat": lat,
            "lng": lng,
            "accuracy": location.get("accuracy"),
            "acceleration": acceleration,
            "gyroscope": gyroscope,
        }

        with data_lock:
            window = sample_windows[device_id]
            window.append(sample)

            if len(window) < WINDOW_SIZE:
                return

            # Proses satu jendela sampel.
            batch = window[:WINDOW_SIZE]
            del window[:WINDOW_SIZE]

            accel_rms = math.sqrt(
                sum(s["gravity_error"] ** 2 for s in batch)
                / len(batch)
            )

            gyro_rms = math.sqrt(
                sum(s["gyro_magnitude"] ** 2 for s in batch)
                / len(batch)
            )

            latest = batch[-1]
            condition = classify_road(accel_rms, gyro_rms)

            report = {
                "device_id": device_id,
                "timestamp": latest["timestamp"],
                "lat": latest["lat"],
                "lng": latest["lng"],
                "accuracy": latest["accuracy"],
                "condition": condition,
                "accel_rms": round(accel_rms, 4),
                "gyro_rms": round(gyro_rms, 4),
                "acceleration": latest["acceleration"],
                "gyroscope": latest["gyroscope"],
            }

            road_reports.append(report)

            if len(road_reports) > 100:
                road_reports.pop(0)

        print(
            f"[DATA DIPROSES] {device_id} | "
            f"RMS={accel_rms:.4f} | "
            f"Gyro RMS={gyro_rms:.4f} | "
            f"{condition} | GPS=({lat}, {lng})"
        )

    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        print(f"[DATA ERROR] {e}")
    except Exception as e:
        print(f"[ERROR] Gagal memproses pesan: {e}")


# =========================
# MQTT CLIENT
# =========================
mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="server_dashboard",
)

mqtt_client.tls_set()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()


# =========================
# ROUTE WEB
# =========================
@app.route("/")
def index():
    return render_template("dashboard.html", project_id=PROJECT_ID)


@app.route("/mobile")
def mobile():
    return render_template("mobile.html", project_id=PROJECT_ID)


@app.route("/api/data")
def get_data():
    with data_lock:
        return jsonify(list(road_reports))


if __name__ == "__main__":
    # Hindari Flask reloader membuat MQTT client berjalan dua kali.
    app.run(host="0.0.0.0", port=5000, debug=False)
