# OtoGrid Backend Services (Hyperlocal On-Demand Mechanic)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/Django_REST_Framework-ff1744?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)

Backend OtoGrid adalah layanan *command center* berbasis REST API dan WebSockets yang menangani logika bisnis, pemrosesan data geospasial presisi tinggi, integrasi kecerdasan buatan (AI Triage Engine), serta komunikasi *real-time* dua arah antara pelanggan dan mitra mekanik.

---

## 1. Deskripsi Sistem dan Arsitektur

Sistem backend ini dibangun menggunakan Django & Django REST Framework (DRF) berpasangan dengan PostgreSQL dan PostGIS. Mengadopsi arsitektur monolitik yang beroperasi secara efisien di atas *bare-metal Linux server* untuk meminimalisir latensi jaringan dan memaksimalkan throughput I/O.

### Prinsip Desain: "Thin Views, Fat Services"
* **Views / ViewSets (`apps/*/views.py`):** Hanya bertugas menangani HTTP Request/Response, validasi masukan serializer, dan mengembalikan data JSON.
* **Service Layer (`apps/*/services/`):** Menyimpan seluruh logika bisnis terisolasi (misalnya kalkulasi geo-matching, transaksi order state machine, dan prompt injection ke Gemini API).
* **Data Access Layer (`apps/*/models.py`):** Entitas murni yang merepresentasikan skema tabel database dengan indeks geospasial.

---

## 2. Spesifikasi Teknologi (Tech Stack & Badges)

