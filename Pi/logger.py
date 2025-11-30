from flask import Flask, request
from datetime import datetime
import json, hashlib, os

app = Flask(__name__)

LOGFILE = "measurements.log"
LAST_HASHFILE = "last_hash.txt"

def load_last_hash():
    if not os.path.exists(LAST_HASHFILE):
        return ""
    return open(LAST_HASHFILE).read().strip()

def save_last_hash(h):
    with open(LAST_HASHFILE, "w") as f:
        f.write(h)

def risk(temp, hum):
    if hum < 60:
        return 0.0
    if hum > 85:
        hum = 85
    return (hum - 60) / 25.0  # 0..1

@app.route("/measurements", methods=["POST"])
def measurements():
    data = request.get_json(force=True)
    ts = datetime.utcnow().isoformat() + "Z"

    r = risk(float(data["temp"]), float(data["hum"]))

    last_hash = load_last_hash()

    payload = {
        "ts": ts,
        "node": data.get("node", "unknown"),
        "temp": float(data["temp"]),
        "hum": float(data["hum"]),
        "press": float(data["press"]),
        "risk": r,
        "prev_hash": last_hash,
    }

    line = json.dumps(payload, ensure_ascii=False)
    h = hashlib.sha256(line.encode("utf-8")).hexdigest()
    payload["hash"] = h

    with open(LOGFILE, "a") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    save_last_hash(h)

    return "OK\n", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
