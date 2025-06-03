&lt;br>

&lt;p align="center">
&lt;img src="assets/images/logo_digipustaka.png" alt="Logo DigiPustaka" width="150"/>
&lt;/p>

&lt;h1 align="center">📚 DigiPustaka - Sistem Informasi Perpustakaan Digital 💻&lt;/h1>

&lt;p align="center">
Solusi modern untuk manajemen perpustakaan berbasis web, dibangun dengan Flask & Python.
&lt;/p>

&lt;p align="center">
&lt;img src="[tautan mencurigakan telah dihapus]" alt="Python Version">
&lt;img src="[tautan mencurigakan telah dihapus]" alt="Flask Version">
&lt;img src="[tautan mencurigakan telah dihapus]" alt="Database">
&lt;img src="[tautan mencurigakan telah dihapus]" alt="Frontend">
&lt;/p>

DigiPustaka adalah sebuah sistem informasi perpustakaan digital berbasis web yang dirancang untuk mengelola koleksi buku (fisik dan digital) serta aktivitas peminjaman oleh anggota. Aplikasi ini dibangun menggunakan framework Flask dengan bahasa pemrograman Python, dan menggunakan SQLite sebagai database untuk menyimpan data buku, pengguna, dan transaksi.

✨ Fitur Utama
👤 Untuk Pengguna/Anggota:
🔑 Registrasi dan login akun yang aman.
📖 Katalog buku fisik dan digital yang interaktif dengan fitur pencarian canggih dan filter berdasarkan kategori.
ℹ️ Halaman detail buku yang informatif, menampilkan ringkasan, status ketersediaan, dan informasi relevan lainnya.
📥 Fasilitas peminjaman buku fisik dan pengunduhan e-book untuk koleksi digital.
📊 Dashboard anggota untuk melihat histori peminjaman pribadi, status buku, dan notifikasi jatuh tempo.
✏️ Kemampuan untuk mengedit profil pribadi.
💳 Cetak kartu anggota digital dengan QR Code.
🛠️ Untuk Admin:
📈 Dashboard admin yang menyediakan ringkasan statistik penting perpustakaan.
📚 Manajemen koleksi buku secara penuh (CRUD - Tambah, Baca, Ubah, Hapus), termasuk kemampuan untuk mengunggah file e-book (PDF) dan gambar sampul.
👥 Manajemen pengguna, meliputi melihat daftar pengguna, detail akun, serta mengaktifkan atau menonaktifkan akun anggota.
🔄 Pengelolaan transaksi peminjaman buku fisik, termasuk proses pengembalian buku dan perhitungan denda secara otomatis.
📄 Fitur pelaporan untuk melihat berbagai aktivitas perpustakaan.
💰 Pengaturan tarif denda keterlambatan pengembalian buku.
🖼️ Tampilan Aplikasi (Contoh)
&lt;details>
&lt;summary>&lt;strong>Klik untuk melihat tampilan aplikasi&lt;/strong>&lt;/summary>
&lt;br>

Halaman Utama

&lt;p align="center">
&lt;img src="assets/images/beranda.jpg" alt="Tampilan Halaman Utama DigiPustaka" width="700"/>
&lt;/p>

Katalog Buku Digital

&lt;p align="center">
&lt;img src="assets/images/katalog_buku_digital.jpg" alt="Tampilan Katalog Buku Digital" width="700"/>
&lt;/p>

Detail Buku

&lt;p align="center">
&lt;img src="assets/images/detail_buku.jpg" alt="Tampilan Detail Buku" width="700"/>
&lt;/p>

Dashboard Anggota

&lt;p align="center">
&lt;img src="assets/images/dashboar_anggota.png" alt="Tampilan Dashboard Anggota" width="700"/>
&lt;/p>

Login & Registrasi

&lt;p align="center">
&lt;img src="assets/images/login.png" alt="Tampilan Halaman Login" width="350"/>
&lt;img src="assets/images/register.png" alt="Tampilan Halaman Registrasi" width="350"/>
&lt;/p>

Dashboard Admin

&lt;p align="center">
&lt;img src="assets/images/dashboard_admin.png" alt="Tampilan Dashboard Admin" width="700"/>
&lt;/p>

(Pastikan file gambar seperti beranda.jpg, katalog_buku_digital.jpg, dll., ada di dalam folder assets/images/ di repository Anda)

&lt;/details>

🚀 Teknologi yang Digunakan
Backend: Python 3 dengan framework Flask
Frontend: HTML5, CSS3, JavaScript
Database: SQLite
Templating Engine: Jinja2 (bawaan Flask)
Fitur Tambahan:
Pratinjau PDF untuk e-book (menggunakan pustaka PDF.js)
Pembuatan QR Code untuk validasi struk peminjaman (menggunakan pustaka qrcode.js)
🎯 Tujuan Proyek
Aplikasi DigiPustaka bertujuan untuk memodernisasi layanan perpustakaan dengan menyediakan platform digital yang intuitif dan mudah digunakan. Ini diharapkan dapat memudahkan anggota dalam mengakses informasi buku, melakukan peminjaman, dan mengelola akun mereka secara mandiri. Di sisi lain, sistem ini juga dirancang untuk membantu pustakawan atau admin dalam mengelola operasional perpustakaan secara lebih efisien. Proyek ini dikembangkan dengan memperhatikan aspek desain responsif sehingga dapat diakses dengan baik melalui berbagai perangkat, baik desktop maupun mobile.

