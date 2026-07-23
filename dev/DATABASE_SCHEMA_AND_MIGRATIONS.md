# Dokumentasi Skema Database & Alur Migrasi OtoGrid

Dokumen ini mencatat alur migrasi database, hirarki tabel, serta panduan pengelolaan skema untuk sistem backend **OtoGrid**.

---

## 1. Alur & Histori Migrasi (Migration History)

Seluruh migrasi terpusat pada masing-masing modul aplikasi di bawah `apps/`:

### A. Modul Autentikasi (`apps/authentication`)
* **Migrasi `0001_initial.py`**:
  - Membuat tabel `authentication_user` (Custom User Model).
  - Kolom Utama: `username`, `email`, `phone_number`, `role` (`CUSTOMER` / `MECHANIC`), `is_online` (Boolean).
  - Kolom Spasial: `location_data` (`JSONField` yang menyimpan koordinat `{"lat": float, "lng": float}` dengan wrapper `@property current_location` GEOS Point).

### B. Modul Pesanan (`apps/orders`)
* **Migrasi `0001_initial.py`**:
  - Membuat tabel `orders_order`.
  - Foreign Key: `customer` (FK -> `User`), `mechanic` (FK -> `User`, Nullable).
  - Status Enum: `SEARCHING`, `ACCEPTED`, `ON_THE_WAY`, `ARRIVED`, `WORKING`, `COMPLETED`, `CANCELLED`.
  - Kolom Data: `complaint_text` (Text), `ai_triage_result` (JSONField dari Gemini AI), `location_data` (JSONField lokasi kejadian).

---

## 2. Diagram Skema Basis Data (ERD)

```text
  +-----------------------------------+             +-----------------------------------+
  |        authentication_user        |             |            orders_order           |
  +-----------------------------------+             +-----------------------------------+
  | PK  id (BigInt / Auto)            | <-------+   | PK  id (UUID)                     |
  |     username (VarChar)            |         |-- | FK  customer_id (BigInt)          |
  |     email (VarChar)               |         +-- | FK  mechanic_id (BigInt, Null)    |
  |     phone_number (VarChar)        |             |     status (VarChar)              |
  |     role (VarChar: CUSTOMER/MECH) |             |     complaint_text (Text)         |
  |     is_online (Boolean)           |             |     ai_triage_result (JSONB)      |
  |     location_data (JSONB)         |             |     location_data (JSONB)         |
  |     date_joined (Timestamp)       |             |     created_at (Timestamp)        |
  +-----------------------------------+             |     updated_at (Timestamp)        |
                                                    +-----------------------------------+
```

---

## 3. Panduan Pengelolaan Migrasi (Migration Workflow Guide)

Jika Anda melakukan perubahan pada `models.py` (misalnya menambahkan field baru atau mengubah constraints), ikuti alur standar berikut:

### Langkah 1: Ubah Model di Layer Data
Edit file model terkait:
- User Model: `apps/authentication/data/models.py`
- Order Model: `apps/orders/data/models.py`

### Langkah 2: Buat Berkas Migrasi Baru
Jalankan perintah berikut untuk menggenerasi file migrasi otomatis:
```bash
venv/bin/python manage.py makemigrations
```
*Tips: Pastikan file migrasi baru tercipta di `apps/<app_name>/migrations/000X_<deskrpisi>.py`.*

### Langkah 3: Eksekusi Migrasi ke Database
Terapkan migrasi ke database PostgreSQL:
```bash
venv/bin/python manage.py migrate
```

### Langkah 4: Verifikasi Status Migrasi
Periksa apakah seluruh migrasi telah terapkan (`[X]`):
```bash
venv/bin/python manage.py showmigrations
```

### Langkah 5: Cara Rollback (Jika Ada Kendala)
Untuk mengembalikan migrasi aplikasi ke versi tertentu (misalnya kembali ke `0001_initial` pada modul `orders`):
```bash
venv/bin/python manage.py migrate orders 0001_initial
```

---

## 4. Penanganan Spasial Dual-Mode (PostGIS vs Haversine Fallback)

Secara arsitektur, lokasi disimpan menggunakan format JSON universal `{"lat": float, "lng": float}` pada kolom `location_data`. Hal ini memastikan:
1. **Tanpa Lock-in PostGIS**: Jika dijalankan pada server standar tanpa ekstensi PostGIS, kalkulasi jarak otomatis menggunakan **Haversine Formula**.
2. **Fleksibilitas PostGIS**: Pada server produksi dengan PostGIS aktif, properti `current_location` dan `location` secara dinamis dikonversi menjadi `Point(lng, lat, srid=4326)` untuk kueri spasial resolusi tinggi (`ST_DWithin`).
