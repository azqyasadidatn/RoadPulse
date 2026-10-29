# RoadPulse
### Sistem Pemantauan Kondisi Jalan Berbasis Sensor Smartphone

RoadPulse merupakan sistem pemantauan kondisi jalan yang memanfaatkan sensor gerak dan GPS pada smartphone untuk mengumpulkan data getaran selama perjalanan. Data tersebut diproses menggunakan metode *rule-based classification* untuk memperkirakan kondisi jalan, kemudian divisualisasikan melalui dashboard berbasis web dengan peta interaktif.

RoadPulse dirancang agar pengumpulan data dapat dilakukan langsung melalui browser smartphone, tanpa memerlukan instalasi aplikasi khusus atau menjalankan program Python pada perangkat pengguna.

## Fitur Utama

- **Pengumpulan Data Sensor** — Mengambil data accelerometer dan gyroscope melalui browser smartphone.
- **Pelacakan Lokasi** — Merekam koordinat GPS dan akurasi lokasi untuk setiap laporan.
- **Komunikasi MQTT** — Mengirimkan data telemetri melalui broker HiveMQ.
- **Klasifikasi Kondisi Jalan** — Memperkirakan kondisi jalan berdasarkan nilai RMS sensor menggunakan aturan yang ditentukan.
- **Visualisasi Geospasial** — Menampilkan lokasi laporan pada peta interaktif menggunakan Leaflet dan OpenStreetMap.
- **Dashboard Pemantauan** — Menampilkan nilai RMS, identitas perangkat, lokasi, dan hasil klasifikasi dengan pembaruan berkala.
- **Dukungan Lintas Jaringan** — Memungkinkan smartphone dan laptop beroperasi pada jaringan internet yang berbeda.

## Arsitektur Sistem

```text
┌──────────────────────────────┐
│       Smartphone             │
│                              │
│  Accelerometer               │
│  Gyroscope                   │
│  GPS                         │
│                              │
│  mobile.html                 │
└──────────────┬───────────────┘
               │
               │ MQTT over WSS
               ▼
┌──────────────────────────────┐
│       HiveMQ Broker          │
│                              │
│  Perantara pesan telemetri   │
└──────────────┬───────────────┘
               │
               │ MQTT over TLS
               ▼
┌──────────────────────────────┐
│       Flask Backend          │
│          server.py           │
│                              │
│  • Penerimaan data           │
│  • Perhitungan RMS           │
│  • Klasifikasi kondisi       │
│  • Penyimpanan laporan       │
│  • REST API                  │
└──────────────┬───────────────┘
               │
               │ GET /api/data
               ▼
┌──────────────────────────────┐
│       Dashboard Web          │
│       dashboard.html         │
│                              │
│  • Peta interaktif           │
│  • Log telemetri             │
│  • Nilai RMS sensor          │
│  • Kondisi jalan             │
└──────────────────────────────┘
```

**Cloudflare Tunnel** digunakan sebagai jalur akses HTTPS agar halaman mobile yang berjalan pada laptop dapat dibuka dari smartphone melalui internet. Sementara itu, pengiriman data sensor dilakukan melalui MQTT.

Dengan pemisahan tersebut, smartphone dan laptop tidak harus terhubung ke jaringan Wi-Fi yang sama.

## Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python | Pemrosesan data pada backend |
| Flask | Server web dan penyedia REST API |
| Paho MQTT | Komunikasi MQTT pada backend |
| MQTT.js | Pengiriman telemetri dari browser |
| HTML, CSS, JavaScript | Antarmuka mobile dan dashboard |
| Browser Motion APIs | Pengambilan data gerak smartphone |
| Geolocation API | Pengambilan koordinat GPS |
| Leaflet | Visualisasi peta interaktif |
| OpenStreetMap | Penyedia peta dasar |
| HiveMQ | Broker komunikasi MQTT |
| Cloudflare Tunnel | Akses jarak jauh ke server lokal |

## Struktur Proyek

```text
roadpulse/
├── server.py
├── edge.py
├── requirements.txt
└── templates/
    ├── mobile.html
    └── dashboard.html
```

