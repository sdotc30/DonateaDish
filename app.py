from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Connect to MySQL (XAMPP)
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Default XAMPP MySQL user
    password="Devansh03",  # Leave empty if no password
    database="donate_a_dish"
)
cursor = db.cursor(dictionary=True)

# Test Route
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/login')
def login():
    return render_template('login.html')

# Fetch all users
@app.route("/recipient", methods=["GET"])
def get_users():
    cursor.execute("SELECT * FROM recipient")
    recipient = cursor.fetchall()
    return jsonify(recipient)

# Add a new user
@app.route("/recipient", methods=["POST"])
def add_user():
    data = request.json
    cursor.execute("INSERT INTO recipients (Itm, Qty, loc, des) VALUES (%s, %s, %s, %s)", (data["Itm"], data["Qty"], data["loc"], data["des"]))
    db.commit()
    return jsonify({"message": "User added successfully!"})

# Run Flask Server
if __name__ == "__main__":
    app.run(debug=True)



app.run(debug = True)