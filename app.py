import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g, flash, session, abort, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import functools 
import os
import datetime
import re 
from markupsafe import Markup, escape

app = Flask(__name__)
DATABASE = 'digipustaka.db'
app.secret_key = 'ganti_dengan_kunci_rahasia_super_aman_dan_unik_milik_anda_123!@#' 

# Konfigurasi Path dan Folder Upload
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')
UPLOAD_FOLDER_COVER = os.path.join(STATIC_FOLDER, 'uploads', 'covers')
UPLOAD_FOLDER_EBOOK = os.path.join(STATIC_FOLDER, 'uploads', 'ebooks')
UPLOAD_FOLDER_PROFILE = os.path.join(STATIC_FOLDER, 'uploads', 'profile_photos')
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_EBOOK = {'pdf', 'epub', 'mobi'} 
app.config['UPLOAD_FOLDER_COVER'] = UPLOAD_FOLDER_COVER
app.config['UPLOAD_FOLDER_EBOOK'] = UPLOAD_FOLDER_EBOOK
app.config['UPLOAD_FOLDER_PROFILE'] = UPLOAD_FOLDER_PROFILE
os.makedirs(UPLOAD_FOLDER_COVER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_EBOOK, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_PROFILE, exist_ok=True)

DENDA_PER_HARI = 500 
JATUH_TEMPO_HARI_PERINGATAN = 3

@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ''
    s_escaped = escape(str(s))
    s_br = re.sub(r'(\r\n|\r|\n)', '<br>\n', s_escaped)
    return Markup(s_br)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        default_categories = [
            'Fiksi', 'Non-Fiksi', 'Sains & Teknologi', 'Komputer & Internet', 
            'Sejarah', 'Biografi', 'Pendidikan', 'Bahasa & Sastra', 
            'Seni & Desain', 'Psikologi', 'Pengembangan Diri', 'Bisnis & Ekonomi',
            'Kesehatan', 'Agama & Spiritualitas', 'Anak-Anak', 'Remaja', 
            'Komik', 'Referensi', 'Novel', 'Majalah', 'Jurnal Ilmiah'
        ]
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(category_id) FROM categories")
        count = cursor.fetchone()[0]
        if count == 0: 
            for category_name in default_categories:
                try:
                    cursor.execute("INSERT INTO categories (nama_kategori) VALUES (?)", (category_name,))
                except sqlite3.IntegrityError:
                    pass 
            db.commit()
            print(f"{len(default_categories)} kategori default telah ditambahkan.")
        else:
            print("Tabel kategori tidak kosong, kategori default tidak ditambahkan.")
    print("Database initialized.")

@app.cli.command('init-db')
def init_db_command():
    init_db()
    print('Database telah diinisialisasi dengan benar (termasuk kategori default jika tabel kosong).')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Anda harus login untuk mengakses halaman ini.", "warning")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Anda harus login untuk mengakses halaman ini.", "warning")
            return redirect(url_for('login', next=request.url))
        if g.user['role'] != 'admin':
            flash("Anda tidak memiliki izin Admin untuk mengakses halaman ini.", "danger")
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

def staff_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Anda harus login untuk mengakses halaman ini.", "warning")
            return redirect(url_for('login', next=request.url))
        if g.user['role'] not in ['admin', 'pustakawan']:
            flash("Anda tidak memiliki izin Staf untuk mengakses halaman ini.", "danger")
            if g.user['role'] == 'anggota':
                return redirect(url_for('dashboard'))
            return redirect(url_for('index')) 
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None 
    if user_id is not None:
        db = get_db()
        user_data_row = db.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
        if user_data_row and user_data_row['is_active'] == 1:
             g.user = dict(user_data_row) 
             g.user['tgl_daftar_dt'] = parse_datetime_str(g.user.get('tgl_daftar'))
             g.user['updated_at_dt'] = parse_datetime_str(g.user.get('updated_at'))
        elif user_data_row and user_data_row['is_active'] == 0:
             session.clear() 

def parse_datetime_str(date_str, format='%Y-%m-%d %H:%M:%S'):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str.split('.')[0], format)
    except (ValueError, TypeError):
        print(f"Warning: Could not parse date string '{date_str}' with format '{format}'")
        return None

@app.context_processor
def inject_global_vars():
    user_for_template = g.get('user', None) 
    return {'current_year': datetime.datetime.now().year, 
            'g_user': user_for_template,
            'now': datetime.datetime.now()}

