import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Select
from bokeh.layouts import column
from bokeh.plotting import figure

LOGFILE = Path("/home/pi/Humidity_Temp_Monitor/measurements.log")

def load_data():
    if not LOGFILE.exists():
        return pd.DataFrame(columns=["ts", "node", "temp", "hum", "risk"])

    rows = []
    for line in LOGFILE.open():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            rows.append({
                "ts": datetime.fromisoformat(o["ts_local"].replace("Z", "+00:00")),
                "node": o["node"],
                "temp": o["temp"],
                "hum": o["hum"],
                "risk": o.get("risk", 0),
            })
        except:
            pass

    if not rows:
        return pd.DataFrame(columns=["ts", "node", "temp", "hum", "risk"])

    df = pd.DataFrame(rows)
    return df.sort_values("ts")

df_all = load_data()
nodes = sorted(df_all["node"].unique()) if not df_all.empty else ["unknown"]

node_select = Select(title="Sensor Node", value=nodes[0], options=nodes)

src_t = ColumnDataSource(data=dict(ts=[], val=[]))
src_h = ColumnDataSource(data=dict(ts=[], val=[]))
src_r = ColumnDataSource(data=dict(ts=[], val=[]))

p1 = figure(x_axis_type="datetime", height=250, title="Temperature (°C)")
p1.line("ts", "val", source=src_t)

p2 = figure(x_axis_type="datetime", height=250, title="Humidity (%)")
p2.line("ts", "val", source=src_h)

p3 = figure(x_axis_type="datetime", height=250, title="Risk (0..1)")
p3.line("ts", "val", source=src_r)

def update():
    df = load_data()
    if df.empty:
        return
    dfn = df[df["node"] == node_select.value]

    src_t.data = {"ts": dfn["ts"], "val": dfn["temp"]}
    src_h.data = {"ts": dfn["ts"], "val": dfn["hum"]}
    src_r.data = {"ts": dfn["ts"], "val": dfn["risk"]}

def change_node(attr, old, new):
    update()

node_select.on_change("value", change_node)

update()

curdoc().add_root(column(node_select, p1, p2, p3))
curdoc().title = "Air Sensor Dashboard"
curdoc().add_periodic_callback(update, 10_000)
