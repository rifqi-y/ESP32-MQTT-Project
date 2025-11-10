# ESP32 MQTT + Flask + MySQL (UTS Pemrograman IoT)

Proyek ini menampilkan arsitektur sederhana untuk streaming data sensor dari ESP32 ke backend Python melalui MQTT, menyimpan ke MySQL secara real‑time, dan menampilkannya di dashboard web beserta API JSON sesuai ketentuan soal.

## Ringkas Arsitektur

- ESP32 (DHT22 + LDR + RTC) publish data ke broker MQTT publik
- Python `mqtt.py` subscribe, parsing JSON, lalu insert ke MySQL
- Python `main.py` (Flask) expose API dan dashboard HTML untuk menampilkan data

```
ESP32 --> MQTT (broker.hivemq.com) --> mqtt.py --> MySQL
																				 |             \
																				 v              \
																			main.py (API/WEB)  -> Browser UI
```

## Struktur Folder

- `UTSIOT/` — proyek ESP32 (PlatformIO)
- `main.py` — server Flask (API + web)
- `mqtt.py` — ingestor MQTT -> DB (loop forever)
- `sql.py` — fungsi sederhana MySQL (buat tabel, insert, ringkasan)
- `templates/index.html` — halaman dashboard
- `static/styles.css` — styling sederhana

## Topik MQTT dan Payload

- Broker: `broker.hivemq.com` (port 1883)
- Publish data oleh ESP32: `152023003/pemiot/data`
- Perintah LED dari backend: `152023003/pemiot/cmd/led` (payload: `ON` atau `OFF`)

Contoh payload sensor dari ESP32:

```json
{
  "temperature": 27.5,
  "humidity": 60.0,
  "lightlevel": 1750,
  "datetime": "2025-11-08T12:34:56"
}
```

## Skema Database

Database: `uts_pemiot`

Tabel `data_sensor`:

```sql
CREATE TABLE IF NOT EXISTS data_sensor (
	id INT AUTO_INCREMENT PRIMARY KEY,
	suhu FLOAT NOT NULL,
	humidity FLOAT NOT NULL,
	lux INT NOT NULL,
	timestamp DATETIME NOT NULL
) ENGINE=InnoDB;
```

Kolom sesuai soal: `{id, suhu, humidity, lux, timestamp}`.

## Prasyarat

- Windows + PowerShell
- Python 3.10+ dan paket: Flask, paho-mqtt, mysql-connector-python
- MySQL Server (buat database `uts_pemiot` dengan user `root`)
- PlatformIO (VS Code) atau Arduino IDE untuk ESP32

## Instalasi Python (opsional venv)

```powershell
# (opsional) aktifkan virtualenv yang sudah ada
./uts/Scripts/Activate.ps1

# instal paket jika diperlukan
pip install flask paho-mqtt mysql-connector-python
```

## Menjalankan Backend

Jalankan dua proses di terminal terpisah:

```powershell
# 1) Ingestor MQTT -> Database
python .\mqtt.py

# 2) API + Web (Flask)
python .\main.py
```

Buka browser: http://127.0.0.1:5000/

## Menjalankan Firmware ESP32

File firmware: `UTSIOT/src/main.cpp`

- WiFi: `Wokwi-GUEST` (default untuk simulasi Wokwi) — sesuaikan jika menggunakan jaringan lain
- Broker: `broker.hivemq.com`
- Topik publish data: `152023003/pemiot/data`
- Topik subscribe perintah LED: `152023003/pemiot/cmd/led`

Build dan upload via PlatformIO, atau jalankan simulasi di Wokwi.

## API (Ringkas)

- `GET /api/summary` — JSON ringkasan sesuai contoh pada soal
- `GET /api/sensors/latest` — satu baris terakhir
- `GET /api/sensors?limit=50` — daftar N baris terbaru
- `POST /api/led` — body `{ "state": "on" | "off" }` untuk menyalakan/mematikan LED ESP32

Contoh uji cepat (opsional):

```powershell
curl http://127.0.0.1:5000/api/summary
curl http://127.0.0.1:5000/api/sensors?limit=5
curl -X POST http://127.0.0.1:5000/api/led -H "Content-Type: application/json" -d '{"state":"on"}'
```

## Format JSON Ringkasan (contoh)

```json
{
  "suhumax": 36,
  "suhumin": 21,
  "suhurata": 28.35,
  "nilai_suhu_max_humid_max": [
    {
      "idx": 101,
      "suhu": 36,
      "humid": 28,
      "kecerahan": 25,
      "timestamp": "2010-09-18 07:23:48"
    },
    {
      "idx": 226,
      "suhu": 29,
      "humid": 36,
      "kecerahan": 27,
      "timestamp": "2011-05-02 12:29:34"
    }
  ],
  "month_year_max": [{ "month_year": "9-2010" }, { "month_year": "5-2011" }]
}
```

## Konfigurasi

- Ubah kredensial MySQL di `sql.py` jika diperlukan:
  - `HOST`, `USER`, `PASSWORD`, `DATABASE`
- Topik MQTT dan broker ada di `mqtt.py` dan pada `main.cpp` (ESP32) — pastikan sama.

## Troubleshooting

- Tidak ada data di UI? Periksa:
  1.  `mqtt.py` sedang berjalan dan terkoneksi broker
  2.  ESP32 berhasil publish (lihat Serial Monitor)
  3.  Database `uts_pemiot` tersedia dan tabel `data_sensor` otomatis dibuat
  4.  Endpoint `GET /api/sensors?limit=1` mengembalikan data
- Gagal konek broker: pastikan jaringan mengizinkan port 1883 dan tidak ada firewall yang memblokir.
- Error MySQL auth: sesuaikan user/password DB pada `sql.py`.

---

Selamat mencoba! Jika kamu butuh menambah filter tanggal, grafik, atau pembacaan state LED dari topik `.../state/led`, tinggal minta—struktur sekarang sudah siap dikembangkan.