# --- RUTE PUBLIK DAN ANGGOTA ---
@app.route('/')
def index():
    db = get_db()
    recent_books = db.execute(
        """
        SELECT b.book_id, b.judul, b.pengarang, b.cover_image_path, b.jenis_buku, c.nama_kategori
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        ORDER BY b.book_id DESC 
        LIMIT 4 
        """
    ).fetchall()
    total_buku = db.execute("SELECT COUNT(book_id) FROM books").fetchone()[0] or 0
    total_anggota = db.execute("SELECT COUNT(user_id) FROM users WHERE role = 'anggota' AND is_active = 1").fetchone()[0] or 0
    total_peminjaman_fisik_aktif = db.execute("SELECT COUNT(loan_id) FROM loans WHERE status_pinjaman = 'dipinjam' AND tipe_pinjaman = 'fisik'").fetchone()[0] or 0
    total_unduhan_digital = db.execute("SELECT COUNT(loan_id) FROM loans WHERE tipe_pinjaman = 'digital' AND status_pinjaman = 'diunduh'").fetchone()[0] or 0
    return render_template('index.html', 
                           title="Selamat Datang di Digi Pustaka", 
                           recent_books=recent_books,
                           total_buku=total_buku,
                           total_anggota=total_anggota,
                           total_peminjaman_fisik_aktif=total_peminjaman_fisik_aktif,
                           total_unduhan_digital=total_unduhan_digital)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        nama_lengkap = request.form['nama_lengkap']
        email = request.form['email']
        password = request.form['password']
        konfirmasi_password = request.form['konfirmasi_password']
        alamat = request.form.get('alamat', '').strip()
        no_telepon = request.form.get('nomor_telepon', '').strip()
        db = get_db()
        error = None
        nomor_anggota_final = None
        prefix_id = "DP" 
        panjang_nomor_angka = 6 
        try:
            last_member_data = db.execute(
                f"SELECT nomor_anggota FROM users WHERE nomor_anggota LIKE '{prefix_id}%' "
                f"ORDER BY CAST(SUBSTR(nomor_anggota, {len(prefix_id) + 1}) AS INTEGER) DESC LIMIT 1"
            ).fetchone()
            next_num = 1
            if last_member_data and last_member_data['nomor_anggota']:
                numeric_part_str = last_member_data['nomor_anggota'][len(prefix_id):]
                if numeric_part_str.isdigit():
                    next_num = int(numeric_part_str) + 1
            nomor_anggota_final = f"{prefix_id}{str(next_num).zfill(panjang_nomor_angka)}"
        except Exception as e:
            error = f"Gagal menghasilkan nomor anggota: {e}"
        if not error:
            if not nama_lengkap: error = 'Nama lengkap diperlukan.'
            elif not email: error = 'Email diperlukan.'
            elif not password: error = 'Password diperlukan.'
            elif len(password) < 6: error = 'Password minimal 6 karakter.'
            elif password != konfirmasi_password: error = 'Password dan konfirmasi password tidak cocok.'
        if not error:
            user_by_email = db.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
            if user_by_email: error = f"Email {email} sudah terdaftar."
        if not error:
            try:
                db.execute(
                    """INSERT INTO users (nama_lengkap, email, password, nomor_anggota, role, 
                                          alamat, no_telepon, foto_profil_path, 
                                          tgl_daftar, updated_at, is_active) 
                       VALUES (?, ?, ?, ?, 'anggota', ?, ?, NULL, datetime('now', 'localtime'), datetime('now', 'localtime'), 1)""",
                    (nama_lengkap, email, generate_password_hash(password), nomor_anggota_final,
                     alamat if alamat else None, no_telepon if no_telepon else None),
                )
                db.commit()
                flash('Registrasi berhasil! Silakan login.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError: error = "Terjadi kesalahan unik saat menyimpan data (misal nomor anggota duplikat). Coba lagi."
            except sqlite3.Error as e: 
                error = f"Gagal menyimpan ke database: {e}"
                print(f"SQLite Error on INSERT: {e}")
        if error: flash(error, 'danger')
    return render_template('register.html', title="Registrasi Anggota")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        if g.user['role'] in ['admin', 'pustakawan']:
            return redirect(url_for('admin_dashboard'))
        elif g.user['role'] == 'anggota':
            return redirect(url_for('dashboard'))
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user_data = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user_data is None: error = 'Email tidak ditemukan.'
        elif not check_password_hash(user_data['password'], password): error = 'Password salah.'
        elif user_data['is_active'] == 0: 
            error = 'Akun Anda saat ini tidak aktif. Silakan hubungi administrator.'
        if error is None:
            session.clear()
            session['user_id'] = user_data['user_id']
            session['user_role'] = user_data['role'] 
            flash(f"Selamat datang kembali, {user_data['nama_lengkap']}!", 'success')
            if user_data['role'] == 'admin' or user_data['role'] == 'pustakawan':
                return redirect(url_for('admin_dashboard'))
            elif user_data['role'] == 'anggota':
                return redirect(url_for('dashboard'))
            else: 
                return redirect(url_for('index'))
        flash(error, 'danger')
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    session.clear()
    g.user = None
    flash("Anda telah berhasil logout.", 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if g.user['role'] != 'anggota':
        flash("Halaman ini hanya untuk Anggota.", "warning")
        if g.user['role'] in ['admin', 'pustakawan']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    db = get_db()
    loan_history_raw = db.execute(
        """
        SELECT l.loan_id, l.tanggal_pinjam, l.tanggal_jatuh_tempo, l.tanggal_kembali, 
               l.tipe_pinjaman, l.status_pinjaman, l.denda, b.judul AS judul_buku, b.book_id
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        WHERE l.user_id = ?
        ORDER BY l.tanggal_pinjam DESC
        """,
        (g.user['user_id'],)
    ).fetchall()
    
    loan_history = []
    for row_raw in loan_history_raw:
        loan_item = dict(row_raw)
        loan_item['tanggal_pinjam_dt'] = parse_datetime_str(loan_item.get('tanggal_pinjam'))
        loan_item['tanggal_jatuh_tempo_dt'] = parse_datetime_str(loan_item.get('tanggal_jatuh_tempo'))
        loan_item['tanggal_kembali_dt'] = parse_datetime_str(loan_item.get('tanggal_kembali'))
        loan_history.append(loan_item)

    total_unpaid_fines = 0
    upcoming_due_books = []
    overdue_books = []
    today = datetime.date.today() 
    for loan in loan_history:
        if loan['status_pinjaman'] == 'terlambat_dikembalikan' and loan['denda'] > 0:
             total_unpaid_fines += loan['denda']
        if loan['tipe_pinjaman'] == 'fisik' and loan['status_pinjaman'] == 'dipinjam' and loan.get('tanggal_jatuh_tempo_dt'):
            due_date = loan['tanggal_jatuh_tempo_dt'].date()
            days_until_due = (due_date - today).days
            if days_until_due < 0: 
                overdue_books.append({
                    'judul': loan['judul_buku'], 'jatuh_tempo': due_date.strftime('%Y-%m-%d'),
                    'hari_terlambat': abs(days_until_due), 'book_id': loan['book_id']
                })
            elif 0 <= days_until_due <= JATUH_TEMPO_HARI_PERINGATAN: 
                upcoming_due_books.append({
                    'judul': loan['judul_buku'], 'jatuh_tempo': due_date.strftime('%Y-%m-%d'),
                    'sisa_hari': days_until_due, 'book_id': loan['book_id']
                })
    return render_template('dashboard.html', 
                           title="Dashboard Anggota", loan_history=loan_history, 
                           total_unpaid_fines=total_unpaid_fines,
                           upcoming_due_books=upcoming_due_books, overdue_books=overdue_books)

@app.route('/member_card')
@login_required
def member_card():
    if g.user['role'] != 'anggota':
        flash("Hanya anggota yang memiliki kartu anggota.", "warning")
        return redirect(url_for('index'))
    if not g.user:
        flash("Gagal memuat data pengguna.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('member_card.html', title="Kartu Anggota Digital", user=g.user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db = get_db()
    error = None
    if request.method == 'POST':
        nama_lengkap = request.form['nama_lengkap']
        email_baru = request.form['email']
        alamat_baru = request.form.get('alamat', '').strip()
        no_telepon_baru = request.form.get('nomor_telepon', '').strip()
        password_baru = request.form.get('password_baru') 
        konfirmasi_password_baru = request.form.get('konfirmasi_password_baru')
        if not nama_lengkap: error = "Nama lengkap tidak boleh kosong."
        elif not email_baru: error = "Email tidak boleh kosong."
        if email_baru != g.user['email']:
            user_dengan_email_baru = db.execute('SELECT user_id FROM users WHERE email = ? AND user_id != ?', (email_baru, g.user['user_id'])).fetchone()
            if user_dengan_email_baru: error = f"Email {email_baru} sudah digunakan oleh pengguna lain."
        hashed_password_to_update = g.user['password'] 
        if password_baru: 
            if password_baru != konfirmasi_password_baru: error = "Password baru dan konfirmasi password tidak cocok."
            elif len(password_baru) < 6: error = "Password baru minimal harus 6 karakter."
            else: hashed_password_to_update = generate_password_hash(password_baru)
        foto_profil_path_to_update = g.user['foto_profil_path'] 
        if 'foto_profil' in request.files:
            file_foto = request.files['foto_profil']
            if file_foto.filename != '': 
                if allowed_file(file_foto.filename, ALLOWED_EXTENSIONS_IMAGE):
                    if g.user['foto_profil_path']:
                        old_photo_full_path = os.path.join(STATIC_FOLDER, g.user['foto_profil_path'])
                        if os.path.exists(old_photo_full_path):
                            try: os.remove(old_photo_full_path)
                            except OSError as e: print(f"Error deleting old profile photo: {e}") 
                    filename_foto = secure_filename(file_foto.filename)
                    unique_filename_foto = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename_foto}"
                    file_foto.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], unique_filename_foto))
                    foto_profil_path_to_update = os.path.join('uploads', 'profile_photos', unique_filename_foto).replace('\\', '/')
                else: error = "Format file foto profil tidak diizinkan."
        if error is None:
            try:
                db.execute(
                    """UPDATE users SET nama_lengkap = ?, email = ?, password = ?, 
                           foto_profil_path = ?, alamat = ?, no_telepon = ?, updated_at = datetime('now', 'localtime')
                       WHERE user_id = ?""",
                    (nama_lengkap, email_baru, hashed_password_to_update, 
                     foto_profil_path_to_update, 
                     alamat_baru if alamat_baru else None, 
                     no_telepon_baru if no_telepon_baru else None, 
                     g.user['user_id'])
                )
                db.commit()
                flash("Profil berhasil diperbarui.", "success")
                user_data_row = db.execute('SELECT * FROM users WHERE user_id = ?', (g.user['user_id'],)).fetchone()
                if user_data_row:
                    g.user = dict(user_data_row)
                    g.user['tgl_daftar_dt'] = parse_datetime_str(g.user.get('tgl_daftar'))
                    g.user['updated_at_dt'] = parse_datetime_str(g.user.get('updated_at'))

                if g.user['role'] in ['admin', 'pustakawan']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard')) 
            except sqlite3.Error as e: 
                error = f"Gagal memperbarui profil: {e}"
                print(f"SQLite Error on UPDATE: {e}")
        if error: flash(error, "danger")
    
    current_user_data_for_form = dict(g.user) if g.user else {}
    if 'tgl_daftar_dt' not in current_user_data_for_form and current_user_data_for_form.get('tgl_daftar'):
        current_user_data_for_form['tgl_daftar_dt'] = parse_datetime_str(current_user_data_for_form['tgl_daftar'])
    if 'updated_at_dt' not in current_user_data_for_form and current_user_data_for_form.get('updated_at'):
        current_user_data_for_form['updated_at_dt'] = parse_datetime_str(current_user_data_for_form['updated_at'])

    if request.method == 'POST' and error: 
        current_user_data_for_form['nama_lengkap'] = request.form.get('nama_lengkap', current_user_data_for_form.get('nama_lengkap', ''))
        current_user_data_for_form['email'] = request.form.get('email', current_user_data_for_form.get('email', ''))
        current_user_data_for_form['alamat'] = request.form.get('alamat', current_user_data_for_form.get('alamat', ''))
        current_user_data_for_form['no_telepon'] = request.form.get('nomor_telepon', current_user_data_for_form.get('no_telepon', ''))
    
    return render_template('edit_profile.html', title="Edit Profil", user_data=current_user_data_for_form)

def get_books_by_type_and_category(book_type=None):
    db = get_db()
    search_query = request.args.get('search', '').strip()
    category_filter_id = request.args.get('category_id', type=int) 
    base_query = "SELECT b.book_id, b.judul, b.pengarang, b.cover_image_path, b.jenis_buku, c.nama_kategori FROM books b LEFT JOIN categories c ON b.category_id = c.category_id"
    conditions = []
    params = []
    if book_type:
        conditions.append("b.jenis_buku = ?")
        params.append(book_type)
    if category_filter_id: 
        conditions.append("b.category_id = ?")
        params.append(category_filter_id)
    if search_query:
        search_conditions_group = "(b.judul LIKE ? OR b.pengarang LIKE ? OR c.nama_kategori LIKE ?)"
        conditions.append(search_conditions_group)
        search_term = f"%{search_query}%"
        params.extend([search_term, search_term, search_term])
    query_sql = base_query
    if conditions:
        query_sql += " WHERE " + " AND ".join(conditions) 
    query_sql += " ORDER BY b.judul ASC"
    books_data = db.execute(query_sql, params).fetchall()
    all_categories = db.execute("SELECT category_id, nama_kategori FROM categories ORDER BY nama_kategori ASC").fetchall()
    return books_data, search_query, all_categories, category_filter_id