| Berkas | Fungsi |
|---|---|
| `server.py` | Menjalankan Flask, menerima pesan MQTT, menghitung RMS, melakukan klasifikasi, dan menyediakan API. |
| `templates/mobile.html` | Mengambil data sensor dan GPS dari smartphone serta mengirimkannya melalui MQTT. |
| `templates/dashboard.html` | Menampilkan peta, laporan telemetri, nilai RMS, dan kondisi jalan. |
| `requirements.txt` | Mendefinisikan dependensi Python. |
| `edge.py` | Komponen Python versi sebelumnya yang tidak digunakan dalam alur pengumpulan data berbasis browser saat ini. |

## Persyaratan Sistem

Sebelum menjalankan RoadPulse, siapkan:

- Python 3.10 atau versi yang lebih baru.
- Browser smartphone yang mendukung sensor gerak dan geolokasi.
- Koneksi internet pada smartphone dan laptop.
- Broker MQTT yang dapat diakses melalui koneksi TLS dan WebSocket Secure.
- Cloudflare Tunnel untuk mengakses halaman mobile dari jaringan berbeda.
- Izin akses sensor gerak dan lokasi pada browser smartphone.

Ketersediaan sensor dan mekanisme pemberian izin dapat berbeda bergantung pada perangkat serta browser yang digunakan.

## Instalasi dan Konfigurasi

### 1. Kloning repository

```bash
git clone <URL_REPOSITORY>
cd roadpulse
```

Ganti `<URL_REPOSITORY>` dengan alamat repository GitHub yang digunakan.

### 2. Membuat virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux atau macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Menginstal dependensi

```bash
pip install -r requirements.txt
```

Pastikan dependensi backend yang digunakan, termasuk Flask dan Paho MQTT, tercantum dalam `requirements.txt`.

### 4. Mengatur konfigurasi MQTT

Konfigurasi backend saat ini menggunakan:

```python
PROJECT_ID = "roadpulse_kelompok_06"
MQTT_HOST = "broker.hivemq.com"
MQTT_PORT = 8883
TOPIC_SUB = f"roadpulse/{PROJECT_ID}/edge/+/telemetry"
```

Topic yang digunakan oleh browser smartphone harus sesuai dengan pola topic yang di-subscribe oleh backend.

Koneksi MQTT Python menggunakan TLS pada port `8883`, sedangkan koneksi browser menggunakan MQTT melalui WebSocket Secure.

## Menjalankan Sistem

### 1. Menjalankan backend

Jalankan perintah berikut dari direktori proyek:

```bash
python server.py
```

Server lokal tersedia melalui:

```text
http://127.0.0.1:5000/
```

Backend akan menerima pesan MQTT, memproses data sensor, dan menyediakan laporan melalui API.

### 2. Menjalankan Cloudflare Tunnel

Pastikan Cloudflare Tunnel telah terpasang, kemudian jalankan pada terminal terpisah:

```powershell
cloudflared tunnel --url http://localhost:5000
```

Salin URL HTTPS yang dihasilkan. Terminal tunnel harus tetap berjalan selama sistem digunakan.

### 3. Membuka halaman mobile

Akses URL berikut melalui browser smartphone:

```text
https://URL-TUNNEL/mobile
```

Ganti `URL-TUNNEL` dengan URL yang dihasilkan Cloudflare Tunnel. Berikan izin sensor gerak dan lokasi, kemudian tekan tombol **Start** pada halaman mobile.

### 4. Membuka dashboard

Pada browser laptop, buka:

```text
http://127.0.0.1:5000/
```

Dashboard akan mengambil data dari API secara berkala dan memperbarui visualisasi peta serta daftar laporan.

## Alur Pemrosesan Data

### 1. Pengumpulan data

Browser smartphone mengambil data dari tiga sumber utama:

- **Accelerometer:** mengukur percepatan gerak smartphone.
- **Gyroscope:** mengukur gerakan rotasi smartphone.
- **GPS:** menyediakan koordinat lintang, bujur, dan akurasi lokasi.

Data tersebut dikemas dalam format JSON untuk dikirim ke broker MQTT.

### 2. Pengiriman telemetri

Browser mengirimkan pesan ke topic MQTT yang telah dikonfigurasi. Backend menerima pesan melalui mekanisme *subscription* dan mengelompokkan sampel berdasarkan identitas perangkat.

### 3. Perhitungan RMS

Backend memproses sampel sensor dalam jendela yang terdiri dari 10 sampel per perangkat.

RMS (*Root Mean Square*) digunakan untuk menggambarkan besarnya sinyal sensor selama suatu jendela pengukuran.

Secara umum, rumus RMS adalah:

