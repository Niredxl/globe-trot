from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = "hello-there"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_NAME = "users.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            city TEXT,
            country TEXT,
            bio TEXT,
            photo TEXT,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        # Form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form.get('phone')
        city = request.form.get('city')
        country = request.form.get('country')
        bio = request.form.get('bio')
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Backend validation (NEVER trust JS only)
        if password != confirm_password or len(password) < 8:
            flash("Password validation failed", "danger")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        # Photo upload
        photo = request.files.get('photo')
        photo_filename = None
        if photo and photo.filename:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))

        try:
            conn = get_db()
            conn.execute("""
                INSERT INTO users
                (first_name, last_name, email, phone, city, country, bio, photo, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name, last_name, email,
                phone, city, country, bio,
                photo_filename, hashed_password
            ))
            conn.commit()
            conn.close()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash("Email already exists", "danger")
            return redirect(url_for('signup'))

    return render_template('register.html')


@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['first_name']
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/test')
def test():
    return render_template('home.html')

@app.route('/profile')
def user_profile():
    return render_template('user_profile.html')


@app.route('/createtrip')
def create_trip():
    return render_template('create_trip.html')

@app.route('/builditinerary')
def build_itinerary():
    return render_template('build_itinerary.html')

@app.route('/triplisting')
def trip_listing():
    return render_template('trip_listing.html')

@app.route('/search')
def activity_search():
    return render_template('activity_search.html')

@app.route('/itineraryview')
def itinerary_view():
    return render_template('itinerary_view.html')

@app.route('/communitytab')
def community_tab():
    return render_template('community_tab.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