@app.route('/books/physical')
def books_catalog_physical():
    books_data, search_query, all_categories, category_filter_id = get_books_by_type_and_category('fisik')
    return render_template('books_catalog.html', title="Katalog Buku Fisik", books=books_data, search_query=search_query, catalog_type='fisik', categories=all_categories,selected_category_id=category_filter_id)

@app.route('/books/digital')
def books_catalog_digital():
    books_data, search_query, all_categories, category_filter_id = get_books_by_type_and_category('digital')
    return render_template('books_catalog.html', title="Katalog Buku Digital", books=books_data, search_query=search_query, catalog_type='digital',categories=all_categories,selected_category_id=category_filter_id)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    db = get_db()
    book_raw = db.execute("SELECT b.*, c.nama_kategori FROM books b LEFT JOIN categories c ON b.category_id = c.category_id WHERE b.book_id = ?", (book_id,)).fetchone()
    if book_raw is None: abort(404) 
    book = dict(book_raw)
    book['created_at_dt'] = parse_datetime_str(book.get('created_at'))
    book['updated_at_dt'] = parse_datetime_str(book.get('updated_at'))
    return render_template('book_detail.html', title=book['judul'], book=book)

@app.route('/borrow_book/<int:book_id>', methods=['GET'])
@login_required
def borrow_book(book_id):
    db = get_db()
    book = db.execute('SELECT * FROM books WHERE book_id = ?', (book_id,)).fetchone()
    if book is None:
        flash("Buku tidak ditemukan.", "danger")
        return redirect(request.referrer or url_for('index'))
    if book['jenis_buku'] == 'digital':
        if not book['file_ebook_path']:
            flash("File eBook untuk buku ini tidak tersedia.", "danger")
            return redirect(url_for('book_detail', book_id=book_id))
        try:
            tanggal_pinjam_digital = datetime.datetime.now()
            db.execute(
                "INSERT INTO loans (user_id, book_id, tanggal_pinjam, tipe_pinjaman, status_pinjaman) VALUES (?, ?, ?, ?, ?)",
                (g.user['user_id'], book_id, tanggal_pinjam_digital, 'digital', 'diunduh')
            )
            db.commit()
            flash(f"Anda telah meminjam (mengunduh) buku '{book['judul']}'.", "success")
            directory = app.config['UPLOAD_FOLDER_EBOOK']
            filename = os.path.basename(book['file_ebook_path'])
            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        except Exception as e:
            flash(f"Terjadi kesalahan saat memproses peminjaman digital: {e}", "danger")
        return redirect(url_for('book_detail', book_id=book_id))
    elif book['jenis_buku'] == 'fisik':
        try:
            existing_loan = db.execute(
                "SELECT loan_id FROM loans WHERE user_id = ? AND book_id = ? AND status_pinjaman IN ('dipinjam', 'menunggu_konfirmasi_admin')",
                (g.user['user_id'], book_id)
            ).fetchone()
            if existing_loan:
                flash(f"Anda sudah memiliki permintaan peminjaman atau sedang meminjam buku fisik '{book['judul']}'.", "warning")
                return redirect(url_for('book_detail', book_id=book_id))
            if book['stok_fisik'] > 0:
                tanggal_permintaan_pinjam = datetime.datetime.now()
                tanggal_jatuh_tempo_pinjam = tanggal_permintaan_pinjam + datetime.timedelta(days=7) 
                cursor = db.execute(
                    "INSERT INTO loans (user_id, book_id, tanggal_pinjam, tanggal_jatuh_tempo, tipe_pinjaman, status_pinjaman) VALUES (?, ?, ?, ?, ?, ?)",
                    (g.user['user_id'], book_id, tanggal_permintaan_pinjam, tanggal_jatuh_tempo_pinjam, 'fisik', 'menunggu_konfirmasi_admin')
                )
                db.commit()
                new_loan_id = cursor.lastrowid
                flash(f"Permintaan peminjaman buku fisik '{book['judul']}' telah diajukan. Silakan tunggu konfirmasi admin/pustakawan.", "info")
                if new_loan_id:
                    return redirect(url_for('loan_receipt', loan_id=new_loan_id))
                return redirect(url_for('book_detail', book_id=book_id))
            else:
                flash(f"Maaf, stok buku fisik '{book['judul']}' sedang habis.", "warning")
        except sqlite3.Error as e:
            flash(f"Terjadi kesalahan database saat mengajukan peminjaman: {e}", "danger")
        return redirect(url_for('book_detail', book_id=book_id))
    else:
        flash("Jenis buku tidak dikenal.", "danger")
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/loan_receipt/<int:loan_id>')
@login_required
def loan_receipt(loan_id):
    db = get_db()
    loan_data_raw = db.execute(
        """
        SELECT l.loan_id, l.tanggal_pinjam, l.tanggal_jatuh_tempo, l.user_id AS peminjam_user_id,
               l.status_pinjaman, l.tipe_pinjaman,
               u.nama_lengkap AS nama_peminjam, u.nomor_anggota,
               b.judul AS judul_buku
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.loan_id = ? 
        """, (loan_id,)
    ).fetchone()

    if not loan_data_raw:
        flash("Struk peminjaman tidak ditemukan.", "danger")
        return redirect(url_for('dashboard'))
    
    loan_data = dict(loan_data_raw) 
    loan_data['tanggal_pinjam_dt'] = parse_datetime_str(loan_data.get('tanggal_pinjam'))
    loan_data['tanggal_jatuh_tempo_dt'] = parse_datetime_str(loan_data.get('tanggal_jatuh_tempo'))

    if loan_data['peminjam_user_id'] != g.user['user_id'] and g.user['role'] not in ['admin', 'pustakawan']:
        flash("Anda tidak memiliki izin untuk melihat struk peminjaman ini.", "danger")
        return redirect(url_for('dashboard'))

    return render_template('loan_receipt.html', 
                           title="Struk Peminjaman/Permintaan Buku", 
                           loan=loan_data)

# --- RUTE API UNTUK MENGAMBIL DETAIL PEMINJAMAN ---
@app.route('/api/loan/<int:loan_id>/details')
@staff_required
def loan_details_api(loan_id):
    db = get_db()
    loan_details = db.execute(
        """
        SELECT 
            l.loan_id, l.status_pinjaman,
            u.nama_lengkap as nama_peminjam,
            b.judul as judul_buku
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.loan_id = ?
        """, (loan_id,)
    ).fetchone()

    if not loan_details:
        return jsonify({'error': 'Peminjaman tidak ditemukan'}), 404
    
    # PERBAIKAN: Memeriksa apakah statusnya valid untuk diproses (konfirmasi atau pengembalian)
    allowed_statuses = ['menunggu_konfirmasi_admin', 'dipinjam', 'terlambat_dikembalikan']
    if loan_details['status_pinjaman'] not in allowed_statuses:
        return jsonify({'error': f"Status peminjaman saat ini '{loan_details['status_pinjaman'].replace('_', ' ').title()}', tidak bisa diproses."}), 400

    return jsonify(dict(loan_details))

# --- RUTE ADMIN & PUSTAKAWAN ---
@app.route('/admin') 
@app.route('/admin/dashboard')
@staff_required 
def admin_dashboard():
    db = get_db()
    total_buku = db.execute("SELECT COUNT(book_id) FROM books").fetchone()[0] or 0
    total_anggota_aktif = db.execute("SELECT COUNT(user_id) FROM users WHERE role = 'anggota' AND is_active = 1").fetchone()[0] or 0
    total_peminjaman_aktif = db.execute("SELECT COUNT(loan_id) FROM loans WHERE status_pinjaman = 'dipinjam' AND tipe_pinjaman = 'fisik'").fetchone()[0] or 0
    total_permintaan_pending = db.execute("SELECT COUNT(loan_id) FROM loans WHERE status_pinjaman = 'menunggu_konfirmasi_admin'").fetchone()[0] or 0
    total_pustakawan_aktif = 0
    total_user_action_requests_pending = 0
    if g.user and g.user['role'] == 'admin':
        total_pustakawan_aktif = db.execute("SELECT COUNT(user_id) FROM users WHERE role = 'pustakawan' AND is_active = 1").fetchone()[0] or 0
        total_user_action_requests_pending = db.execute("SELECT COUNT(request_id) FROM user_action_requests WHERE status = 'pending'").fetchone()[0] or 0
    
    recent_activities_raw = db.execute("""
        SELECT 
            'Buku Ditambahkan' as activity_type, 
            'Buku "' || b.judul || '" ditambahkan ke katalog.' as description, 
            b.created_at as timestamp
        FROM books b
        
        UNION ALL
        
        SELECT 
            'Peminjaman Baru' as activity_type, 
            u.nama_lengkap || ' mengajukan peminjaman buku "' || b.judul || '".' as description, 
            l.tanggal_pinjam as timestamp
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.status_pinjaman = 'menunggu_konfirmasi_admin'

        UNION ALL

        SELECT 
            'Pengguna Baru' as activity_type,
            'Anggota baru "' || u.nama_lengkap || '" telah terdaftar.' as description,
            u.tgl_daftar as timestamp
        FROM users u
        WHERE u.role = 'anggota'

        ORDER BY timestamp DESC
        LIMIT 7
    """).fetchall()

    recent_activities = []
    for row_raw in recent_activities_raw:
        row = dict(row_raw)
        row['timestamp_dt'] = parse_datetime_str(row.get('timestamp'))
        recent_activities.append(row)

    return render_template('admin/admin_dashboard.html', 
                           title="Dashboard Staf", 
                           total_buku=total_buku,
                           total_anggota_aktif=total_anggota_aktif,
                           total_peminjaman_aktif=total_peminjaman_aktif,
                           total_permintaan_pending=total_permintaan_pending,
                           total_pustakawan_aktif=total_pustakawan_aktif,
                           total_user_action_requests_pending=total_user_action_requests_pending,
                           recent_activities=recent_activities)