🛠️ Cara Instalasi dan Menjalankan Proyek
Berikut adalah langkah-langkah untuk menjalankan proyek DigiPustaka di lingkungan lokal Anda:

Prasyarat:

Pastikan Anda sudah menginstal Python 3.7 atau versi lebih baru.
Pastikan Anda sudah menginstal pip (biasanya sudah terinstal bersama Python).
(Opsional, tapi sangat disarankan) Git untuk mengkloning repository.
Kloning Repository (Jika Menggunakan Git):

Bash

git clone https://github.com/kidinggg/DigiPustaka.git
cd DigiPustaka
Jika Anda mengunduh sebagai ZIP, ekstrak file ZIP tersebut.

Buat dan Aktifkan Lingkungan Virtual (Virtual Environment):
Sangat disarankan untuk menggunakan lingkungan virtual agar dependensi proyek terisolasi.

Bash

# Membuat lingkungan virtual (misalnya, bernama 'venv')
python -m venv venv

# Mengaktifkan lingkungan virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
Instal Dependensi:
Semua pustaka Python yang dibutuhkan proyek tercantum dalam file requirements.txt. Instal dengan perintah:

Bash

pip install -r requirements.txt
Inisialisasi Database:
Jika ini adalah pertama kalinya Anda menjalankan aplikasi atau jika file database (digipustaka.db) belum ada, Anda perlu menginisialisasi database menggunakan skema yang telah disediakan:

Bash

flask init-db
Perintah ini akan membuat file digipustaka.db dan tabel-tabel yang dibutuhkan, termasuk mengisi kategori default.

Jalankan Aplikasi Flask:

Bash

flask run
Atau, jika Anda ingin menjalankan dalam mode debug (akan otomatis me-reload jika ada perubahan kode):

Bash

python app.py 
(Pastikan di dalam app.py Anda ada if __name__ == '__main__': app.run(debug=True))

Buka Aplikasi di Browser:
Setelah server Flask berjalan, buka browser web Anda dan kunjungi alamat yang ditampilkan di terminal (biasanya http://127.0.0.1:5000/ atau http://localhost:5000/).

🧑‍💻 Pengembang Utama (Full Stack Developer)
Nama: Zacky Putra Setyawan
Status: Mahasiswa Sistem Informasi
Institusi: Universitas Buana Perjuangan Karawang
Fokus Utama: Bertanggung jawab atas keseluruhan arsitektur aplikasi, pengembangan backend (logika bisnis, manajemen database, API), implementasi frontend (struktur HTML, integrasi dengan backend), serta memastikan fungsionalitas dan integrasi semua fitur berjalan dengan baik.
Kontak Email: zackyputra1905@gmail.com
Profil GitHub: https://github.com/kidinggg
🤝 Tim Kontributor (Kelompok)
Naufal Fauzi Rahman

Peran Kontribusi: Desain UI/UX
Status: Mahasiswa Sistem Informasi
Institusi: Universitas Buana Perjuangan Karawang
Fokus: Merancang tampilan antarmuka pengguna (UI) yang menarik dan pengalaman pengguna (UX) yang nyaman untuk aplikasi DigiPustaka, termasuk skema warna, tata letak, dan alur navigasi.
Alfiansyah Hidayat

Peran Kontribusi: Perancangan Database & Analisis Data Awal
Status: Mahasiswa Sistem Informasi
Institusi: Universitas Buana Perjuangan Karawang
Fokus: Berkontribusi dalam perancangan skema database, normalisasi data, dan analisis awal kebutuhan data untuk fitur-fitur aplikasi.
Farid Firdaus

Peran Kontribusi: Pengelolaan Konten Database & Pengujian Modul
Status: Mahasiswa Sistem Informasi
Institusi: Universitas Buana Perjuangan Karawang
Fokus: Membantu dalam pengisian data awal (seeding) ke dalam database, serta melakukan pengujian fungsional pada modul-modul spesifik untuk memastikan integritas data.
Rahma Khoirunnisa

Peran Kontribusi: Dokumentasi Proyek & Riset Pengguna
Status: Mahasiswa Sistem Informasi
Institusi: Universitas Buana Perjuangan Karawang
Fokus: Bertanggung jawab atas penyusunan dokumentasi teknis dan pengguna, serta melakukan riset kebutuhan pengguna untuk memastikan fitur yang dikembangkan sesuai dengan ekspektasi.
&lt;br>

