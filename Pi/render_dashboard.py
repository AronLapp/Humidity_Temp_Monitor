import json
from collections import deque
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter

LOGFILE = Path("/home/pi/Humidity_Temp_Monitor/measurements.log")
OUTDIR  = Path("/home/pi/Humidity_Temp_Monitor/www")
OUTDIR.mkdir(exist_ok=True)

MAX_LINES = 2000

def load_data():
    if not LOGFILE.exists():
        return pd.DataFrame(columns=["ts", "node", "temp", "hum", "risk"])

    lines = deque(maxlen=MAX_LINES)
    with LOGFILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    rows = []
    for line in lines:
        try:
            o = json.loads(line)
            rows.append({
                "ts":   datetime.fromisoformat(o["ts_local"]).replace(tzinfo=None),
                "node": o["node"],
                "temp": o["temp"],
                "hum":  o["hum"],
                "risk": o.get("risk", 0.0),
            })
        except Exception:
            pass

    if not rows:
        return pd.DataFrame(columns=["ts", "node", "temp", "hum", "risk"])

    df = pd.DataFrame(rows)
    return df.sort_values("ts")


def plot_all(df):
    if df.empty:
        return

    nodes = sorted(df["node"].unique())

    plots = [
        ("temp", "temp.png", "Temperature (°C)"),
        ("hum",  "hum.png",  "Humidity (%)"),
        ("risk", "risk.png", "Risk (0..1)"),
    ]

    for col, fname, ylabel in plots:
        fig, ax = plt.subplots(figsize=(8, 3))

        for node in nodes:
            dfn = df[df["node"] == node]
            ax.plot(dfn["ts"], dfn[col], label=node)

        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, linestyle=":", linewidth=0.5)

        locator = AutoDateLocator()
        formatter = DateFormatter("%m-%d %H:%M")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        fig.autofmt_xdate()

        fig.savefig(OUTDIR / fname)
        plt.close(fig)


def write_html():
    html = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Air monitoring</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    img { max-width: 100%%; }
  </style>
</head>
<body>
  <h1>Air monitoring</h1>
  <p>Generated on: %s</p>
  <h2>Temperature</h2>
  <img src="temp.png" alt="Temperature">
  <h2>Humidity</h2>
  <img src="hum.png" alt="Humidity">
  <h2>Risk</h2>
  <img src="risk.png" alt="Risk">
</body>
</html>
""" % datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    (OUTDIR / "index.html").write_text(html, encoding="utf-8")

def main():
    while True:
        df = load_data()
        plot_all(df)
        write_html()
        time.sleep(60)

if __name__ == "__main__":
    main()
