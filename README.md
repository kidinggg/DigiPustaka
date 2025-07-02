# 📚 DigiPustaka - Sistem Informasi Perpustakaan Digital 💻

---

## ✨ Fitur Utama

### 👤 Untuk Pengguna/Anggota:

- 🔑 Registrasi dan login aman (akun diverifikasi aktif).
- 📖 Jelajahi katalog buku fisik & digital dengan filter dan pencarian.
- ℹ️ Lihat detail buku: ringkasan, kategori, status, dan file.
- 📥 Unduh eBook (jika tersedia) langsung dari sistem.
- 📅 Ajukan permintaan peminjaman buku fisik.
- 🔔 Notifikasi peminjaman, jatuh tempo, dan denda keterlambatan otomatis.
- 📊 Dashboard pribadi: histori peminjaman & status buku.
- ✏️ Edit profil & unggah foto.
- 💳 Kartu anggota digital dengan QR Code.

### 🛠️ Untuk Staf/Admin/Pustakawan:

- 📊 Dashboard statistik lengkap & aktivitas terbaru.
- 📖 CRUD buku, kategori, cover, dan file eBook.
- 🗂️ Tambahkan kategori baru saat input buku.
- 📑 Kelola permintaan pinjam buku fisik (konfirmasi & pengembalian).
- ⏰ Denda otomatis untuk pengembalian terlambat.
- 👥 Manajemen pengguna: edit, aktif/nonaktif, ubah peran.
- 📨 Sistem permintaan aksi (oleh pustakawan → disetujui admin).
- 🔐 Hak akses berdasarkan role (anggota, pustakawan, admin).
- 📡 API JSON untuk detail peminjaman (khusus pustakawan/admin).

---

## 🖼️ Tampilan Aplikasi

### Halaman Beranda

### Katalog & Detail Buku

### Dashboard Anggota & Admin

### Login & Registrasi

---

## 🛠️ Cara Instalasi

### Prasyarat:

- Python >= 3.7
- pip
- (Opsional) Git

### Langkah-langkah:

1. **Klon Repository**:

```bash
git clone https://github.com/kidinggg/DigiPustaka.git
cd DigiPustaka
```

2. **Buat & Aktifkan Virtual Environment**:

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install Dependensi**:

```bash
pip install -r requirements.txt
```

4. **Inisialisasi Database (sekali saja)**:

```bash
flask --app app.py init-db
```

5. **Jalankan Aplikasi**:

```bash
flask run
# atau
python app.py
```

6. **Akses Aplikasi**: Buka browser dan kunjungi: [http://localhost:5000](http://localhost:5000)

---

## ⚙️ Teknologi yang Digunakan

- **Backend**: Python 3 + Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite
- **Templating**: Jinja2
- **Fitur Tambahan**:
  - Pratinjau PDF (PDF.js)
  - QR Code (qrcode.js)
  - Session, Flash Message
  - Hak Akses Berbasis Role

---

## 👨‍💻 Pengembang Utama

**Zacky Putra Setyawan**\
Full Stack Developer (Backend, Frontend, Database, Integrasi Fitur)\
Mahasiswa Sistem Informasi – Universitas Buana Perjuangan Karawang\
📧 [zackyputra1905@gmail.com](mailto\:zackyputra1905@gmail.com)\
📧 [si23.zackysetyawan@mhs.ubpkarawang.ac.id](mailto\:si23.zackysetyawan@mhs.ubpkarawang.ac.id)\
🔗 [GitHub @kidinggg](https://github.com/kidinggg)

---

## 🤝 Tim Kontributor

- **Naufal Fauzi Rahman** – UI/UX & Dokumentasi
- **Alfiansyah Hidayat** – Konten, Database & Analisis Data
- **Farid Firdaus** – Pengujian Modul & Konten
- **Rahma Khoirunnisa** – Riset Pengguna & Database

> Seluruh kontributor merupakan mahasiswa Sistem Informasi Universitas Buana Perjuangan Karawang.

---

## 🎯 Tujuan Proyek

**DigiPustaka** bertujuan menjadi sistem informasi perpustakaan yang:

- Modern & Responsif
- Mendukung peminjaman digital dan fisik
- Meningkatkan efisiensi kerja pustakawan/admin
- Mempermudah akses buku bagi mahasiswa

---

## 📬 Kontak & Kontribusi

Untuk laporan bug, permintaan fitur, atau kontribusi:

- Buka [Issues](https://github.com/kidinggg/DigiPustaka/issues)
- Atau hubungi langsung melalui email pengembang utama

---

🚀 Selamat menggunakan **DigiPustaka** dan ikut serta dalam modernisasi perpustakaan digital Indonesia!