# Sisa kode lengkap dari file Anda akan mengikuti...
@app.route('/admin/add_book', methods=['GET', 'POST'])
@staff_required 
def admin_add_book():
    db = get_db() 
    all_categories = db.execute("SELECT category_id, nama_kategori FROM categories ORDER BY nama_kategori ASC").fetchall()
    if request.method == 'POST':
        judul = request.form['judul']
        pengarang = request.form['pengarang']
        penerbit = request.form.get('penerbit')
        tahun_terbit = request.form.get('tahun_terbit')
        isbn = request.form.get('isbn')
        jumlah_halaman = request.form.get('jumlah_halaman')
        kategori_id_input = request.form.get('category_id') 
        kategori_nama_baru = request.form.get('kategori_nama_baru', '').strip() 
        jenis_buku = request.form['jenis_buku'] 
        ringkasan = request.form.get('ringkasan', '')
        stok_fisik = request.form.get('stok_fisik', 0)
        cover_image_path = None
        file_ebook_path = None
        error = None
        if not judul: error = "Judul buku diperlukan."
        category_id_to_use = None
        if kategori_id_input and kategori_id_input != "new":
            category_id_to_use = int(kategori_id_input)
        elif kategori_id_input == "new" and kategori_nama_baru:
            normalized_kategori_baru = kategori_nama_baru.title()
            existing_category = db.execute("SELECT category_id FROM categories WHERE nama_kategori = ?", (normalized_kategori_baru,)).fetchone()
            if existing_category:
                category_id_to_use = existing_category['category_id']
                flash(f"Menggunakan kategori yang sudah ada: '{normalized_kategori_baru}'.", "info")
            else:
                try:
                    cursor = db.execute('INSERT INTO categories (nama_kategori) VALUES (?)', (normalized_kategori_baru,))
                    db.commit()
                    category_id_to_use = cursor.lastrowid
                    flash(f"Kategori baru '{normalized_kategori_baru}' berhasil ditambahkan.", "success")
                    all_categories = db.execute("SELECT category_id, nama_kategori FROM categories ORDER BY nama_kategori ASC").fetchall() 
                except sqlite3.IntegrityError: 
                    error = f"Kategori '{normalized_kategori_baru}' sudah ada atau terjadi kesalahan."
                except Exception as e:
                    error = f"Gagal membuat kategori baru: {e}"
        elif not kategori_id_input and not kategori_nama_baru : 
             error = "Silakan pilih kategori atau tambahkan kategori baru."
        if error: 
            flash(error, "danger")
            return render_template('admin/add_book.html', title="Tambah Buku Baru", categories=all_categories, request_form=request.form)
        if 'cover_image' in request.files:
            file_cover = request.files['cover_image']
            if file_cover.filename != '' and allowed_file(file_cover.filename, ALLOWED_EXTENSIONS_IMAGE):
                filename_cover = secure_filename(file_cover.filename)
                unique_filename_cover = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename_cover}"
                file_cover.save(os.path.join(app.config['UPLOAD_FOLDER_COVER'], unique_filename_cover))
                cover_image_path = os.path.join('uploads', 'covers', unique_filename_cover).replace('\\', '/')
            elif file_cover.filename != '': error = "Format file sampul tidak diizinkan."
        if jenis_buku == 'digital':
            if 'file_ebook' not in request.files or request.files['file_ebook'].filename == '': 
                error = "File eBook diperlukan untuk buku digital."
            else:
                file_ebook = request.files['file_ebook']
                if file_ebook and allowed_file(file_ebook.filename, ALLOWED_EXTENSIONS_EBOOK):
                    filename_ebook = secure_filename(file_ebook.filename)
                    unique_filename_ebook = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename_ebook}"
                    file_ebook.save(os.path.join(app.config['UPLOAD_FOLDER_EBOOK'], unique_filename_ebook))
                    file_ebook_path = os.path.join('uploads', 'ebooks', unique_filename_ebook).replace('\\', '/')
                elif file_ebook.filename != '': error = "Format file eBook tidak diizinkan."
        else: 
            file_ebook_path = None
            try:
                stok_fisik = int(stok_fisik) if str(stok_fisik).strip() else 0
                if stok_fisik < 0: stok_fisik = 0
            except ValueError:
                stok_fisik = 0
                error = "Stok fisik harus berupa angka."
        if error is None:
            try:
                db.execute(
                    """INSERT INTO books (judul, pengarang, penerbit, tahun_terbit, isbn, jumlah_halaman, category_id, jenis_buku, ringkasan, file_ebook_path, cover_image_path, stok_fisik, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))""",
                    (judul, pengarang, penerbit, tahun_terbit, isbn, jumlah_halaman, category_id_to_use, jenis_buku, ringkasan, file_ebook_path, cover_image_path, stok_fisik if jenis_buku == 'fisik' else 0)
                )
                db.commit()
                flash(f"Buku '{judul}' berhasil ditambahkan!", "success")
                return redirect(url_for('admin_list_books')) 
            except Exception as e: 
                error = f"Gagal menyimpan buku ke database: {e}"
        if error: flash(error, "danger")
    return render_template('admin/add_book.html', title="Tambah Buku Baru", categories=all_categories, request_form=request.form if request.method == 'POST' else None)

@app.route('/admin/books')
@staff_required 
def admin_list_books():
    db = get_db()
    books_data_raw = db.execute(
        """
        SELECT b.book_id, b.judul, b.pengarang, b.jenis_buku, b.stok_fisik, b.cover_image_path, c.nama_kategori, b.created_at
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        ORDER BY b.book_id DESC
        """
    ).fetchall()
    books_data = []
    for row_raw in books_data_raw:
        row = dict(row_raw)
        row['created_at_dt'] = parse_datetime_str(row.get('created_at'))
        books_data.append(row)
    return render_template('admin/list_books.html', title="Daftar Semua Buku", books=books_data)

