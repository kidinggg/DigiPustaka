DigiPustaka adalah sebuah sistem informasi perpustakaan digital berbasis web yang dirancang untuk mengelola koleksi buku (fisik dan digital) serta aktivitas peminjaman oleh anggota. Aplikasi ini dibangun menggunakan framework Flask dengan bahasa pemrograman Python, dan menggunakan SQLite sebagai database untuk menyimpan data buku, pengguna, dan transaksi.

Fitur Utama:

Untuk Pengguna/Anggota:
Registrasi dan login akun.
Melihat katalog buku fisik dan digital dengan fitur pencarian dan filter per kategori.
Melihat detail buku, termasuk ringkasan dan status ketersediaan.
Meminjam buku fisik dan mengunduh e-book untuk buku digital.
Melihat histori peminjaman pribadi dan notifikasi jatuh tempo.
Mengedit profil pribadi dan mencetak kartu anggota digital.
Untuk Admin:
Dashboard admin dengan ringkasan statistik perpustakaan.
Manajemen koleksi buku secara penuh (CRUD - Tambah, Baca, Ubah, Hapus), termasuk unggah file e-book dan gambar sampul.
Manajemen pengguna (melihat daftar pengguna, detail, dan mengaktifkan/menonaktifkan akun).
Mengelola transaksi peminjaman buku fisik (proses pengembalian dan perhitungan denda).
Melihat laporan aktivitas perpustakaan.
Mengatur tarif denda keterlambatan.
Teknologi yang Digunakan (Implied):

Backend: Python (Flask)
Frontend: HTML, CSS, JavaScript
Database: SQLite
Templating Engine: Jinja2 (bawaan Flask)
Fitur Tambahan: Preview PDF untuk e-book (menggunakan PDF.js), pembuatan QR Code untuk struk peminjaman.
Tujuan Proyek:

Aplikasi ini bertujuan untuk memodernisasi layanan perpustakaan dengan menyediakan platform digital yang memudahkan anggota untuk mengakses informasi buku, meminjam, dan mengelola akun mereka, serta memudahkan pustakawan/admin dalam mengelola operasional perpustakaan. Proyek ini juga telah dikembangkan dengan memperhatikan aspek responsivitas agar dapat diakses dengan baik melalui perangkat desktop maupun mobile.

