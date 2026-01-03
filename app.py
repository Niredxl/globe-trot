from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import random
from datetime import date, datetime
import sqlite3, os

LOCATION_IMAGES = {
    "Paris, France": ["paris1.jpg", "paris2.jpg", "paris3.jpg"],
        "Tokyo, Japan": ["japan1.jpg", "japan2.jpg", "japan3.jpg"],
        "New York, USA": ["newyork1.jpg", "newyork2.jpg", "newyork3.jpg"],
        "Dubai, UAE": ["dubai1.jpg","dubai2.jpg","dubai3.jpg"],
        "Barcelona, Spain": ["barcelona1.jpg","barcelona2.jpg","barcelona3.jpg"],
        "London, UK": ["london1.jpg","london2.jpg","london3.jpg"],
        "Rome, Italy": ["rome1.jpg","rome2.jpg","rome3.jpg"],
        "Bali, Indonesia": ["bali1.jpg","bali2.jpg","bali3.jpg"]
}

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
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        description TEXT,
        budget_limit REAL DEFAULT 0.0,
        is_public BOOLEAN DEFAULT 0,
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
    
    # Global catalog of activities (searchable)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        cost_estimate REAL DEFAULT 0.0,
        image_url TEXT
    );
    """)

    # Activities specific to a trip's stop
    conn.execute("""
    CREATE TABLE IF NOT EXISTS trip_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stop_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        cost REAL DEFAULT 0.0,
        start_time DATETIME,
        booked BOOLEAN DEFAULT 0,
        FOREIGN KEY (stop_id) REFERENCES itinerary_stops(id)
    );
    """)
    
    conn.commit()
    conn.close()

def migrate_db():
    """Simple migration to add missing columns if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check trips table for new columns
    try:
        cursor.execute("SELECT description, budget_limit, is_public FROM trips LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating trips table...")
        try:
            cursor.execute("ALTER TABLE trips ADD COLUMN description TEXT")
        except sqlite3.OperationalError: pass
        try:
            cursor.execute("ALTER TABLE trips ADD COLUMN budget_limit REAL DEFAULT 0.0")
        except sqlite3.OperationalError: pass
        try:
            cursor.execute("ALTER TABLE trips ADD COLUMN is_public BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError: pass
        conn.commit()

    # Check activities table for new columns
    try:
        cursor.execute("SELECT cost_estimate, image_url FROM activities LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating activities table...")
        try:
            cursor.execute("ALTER TABLE activities ADD COLUMN cost_estimate REAL DEFAULT 0.0")
        except sqlite3.OperationalError: pass
        try:
            cursor.execute("ALTER TABLE activities ADD COLUMN image_url TEXT")
        except sqlite3.OperationalError: pass
        conn.commit()
        
    conn.close()

init_db()
migrate_db()

def handle_trip_creation():
    location = request.form['location']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    description = request.form.get('description', '')
    budget_limit = request.form.get('budget_limit', 0.0)
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trips (user_id, location, start_date, end_date, description, budget_limit)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, location, start_date, end_date, description, budget_limit))

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
        conn = get_db()
        rows = conn.execute("""
            SELECT t.*, COUNT(s.id) as stop_count 
            FROM trips t 
            LEFT JOIN itinerary_stops s ON t.id = s.trip_id 
            WHERE t.user_id = ? 
            GROUP BY t.id
            ORDER BY t.start_date DESC
        """, (session['user_id'],)).fetchall()
        
        trips = []
        for trip in rows:
            trip_data = dict(trip)
            images = LOCATION_IMAGES.get(trip["location"], ["default1.jpg", "default2.jpg", "default3.jpg"])
            trip_data["image"] = random.choice(images)
            trips.append(trip_data)
        conn.close()
        
        return render_template('home.html', trips=trips)
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


