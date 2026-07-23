# **Software Requirements Specification (SRS) \- Backend Services**

**Project Name:** OtoGrid (Hyperlocal On-Demand Mechanic)  
**Platform:** Web Services (REST API & WebSockets)  
**Tech Stack:** Python 3, Django, DRF, PostgreSQL, PostGIS, Redis  
**Paradigma Arsitektur:** Monolithic Core dengan Layered/Service Architecture  
**Environment Target:** Bare-metal Linux Server

## **1\. DESKRIPSI SISTEM & ARSITEKTUR**

Backend OtoGrid berfungsi sebagai pusat kendali (*command center*) yang menangani logika bisnis, pemrosesan data spasial, integrasi kecerdasan buatan, dan komunikasi *real-time* dua arah. Sistem ini dibangun dengan arsitektur Monolitik yang efisien, beroperasi langsung di atas sistem operasi (bare-metal) untuk meminimalisir latensi jaringan internal dan memaksimalkan operasi I/O pada perangkat keras.  
Sistem mengadopsi prinsip **"Thin Views, Fat Services"**:

* **Views / ViewSets:** Hanya bertanggung jawab untuk menerima *request* HTTP, memanggil lapisan layanan (Service Layer), dan mengembalikan *response* (REST/JSON).  
* **Service Layer:** Semua logika bisnis yang kompleks (seperti algoritma pencocokan mekanik atau perhitungan tarif) wajib diletakkan dalam modul layanan terpisah (misal: order\_service.py, geo\_service.py).  
* **Data Access (Models):** Entitas murni yang merepresentasikan skema tabel database.

## **2\. SPESIFIKASI DATABASE & GEO-SPASIAL**

Menggunakan **PostgreSQL** yang diperkuat dengan ekstensi **PostGIS** untuk memproses data lokasi secara presisi.

* **Tipe Data Lokasi:** Entitas seperti profil mekanik dan pesanan darurat wajib menggunakan models.PointField(srid=4326) dari modul django.contrib.gis.db.  
* **Spatial Indexing:** Kolom koordinat wajib menggunakan indeks spasial (GiST \- *Generalized Search Tree*) pada tingkat *database* untuk menjamin eksekusi *query* geografis berskala besar dapat diselesaikan dalam hitungan milidetik.  
* **Fungsi Pencarian Radius:** Sistem menggunakan fungsi ST\_DWithin secara eksklusif untuk memindai koordinat mekanik yang berada di dalam area darurat, bukan menggunakan kalkulasi jarak *Haversine* tingkat aplikasi (Python) yang memakan banyak memori.

## **3\. MODUL SISTEM UTAMA (MODULES)**

### **3.1. Modul Autentikasi & Keamanan (Auth Service)**

* **Otentikasi Basis Token:** Menggunakan JSON Web Tokens (JWT) yang diterbitkan oleh djangorestframework-simplejwt.  
* **Role-Based Access Control (RBAC):** Token akan memuat klaim khusus (*custom claims*) yang membedakan otoritas antara *Customer* dan *Mechanic*, memblokir akses lintas *endpoint* di tingkat *middleware*.

### **3.2. Modul Pemrosesan Pesanan (Order State Machine)**

Siklus hidup pesanan harus dipastikan konsisten dan aman dari kondisi balapan (*race condition*).

* **Concurrency Control:** Menerapkan transaksi select\_for\_update() pada tingkat *database*. Jika dua pelanggan secara tidak sengaja mendapatkan mekanik yang sama dari hasil pencarian spasial, transaksi database akan mengunci *row* mekanik tersebut, memastikan mekanik hanya bisa menerima satu pesanan aktif.  
* **State Transisi:** Status pesanan bersifat kaku dan harus berurutan: SEARCHING \-\> ACCEPTED \-\> ON\_THE\_WAY \-\> WORKING \-\> COMPLETED.

### **3.3. Modul Integrasi AI (Triage Engine)**

* **Prompt Injection Terpusat:** *Endpoint* AI menerima teks bebas dari pengguna. Backend kemudian menyuntikkan *System Prompt* tersembunyi untuk mengarahkan Google Gemini API agar beroperasi murni sebagai asisten mekanik.  
* **Strict JSON Output:** *Response* dari Gemini API dipaksa dan divalidasi ke dalam skema JSON yang ketat sebelum disimpan ke dalam *database* dan disiarkan ke aplikasi mekanik.

## **4\. SPESIFIKASI KOMUNIKASI REAL-TIME (WEBSOCKETS)**

Sistem menggunakan **Django Channels** dan **Redis** (seperti *channel layer backing store*).

* **Telemetry Stream:** Saat pesanan berada pada fase ON\_THE\_WAY, *endpoint* WebSocket terbuka. Klien mekanik mengirimkan *payload* koordinat GPS (Latitude/Longitude) setiap 5 detik.  
* **Event Broadcasting:** Redis meneruskan *payload* tersebut seketika kepada klien pelanggan yang terhubung pada "ruang" (*channel group*) ID pesanan yang sama.  
* **Pemutusan Otomatis:** Koneksi soket akan otomatis diputus (*disconnect*) begitu status pesanan berubah menjadi ARRIVED atau CANCELED untuk mencegah kebocoran memori pada server Redis.

## **5\. DEPENDENSI SISTEM & PAKET (REQUIREMENTS.TXT)**

### **5.1. Kebutuhan Sistem Operasi (OS Level)**

* postgresql-14-postgis-3 (Mesin Database Inti).  
* redis-server (Message Broker & Cache In-Memory).  
* binutils, libproj-dev, gdal-bin (Pustaka C esensial untuk penerjemahan fungsi GIS oleh Python).

### **5.2. Pustaka Python Inti**

* **Web & API:** django, djangorestframework.  
* **API Documentation:** drf-spectacular (Wajib: untuk auto-generate Swagger/OpenAPI UI).  
* **Keamanan:** djangorestframework-simplejwt (Manajemen sesi asinkron), python-dotenv (Isolasi kredensial lingkungan).  
* **Database Driver:** psycopg2-binary (Adaptor PostgreSQL untuk Python berkinerja tinggi).  
* **Asynchronous Engine:** channels, channels-redis (Penanganan protokol WSS/WS), daphne (ASGI Server).  
* **AI SDK:** google-generativeai (Konektor resmi Gemini API).

## **6\. STANDAR KUALITAS KODE (CLEAN CODE)**

* **Type Hinting:** Setiap fungsi dan metode dalam *Service Layer* diwajibkan menggunakan *Type Hints* bawaan Python 3 (misal: def calculate\_radius(lat: float, lng: float) \-\> list:).  
* **Environment Variables:** Tidak boleh ada satupun *API Key* (seperti token Gemini), kredensial *database*, atau kata sandi *hash* yang ditulis keras (*hardcoded*) di dalam arsip proyek. Semua wajib dibaca dari berkas .env yang dikecualikan dari *version control*.