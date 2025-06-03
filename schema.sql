DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS loans;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_lengkap TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nomor_anggota TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'user', -- 'user' atau 'admin'
    foto_profil_path TEXT,
    alamat TEXT,                       -- KOLOM BARU
    no_telepon TEXT,                   -- KOLOM BARU
    is_active INTEGER DEFAULT 1, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP 
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_kategori TEXT UNIQUE NOT NULL 
);

CREATE TABLE books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    pengarang TEXT,
    category_id INTEGER,
    jenis_buku TEXT NOT NULL, 
    ringkasan TEXT,
    file_ebook_path TEXT,
    cover_image_path TEXT,
    stok_fisik INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE SET NULL 
);

CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    tanggal_pinjam TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanggal_jatuh_tempo TIMESTAMP,
    tanggal_kembali TIMESTAMP,
    tipe_pinjaman TEXT NOT NULL, 
    status_pinjaman TEXT NOT NULL DEFAULT 'dipinjam', 
    denda REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE 
);
