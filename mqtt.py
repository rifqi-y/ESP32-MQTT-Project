import paho.mqtt.client as mqtt
import json
import datetime
from sql import insert_data

broker = "broker.hivemq.com"
port = 1883
DATA_TOPIC = "152023003/pemiot/data"
CMD_TOPIC = "152023003/pemiot/cmd/led"  # untuk publish perintah ke device


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")
        client.subscribe(DATA_TOPIC, qos=1)
    else:
        print("MQTT connect failed rc=", rc)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        suhu = float(data.get("temperature"))
        humidity = float(data.get("humidity"))
        # Firmware mengirim 'lightlevel' dan 'datetime'
        lux = int(data.get("lightlevel"))
        ts_raw = data.get("datetime")
        try:
            # ISO timestamp dengan 'Z'
            timestamp = datetime.datetime.fromisoformat(ts_raw.replace("Z", "")) if ts_raw else None
        except Exception:
            timestamp = None
        insert_data(suhu, humidity, lux, timestamp)
        print(f"Inserted sensor data: suhu={suhu} humid={humidity} lux={lux} ts={timestamp}")
    except Exception as e:
        print("Error processing MQTT message:", e)


def publish_pump(client, state: str):
    if state not in ("on", "off"):
        raise ValueError("state harus 'on' atau 'off'")
    # Tidak dipakai untuk LED, disisakan bila butuh pompa di masa depan
    payload = json.dumps({"pump": state})
    client.publish(CMD_TOPIC, payload, qos=1)
    print("Published pump command", payload)


def publish_led_command(state: str):
    """Publikasikan perintah LED on/off menggunakan client sementara.
    Dipakai oleh endpoint Flask agar tidak perlu loop network terpisah.
    """
    if state not in ("on", "off"):
        raise ValueError("state harus 'on' atau 'off'")
    temp_client = mqtt.Client(client_id="Server_152023003_api_pub")
    temp_client.connect(broker, port, keepalive=30)
    # Kirim string sederhana sesuai firmware: ON/OFF
    payload = "ON" if state.lower() == "on" else "OFF"
    info = temp_client.publish(CMD_TOPIC, payload, qos=1)
    try:
        info.wait_for_publish()
    except Exception:
        pass
    temp_client.disconnect()


client = mqtt.Client(client_id="Server_152023003_ingestor")
client.on_connect = on_connect
client.on_message = on_message

if __name__ == "__main__":
    client.connect(broker, port, keepalive=60)
    client.loop_forever()