@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
@staff_required 
def admin_edit_book(book_id):
    db = get_db()
    book_to_edit_raw = db.execute(
        "SELECT b.*, c.nama_kategori FROM books b LEFT JOIN categories c ON b.category_id = c.category_id WHERE b.book_id = ?",
        (book_id,)
    ).fetchone()
    if book_to_edit_raw is None:
        flash(f"Buku dengan ID {book_id} tidak ditemukan.", "danger")
        return redirect(url_for('admin_list_books'))
    book_to_edit = dict(book_to_edit_raw)
    book_to_edit['created_at_dt'] = parse_datetime_str(book_to_edit.get('created_at'))
    book_to_edit['updated_at_dt'] = parse_datetime_str(book_to_edit.get('updated_at'))

    all_categories = db.execute("SELECT category_id, nama_kategori FROM categories ORDER BY nama_kategori ASC").fetchall()
    if request.method == 'POST':
        # ... (logika POST sama seperti yang Anda berikan)
        judul = request.form['judul']
        pengarang = request.form['pengarang']
        penerbit = request.form.get('penerbit')
        tahun_terbit = request.form.get('tahun_terbit')
        isbn = request.form.get('isbn')
        jumlah_halaman = request.form.get('jumlah_halaman')
        kategori_id_input = request.form.get('category_id')
        kategori_nama_baru = request.form.get('kategori_nama_baru', '').strip()
        jenis_buku = request.form['jenis_buku']
        ringkasan = request.form.get('ringkasan', '')
        stok_fisik = request.form.get('stok_fisik', book_to_edit['stok_fisik']) 
        current_cover_image_path = book_to_edit['cover_image_path']
        current_file_ebook_path = book_to_edit['file_ebook_path']
        error = None
        if not judul: error = "Judul buku diperlukan."
        category_id_to_use = book_to_edit['category_id'] 
        if kategori_id_input and kategori_id_input != "new":
            category_id_to_use = int(kategori_id_input)
        elif kategori_id_input == "new" and kategori_nama_baru:
            normalized_kategori_baru = kategori_nama_baru.title()
            existing_category = db.execute("SELECT category_id FROM categories WHERE nama_kategori = ?", (normalized_kategori_baru,)).fetchone()
            if existing_category:
                category_id_to_use = existing_category['category_id']
                flash(f"Menggunakan kategori yang sudah ada: '{normalized_kategori_baru}'.", "info")
            else:
                try:
                    cursor = db.execute('INSERT INTO categories (nama_kategori) VALUES (?)', (normalized_kategori_baru,))
                    db.commit()
                    category_id_to_use = cursor.lastrowid
                    flash(f"Kategori baru '{normalized_kategori_baru}' berhasil ditambahkan.", "success")
                    all_categories = db.execute("SELECT category_id, nama_kategori FROM categories ORDER BY nama_kategori ASC").fetchall() 
                except sqlite3.IntegrityError: error = f"Kategori '{normalized_kategori_baru}' sudah ada."
                except Exception as e: error = f"Gagal membuat kategori baru: {e}"
        elif kategori_id_input == "new" and not kategori_nama_baru:
             error = "Nama kategori baru tidak boleh kosong jika memilih 'Tambah Kategori Baru'."
        
        form_data_for_render = { **book_to_edit, **request.form } 
        form_data_for_render['category_id'] = category_id_to_use 
        if category_id_to_use:
             cat_name_row = db.execute("SELECT nama_kategori FROM categories WHERE category_id = ?", (category_id_to_use,)).fetchone()
             form_data_for_render['nama_kategori'] = cat_name_row['nama_kategori'] if cat_name_row else book_to_edit.get('nama_kategori')
        else:
             form_data_for_render['nama_kategori'] = book_to_edit.get('nama_kategori')

        if error:
            flash(error, "danger")
            form_data_for_render['cover_image_path'] = current_cover_image_path 
            form_data_for_render['file_ebook_path'] = current_file_ebook_path
            return render_template('admin/edit_book.html', title=f"Edit Buku: {book_to_edit['judul']}", book=form_data_for_render, categories=all_categories)
        new_cover_image_path = current_cover_image_path
        if 'cover_image' in request.files:
            file_cover = request.files['cover_image']
            if file_cover.filename != '': 
                if allowed_file(file_cover.filename, ALLOWED_EXTENSIONS_IMAGE):
                    if current_cover_image_path and os.path.exists(os.path.join(STATIC_FOLDER, current_cover_image_path)):
                        try: os.remove(os.path.join(STATIC_FOLDER, current_cover_image_path))
                        except OSError as e: print(f"Error deleting old cover: {e}")
                    filename_cover = secure_filename(file_cover.filename)
                    unique_filename_cover = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename_cover}"
                    file_cover.save(os.path.join(app.config['UPLOAD_FOLDER_COVER'], unique_filename_cover))
                    new_cover_image_path = os.path.join('uploads', 'covers', unique_filename_cover).replace('\\', '/')
                else: error = "Format file sampul baru tidak diizinkan."
        new_file_ebook_path = current_file_ebook_path
        if jenis_buku == 'digital':
            if 'file_ebook' in request.files:
                file_ebook = request.files['file_ebook']
                if file_ebook.filename != '': 
                    if allowed_file(file_ebook.filename, ALLOWED_EXTENSIONS_EBOOK):
                        if current_file_ebook_path and os.path.exists(os.path.join(STATIC_FOLDER, current_file_ebook_path)):
                            try: os.remove(os.path.join(STATIC_FOLDER, current_file_ebook_path))
                            except OSError as e: print(f"Error deleting old ebook: {e}")
                        filename_ebook = secure_filename(file_ebook.filename)
                        unique_filename_ebook = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename_ebook}"
                        file_ebook.save(os.path.join(app.config['UPLOAD_FOLDER_EBOOK'], unique_filename_ebook))
                        new_file_ebook_path = os.path.join('uploads', 'ebooks', unique_filename_ebook).replace('\\', '/')
                    else: error = "Format file eBook baru tidak diizinkan."
            elif not new_file_ebook_path: 
                error = "File eBook diperlukan untuk buku digital."
        else: 
            new_file_ebook_path = None 
            if current_file_ebook_path and os.path.exists(os.path.join(STATIC_FOLDER, current_file_ebook_path)):
                try: os.remove(os.path.join(STATIC_FOLDER, current_file_ebook_path))
                except OSError as e: print(f"Error deleting old ebook when switching to physical: {e}")
            try:
                stok_fisik = int(stok_fisik) if str(stok_fisik).strip() else 0
                if stok_fisik < 0: stok_fisik = 0
            except ValueError:
                stok_fisik = 0
                error = "Stok fisik harus berupa angka."
        if error is None:
            try:
                db.execute(
                    """UPDATE books 
                       SET judul = ?, pengarang = ?, penerbit = ?, tahun_terbit = ?, isbn = ?, jumlah_halaman = ?, 
                           category_id = ?, jenis_buku = ?, ringkasan = ?, file_ebook_path = ?, 
                           cover_image_path = ?, stok_fisik = ?, updated_at = datetime('now', 'localtime')
                       WHERE book_id = ?""",
                    (judul, pengarang, penerbit, tahun_terbit, isbn, jumlah_halaman, category_id_to_use, jenis_buku, ringkasan, 
                     new_file_ebook_path, new_cover_image_path, 
                     stok_fisik if jenis_buku == 'fisik' else 0, 
                     book_id)
                )
                db.commit()
                flash(f"Buku '{judul}' berhasil diperbarui!", "success")
                return redirect(url_for('admin_list_books'))
            except Exception as e: error = f"Gagal memperbarui buku di database: {e}"
        if error: 
            flash(error, "danger")
            form_data_for_render['cover_image_path'] = new_cover_image_path if 'cover_image' in request.files and request.files['cover_image'].filename != '' and not error else current_cover_image_path
            form_data_for_render['file_ebook_path'] = new_file_ebook_path if 'file_ebook' in request.files and request.files['file_ebook'].filename != '' and not error else current_file_ebook_path
            form_data_for_render['created_at_dt'] = parse_datetime_str(form_data_for_render.get('created_at'))
            form_data_for_render['updated_at_dt'] = parse_datetime_str(form_data_for_render.get('updated_at'))
            return render_template('admin/edit_book.html', title=f"Edit Buku: {book_to_edit['judul']}", book=form_data_for_render, categories=all_categories)
    return render_template('admin/edit_book.html', title=f"Edit Buku: {book_to_edit['judul']}", book=book_to_edit, categories=all_categories)

@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
@staff_required 
def admin_delete_book(book_id):
    db = get_db()
    book_to_delete = db.execute("SELECT judul, cover_image_path, file_ebook_path FROM books WHERE book_id = ?", (book_id,)).fetchone()
    if book_to_delete is None:
        flash(f"Buku dengan ID {book_id} tidak ditemukan.", "warning")
        return redirect(url_for('admin_list_books'))
    try:
        db.execute("DELETE FROM loans WHERE book_id = ?", (book_id,)) 
        db.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        db.commit()
        if book_to_delete['cover_image_path']:
            cover_path_to_delete = os.path.join(STATIC_FOLDER, book_to_delete['cover_image_path'])
            if os.path.exists(cover_path_to_delete):
                try: os.remove(cover_path_to_delete)
                except OSError as e: flash(f"Gagal menghapus file sampul: {e}", "warning")
        if book_to_delete['file_ebook_path']:
            ebook_path_to_delete = os.path.join(STATIC_FOLDER, book_to_delete['file_ebook_path'])
            if os.path.exists(ebook_path_to_delete):
                try: os.remove(ebook_path_to_delete)
                except OSError as e: flash(f"Gagal menghapus file eBook: {e}", "warning")
        flash(f"Buku '{book_to_delete['judul']}' (ID: {book_id}) dan data peminjaman terkait telah berhasil dihapus.", "success")
    except sqlite3.Error as e:
        flash(f"Gagal menghapus buku dari database: {e}", "danger")
    except Exception as e_file:
        flash(f"Terjadi kesalahan saat menghapus file terkait: {e_file}", "danger")
    return redirect(url_for('admin_list_books'))

@app.route('/admin/pending_loans', methods=['GET', 'POST'])
@staff_required 
def admin_pending_loans():
    if request.method == 'POST':
        loan_id_manual = request.form.get('loan_id_manual')
        if loan_id_manual:
            try:
                loan_id_int = int(loan_id_manual)
                return admin_confirm_loan_action(loan_id_int) 
            except ValueError:
                flash("ID Peminjaman harus berupa angka.", "danger")
        else:
            flash("ID Peminjaman tidak boleh kosong.", "warning")
        return redirect(url_for('admin_pending_loans'))

    db = get_db()
    pending_loans_raw = db.execute(
        """
        SELECT l.loan_id, l.tanggal_pinjam AS tanggal_permintaan, l.user_id AS peminjam_user_id,
               u.nama_lengkap AS nama_peminjam, u.nomor_anggota,
               b.judul AS judul_buku, b.book_id
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.tipe_pinjaman = 'fisik' AND l.status_pinjaman = 'menunggu_konfirmasi_admin'
        ORDER BY l.tanggal_pinjam ASC
        """
    ).fetchall()
    pending_loans = []
    for row_raw in pending_loans_raw:
        row = dict(row_raw)
        row['tanggal_permintaan_dt'] = parse_datetime_str(row.get('tanggal_permintaan'))
        pending_loans.append(row)
    return render_template('admin/pending_loans.html', 
                           title="Konfirmasi Peminjaman Buku", 
                           pending_loans=pending_loans)

