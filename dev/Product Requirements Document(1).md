# **Product Requirements Document (PRD) \- OtoGrid & OtoGrid Partner**

**Project Name:** OtoGrid (Hyperlocal On-Demand Mechanic)  
**Platform:** Mobile App (Flutter untuk iOS & Android) & Backend (Django API)  
**Target Market:** Pengendara roda dua dan empat di area urban dan sub-urban.

## **1\. PENDAHULUAN & VISI PRODUK**

OtoGrid adalah platform SaaS (Software as a Service) hiperlokal yang menghubungkan pengendara yang mengalami kendala kendaraan darurat di jalan dengan mekanik independen atau bengkel terdekat secara seketika (*real-time*).  
Visi utama OtoGrid adalah menghilangkan kepanikan, ketidakpastian harga, dan lamanya waktu tunggu saat kendaraan mogok, sekaligus memberdayakan mekanik lokal (UMKM) agar mendapatkan akses langsung ke pelanggan tanpa harus memiliki bengkel fisik di jalan raya utama. Sistem ini ditenagai oleh kecerdasan buatan (AI) untuk diagnosis awal dan teknologi pemetaan geospasial presisi tinggi.

## **2\. DETAIL MASALAH DAN SOLUSI (PROBLEM & SOLUTION)**

### **2.1. Masalah Pengguna (Pain Points)**

* **Sisi Pelanggan (Pengendara):**  
  * Kepanikan tingkat tinggi saat kendaraan mati mendadak di tengah jalan, terutama di malam hari atau di area sepi.  
  * Keterbatasan pengetahuan teknis otomotif (tidak tahu cara menjelaskan kerusakan kepada mekanik).  
  * Ketakutan akan "getok harga" atau penipuan tarif perbaikan oleh bengkel yang tidak bertanggung jawab.  
* **Sisi Mitra (Mekanik/Bengkel Kecil):**  
  * Bengkel yang berlokasi di dalam gang atau jauh dari jalan raya utama kehilangan potensi pelanggan darurat.  
  * Sering kali mekanik tiba di lokasi mogok tanpa membawa suku cadang atau kunci yang tepat karena pelanggan tidak bisa menjelaskan kerusakannya dengan jelas di telepon.

### **2.2. Solusi Produk (OtoGrid)**

* **AI-Powered Triage (Diagnosis Cerdas):** Pelanggan cukup mengetik keluhan awam (contoh: "mesin bunyi kletek-kletek lalu keluar asap"). Sistem AI akan menerjemahkan bahasa awam tersebut menjadi diagnosis teknis probabilitas tinggi, sehingga mekanik tahu persis alat dan suku cadang apa yang harus dibawa sebelum berangkat.  
* **Absolute Radius Matching:** Menggunakan teknologi spasial (PostGIS), sistem tidak melempar pesanan ke sembarang bengkel, melainkan memindai koordinat mekanik yang sedang aktif dalam radius absolut 3 hingga 5 kilometer untuk menjamin waktu tiba (ETA) di bawah 15 menit.  
* **Real-time Transparency:** Pelanggan dapat melihat pergerakan mekanik di atas peta secara langsung (seperti aplikasi pemesanan kendaraan), memberikan rasa aman dan kepastian.

## **3\. PROFIL PENGGUNA (USER PERSONA)**

### **3.1. Pengguna Utama (OtoGrid App)**

* **Demografi:** Pria & Wanita, usia 18 \- 45 tahun, pekerja kantoran, mahasiswa, atau pengendara komuter harian.  
* **Kondisi Psikologis saat Menggunakan Aplikasi:** Sedang cemas, terburu-buru, panik, dan membutuhkan solusi secepat mungkin tanpa harus berpikir keras.  
* **Kebutuhan Antarmuka:** Tombol besar, teks kontras, proses pemesanan kurang dari 3 langkah, dan kejelasan status.

### **3.2. Mitra Mekanik (OtoGrid Partner App)**

* **Demografi:** Pria, usia 20 \- 55 tahun, mekanik lepasan, atau pemilik bengkel kecil UMKM.  
* **Kondisi Psikologis saat Menggunakan Aplikasi:** Sedang bekerja, tangan kotor, atau sedang mengendarai motor menuju lokasi pelanggan.  
* **Kebutuhan Antarmuka:** Notifikasi suara yang sangat keras, teks raksasa untuk membaca diagnosis, dan navigasi GPS (Google Maps) yang terintegrasi dalam satu ketukan.

## **4\. SPESIFIKASI FITUR SECARA MENDETAIL (CORE FEATURES)**

### **4.1. Modul Pembuatan Pesanan & Diagnosis AI**

Proses ini dirancang agar selesai dalam waktu kurang dari 30 detik.