@app.route('/trip/<int:trip_id>/itinerary', methods=['GET'])
def build_itinerary(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    
    # Get Trip Details
    trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip or trip['user_id'] != session['user_id']:
        return redirect(url_for('trip_listing'))
        
    # Get Stops
    stops = conn.execute("SELECT * FROM itinerary_stops WHERE trip_id = ? ORDER BY start_date", (trip_id,)).fetchall()
    
    # Get Activities for each stop
    stops_data = []
    for stop in stops:
        activities = conn.execute("SELECT * FROM trip_activities WHERE stop_id = ?", (stop['id'],)).fetchall()
        stop_dict = dict(stop)
        stop_dict['activities'] = [dict(a) for a in activities]
        stops_data.append(stop_dict)

    conn.close()
    return render_template('build_itinerary.html', trip=trip, stops=stops_data)

@app.route('/trip/<int:trip_id>/add_stop', methods=['POST'])
def add_stop(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    city = request.form['city']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    description = request.form.get('description')
    budget = request.form.get('budget', 0)
    
    conn = get_db()
    conn.execute("""
        INSERT INTO itinerary_stops (trip_id, city, description, start_date, end_date, budget)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (trip_id, city, description, start_date, end_date, budget))
    conn.commit()
    conn.close()
    return redirect(url_for('build_itinerary', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/stop/<int:stop_id>/add_activity', methods=['POST'])
def add_activity(trip_id, stop_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    name = request.form['name']
    category = request.form['category']
    cost = request.form.get('cost', 0)
    start_time = request.form.get('start_time') # Optional
    
    conn = get_db()
    conn.execute("""
        INSERT INTO trip_activities (stop_id, name, category, cost, start_time)
        VALUES (?, ?, ?, ?, ?)
    """, (stop_id, name, category, cost, start_time))
    conn.commit()
    conn.close()
    return redirect(url_for('build_itinerary', trip_id=trip_id))


@app.route('/test')
def test():
    return render_template('home.html')

@app.route('/profile')
def user_profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Fetch trips for stats
    rows = conn.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY start_date DESC", (session['user_id'],)).fetchall()
    conn.close()

    trips = []
    for trip in rows:
        trip_data = dict(trip)
        images = LOCATION_IMAGES.get(trip["location"], ["default1.jpg", "default2.jpg", "default3.jpg"])
        trip_data["image"] = random.choice(images)
        trips.append(trip_data)
    
    return render_template('user_profile.html', user=user, trips=trips)




@app.route('/triplisting')
def trip_listing():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    conn = get_db()
    rows = conn.execute("""
        SELECT 
            t.id,
            t.location,
            t.start_date,
            t.end_date,
            COUNT(s.id) AS stop_count
        FROM trips t
        LEFT JOIN itinerary_stops s ON t.id = s.trip_id
        WHERE t.user_id = ?
        GROUP BY t.id
        ORDER BY t.start_date ASC
    """, (user_id,)).fetchall()
    conn.close()

    ongoing, upcoming, completed = [], [], []

    for trip in rows:
        start = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(trip["end_date"], "%Y-%m-%d").date()

        images = LOCATION_IMAGES.get(
            trip["location"],
            ["default1.jpg", "default2.jpg", "default3.jpg"]
        )

        trip_data = dict(trip)
        trip_data["image"] = random.choice(images)

        if start <= today <= end:
            ongoing.append(trip_data)
        elif start > today:
            upcoming.append(trip_data)
        else:
            completed.append(trip_data)

    return render_template(
        "trip_listing.html",
        ongoing_trips=ongoing,
        upcoming_trips=upcoming,
        completed_trips=completed
    )

def seed_data():
    conn = get_db()
    cursor = conn.cursor()
    # Check if activities exist
    if cursor.execute("SELECT COUNT(*) FROM activities").fetchone()[0] == 0:
        print("Seeding activities...")
        activities = [
            ("Paris", "Eiffel Tower", "Sightseeing", "Iconic iron tower with city views.", 30.0, "paris1.jpg"),
            ("Paris", "Louvre Museum", "Sightseeing", "World's largest art museum.", 20.0, "paris2.jpg"),
            ("Paris", "Seine River Cruise", "Relaxation", "Boat tour along the Seine.", 15.0, "paris3.jpg"),
            ("London", "London Eye", "Sightseeing", "Giant observation wheel.", 35.0, "london1.jpg"),
            ("London", "British Museum", "Sightseeing", "Human history and culture.", 0.0, "london2.jpg"),
            ("Tokyo", "Senso-ji Temple", "Sightseeing", "Ancient Buddhist temple.", 0.0, "japan1.jpg"),
            ("Tokyo", "Sushi Making Class", "Food & Drink", "Learn to make sushi.", 80.0, "japan2.jpg"),
            ("New York", "Statue of Liberty", "Sightseeing", "Symbol of freedom.", 25.0, "newyork1.jpg"),
            ("New York", "Broadway Show", "Entertainment", "World-famous theater.", 150.0, "newyork2.jpg")
        ]
        cursor.executemany("""
            INSERT INTO activities (city, name, category, description, cost_estimate, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, activities)
        conn.commit()
    conn.close()

seed_data()

@app.route('/search')
def activity_search():
    query = request.args.get('q', '')
    city = request.args.get('city', '')
    
    conn = get_db()
    sql = "SELECT * FROM activities WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f'%{query}%', f'%{query}%'])
    if city:
        sql += " AND city LIKE ?"
        params.append(f'%{city}%')
        
    results = conn.execute(sql, params).fetchall()
    conn.close()
    
    # If AJAX request (JSON)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'results': [dict(r) for r in results]}
        
    return render_template('activity_search.html', results=results, query=query, city=city)

@app.route('/trip/<int:trip_id>/public')
def public_trip_view(trip_id):
    conn = get_db()
    trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    
    if not trip:
        conn.close()
        return "Trip not found", 404
        
    # Check if public or if current user owns it
    is_owner = 'user_id' in session and session['user_id'] == trip['user_id']
    if not trip['is_public'] and not is_owner:
        conn.close()
        return "This trip is private.", 403

    # Fetch details
    stops = conn.execute("SELECT * FROM itinerary_stops WHERE trip_id = ? ORDER BY start_date", (trip_id,)).fetchall()
    stops_data = []
    total_cost = 0
    
    for stop in stops:
        activities = conn.execute("SELECT * FROM trip_activities WHERE stop_id = ?", (stop['id'],)).fetchall()
        stop_dict = dict(stop)
        stop_dict['activities'] = [dict(a) for a in activities]
        stop_dict['stop_cost'] = sum(a['cost'] for a in activities) + (stop['budget'] or 0) # simplified cost logic
        total_cost += stop_dict['stop_cost']
        stops_data.append(stop_dict)
        
    conn.close()
    
    return render_template('itinerary_view.html', trip=trip, stops=stops_data, is_owner=is_owner, total_cost=total_cost)

@app.route('/trip/<int:trip_id>/toggle_public', methods=['POST'])
def toggle_trip_public(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db()
    # Verify owner
    trip = conn.execute("SELECT user_id, is_public FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if trip and trip['user_id'] == session['user_id']:
        new_status = not trip['is_public']
        conn.execute("UPDATE trips SET is_public = ? WHERE id = ?", (new_status, trip_id))
        conn.commit()
    conn.close()
    
    return redirect(url_for('build_itinerary', trip_id=trip_id))

@app.route('/community')
def community_tab():
    # Show all public trips
    conn = get_db()
    trips = conn.execute("""
        SELECT t.*, u.first_name, u.photo 
        FROM trips t 
        JOIN users u ON t.user_id = u.id 
        WHERE t.is_public = 1 
        ORDER BY t.created_at DESC
    """).fetchall()
    conn.close()
    return render_template('community_tab.html', trips=trips)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session: return redirect(url_for('login')) # simplistic auth
    conn = get_db()
    # stats
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trip_count = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    # recent trips
    recent_trips = conn.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()
    return render_template('admin.html', user_count=user_count, trip_count=trip_count, recent_trips=recent_trips)

@app.route('/trip/<int:trip_id>/delete', methods=['POST'])
def delete_trip(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db()
    # Verify owner
    trip = conn.execute("SELECT user_id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if trip and trip['user_id'] == session['user_id']:
        # Delete dependencies
        conn.execute("DELETE FROM trip_activities WHERE stop_id IN (SELECT id FROM itinerary_stops WHERE trip_id = ?)", (trip_id,))
        conn.execute("DELETE FROM itinerary_stops WHERE trip_id = ?", (trip_id,))
        conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
    conn.close()
    
    return redirect(url_for('trip_listing'))
if __name__ == '__main__':
    app.run(debug=True)