\[
\operatorname{RMS}(x)=
\sqrt{\frac{1}{N}\sum_{i=1}^{N}x_i^2}
\]

dengan \(N\) merupakan jumlah sampel dan \(x_i\) merupakan nilai sinyal pada sampel ke-\(i\).

Pada implementasi saat ini:

- `accel_rms` dihitung dari pendekatan selisih magnitudo percepatan terhadap gravitasi standar.
- `gyro_rms` dihitung dari RMS magnitudo vektor tiga sumbu gyroscope.

Kedua nilai disimpan secara terpisah karena merepresentasikan karakteristik gerak yang berbeda.

### 4. Klasifikasi kondisi jalan

RoadPulse menggunakan pendekatan *rule-based classification*, yaitu menentukan kategori berdasarkan ambang nilai yang telah ditetapkan dalam program.

Ambang awal untuk accelerometer:

| Nilai Acceleration RMS | Kategori |
|---|---|
| Di bawah 0,3 | Normal |
| 0,3 hingga kurang dari 1,0 | Bumpy |
| 1,0 hingga kurang dari 2,0 | Pothole |
| 2,0 atau lebih | Impact |

Apabila gyroscope juga digunakan dalam penentuan kondisi, ambang gyroscope dan aturan penggabungannya perlu dikonfigurasi secara terpisah di `server.py`.

Klasifikasi tersebut merupakan indikasi tingkat getaran, bukan konfirmasi langsung bahwa suatu lokasi mengalami kerusakan jalan. Ambang perlu dievaluasi menggunakan pengukuran nyata sebelum digunakan untuk penilaian kondisi jalan yang lebih andal.

### 5. Penyimpanan dan visualisasi

Setiap laporan yang telah diproses dapat memuat:

- Identitas perangkat.
- Timestamp.
- Koordinat dan akurasi GPS.
- Acceleration RMS.
- Gyroscope RMS.
- Hasil klasifikasi kondisi jalan.
- Data accelerometer dan gyroscope terbaru.

Backend menyediakan laporan melalui endpoint:

```http
GET /api/data
```

Dashboard mengambil data tersebut secara berkala untuk memperbarui marker pada peta dan daftar telemetri.

## API

### `GET /api/data`

Mengembalikan daftar laporan telemetri yang telah diproses dalam format JSON.

Contoh struktur respons:

```json
[
  {
    "device_id": "browser_hp_example",
    "timestamp": 1793160000000,
    "lat": -7.05,
    "lng": 110.44,
    "accuracy": 10,
    "condition": "Normal",
    "accel_rms": 0.1015,
    "gyro_rms": 0.245,
    "acceleration": {
      "x": 0.12,
      "y": 0.08,
      "z": 9.79
    },
    "gyroscope": {
      "x": 0.5,
      "y": 1.2,
      "z": 0.3
    }
  }
]
```

Nilai di atas hanya ilustrasi. Data aktual bergantung pada pengukuran smartphone dan implementasi program.

## Keterbatasan dan Keamanan

- Broker HiveMQ publik digunakan untuk pengujian. Topic publik tidak boleh dianggap sebagai saluran privat.
- Gunakan autentikasi, pembatasan akses topic, dan konfigurasi keamanan yang sesuai untuk penerapan produksi.
- URL Cloudflare Quick Tunnel bersifat sementara dan dapat berubah.
- Server Flask bawaan ditujukan untuk pengembangan, bukan sebagai server produksi.
- Laporan disimpan dalam memori oleh implementasi saat ini sehingga akan hilang ketika backend dimulai ulang.
- Hasil sensor dipengaruhi orientasi smartphone, gerakan pengguna, kualitas sensor, dan akurasi GPS.
- Nilai RMS tinggi tidak selalu menunjukkan jalan berlubang; gerakan perangkat juga dapat menghasilkan nilai serupa.
- Pengumpulan data dan klasifikasi membutuhkan pengujian serta kalibrasi lebih lanjut.

## Status Proyek

RoadPulse merupakan prototipe pemantauan getaran jalan berbasis smartphone. Fokus implementasi saat ini adalah mengumpulkan data sensor, memperkirakan tingkat getaran menggunakan aturan klasifikasi, dan menyajikan laporan berbasis lokasi melalui dashboard web.

---

**RoadPulse — Mengubah data gerak smartphone menjadi informasi kondisi jalan.**