### Technical Stack Summary
| Komponen Sistem | Teknologi Utama | Badge Status |
| :--- | :--- | :--- |
| **Language** | Python 3.12+ | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) |
| **Web Framework** | Django 6.0+ | ![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white) |
| **API Architecture** | Django REST Framework 3.17+ | ![DRF](https://img.shields.io/badge/DRF-ff1744?style=flat-square&logo=django&logoColor=white) |
| **Spatial Database** | PostgreSQL 14+ & PostGIS 3+ | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![PostGIS](https://img.shields.io/badge/PostGIS-336791?style=flat-square&logo=postgresql&logoColor=white) |
| **Broker & Cache** | Redis Server 8.0+ | ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white) |
| **Real-time Protocol** | Django Channels & WebSockets (WSS) | ![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=flat-square&logo=socketdotio&logoColor=white) |
| **AI Triage Engine** | Google Gemini API (`google-generativeai`) | ![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white) |
| **API Documentation** | `drf-spectacular` (OpenAPI 3.0) | ![Swagger](https://img.shields.io/badge/Swagger-85EA2D?style=flat-square&logo=swagger&logoColor=black) |
| **Authentication** | SimpleJWT (JSON Web Tokens) | ![JWT](https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white) |

---

## 3. Struktur Direktori Proyek

```text
backend_otogrid/
├── apps/
│   ├── authentication/    # Manajemen identitas, User, & Role-Based Access Control (RBAC)
│   ├── core/              # Komponen utilitas global, middleware, & layanan basis
│   └── orders/            # Order State Machine, AI Triage Engine, & Geo-Matching
├── config/
│   ├── __init__.py
│   ├── asgi.py            # Konfigurasi ASGI untuk WebSockets (Django Channels)
│   ├── settings.py        # Pengaturan utama Django & integrasi ekstensi
│   ├── urls.py            # Routing URL utama & Swagger OpenAPI UI
│   └── wsgi.py            # Konfigurasi WSGI HTTP standar
├── dev/                   # Dokumen PRD dan SRS arsitektur sistem
├── manage.py              # Script utilitas CLI Django
├── requirements.txt       # Daftar dependensi paket Python
├── .env                   # Variabel lingkungan (dikecualikan dari Git)
├── .gitignore             # Daftar berkas/direktori yang diabaikan oleh Git
└── README.md              # Dokumentasi utama proyek
```

---

## 4. Prasyarat Sistem (System Prerequisites)

Sebelum menjalankan aplikasi, pastikan sistem operasi Linux atau lingkungan pengembang Anda telah terpasang dependensi berikut:

### Paket Tingkat Sistem Operasi (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib postgis postgresql-14-postgis-3
sudo apt-get install -y redis-server
sudo apt-get install -y binutils libproj-dev gdal-bin
```

---

## 5. Panduan Instalasi dan Pengaturan

### Langkah 1: Kloning Repositori
```bash
git clone <repository-url>
cd backend_otogrid
```

### Langkah 2: Buat dan Aktifkan Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Langkah 3: Instal Dependensi Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Konfigurasi Variabel Lingkungan (.env)

Buat file `.env` di direktori akar proyek dengan menyalin format di bawah ini dan menyesuaikan nilainya:

```env
DEBUG=True
SECRET_KEY=ganti-dengan-secret-key-produksi-yang-aman
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL/PostGIS)
DB_NAME=otogrid_db
DB_USER=otogrid_user
DB_PASSWORD=otogrid_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis Configuration (Channels / Cache)
REDIS_URL=redis://127.0.0.1:6379/1

# Google Gemini API Configuration
GEMINI_API_KEY=your_google_gemini_api_key_here
```

---

## 7. Setup Database dan Migrasi

### Langkah 1: Buat Database dan Ekstensi PostGIS di PostgreSQL
```bash
sudo -u postgres psql
```
Di dalam psql prompt:
```sql
CREATE DATABASE otogrid_db;
CREATE USER otogrid_user WITH PASSWORD 'otogrid_password';
ALTER ROLE otogrid_user SET client_encoding TO 'utf8';
ALTER ROLE otogrid_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE otogrid_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE otogrid_db TO otogrid_user;

\c otogrid_db
CREATE EXTENSION IF NOT EXISTS postgis;
\q
```

### Langkah 2: Jalankan Migrasi Database
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 8. Menjalankan Server Pengembangan

### Menjalankan Server ASGI (HTTP & WebSockets)
Untuk mendukung fungsi *real-time stream* koordinat mekanik dan WebSockets, jalankan server pengembang berbasis ASGI:

```bash
python manage.py runserver
```
Atau menggunakan Daphne ASGI server:
```bash
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

---

## 9. Fitur Utama Backend

1. **AI-Powered Triage Engine:**
   - Memproses teks keluhan kerusakan dari pengguna.
   - Menyuntikkan *System Prompt* terstruktur ke Google Gemini API.
   - Mengembalikan estimasi kerusakan, tingkat urgensi, dan rekomendasi suku cadang dalam format JSON ketat.

2. **Geo-Matching Radius Presisi:**
   - Menggunakan kalkulasi geospasial database `ST_DWithin` pada `PointField(srid=4326)`.
   - Menggunakan indeks **GiST** untuk pencarian mekanik aktif dalam radius 3–5 KM dengan eksekusi milidetik.

3. **Order State Machine:**
   - Mengelola transisi status pesanan (`SEARCHING` -> `ACCEPTED` -> `ON_THE_WAY` -> `ARRIVED` -> `WORKING` -> `COMPLETED` / `CANCELED`).
   - Menerapkan penguncian baris database `select_for_update()` untuk mencegah kondisi balapan (*race condition*).

4. **WebSockets Telemetry Stream:**
   - Meneruskan pembaruan koordinat GPS mekanik setiap 5 detik ke aplikasi pelanggan selama fase `ON_THE_WAY`.

---

## 10. Akses Dokumentasi API (Swagger UI)

Setelah server berjalan, dokumentasi interaktif API dapat diakses melalui browser pada alamat:

* **Swagger UI:** `http://127.0.0.1:8000/api/schema/swagger-ui/`
* **Redoc UI:** `http://127.0.0.1:8000/api/schema/redoc/`
* **OpenAPI Schema (JSON):** `http://127.0.0.1:8000/api/schema/`

---

## 11. Standar Kualitas Kode

* Wajib menggunakan **Type Hinting** pada setiap fungsi di lapisan *Service Layer*.
* Dilarang menuliskan API Key, kata sandi, atau token keamanan secara *hardcoded* di dalam berkas kode. Semua konfigurasi wajib dibaca dari berkas `.env`.
* Ikuti kaidah nama PEP 8 untuk kode Python.
