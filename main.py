from flask import Flask, jsonify, render_template, request
from sql import get_lastdata, get_summary, get_conn
from mqtt import publish_led_command

app = Flask(__name__)


@app.route("/")
def home():
        return render_template("index.html")


@app.route("/api/summary")
def api_summary():
        data = get_summary()
        return jsonify(data)


@app.route("/json-summary")
def json_summary_page():
        return render_template("json_summary.html")


@app.route("/api/sensors/latest")
def api_latest():
        row = get_lastdata()
        if not row:
                return jsonify({}), 200
        # tuple: (id, suhu, humidity, lux, timestamp)
        payload = {
                "id": row[0],
                "suhu": float(row[1]),
                "humidity": float(row[2]),
                "lux": int(row[3]),
                "timestamp": row[4].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row[4], "strftime") else str(row[4]),
        }
        return jsonify(payload)


@app.route("/api/sensors")
def api_list():
        try:
                limit = int(request.args.get("limit", 50))
        except Exception:
                limit = 50
        if limit < 1:
                limit = 1
        if limit > 500:
                limit = 500
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, suhu, humidity, lux, timestamp FROM data_sensor ORDER BY id DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        result = []
        for r in rows:
                result.append({
                        "id": r[0],
                        "suhu": float(r[1]),
                        "humidity": float(r[2]),
                        "lux": int(r[3]),
                        "timestamp": r[4].strftime("%Y-%m-%d %H:%M:%S") if hasattr(r[4],"strftime") else str(r[4])
                })
        return jsonify(result)


@app.route("/health")
def health():
        return {"ok": True}

@app.route("/api/led", methods=["POST"])
def api_led():
        payload = request.get_json(silent=True) or {}
        state = str(payload.get("state", "")).lower()
        if state not in ("on", "off"):
                return jsonify({"error": "state harus 'on' atau 'off'"}), 400
        try:
                publish_led_command(state)
                return jsonify({"status": "sent", "state": state}), 202
        except Exception as e:
                return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
        app.run(debug=True)