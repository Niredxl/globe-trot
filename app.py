from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/createtrip')
def create_trip():
    return render_template('create_trip.html')

if __name__ == '__main__':
    app.run(debug=True)