@app.route('/admin/confirm_loan/<int:loan_id>', methods=['POST'])
@staff_required 
def admin_confirm_loan_action(loan_id):
    db = get_db()
    loan_to_confirm = db.execute("SELECT * FROM loans WHERE loan_id = ? AND status_pinjaman = 'menunggu_konfirmasi_admin'", (loan_id,)).fetchone()
    if not loan_to_confirm:
        flash("Peminjaman tidak ditemukan atau sudah dikonfirmasi.", "warning")
        return redirect(url_for('admin_pending_loans'))
    book_id = loan_to_confirm['book_id']
    book = db.execute("SELECT stok_fisik, judul FROM books WHERE book_id = ?", (book_id,)).fetchone()
    if not book or book['stok_fisik'] <= 0:
        flash(f"Stok buku '{book['judul'] if book else 'Tidak Diketahui'}' habis. Konfirmasi dibatalkan.", "danger")
        return redirect(url_for('admin_pending_loans'))
    try:
        db.execute(
            "UPDATE loans SET status_pinjaman = 'dipinjam' WHERE loan_id = ?", 
            (loan_id,)
        )
        db.execute("UPDATE books SET stok_fisik = stok_fisik - 1 WHERE book_id = ?", (book_id,))
        db.commit()
        flash(f"Peminjaman buku '{book['judul']}' untuk ID Pinjam {loan_id} berhasil dikonfirmasi.", "success")
    except sqlite3.Error as e:
        db.rollback()
        flash(f"Gagal mengkonfirmasi peminjaman: {e}", "danger")
    return redirect(url_for('admin_pending_loans'))

@app.route('/admin/active_loans', methods=['GET', 'POST'])
@staff_required 
def admin_active_loans():
    if request.method == 'POST':
        loan_id_manual = request.form.get('loan_id_manual')
        if loan_id_manual:
            try:
                loan_id_int = int(loan_id_manual)
                return admin_return_book(loan_id_int)
            except ValueError:
                flash("ID Peminjaman harus berupa angka.", "danger")
        else:
            flash("ID Peminjaman tidak boleh kosong.", "warning")
        return redirect(url_for('admin_active_loans'))
    
    db = get_db()
    active_physical_loans_raw = db.execute(
        """
        SELECT l.loan_id, l.tanggal_pinjam, l.tanggal_jatuh_tempo, l.status_pinjaman,
               u.user_id AS peminjam_user_id, u.nama_lengkap AS nama_peminjam, u.nomor_anggota,
               b.judul AS judul_buku, b.book_id
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.tipe_pinjaman = 'fisik' AND l.status_pinjaman IN ('dipinjam', 'terlambat_dikembalikan') 
        ORDER BY l.tanggal_jatuh_tempo ASC
        """
    ).fetchall()
    active_physical_loans = []
    for row_raw in active_physical_loans_raw:
        row = dict(row_raw)
        row['tanggal_pinjam_dt'] = parse_datetime_str(row.get('tanggal_pinjam'))
        row['tanggal_jatuh_tempo_dt'] = parse_datetime_str(row.get('tanggal_jatuh_tempo'))
        active_physical_loans.append(row)

    processed_loan_id = request.args.get('processed_loan_id', type=int)
    processed_loan_details = None
    if processed_loan_id:
        pld_raw = db.execute(
             """
             SELECT l.*, u.nama_lengkap AS nama_peminjam, u.user_id, u.nomor_anggota, b.judul AS judul_buku 
             FROM loans l 
             JOIN users u ON l.user_id = u.user_id 
             JOIN books b ON l.book_id = b.book_id 
             WHERE l.loan_id = ?
             """, (processed_loan_id,)
        ).fetchone()
        if pld_raw:
            processed_loan_details = dict(pld_raw)
            processed_loan_details['tanggal_pinjam_dt'] = parse_datetime_str(processed_loan_details.get('tanggal_pinjam'))
            processed_loan_details['tanggal_jatuh_tempo_dt'] = parse_datetime_str(processed_loan_details.get('tanggal_jatuh_tempo'))
            processed_loan_details['tanggal_kembali_dt'] = parse_datetime_str(processed_loan_details.get('tanggal_kembali'))
    return render_template('admin/active_loans.html', 
                           title="Peminjaman Buku Fisik Aktif", 
                           loans=active_physical_loans,
                           processed_loan_details=processed_loan_details)

@app.route('/admin/return_book/<int:loan_id>', methods=['POST'])
@staff_required 
def admin_return_book(loan_id):
    db = get_db()
    loan = db.execute("SELECT * FROM loans WHERE loan_id = ? AND tipe_pinjaman = 'fisik' AND status_pinjaman IN ('dipinjam', 'terlambat_dikembalikan')", (loan_id,)).fetchone()
    if not loan:
        flash("Data peminjaman tidak ditemukan atau buku sudah dikembalikan.", "warning")
        return redirect(url_for('admin_active_loans'))
    book_id = loan['book_id']
    user_id_peminjam = loan['user_id'] 
    tanggal_kembali = datetime.datetime.now()
    tanggal_jatuh_tempo_str = loan['tanggal_jatuh_tempo']
    denda_final = 0
    status_baru = 'dikembalikan'
    try:
        if tanggal_jatuh_tempo_str:
            jatuh_tempo_dt_obj = parse_datetime_str(tanggal_jatuh_tempo_str)
            if jatuh_tempo_dt_obj and tanggal_kembali.date() > jatuh_tempo_dt_obj.date():
                selisih_hari = (tanggal_kembali.date() - jatuh_tempo_dt_obj.date()).days
                denda_final = selisih_hari * DENDA_PER_HARI 
                status_baru = 'terlambat_dikembalikan' 
                flash(f"Buku dikembalikan terlambat {selisih_hari} hari. Denda: Rp {denda_final:,.0f}", "warning")
        
        db.execute(
            "UPDATE loans SET tanggal_kembali = ?, status_pinjaman = ?, denda = ? WHERE loan_id = ?",
            (tanggal_kembali, status_baru, denda_final, loan_id)
        )
        db.execute("UPDATE books SET stok_fisik = stok_fisik + 1 WHERE book_id = ?", (book_id,))
        db.commit()
        flash("Buku telah ditandai sebagai dikembalikan.", "success")
        return redirect(url_for('admin_active_loans', processed_loan_id=loan_id, user_id_peminjam=user_id_peminjam))
    except sqlite3.Error as e:
        db.rollback() 
        flash(f"Gagal memproses pengembalian buku: {e}", "danger")
    except ValueError as ve: 
        flash(f"Format tanggal jatuh tempo tidak valid pada data peminjaman: {ve}", "danger")
    return redirect(url_for('admin_active_loans'))

# --- MANAJEMEN PENGGUNA DENGAN ALUR PERMINTAAN ---
@app.route('/admin/users')
@staff_required 
def admin_list_users():
    db = get_db()
    users_data_raw = db.execute("""
        SELECT u.user_id, u.nama_lengkap, u.email, u.nomor_anggota, u.role, u.is_active, u.tgl_daftar,
               (SELECT COUNT(*) FROM user_action_requests ar 
                WHERE ar.target_user_id = u.user_id AND ar.status = 'pending') as pending_requests_count
        FROM users u
        ORDER BY 
            CASE u.role
                WHEN 'admin' THEN 1
                WHEN 'pustakawan' THEN 2
                WHEN 'anggota' THEN 3
                ELSE 4
            END ASC,
            u.tgl_daftar ASC
    """).fetchall()
    users_data = []
    for row_raw in users_data_raw:
        row = dict(row_raw)
        row['tgl_daftar_dt'] = parse_datetime_str(row.get('tgl_daftar'))
        users_data.append(row)
    return render_template('admin/list_users.html', title="Manajemen Pengguna", users=users_data)

