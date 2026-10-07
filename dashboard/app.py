"""Streamlit dashboard: hien thi raw + processed realtime."""
from pathlib import Path

import yaml
import pandas as pd
import streamlit as st
import plotly.express as px
from influxdb_client import InfluxDBClient
from streamlit_autorefresh import st_autorefresh

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

st.set_page_config(page_title="IoT Lab 2 Dashboard", layout="wide")
st_autorefresh(interval=5000, key="refresh")
st.title("🌡️ IoT Lab 2 – Dashboard giam sat")

client = InfluxDBClient(
    url=cfg["influxdb"]["url"],
    token=cfg["influxdb"]["token"],
    org=cfg["influxdb"]["org"],
)
query_api = client.query_api()


def query_to_df(flux: str) -> pd.DataFrame:
    df = query_api.query_data_frame(flux)
    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()
    if df.empty:
        return df
    df = df.pivot_table(index="_time", columns="_field", values="_value")
    df.index = pd.to_datetime(df.index, utc=True)
    return df.sort_index()


raw_flux = f'''
from(bucket:"{cfg["influxdb"]["bucket_raw"]}")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "raw_sensor")
'''
df_raw = query_to_df(raw_flux)

proc_flux = f'''
from(bucket:"{cfg["influxdb"]["bucket_processed"]}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "processed_sensor")
'''
df_proc = query_to_df(proc_flux)

col1, col2, col3, col4 = st.columns(4)
if not df_raw.empty:
    last = df_raw.iloc[-1]
    col1.metric("Nhiet do", f"{last.get('temperature', 0):.1f} °C")
    col2.metric("Do am", f"{last.get('humidity', 0):.1f} %")
    col3.metric("Anh sang", f"{last.get('light', 0):.0f}")
    if "latency_sec" in df_raw.columns:
        col4.metric("Latency moi nhat", f"{last.get('latency_sec', 0)*1000:.0f} ms")
else:
    st.info("Chua co du lieu raw. Hay chay collector va Wokwi simulator.")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🔵 Raw – 15 phut gan nhat")
    if not df_raw.empty:
        cols = [c for c in ["temperature", "humidity", "light"] if c in df_raw.columns]
        st.plotly_chart(px.line(df_raw, y=cols, title="Raw sensor"), use_container_width=True)
    else:
        st.write("Khong co du lieu.")

with right:
    st.subheader("🟢 Processed – 24 gio gan nhat")
    if not df_proc.empty:
        cols = [c for c in ["temperature", "temp_roll_mean"] if c in df_proc.columns]
        st.plotly_chart(px.line(df_proc, y=cols, title="Temperature vs rolling mean"), use_container_width=True)
        if "temperature_anomaly" in df_proc.columns:
            n_anom = int(df_proc["temperature_anomaly"].sum())
            st.metric("So outlier nhiet do", n_anom)
    else:
        st.write("Khong co du lieu processed. Hay chay preprocess.")

if not df_raw.empty and "latency_sec" in df_raw.columns:
    st.divider()
    st.subheader("⏱️ Phan tich do tre (end-to-end tu thiet bi -> collector)")
    lat = df_raw["latency_sec"].dropna() * 1000
    c1, c2, c3 = st.columns(3)
    c1.metric("p50", f"{lat.quantile(0.5):.0f} ms")
    c2.metric("p95", f"{lat.quantile(0.95):.0f} ms")
    c3.metric("Max", f"{lat.max():.0f} ms")

st.caption("Dashboard tu dong refresh moi 5 giay.")
