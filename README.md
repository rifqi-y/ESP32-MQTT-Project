## ESP32 + MQTT + Flask Dashboard

Repositori ini berisi contoh sistem IoT end‑to‑end sederhana: sebuah board ESP32 mengukur beberapa sensor (suhu/kelembapan, intensitas cahaya, waktu RTC), mengirimkan data secara periodik melalui MQTT ke server aplikasi Python. Server melakukan ingest data, menyimpannya ke basis data relasional, lalu menampilkan dashboard web dengan ringkasan, daftar pembacaan terbaru, serta kontrol LED dua arah (publish perintah dari web, perangkat menerima dan merespon).

> Fokus README: bagaimana membangun ulang sistem serupa. Detail sensitif seperti nama topik MQTT, nama database, table, dsb sengaja digeneralisasi menjadi placeholder agar Anda menyesuaikannya sendiri.

---

### 1. Arsitektur Sistem (Ringkas)

Komponen utama:

1. Perangkat (ESP32 firmware) – Membaca sensor (misal DHT22 & LDR), menyertakan timestamp (RTC), mem-publish payload JSON ke topik data MQTT, dan subscribe topik perintah LED. Setelah menerima perintah LED (ON/OFF/TOGGLE), perangkat memperbarui LED dan mem-publish state LED terakhir (retained) ke topik status.
2. Broker MQTT – Perantara pesan publish/subscribe (dapat memakai broker publik atau self-hosted). Tidak perlu modifikasi khusus.
3. Service Ingest Python (`mqtt.py`) – Client MQTT yang subscribe topik data, parse JSON, simpan ke database. Juga menyediakan fungsi untuk kirim perintah LED (publish singkat) yang dipanggil oleh API web.
4. Layer Data (`sql.py`) – Koneksi ke database relasional (MySQL dalam contoh) + pembuatan tabel jika belum ada + operasi insert & agregasi (summary, nilai ekstrem, dll.).
5. REST + Dashboard Web (`main.py` + `templates/` + `static/`) – Aplikasi Flask yang menyediakan endpoint JSON (latest, list, summary, kontrol LED) serta halaman HTML interaktif yang auto-refresh.

Alur data:
ESP32 -> (JSON sensor) -> MQTT Broker -> Service Ingest -> Database -> Flask API -> Browser (polling 5 detik)

Alur kontrol LED:
Browser -> Flask API (POST) -> Publish perintah LED -> MQTT Broker -> ESP32 -> Update LED -> Publish state terkini (retained)

### 2. Struktur Folder (Inti)

```
.
├── main.py              # Aplikasi Flask (routing dashboard & API)
├── mqtt.py              # Klien MQTT untuk ingest & fungsi publish perintah LED
├── sql.py               # Abstraksi akses database & agregasi data
├── requirements.txt     # Daftar dependensi Python
├── templates/           # HTML Jinja (dashboard & tampilan JSON)
├── static/styles.css    # Styling dashboard
└── UTSIOT/src/main.cpp  # Firmware ESP32 (sensor + MQTT + LED handling)
```

Anda bebas menambah file konfigurasi seperti `.env` untuk menyembunyikan kredensial atau nama topik.

### 3. Prasyarat

Perangkat & Software yang dibutuhkan:

- Board ESP32 (dengan koneksi WiFi)
- Sensor suhu/kelembapan (misal DHT22) & LDR (atau sensor cahaya lain)
- RTC (opsional; dapat diganti dengan waktu dari NTP / internal)
- Python 3.10+ (direkomendasikan)
- Server database relasional (MySQL/MariaDB atau ganti dengan sistem lain yang mendukung CRUD dasar)
- Akses ke broker MQTT (publik atau lokal)
- Git (untuk kloning repositori)

### 4. Konfigurasi Nilai Kustom

Anda perlu menetapkan:

- Kredensial database (HOST, USER, PASSWORD, DB_NAME)
- Broker MQTT (HOST & PORT)
- Nama topik sensor (DATA_TOPIC) & perintah LED (LED_CMD_TOPIC), serta topik state LED (LED_STATE_TOPIC)

Opsi 1 (paling sederhana): Hardcode nilai di `sql.py` & `mqtt.py` (seperti contoh).

Opsi 2 (direkomendasikan produksi): Pakai `.env` + `python-dotenv`. Contoh isi:

```
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=secret
DB_NAME=iotdb
MQTT_BROKER=broker.example.com
MQTT_PORT=1883
DATA_TOPIC=my/device/data
LED_CMD_TOPIC=my/device/cmd/led
LED_STATE_TOPIC=my/device/state/led
```

Kemudian modifikasi `sql.py` & `mqtt.py` untuk membaca lewat `os.getenv()`.

### 5. Instalasi (Langkah Menyiapkan Lingkungan Lokal)

