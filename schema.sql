-- Skema Database DigiPustaka

-- Hapus tabel jika sudah ada (untuk kemudahan inisialisasi ulang selama pengembangan)
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- Tabel Pengguna
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_lengkap TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nomor_anggota TEXT UNIQUE NOT NULL CHECK(LENGTH(nomor_anggota) == 8 AND SUBSTR(nomor_anggota, 1, 2) == 'DP'), -- Contoh: DP000001
    role TEXT NOT NULL DEFAULT 'anggota' CHECK(role IN ('admin', 'pustakawan', 'anggota')),
    alamat TEXT,
    no_telepon TEXT,
    foto_profil_path TEXT, -- Path relatif dari folder static
    tgl_daftar DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)) -- 1 untuk aktif, 0 untuk tidak aktif
);

-- Tabel Kategori Buku
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_kategori TEXT UNIQUE NOT NULL
);

-- Tabel Buku
CREATE TABLE books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    pengarang TEXT,
    penerbit TEXT,
    tahun_terbit INTEGER,
    isbn TEXT UNIQUE,
    jumlah_halaman INTEGER,
    category_id INTEGER, -- Foreign Key ke tabel categories
    jenis_buku TEXT NOT NULL CHECK(jenis_buku IN ('fisik', 'digital')), -- 'fisik' atau 'digital'
    ringkasan TEXT,
    file_ebook_path TEXT, -- Path relatif jika jenis_buku = 'digital'
    cover_image_path TEXT, -- Path relatif untuk gambar sampul
    stok_fisik INTEGER DEFAULT 0, -- Hanya berlaku jika jenis_buku = 'fisik'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Untuk waktu pembuatan buku
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE SET NULL -- Aksi jika kategori dihapus
);

-- Tabel Peminjaman
CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- Foreign Key ke tabel users
    book_id INTEGER NOT NULL, -- Foreign Key ke tabel books
    tanggal_pinjam DATETIME DEFAULT CURRENT_TIMESTAMP,
    tanggal_jatuh_tempo DATETIME, -- Untuk buku fisik
    tanggal_kembali DATETIME, -- Untuk buku fisik
    tipe_pinjaman TEXT NOT NULL CHECK(tipe_pinjaman IN ('fisik', 'digital')), -- Sesuai jenis_buku
    status_pinjaman TEXT NOT NULL DEFAULT 'menunggu_konfirmasi_admin' CHECK( -- Default diubah
        status_pinjaman IN (
            'menunggu_konfirmasi_admin', 
            'dipinjam',                 
            'dikembalikan',             
            'terlambat_dikembalikan',   
            'diunduh'                   
        )
    ),
    denda INTEGER DEFAULT 0, -- Hanya berlaku untuk buku fisik yang terlambat
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE, -- Aksi jika pengguna dihapus
    FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE  -- Aksi jika buku dihapus
);

-- Indeks untuk optimasi query
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_books_judul ON books (judul);
CREATE INDEX IF NOT EXISTS idx_books_category_id ON books (category_id);
CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans (user_id);
CREATE INDEX IF NOT EXISTS idx_loans_book_id ON loans (book_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans (status_pinjaman);

-- ... (definisi tabel lain seperti users, books, loans, categories) ...

-- Tabel untuk Permintaan Aksi Pengguna oleh Pustakawan
CREATE TABLE user_action_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_user_id INTEGER NOT NULL, -- ID Pustakawan yang meminta
    target_user_id INTEGER NOT NULL,    -- ID Anggota yang menjadi target aksi
    action_type TEXT NOT NULL CHECK(action_type IN ('deactivate_account', 'activate_account', 'change_role_to_pustakawan', 'change_role_to_anggota')),
    reason TEXT, -- Alasan permintaan (opsional, tapi bagus untuk ada)
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_by_admin_id INTEGER, -- ID Admin yang memproses
    processed_at DATETIME,
    admin_notes TEXT, -- Catatan dari Admin saat memproses
    FOREIGN KEY (requester_user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (processed_by_admin_id) REFERENCES users (user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_action_requests_status ON user_action_requests (status);
CREATE INDEX IF NOT EXISTS idx_action_requests_target_user ON user_action_requests (target_user_id);