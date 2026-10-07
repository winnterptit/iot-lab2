# IoT Lab 2 – Thu thập, lưu trữ và tiền xử lý dữ liệu IoT

Dự án mô phỏng toàn bộ pipeline IoT (không cần phần cứng thật) đáp ứng yêu cầu của
**Bài thực hành số 2 – học phần IoT và Ứng dụng (INT14149)**.

## Yêu cầu môi trường
- Docker Desktop (đang chạy)
- VS Code + extensions: PlatformIO IDE, Wokwi for VS Code (đã kích hoạt License miễn phí),
  Python, Docker, Markdown Preview Enhanced
- Python 3.10+
- Pandoc (để xuất báo cáo Word)

## Cấu trúc thư mục
```
firmware/     # ESP32 mô phỏng Wokwi + PlatformIO (firmware thiết bị nhúng)
collector/    # Script thu thập: subscribe MQTT -> validate -> ghi InfluxDB
preprocess/   # Script tiền xử lý: missing/outlier/resample/feature/normalize
dashboard/    # App ứng dụng: Streamlit dashboard giám sát real-time
config/       # File cấu hình chung (config.yaml)
mosquitto/    # Cấu hình MQTT broker
report/       # Báo cáo (Markdown -> xuất Word)
docker-compose.yml
requirements.txt
```

## Các bước chạy

### 1. Khởi động MQTT Broker + InfluxDB
```bash
docker compose up -d
```
Kiểm tra: `docker ps` → thấy `mosquitto` và `influxdb` đang chạy.
InfluxDB UI: http://localhost:8086 (user `admin` / pass `admin12345`).
Bucket `iot_lab2_raw` đã được tạo sẵn; vào **Load Data → Buckets → Create Bucket** để tạo thêm
`iot_lab2_processed` (retention 90 ngày).

### 2. Cài Python packages
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Build & chạy mô phỏng Wokwi
1. Mở thư mục `firmware/` trong VS Code (PlatformIO tự nhận diện `platformio.ini`).
2. Bấm biểu tượng **✓ (Build)** ở thanh PlatformIO dưới cùng → đợi `SUCCESS`.
3. `F1` → `Wokwi: Start Simulator`.
4. Bấm biểu tượng **🔌 Serial Monitor** để xem log publish mỗi 5 giây.

> Nếu ESP32 không kết nối được MQTT: sửa `mqtt_server` trong `firmware/src/main.ino`
> (Windows/Mac: `host.docker.internal`; Linux: IP LAN máy bạn), rồi Build lại.

### 4. Chạy Collector (ghi dữ liệu thô vào InfluxDB)
```bash
python collector/collector.py
```

### 5. Chạy Preprocessor (làm sạch, outlier, resample, feature, chuẩn hóa)
```bash
python preprocess/preprocess.py
```
Chạy lại định kỳ (hoặc đặt cron) sau khi đã có đủ dữ liệu raw.

### 6. Chạy Dashboard (app ứng dụng)
```bash
streamlit run dashboard/app.py
```
Mở http://localhost:8501 — tự refresh mỗi 5 giây, hiển thị dữ liệu raw, dữ liệu đã xử lý,
số outlier và độ trễ (latency p50/p95/max).

### 7. Viết và xuất báo cáo Word
Chỉnh nội dung `report/BaoCao_Lab2.md`, chụp ảnh dashboard/sơ đồ kiến trúc bỏ vào
`report/images/`, sau đó:
```bash
pandoc report/BaoCao_Lab2.md -o report/BaoCao_Lab2.docx
```

## Map với "Sản phẩm cần nộp" của bài lab
| Yêu cầu trong bài | File tương ứng |
|---|---|
| Firmware thiết bị nhúng | `firmware/src/main.ino`, `firmware/diagram.json`, `firmware/platformio.ini` |
| Script thu thập và ghi dữ liệu | `collector/collector.py` |
| Script tiền xử lý | `preprocess/preprocess.py` |
| File cấu hình | `config/config.yaml`, `docker-compose.yml`, `mosquitto/config/mosquitto.conf` |
| README hướng dẫn chạy | file này |
| Báo cáo Word 4–6 trang | `report/BaoCao_Lab2.md` → `report/BaoCao_Lab2.docx` |
| App ứng dụng | `dashboard/app.py` (Streamlit) |

## Map với tiêu chí đánh giá
| Tiêu chí | Điểm | Thành phần đáp ứng |
|---|---|---|
| Pipeline thu thập & lưu trữ ổn định | 3.0 | firmware + collector (validate, log, retry, latency) |
| Tiền xử lý đúng, có ý nghĩa | 2.5 | preprocess (IQR outlier, resample, rolling mean, delta, MinMax normalize) |
| Dashboard & giám sát real-time | 2.0 | dashboard (auto-refresh, raw + processed, KPI) |
| Chất lượng code, xử lý lỗi, README | 1.5 | try/except + logging trong collector/preprocess, cấu trúc module rõ ràng |
| Báo cáo và phân tích | 1.0 | report/BaoCao_Lab2.md |

## Checklist trước khi demo
- [ ] Wokwi publish JSON ổn định (xem Serial Monitor)
- [ ] `docker ps` thấy mosquitto + influxdb chạy
- [ ] Collector ghi được dữ liệu vào bucket `iot_lab2_raw`
- [ ] Bucket `iot_lab2_processed` đã tạo, retention 90 ngày
- [ ] Preprocessor chạy không lỗi, tạo được measurement `processed_sensor`
- [ ] Dashboard hiển thị raw + processed + latency p50/p95
- [ ] Đã đẩy mã nguồn lên GitHub kèm README
- [ ] Báo cáo Word 4–6 trang có ảnh dashboard + bảng số liệu thật (không để "...")

## Lỗi thường gặp
| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| ESP32 không kết nối MQTT | `host.docker.internal` không resolve | Thay bằng IP LAN máy bạn trong `main.ino` |
| Dashboard báo "Chưa có dữ liệu" | Collector/broker chưa chạy | `docker ps`, chạy `collector.py` trước |
| `preprocess` báo rỗng | Chưa đủ dữ liệu raw | Đợi collector ghi vài phút rồi chạy lại |
| Token invalid | Token trong `config.yaml` khác token trong `docker-compose.yml` | Đảm bảo cả hai cùng là `my-super-secret-token-lab2` |

## Gợi ý mở rộng để nâng điểm
- Edge processing: ESP32 tự phát hiện ngưỡng bất thường, gắn thêm field `alert`.
- MQTT TLS (port 8883).
- So sánh hiệu năng InfluxDB vs MongoDB Time-Series.
- Cảnh báo Telegram/Email khi phát hiện outlier.