@app.route('/admin/user/toggle_role/<int:user_id>', methods=['POST'])
@admin_required 
def admin_toggle_user_role(user_id): 
    db = get_db()
    user_to_update = db.execute("SELECT user_id, role, nama_lengkap FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user_to_update:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('admin_list_users'))
    if user_to_update['user_id'] == g.user['user_id']:
        flash("Anda tidak dapat mengubah role diri sendiri melalui antarmuka ini.", "warning")
        return redirect(url_for('admin_list_users'))
    
    action = request.form.get('action')
    new_role = None
    current_role = user_to_update['role']

    if action == 'make_pustakawan' and current_role == 'anggota':
        new_role = 'pustakawan'
    elif action == 'make_anggota' and current_role == 'pustakawan':
        new_role = 'anggota'
    elif action == 'make_admin' and current_role in ['anggota', 'pustakawan']:
        new_role = 'admin'
    elif action == 'revoke_admin_to_pustakawan' and current_role == 'admin':
        new_role = 'pustakawan'
    elif action == 'revoke_admin_to_anggota' and current_role == 'admin':
        new_role = 'anggota'
    else:
        flash(f"Aksi perubahan role tidak valid untuk pengguna dengan role '{current_role}'. Aksi: {action}", "warning")
        return redirect(url_for('admin_list_users'))

    if new_role:
        try:
            db.execute("UPDATE users SET role = ?, updated_at = datetime('now', 'localtime') WHERE user_id = ?", (new_role, user_id))
            db.commit()
            flash(f"Role untuk pengguna '{user_to_update['nama_lengkap']}' berhasil diubah menjadi '{new_role.title()}'.", "success")
        except sqlite3.Error as e:
            flash(f"Gagal mengubah role pengguna: {e}", "danger")
    return redirect(url_for('admin_list_users'))


@app.route('/admin/user/toggle_active/<int:user_id>', methods=['POST'])
@admin_required 
def admin_toggle_user_active_status(user_id): 
    db = get_db()
    user_to_toggle = db.execute("SELECT user_id, nama_lengkap, is_active FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user_to_toggle:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('admin_list_users'))
    if user_to_toggle['user_id'] == g.user['user_id']: 
        flash("Anda tidak dapat menonaktifkan akun Anda sendiri.", "warning")
        return redirect(url_for('admin_list_users'))
    new_status = 0 if user_to_toggle['is_active'] == 1 else 1
    status_text = "dinonaktifkan" if new_status == 0 else "diaktifkan"
    try:
        db.execute("UPDATE users SET is_active = ?, updated_at = datetime('now', 'localtime') WHERE user_id = ?", (new_status, user_id))
        db.commit()
        flash(f"Akun pengguna '{user_to_toggle['nama_lengkap']}' berhasil {status_text}.", "success")
    except sqlite3.Error as e:
        flash(f"Gagal mengubah status akun pengguna: {e}", "danger")
    return redirect(url_for('admin_list_users'))

@app.route('/admin/user/<int:target_user_id>/request_action', methods=['POST'])
@staff_required 
def admin_request_user_action(target_user_id): 
    db = get_db()
    action_type = request.form.get('action_type')
    reason = request.form.get('reason', 'Diajukan oleh staf perpustakaan.') 
    allowed_actions = ['deactivate_account', 'activate_account', 'change_role_to_pustakawan', 'change_role_to_anggota', 'change_role_to_admin']
    if action_type not in allowed_actions:
        flash("Jenis aksi tidak valid.", "danger")
        return redirect(url_for('admin_list_users'))
    target_user = db.execute("SELECT * FROM users WHERE user_id = ?", (target_user_id,)).fetchone()
    if not target_user:
        flash("Pengguna target tidak ditemukan.", "danger")
        return redirect(url_for('admin_list_users'))
    
    if g.user['role'] == 'pustakawan':
        if action_type == 'change_role_to_admin':
            flash("Pustakawan tidak dapat mengajukan perubahan role menjadi Admin.", "warning")
            return redirect(url_for('admin_list_users'))
        if target_user['role'] == 'admin':
            flash("Pustakawan tidak dapat mengajukan aksi terhadap Admin.", "warning")
            return redirect(url_for('admin_list_users'))
        if target_user['role'] == 'pustakawan' and target_user_id == g.user['user_id'] and action_type in ['deactivate_account','change_role_to_anggota']:
            flash("Anda tidak dapat mengajukan aksi ini untuk diri sendiri sebagai Pustakawan.", "warning")
            return redirect(url_for('admin_list_users'))

    try:
        existing_pending_request = db.execute(
            "SELECT request_id FROM user_action_requests WHERE target_user_id = ? AND action_type = ? AND status = 'pending'",
            (target_user_id, action_type)
        ).fetchone()
        if existing_pending_request:
            flash(f"Sudah ada permintaan '{action_type.replace('_', ' ').title()}' yang pending untuk pengguna ini.", "info")
        else:
            db.execute(
                """INSERT INTO user_action_requests 
                   (requester_user_id, target_user_id, action_type, reason, requested_at)
                   VALUES (?, ?, ?, ?, datetime('now', 'localtime'))""",
                (g.user['user_id'], target_user_id, action_type, reason)
            )
            db.commit()
            flash(f"Permintaan '{action_type.replace('_', ' ').title()}' untuk pengguna '{target_user['nama_lengkap']}' telah diajukan dan menunggu persetujuan Admin.", "success")
    except sqlite3.Error as e:
        flash(f"Gagal mengajukan permintaan: {e}", "danger")
    return redirect(url_for('admin_list_users'))

@app.route('/admin/action_requests')
@admin_required 
def admin_view_action_requests(): 
    db = get_db()
    pending_requests_raw = db.execute(
        """
        SELECT ar.*, ru.nama_lengkap as requester_name, tu.nama_lengkap as target_user_name, tu.role as target_current_role
        FROM user_action_requests ar
        JOIN users ru ON ar.requester_user_id = ru.user_id
        JOIN users tu ON ar.target_user_id = tu.user_id
        WHERE ar.status = 'pending'
        ORDER BY ar.requested_at ASC
        """
    ).fetchall()
    pending_requests = [dict(row) for row in pending_requests_raw]
    for req in pending_requests:
        req['requested_at_dt'] = parse_datetime_str(req.get('requested_at'))
        
    processed_requests_raw = db.execute(
        """
        SELECT ar.*, ru.nama_lengkap as requester_name, tu.nama_lengkap as target_user_name, 
               au.nama_lengkap as admin_processor_name
        FROM user_action_requests ar
        JOIN users ru ON ar.requester_user_id = ru.user_id
        JOIN users tu ON ar.target_user_id = tu.user_id
        LEFT JOIN users au ON ar.processed_by_admin_id = au.user_id
        WHERE ar.status != 'pending'
        ORDER BY ar.processed_at DESC
        LIMIT 20 
        """
    ).fetchall()
    processed_requests = [dict(row) for row in processed_requests_raw]
    for req in processed_requests:
        req['requested_at_dt'] = parse_datetime_str(req.get('requested_at'))
        req['processed_at_dt'] = parse_datetime_str(req.get('processed_at'))

    return render_template('admin/action_requests.html', 
                           title="Permintaan Aksi Pengguna", 
                           pending_requests=pending_requests,
                           processed_requests=processed_requests)

@app.route('/admin/action_requests/<int:request_id>/process', methods=['POST'])
@admin_required 
def admin_process_action_request(request_id): 
    db = get_db()
    decision = request.form.get('decision')
    admin_notes = request.form.get('admin_notes', '')
    req_to_process = db.execute("SELECT * FROM user_action_requests WHERE request_id = ? AND status = 'pending'", (request_id,)).fetchone()
    if not req_to_process:
        flash("Permintaan tidak ditemukan atau sudah diproses.", "warning")
        return redirect(url_for('admin_view_action_requests'))
    target_user = db.execute("SELECT * FROM users WHERE user_id = ?", (req_to_process['target_user_id'],)).fetchone()
    if not target_user:
        flash("Pengguna target tidak ditemukan. Permintaan dibatalkan.", "danger")
        db.execute("UPDATE user_action_requests SET status = 'rejected', admin_notes = 'Target user not found', processed_by_admin_id = ?, processed_at = datetime('now', 'localtime') WHERE request_id = ?", (g.user['user_id'], request_id))
        db.commit()
        return redirect(url_for('admin_view_action_requests'))
    if target_user['user_id'] == g.user['user_id'] and req_to_process['action_type'] in ['deactivate_account', 'change_role_to_anggota', 'change_role_to_pustakawan']:
        flash("Admin tidak dapat menonaktifkan atau menurunkan role diri sendiri melalui sistem permintaan ini.", "warning")
        db.execute("UPDATE user_action_requests SET status = 'rejected', admin_notes = 'Admin self-action restricted.', processed_by_admin_id = ?, processed_at = datetime('now', 'localtime') WHERE request_id = ?", (g.user['user_id'], request_id))
        db.commit()
        return redirect(url_for('admin_view_action_requests'))
    try:
        if decision == 'approve':
            action_successful = False
            if req_to_process['action_type'] == 'deactivate_account':
                db.execute("UPDATE users SET is_active = 0, updated_at = datetime('now', 'localtime') WHERE user_id = ?", (target_user['user_id'],))
                action_successful = True
            elif req_to_process['action_type'] == 'activate_account':
                db.execute("UPDATE users SET is_active = 1, updated_at = datetime('now', 'localtime') WHERE user_id = ?", (target_user['user_id'],))
                action_successful = True
            elif req_to_process['action_type'] == 'change_role_to_pustakawan':
                db.execute("UPDATE users SET role = 'pustakawan', updated_at = datetime('now', 'localtime') WHERE user_id = ?", (target_user['user_id'],))
                action_successful = True
            elif req_to_process['action_type'] == 'change_role_to_anggota':
                db.execute("UPDATE users SET role = 'anggota', updated_at = datetime('now', 'localtime') WHERE user_id = ?", (target_user['user_id'],))
                action_successful = True
            elif req_to_process['action_type'] == 'change_role_to_admin':
                db.execute("UPDATE users SET role = 'admin', updated_at = datetime('now', 'localtime') WHERE user_id = ?", (target_user['user_id'],))
                action_successful = True
            if action_successful:
                db.execute("UPDATE user_action_requests SET status = 'approved', processed_by_admin_id = ?, processed_at = datetime('now', 'localtime'), admin_notes = ? WHERE request_id = ?",
                           (g.user['user_id'], admin_notes, request_id))
                db.commit()
                flash(f"Permintaan '{req_to_process['action_type'].replace('_', ' ').title()}' untuk pengguna '{target_user['nama_lengkap']}' telah disetujui.", "success")
            else:
                flash("Jenis aksi pada permintaan tidak dikenal.", "danger")
        elif decision == 'reject':
            db.execute("UPDATE user_action_requests SET status = 'rejected', processed_by_admin_id = ?, processed_at = datetime('now', 'localtime'), admin_notes = ? WHERE request_id = ?",
                       (g.user['user_id'], admin_notes, request_id))
            db.commit()
            flash(f"Permintaan '{req_to_process['action_type'].replace('_', ' ').title()}' untuk pengguna '{target_user['nama_lengkap']}' telah ditolak.", "info")
        else:
            flash("Keputusan tidak valid.", "danger")
    except sqlite3.Error as e:
        db.rollback()
        flash(f"Gagal memproses permintaan: {e}", "danger")
    return redirect(url_for('admin_view_action_requests'))

@app.route('/admin/user/<int:user_id>/detail')
@staff_required 
def admin_user_detail(user_id):
    db = get_db()
    selected_user_raw = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not selected_user_raw:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('admin_list_users'))
    
    selected_user = dict(selected_user_raw)
    selected_user['tgl_daftar_dt'] = parse_datetime_str(selected_user.get('tgl_daftar'))
    selected_user['updated_at_dt'] = parse_datetime_str(selected_user.get('updated_at'))

    loan_history_raw = db.execute(
        """
        SELECT l.loan_id, l.tanggal_pinjam, l.tanggal_jatuh_tempo, l.tanggal_kembali, 
               l.tipe_pinjaman, l.status_pinjaman, l.denda, b.judul AS judul_buku
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        WHERE l.user_id = ?
        ORDER BY l.tanggal_pinjam DESC
        """,
        (user_id,)
    ).fetchall()
    loan_history = []
    for row_raw in loan_history_raw:
        row = dict(row_raw)
        row['tanggal_pinjam_dt'] = parse_datetime_str(row.get('tanggal_pinjam'))
        row['tanggal_jatuh_tempo_dt'] = parse_datetime_str(row.get('tanggal_jatuh_tempo'))
        row['tanggal_kembali_dt'] = parse_datetime_str(row.get('tanggal_kembali'))
        loan_history.append(row)

    total_unpaid_fines_for_user = 0
    for loan in loan_history:
        if loan['status_pinjaman'] == 'terlambat_dikembalikan' and loan['denda'] > 0:
             total_unpaid_fines_for_user += loan['denda']

    user_requests_raw = db.execute(
        """
        SELECT ar.*, ru.nama_lengkap as requester_name, au.nama_lengkap as admin_processor_name
        FROM user_action_requests ar
        JOIN users ru ON ar.requester_user_id = ru.user_id
        LEFT JOIN users au ON ar.processed_by_admin_id = au.user_id
        WHERE ar.target_user_id = ?
        ORDER BY ar.requested_at DESC
        """, (user_id,)
    ).fetchall()
    user_requests = [dict(row) for row in user_requests_raw]
    for req in user_requests:
        req['requested_at_dt'] = parse_datetime_str(req.get('requested_at'))
        req['processed_at_dt'] = parse_datetime_str(req.get('processed_at'))

    return render_template('admin/user_detail.html', 
                           title=f"Detail Pengguna: {selected_user['nama_lengkap']}", 
                           selected_user=selected_user, 
                           loan_history=loan_history,
                           total_unpaid_fines_for_user=total_unpaid_fines_for_user,
                           user_action_requests=user_requests)

@app.route('/admin/reports')
@admin_required 
def admin_reports():
    db = get_db()
    total_loans = db.execute("SELECT COUNT(loan_id) FROM loans").fetchone()[0] or 0
    physical_loans = db.execute("SELECT COUNT(loan_id) FROM loans WHERE tipe_pinjaman = 'fisik'").fetchone()[0] or 0
    digital_loans = db.execute("SELECT COUNT(loan_id) FROM loans WHERE tipe_pinjaman = 'digital'").fetchone()[0] or 0
    total_fines_collected = db.execute("SELECT SUM(denda) FROM loans WHERE denda > 0 AND (status_pinjaman = 'dikembalikan' OR status_pinjaman = 'terlambat_dikembalikan')").fetchone()[0] or 0
    popular_books = db.execute(
        """
        SELECT b.judul, COUNT(l.loan_id) as jumlah_peminjaman
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        GROUP BY l.book_id
        ORDER BY jumlah_peminjaman DESC
        LIMIT 5 
        """
    ).fetchall() 
    users_with_most_fines = db.execute(
        """
        SELECT u.nama_lengkap, u.nomor_anggota, SUM(l.denda) as total_denda
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        WHERE l.denda > 0
        GROUP BY l.user_id
        ORDER BY total_denda DESC
        LIMIT 5
        """
    ).fetchall()
    return render_template('admin/reports.html', 
                           title="Laporan Perpustakaan",
                           total_loans=total_loans,
                           physical_loans=physical_loans,
                           digital_loans=digital_loans,
                           total_fines_collected=total_fines_collected,
                           popular_books=popular_books,
                           users_with_most_fines=users_with_most_fines)

@app.route('/admin/loan/<int:loan_id>/edit_fine', methods=['GET', 'POST'])
@staff_required 
def admin_edit_fine(loan_id):
    db = get_db()
    loan_detail_raw = db.execute(
        """
        SELECT l.*, u.nama_lengkap AS nama_peminjam, u.user_id AS peminjam_user_id, b.judul AS judul_buku
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        JOIN books b ON l.book_id = b.book_id
        WHERE l.loan_id = ? AND l.tipe_pinjaman = 'fisik' 
        AND (l.status_pinjaman = 'dikembalikan' OR l.status_pinjaman = 'terlambat_dikembalikan')
        """, 
        (loan_id,)
    ).fetchone()

    user_id_for_back_link = request.args.get('user_id', type=int) 
    if not loan_detail_raw:
        flash("Data peminjaman tidak ditemukan atau tidak valid untuk penyesuaian denda.", "danger")
        if user_id_for_back_link:
            return redirect(url_for('admin_user_detail', user_id=user_id_for_back_link))
        return redirect(url_for('admin_active_loans'))

    loan_detail = dict(loan_detail_raw)
    loan_detail['tanggal_pinjam_dt'] = parse_datetime_str(loan_detail.get('tanggal_pinjam'))
    loan_detail['tanggal_jatuh_tempo_dt'] = parse_datetime_str(loan_detail.get('tanggal_jatuh_tempo'))
    loan_detail['tanggal_kembali_dt'] = parse_datetime_str(loan_detail.get('tanggal_kembali'))

    if not user_id_for_back_link : 
        user_id_for_back_link = loan_detail['peminjam_user_id']
    
    if request.method == 'POST':
        new_fine_str = request.form.get('denda_baru')
        error = None
        try:
            new_fine = int(new_fine_str)
            if new_fine < 0:
                error = "Jumlah denda tidak boleh negatif."
            if error is None:
                db.execute("UPDATE loans SET denda = ? WHERE loan_id = ?", (new_fine, loan_id))
                db.commit()
                flash(f"Denda untuk peminjaman buku '{loan_detail['judul_buku']}' oleh '{loan_detail['nama_peminjam']}' berhasil diperbarui menjadi Rp {new_fine:,.0f}.", "success")
                if user_id_for_back_link: 
                    return redirect(url_for('admin_user_detail', user_id=user_id_for_back_link))
                return redirect(url_for('admin_active_loans')) 
        except ValueError:
            error = "Jumlah denda harus berupa angka."
        except sqlite3.Error as e:
            error = f"Gagal memperbarui denda: {e}"
        if error:
            flash(error, "danger")
        return render_template('admin/edit_fine.html', title="Edit Denda Peminjaman", loan=loan_detail, user_id_for_back=user_id_for_back_link)
    
    return render_template('admin/edit_fine.html', title="Edit Denda Peminjaman", loan=loan_detail, user_id_for_back=user_id_for_back_link)

if __name__ == '__main__':
    app.run(debug=True)