1. **Konfirmasi Lokasi:** Aplikasi secara otomatis menarik titik koordinat GPS pengguna. Pengguna dapat menggeser pin lokasi untuk akurasi.  
2. **Input Keluhan:** Terdapat kotak teks bebas. Pengguna mengetik masalah mereka.  
3. **Proses Backend (AI):** Begitu tombol "Cari Bantuan" ditekan, backend mengirim keluhan ke Gemini API.  
4. **Output ke Mekanik:** AI menyusun data JSON berisi: Kemungkinan Kerusakan (misal: Busi Mati/Overheat), Tingkat Bahaya (misal: Menengah), dan Rekomendasi Bawaan (misal: Bawa Busi Cadangan, Kunci Pas 10, Air Radiator).

### **4.2. Modul Geo-Matching & Live Radar**

1. **Radar UI (Pelanggan):** Layar pelanggan berubah menjadi animasi radar yang menyapu area.  
2. **Spatial Query (Backend):** Database mencari profil mekanik dengan status is\_online \= True yang berada dalam area ST\_DWithin (radius 5 KM dari lokasi pelanggan).  
3. **Broadcasting (WebSockets):** Notifikasi pesanan masuk dikirimkan ke perangkat mekanik yang memenuhi syarat secara bersamaan.  
4. **Sistem Penerimaan (First-Come-First-Serve):** Mekanik pertama yang menekan "Terima Pesanan" akan mendapatkan pekerjaan tersebut. Sistem langsung membatalkan pesanan di layar mekanik lain.

### **4.3. Modul Order State Machine (Alur Transaksi)**

Status pesanan diatur secara ketat untuk mencegah duplikasi data:

* SEARCHING: Memindai mekanik di sekitar.  
* ACCEPTED: Mekanik merespons, nama dan plat nomor mekanik ditampilkan ke pelanggan.  
* ON\_THE\_WAY: WebSocket aktif. Titik koordinat mekanik dikirim setiap 5 detik ke pelanggan. Peta bergerak secara real-time.  
* ARRIVED: Mekanik menekan tombol "Saya Sudah Sampai". Pelanggan menerima notifikasi.  
* WORKING: Mekanik sedang melakukan perbaikan. Timer durasi perbaikan berjalan.  
* COMPLETED: Perbaikan selesai, total tagihan dimasukkan oleh mekanik, pelanggan memberikan rating dan ulasan.  
* CANCELED: Dibatalkan oleh pelanggan (sebelum mekanik jalan) atau oleh mekanik (kendala di jalan).

## **5\. ARSITEKTUR SISTEM (PRODUCTION-READY)**

* **Frontend Klien & Mitra:** Flutter (Dart) dengan Clean Architecture dan Riverpod State Management.  
* **Backend API:** Python (Django \+ Django REST Framework).  
* **Pemrosesan Spasial:** PostgreSQL dengan ekstensi PostGIS (Penyimpanan koordinat PointField).  
* **Real-time Broker:** Redis dan Django Channels untuk menangani koneksi lalu lintas koordinat (WebSockets).  
* **AI Engine:** Google Gemini API (Terhubung secara aman di sisi server Backend, tidak ada API key di aplikasi Flutter).

## **6\. PANDUAN COPYWRITING & TONE OF VOICE**

Teks di dalam aplikasi harus menghilangkan kesan aplikasi "uji coba". Gaya bahasa (Tone of Voice) harus: **Empatik, Cepat Tanggap, Profesional, dan Menenangkan.**

* **Layar Kosong (Belum ada pesanan \- Aplikasi Pelanggan):**  
  * *Headline:* "Kami siap membantu Anda."  
  * *Sub-teks:* "Aktifkan lokasi Anda agar kami bisa menemukan mekanik terdekat saat Anda membutuhkan bantuan darurat."  
* **Saat Menunggu AI / Mencari Mekanik (Radar Berputar):**  
  * *Teks Indikator:* "Sedang menganalisis kendala Anda..." berubah menjadi "Menghubungi mekanik terdekat dalam radius 5 km..." (Jangan gunakan teks seperti "Loading data" atau "Fetching API").  
* **Notifikasi Pesanan Masuk (Aplikasi Mekanik):**  
  * *Headline:* "Darurat Otomotif Jarak 2.4 KM\!"  
  * *Isi:* "Pelanggan mengalami kebocoran radiator. Estimasi perbaikan ringan. Terima pesanan ini?"  
* **Pesan Error (Jika Koneksi Terputus):**  
  * *Teks:* "Koneksi jaringan Anda tidak stabil. Kami sedang mencoba menyambungkan kembali secara otomatis. Jangan tutup aplikasi."  
* **Saat Mekanik Dalam Perjalanan:**  
  * *Teks Bantuan:* "Bantuan sedang meluncur. Budi (Mekanik) diperkirakan tiba dalam 8 menit. Tetap berada di tempat yang aman."