from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hello-there"
users = {
    "admin": generate_password_hash("password123")
}

@app.route('/')
def home():
    if 'user' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['user'] = username 
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))
@app.route('/test')
def test():
    return render_template('home.html')
if __name__ == '__main__':
    app.run(debug=True)