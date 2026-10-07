---
title: "Báo cáo Bài thực hành số 2 – Thu thập, lưu trữ và tiền xử lý dữ liệu IoT"
author: "Họ và tên – MSSV"
date: "2026"
---

# 1. Sơ đồ kiến trúc hệ thống

![Kiến trúc](images/architecture.png)

Mô tả luồng dữ liệu: ESP32 (mô phỏng Wokwi) → MQTT Broker (Mosquitto) → Collector (Python) →
InfluxDB (bucket raw) → Preprocessor (Python) → InfluxDB (bucket processed) → Dashboard (Streamlit).

# 2. Mô tả schema database

## Bucket raw: `iot_lab2_raw` (retention 30 ngày)
| Thành phần | Giá trị |
|---|---|
| Measurement | raw_sensor |
| Tags | device_id |
| Fields | temperature, humidity, light, latency_sec |
| Timestamp | Thời gian nhận tại collector (Unix ns) |

## Bucket processed: `iot_lab2_processed` (retention 90 ngày)
| Thành phần | Giá trị |
|---|---|
| Measurement | processed_sensor |
| Fields | temperature, humidity, light, temp_roll_mean, temp_delta, temperature_norm, humidity_norm, light_norm, temperature_anomaly, humidity_anomaly, light_anomaly |
| Timestamp | Mốc resample (1 phút/điểm) |

# 3. Kết quả thực nghiệm

![Dashboard](images/dashboard.png)

| Chỉ số | Giá trị |
|---|---|
| p50 latency | ... ms |
| p95 latency | ... ms |
| Max latency | ... ms |
| Tỷ lệ mất gói | ... % |
| Số outlier phát hiện (nhiệt độ) | ... |
| Dung lượng DB sau 1 giờ chạy | ... MB |

# 4. Phân tích độ trễ, vấn đề lưu trữ và đề xuất cải tiến

- Độ trễ end-to-end chủ yếu đến từ: ...
- Vấn đề lưu trữ gặp phải (nếu có): ...
- Đề xuất cải tiến: edge processing trên ESP32, MQTT TLS, so sánh InfluxDB vs MongoDB Time-Series, cảnh báo khi vượt ngưỡng...

# 5. Khó khăn và cách giải quyết

| Khó khăn | Cách giải quyết |
|---|---|
| ... | ... |

# 6. Kết luận

...
