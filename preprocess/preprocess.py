"""Preprocessor: doc raw -> lam sach -> outlier -> resample -> features -> ghi processed."""
import logging
from pathlib import Path

import yaml
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("preprocess")

influx = InfluxDBClient(
    url=cfg["influxdb"]["url"],
    token=cfg["influxdb"]["token"],
    org=cfg["influxdb"]["org"],
)
query_api = influx.query_api()
write_api = influx.write_api(write_options=SYNCHRONOUS)


def load_raw() -> pd.DataFrame:
    flux = f'''
    from(bucket:"{cfg["influxdb"]["bucket_raw"]}")
      |> range(start: {cfg["preprocess"]["query_range"]})
      |> filter(fn: (r) => r._measurement == "raw_sensor")
      |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity" or r._field == "light")
    '''
    df = query_api.query_data_frame(flux)
    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()
    if df.empty:
        return df
    df = df.pivot_table(index="_time", columns="_field", values="_value")
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    log.info(f"Missing truoc xu ly: {df.isna().sum().to_dict()}")
    df = df.interpolate(method="time").ffill().bfill()
    return df


def detect_outliers_iqr(df: pd.DataFrame, cols, factor: float) -> pd.DataFrame:
    for col in cols:
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        lo, hi = Q1 - factor * IQR, Q3 + factor * IQR
        mask = (df[col] < lo) | (df[col] > hi)
        df[f"{col}_anomaly"] = mask.astype(int)
        df.loc[mask, col] = np.nan
        log.info(f"{col}: {mask.sum()} outlier | nguong [{lo:.2f}, {hi:.2f}]")
    return df


def add_features(df: pd.DataFrame, window: int) -> pd.DataFrame:
    df["temp_roll_mean"] = df["temperature"].rolling(window).mean()
    df["temp_delta"] = df["temperature"].diff()
    df["humidity_roll_mean"] = df["humidity"].rolling(window).mean()
    return df


def normalize(df: pd.DataFrame, cols) -> pd.DataFrame:
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[cols])
    for i, col in enumerate(cols):
        df[f"{col}_norm"] = scaled[:, i]
    return df


def write_processed(df: pd.DataFrame):
    bucket = cfg["influxdb"]["bucket_processed"]
    points = []
    for ts, row in df.iterrows():
        def f(v):
            return float(v) if pd.notna(v) else 0.0
        p = (
            Point("processed_sensor")
            .field("temperature", f(row.get("temperature")))
            .field("humidity", f(row.get("humidity")))
            .field("light", f(row.get("light")))
            .field("temp_roll_mean", f(row.get("temp_roll_mean")))
            .field("temp_delta", f(row.get("temp_delta")))
            .field("humidity_roll_mean", f(row.get("humidity_roll_mean")))
            .field("temperature_norm", f(row.get("temperature_norm")))
            .field("humidity_norm", f(row.get("humidity_norm")))
            .field("light_norm", f(row.get("light_norm")))
            .field("temperature_anomaly", int(row.get("temperature_anomaly", 0)))
            .field("humidity_anomaly", int(row.get("humidity_anomaly", 0)))
            .field("light_anomaly", int(row.get("light_anomaly", 0)))
            .time(ts.to_pydatetime())
        )
        points.append(p)
    if points:
        write_api.write(bucket=bucket, record=points)
        log.info(f"Da ghi {len(points)} ban ghi vao bucket {bucket}")
    else:
        log.warning("Khong co ban ghi nao de ghi.")


def main():
    log.info("Bat dau tien xu ly...")
    df = load_raw()
    if df.empty:
        log.warning("Khong co du lieu raw. Hay chay collector truoc.")
        return

    log.info(f"Da load {len(df)} ban ghi raw")

    interval = cfg["preprocess"]["resample_interval"]
    df = df.resample(interval).mean()
    log.info(f"Resample {interval}: con {len(df)} ban ghi")

    df = handle_missing(df)

    df = detect_outliers_iqr(
        df,
        ["temperature", "humidity", "light"],
        cfg["preprocess"]["iqr_factor"],
    )
    df = handle_missing(df)

    df = add_features(df, cfg["preprocess"]["rolling_window"])
    df = normalize(df, ["temperature", "humidity", "light"])

    write_processed(df)
    log.info("Hoan tat tien xu ly.")


if __name__ == "__main__":
    main()
