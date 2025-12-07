from flask import Flask, request
from datetime import datetime
from zoneinfo import ZoneInfo
import json, hashlib, os, math

app = Flask(__name__)

TZ = ZoneInfo("Europe/Berlin")
LOGFILE = "measurements.log"
LAST_HASHFILE = "last_hash.txt"

def load_last_hash():
    if not os.path.exists(LAST_HASHFILE):
        return ""
    return open(LAST_HASHFILE).read().strip()

def save_last_hash(h):
    with open(LAST_HASHFILE, "w") as f:
        f.write(h)

# caluclate dewpoint using magnus formula
def dew_point(temp_c: float, rh: float) -> float:
    if rh <= 0:
        return -100.0
    a = 17.62
    b = 243.12
    gamma = (a * temp_c / (b + temp_c)) + math.log(rh / 100.0)
    return (b * gamma) / (a - gamma)

# approximate risk of mould based on temp and relative humidity
# < 55% humidity -> 0
# delta t = t - dewpoint
# delta t > 5 °C -> 0
# detla t <= 1°C -> 1
# between: linear

def risk(temp, hum):

    if hum < 55:
        return 0.0
    Td = dew_point(temp, hum)
    delta = temp - Td

    if delta > 5.0:
        return 0.0
    if delta <= 1.0:
        return 1.0
    
    return (5.0 - delta) / (5.0 - 1.0)

def humidity_attention(hum: float) -> float:
    # 0 bis 1, ab 55 % langsam ansteigend
    if hum <= 55:
        return 0.0
    if hum >= 75:
        return 1.0
    return (hum - 55.0) / (75.0 - 55.0)


@app.route("/measurements", methods=["POST"])
def measurements():
    data = request.get_json(force=True)
    ts_utc   = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).isoformat()
    ts_local = datetime.now(TZ).isoformat()
    r = risk(float(data["temp"]), float(data["hum"]))
    att = humidity_attention(float(data["hum"]))

    last_hash = load_last_hash()

    payload = {
        "ts_utc": ts_utc,
        "ts_local": ts_local,
        "node": data.get("node", "unknown"),
        "temp": float(data["temp"]),
        "hum": float(data["hum"]),
        "press": float(data["press"]),
        "risk": r,
        "attention": att,
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