Semua perintah berikut untuk PowerShell (Windows). Sesuaikan bila memakai shell lain.

```powershell
# 1. Kloning repositori
git clone <url-repo-anda>
cd <folder-repo>

# 2. Buat virtual environment (opsional namun dianjurkan)
python -m venv venv

# 3. Aktifkan virtual environment
./venv/Scripts/Activate.ps1

# 4. Pasang dependensi
pip install -r requirements.txt

# 5. (Opsional) Buat dan isi file .env
Copy-Item .env.example .env  # jika Anda membuat file contoh
```

Pastikan server database berjalan dan kredensial cocok. Tabel akan dibuat otomatis saat modul `sql.py` di-import (ada fungsi ensure_table()).

### 6. Menjalankan Komponen

Terminal 1 – Jalankan service ingest MQTT:

```powershell
python mqtt.py
```

Terminal 2 – Jalankan aplikasi Flask (API & dashboard):

```powershell
python main.py
```

Firmware ESP32 – Kompilasi & unggah `UTSIOT/src/main.cpp` melalui PlatformIO atau Arduino IDE. Pastikan SSID & password WiFi benar, serta topik/broker sama dengan yang dipakai server.

Setelah ketiganya berjalan:

- Buka browser ke: `http://localhost:5000/` untuk dashboard.
- Endpoint kesehatan: `GET /health` (cek status cepat).
- Data otomatis akan muncul ketika perangkat mem-publish.

### 7. Endpoint REST (Generik)

| Metode | Path                 | Kegunaan                           |
| ------ | -------------------- | ---------------------------------- | ---- |
| GET    | /api/summary         | Ringkasan agregat (max, min, rata) |
| GET    | /api/sensors/latest  | Pembacaan sensor terakhir          |
| GET    | /api/sensors?limit=N | Daftar N pembacaan terbaru         |
| POST   | /api/led             | Kirim perintah LED {state:on       | off} |

Semua respons JSON sederhana agar mudah diintegrasikan.

### 8. Format Payload Sensor (Generik)

Contoh bentuk JSON yang dipublish perangkat (sesuaikan nama field):

```json
{
  "temperature": 25.7,
  "humidity": 61.2,
  "lightlevel": 423,
  "datetime": "2025-11-10T08:21:33"
}
```

Server ingest akan memetakan dan menyimpan ke kolom numerik + timestamp. Jika timestamp tidak valid, fallback ke waktu server.

### 9. Pengujian Cepat Manual

1. Jalankan Flask & MQTT ingest.
2. Gunakan tool MQTT (misal MQTT Explorer) untuk publish payload dummy ke DATA_TOPIC.
3. Pastikan dashboard menampilkan baris baru dan ringkasan ter-update.
4. Uji kontrol LED: klik tombol ON/OFF, lihat pesan di monitor serial ESP32 & perubahan LED.

### 10. Troubleshooting

| Masalah               | Penyebab Umum                        | Solusi Singkat                                                   |
| --------------------- | ------------------------------------ | ---------------------------------------------------------------- |
| Tidak ada data tampil | Topik salah / firmware belum running | Pastikan topik di firmware & server sama, cek log `mqtt.py`      |
| Error koneksi DB      | Kredensial / server belum hidup      | Ubah variabel koneksi, cek service database                      |
| LED tidak merespon    | Format perintah salah                | Gunakan JSON sederhana `{"state":"ON"}` atau string "ON" / "OFF" |
| Timestamp None        | Format waktu perangkat tidak ISO     | Sesuaikan firmware kirim format ISO8601                          |
| Dashboard kosong      | Browser cache / API error            | Buka console devtools, cek network response                      |

### 11. Skalabilitas & Pengembangan Lanjut (Ide)

- Ganti polling di frontend dengan WebSocket / SSE untuk real-time push.
- Tambah autentikasi API (token / session) sebelum kontrol perangkat.
- Pakai persistent config (.env) & secret manager (production).
- Simpan data ke time-series DB (InfluxDB, Timescale) untuk query historis panjang.
- Tambah fitur alert (misal suhu > ambang batas publish notifikasi).

### 12. Keamanan Minimum

- Hindari hardcode kredensial di kode versi produksi.
- Gunakan TLS untuk broker MQTT jika tersedia.
- Validasi payload masuk (tipe & range nilai) sebelum insert.

### 13. Lisensi

Tambahkan lisensi sesuai kebutuhan (misal MIT) di masa mendatang.

---

## Ringkas

Langkah utama: siapkan perangkat & broker -> kloning kode -> pasang dependensi -> jalankan ingest & Flask -> unggah firmware -> sesuaikan konfigurasi -> uji publish data & kontrol LED. Struktur modular memudahkan penggantian komponen (database, broker, sensor) tanpa ubah keseluruhan.

Selamat bereksperimen! 🚀
