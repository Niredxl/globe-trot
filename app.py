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
    conn.execute("""
    
    CREATE TABLE  IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
    
    """)
    conn.execute("""
    
    CREATE TABLE IF NOT EXISTS itinerary_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    city TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    budget REAL,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);
    
    """)
    conn.execute("""
    
    CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT
);
    
    """)
    conn.commit()
    conn.close()

init_db()

def handle_trip_creation():
    location = request.form['location']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trips (user_id, location, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (user_id, location, start_date, end_date))

    trip_id = cursor.lastrowid  
    
    conn.commit()
    conn.close()

    return redirect(url_for('build_itinerary', trip_id=trip_id))

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



@app.route('/trip/create', methods=['GET', 'POST'])
def create_trip():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        return handle_trip_creation()

    return render_template('create_trip.html')

    return redirect(url_for('build_itinerary', trip_id=trip_id))


@app.route('/trip/<int:trip_id>/itinerary', methods=['GET', 'POST'])
def build_itinerary(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cities = request.form.getlist('city[]')
        descriptions = request.form.getlist('description[]')
        start_dates = request.form.getlist('start_date[]')
        end_dates = request.form.getlist('end_date[]')
        budgets = request.form.getlist('budget[]')

        conn = get_db()
        cursor = conn.cursor()

        for i in range(len(cities)):
            cursor.execute("""
                INSERT INTO itinerary_stops
                (trip_id, city, description, start_date, end_date, budget)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trip_id,
                cities[i],
                descriptions[i],
                start_dates[i],
                end_dates[i],
                budgets[i]
            ))

        conn.commit()
        conn.close()

        return redirect(url_for('trip_summary', trip_id=trip_id))

    return render_template('build_itinerary.html', trip_id=trip_id)


@app.route('/test')
def test():
    return render_template('home.html')

@app.route('/profile')
def user_profile():
    return render_template('user_profile.html')




@app.route('/triplisting')
def trip_listing():
    return render_template('trip_listing.html')

if __name__ == '__main__':
    app.run(debug=True)
