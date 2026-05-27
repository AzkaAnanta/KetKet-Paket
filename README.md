# 📦 KetKet Paket — Asisten Rute Kurir Pintar

**KetKet Paket** adalah aplikasi asisten rute kurir berbasis web (*mobile-responsive*) yang dirancang khusus untuk mengoptimalkan urutan pengantaran paket. Dengan memanfaatkan algoritma **TSP (Traveling Salesman Problem)**, aplikasi ini membantu kurir menghemat jarak, waktu, dan biaya bensin secara signifikan dalam pengiriman *last-mile*.

---

## 🚀 Fitur Utama
* **Optimasi TSP Dinamis:** Menghitung urutan rute terbaik dari posisi GPS kurir saat ini ke seluruh titik paket.
* **Integrasi Peta Interaktif:** Visualisasi rute menggunakan Folium Map dengan pin bernomor sesuai urutan optimal.
* **Navigasi Riil Google Maps:** Tombol *redirect* yang langsung membuka aplikasi Google Maps di HP kurir untuk navigasi *turn-by-turn*.
* **Re-routing Otomatis:** Menghitung ulang rute terbaik secara dinamis untuk sisa paket yang belum diantar setelah kurir menekan tombol Selesai Antar.
* **Sistem Fallback Pintar:** Aplikasi tetap berjalan normal secara *offline* atau tanpa dependensi penuh berkat mekanisme *fallback* otomatis.

---

## 🛠️ Panduan Instalasi & Penggunaan

### 1. Prasyarat (Prerequisites)
Pastikan laptop/komputer Anda sudah terinstal Python (versi 3.10 atau di atasnya).

### 2. Instalasi Dependensi
Buka terminal atau command prompt di direktori projek Anda, lalu jalankan perintah berikut untuk menginstal semua library yang dibutuhkan:

pip install -r requirements.txt

### 3. Menjalankan Aplikasi
Untuk meluncurkan server lokal Streamlit dan membuka aplikasi di browser, jalankan perintah berikut:

streamlit run app.py

Tip: Untuk pengalaman terbaik, buka menu Inspect Element di browser dan aktifkan mode tampilan Mobile (Responsive).

---

## 🏛️ Arsitektur Kode
Projek ini dibagi secara modular menjadi dua file utama untuk memisahkan logika bisnis (backend) dan antarmuka pengguna (frontend).

### 1. solver.py — Backend Logic
Mengatur model data, kalkulasi jarak, dan pemecahan algoritma optimasi graf.
* **Stop:** Data model (class) untuk menyimpan informasi setiap titik pengiriman.
* **DUMMY_PACKAGES:** Inisialisasi awal berupa 7 titik paket nyata di Surabaya (Klampis, Dharmahusada, Basuki Rahmat, Kenjeran, dll) yang siap digunakan untuk pengujian.
* **fetch_osrm_matrix():** Mengambil matriks jarak & waktu pengantaran riil lewat jalan raya menggunakan OSRM API.
* **solve_tsp():** Menyelesaikan rute terpendek menggunakan Google OR-Tools (PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH).
* **estimate_savings():** Menghitung statistik penghematan jarak, bensin, dan waktu dibandingkan dengan rute sekuensial (acak/urut input).
* **build_google_maps_url():** Membuat tautan URL navigasi resmi Google Maps untuk diarahkan langsung ke aplikasi bawaan HP.

### 2. app.py — Frontend Streamlit
Mengatur visualisasi antarmuka aplikasi kurir yang dibagi menjadi 3 menu utama (Tabs):
* **📋 Daftar Paket:** Berfungsi untuk menambah atau menghapus alamat secara manual, melihat antrean paket saat ini, dan mengeksekusi tombol Optimalkan Rute.
* **🗺️ Peta Rute:** Menampilkan peta interaktif Folium (CartoDB Positron) dengan pin kurir berwarna merah, pin paket bernomor urut, dan garis rute Navy TSP. Dilengkapi kartu navigasi tujuan terdekat, tombol Google Maps, serta tombol ✅ Selesai Antar.
* **📊 Ringkasan:** Menampilkan progress bar penyelesaian tugas, statistik total penghematan (jarak/bensin/waktu) dalam bentuk dashboard card, tabel urutan pengantaran, dan tombol Reset.


