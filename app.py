from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required
from flask_login import current_user
import os
from flask import jsonify
from flask_cors import CORS
from sqlalchemy import text  # Import the text function
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask_mail import Mail, Message


# Load environment variables
load_dotenv()

# Environment variables for database connection
AIVEN_USER = os.getenv("AIVEN_USER")
AIVEN_PASSWORD = os.getenv("AIVEN_PASSWORD")
AIVEN_HOST = os.getenv("AIVEN_HOST")
AIVEN_PORT = os.getenv("AIVEN_PORT")
AIVEN_DB = os.getenv("AIVEN_DB")

# Validate environment variables
if not all([AIVEN_USER, AIVEN_PASSWORD, AIVEN_HOST, AIVEN_PORT, AIVEN_DB]):
    raise ValueError("Missing one or more database credentials in .env file.")


# After initializing Flask app
app = Flask(__name__)
CORS(app)  # This enables CORS for all routes


# Configure secret key
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is missing in the .env file.")

# Configure SQLAlchemy database URI
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql+pymysql://{AIVEN_USER}:{AIVEN_PASSWORD}@{AIVEN_HOST}:{AIVEN_PORT}/{AIVEN_DB}"

# SSL Configuration for Aiven Cloud MySQL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "ssl": {
            "ssl-mode": "REQUIRED",
        }
    }
}

# Initialize SQLAlchemy and LoginManager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # Your Gmail email
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Your Gmail password or App Password
mail = Mail(app)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Database Models
class Recipient(db.Model):
    rid = db.Column(db.Integer, primary_key=True)
    food_item = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    location = db.Column(db.String(300))
    expiry_time = db.Column(db.DateTime)
    description = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)  # Hashed password
    role = db.Column(db.String(20), nullable=False)  # "donor" or "recipient"

class DonationStatus(db.Model):
    __tablename__ = 'donation_status'
    status_id = db.Column(db.Integer, primary_key=True)
    # Foreign key to the donation request (rid from Recipient table)
    rid = db.Column(db.Integer, db.ForeignKey('recipient.rid'), nullable=False)
    # Foreign key to the donor (user_id from Users table)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Status values: "Acknowledgement Pending", "Donation Accepted", "Donation Ongoing"
    status = db.Column(db.String(50), nullable=False, default="Donation Request Listed") 

class DonorDetails(db.Model):
    __tablename__ = 'donor_details'
    id = db.Column(db.Integer, primary_key=True)
    rid = db.Column(db.Integer, db.ForeignKey('recipient.rid'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    quantity_fulfilled = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())



# Routes

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/donor_dashboard')
@login_required
def donor_dashboard():
    return render_template('donor_dashboard.html')


from datetime import datetime

@app.route('/recipient_dashboard', methods=["GET", "POST"])
@login_required
def recipient_dashboard():
    if request.method == "POST":
        food_item = request.form.get('food_item')
        quantity = request.form.get('quantity')
        location = request.form.get('location')
        expiry_time = request.form.get('date-time')
        description = request.form.get('description')

        expiry_dt = datetime.strptime(expiry_time, "%Y-%m-%dT%H:%M")

        new_request = Recipient(
            food_item=food_item,
            quantity=quantity,
            location=location,
            expiry_time=expiry_dt,
            description=description,
            user_id=current_user.id
        )

        try:
            db.session.add(new_request)
            db.session.commit()
            flash("✅ Request posted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Could not post request. Try again later.", "danger")
            logging.error(f"DB Error: {str(e)}")

        return redirect(url_for('recipient_dashboard'))

    return render_template('recipient_dashboard.html')

@app.route('/api/my_requests')
@login_required
def get_my_requests():
    if current_user.role != 'recipient':
        return jsonify({"error": "Unauthorized access"}), 403

    user_requests = Recipient.query.filter_by(user_id=current_user.id).filter(Recipient.quantity>0).all()
    
    data = []
    for req in user_requests:
        data.append({
            "id": req.rid,
            "food_item": req.food_item,
            "quantity": req.quantity,
            "location": req.location,
            "expiry_time": req.expiry_time.strftime("%Y-%m-%d %I:%M %p"),
            "desc": req.description
        })

    return jsonify(data)

@app.route("/api/delete_request/<int:request_id>", methods=["DELETE"])
@login_required
def delete_request(request_id):
    req = Recipient.query.get(request_id)
    if req and req.user_id == current_user.id:
        try:
            # First delete related records in DonationStatus if they exist
            status_entries = DonationStatus.query.filter_by(rid=request_id).all()
            for status in status_entries:
                db.session.delete(status)
            
            # Then delete related records in DonorDetails if they exist
            donor_details = DonorDetails.query.filter_by(rid=request_id).all()
            for detail in donor_details:
                db.session.delete(detail)
            
            # Finally delete the main record
            db.session.delete(req)
            db.session.commit()
            return jsonify({"message": "Deleted"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting request: {str(e)}")
            return jsonify({"error": "Database error"}), 500
    return jsonify({"error": "Unauthorized"}), 403


@app.route("/api/edit_request/<int:request_id>", methods=["PUT"])
@login_required
def edit_request(request_id):
    req = Recipient.query.get(request_id)
    if req and req.user_id == current_user.id:
        data = request.get_json()
        req.food_item = data.get("food_item", req.food_item)
        req.quantity = data.get("quantity", req.quantity)
        req.location = data.get("location", req.location)
        req.description = data.get("desc", req.description)
        db.session.commit()
        return jsonify({"message": "Updated"}), 200
    return jsonify({"error": "Unauthorized"}), 403


@app.route('/api/all_requests', methods=["GET"])
@login_required
def get_all_requests():
    if current_user.role != 'donor':
        return jsonify({"error": "Unauthorized access"}), 403
   
    location_query = request.args.get('location')
    
    # Get all requests that match the filters with quantity > 0
    query = Recipient.query
    if location_query:
        query = query.filter(Recipient.location.ilike(f"%{location_query}%"))
    
    query = query.filter(Recipient.quantity > 0)
    
    # Get all filtered requests
    all_requests = query.all()
    
    # Get ALL status entries (not just for filtered requests)
    # This is crucial because we need to know ALL requests that have been claimed
    all_status_entries = DonationStatus.query.all()
    
    # Create a dict to track which requests are claimed and by whom
    # Key is request ID, value is donor ID
    claimed_requests = {}
    for entry in all_status_entries:
        if entry.status in ['Acknowledgement Pending', 'Donation Ongoing']:
            claimed_requests[entry.rid] = entry.donor_id
    
    data = []
    for req in all_requests:
        # Check if this request is claimed
        if req.rid in claimed_requests:
            # If claimed by current user, add it
            if claimed_requests[req.rid] == current_user.id:
                data.append({
                    "id": req.rid,
                    "food_item": req.food_item,
                    "quantity": req.quantity,
                    "location": req.location,
                    "expiry_time": req.expiry_time.strftime("%Y-%m-%d %I:%M %p"),
                    "desc": req.description
                })
        else:
            # Not claimed by anyone, add it
            data.append({
                "id": req.rid,
                "food_item": req.food_item,
                "quantity": req.quantity,
                "location": req.location,
                "expiry_time": req.expiry_time.strftime("%Y-%m-%d %I:%M %p"),
                "desc": req.description
            })
    
    return jsonify(data)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/api/profile_data')
@login_required
def profile_data():
    if current_user.role != 'donor':
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Fetching a single user
    user_data = Users.query.filter_by(id=current_user.id).first()

    if user_data is None:
        return jsonify({"error": "User not found"}), 404
    
    # Returning the data as a single object
    userd = {
        "Name": user_data.email.split('@')[0],
        "email": user_data.email,
        "role": user_data.role
    }

    return jsonify(userd)

@app.route('/api/status/create', methods=["POST"])
@login_required
def create_status():
    if current_user.role != "donor":
        return jsonify({"error": "Only donors can create status"}), 403

    data = request.get_json()
    rid = data.get("rid")

    if not rid:
        return jsonify({"error": "Recipient request ID is required"}), 400

    # Check if status already exists for this donor and request
    existing = DonationStatus.query.filter_by(rid=rid, donor_id=current_user.id).first()
    if existing:
        return jsonify({"error": "Status already exists"}), 400

    new_status = DonationStatus(
        rid=rid,
        donor_id=current_user.id,
        status="Acknowledgement Pending"
    )

    try:
        db.session.add(new_status)
        db.session.commit()
        return jsonify({"message": "Status created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating status: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/status', methods=["GET"])
@login_required
def get_statuses():
    if current_user.role == "recipient":
        # Join with Recipient to filter by recipient's user_id
        statuses = db.session.query(DonationStatus, Recipient).join(Recipient).filter(
            Recipient.user_id == current_user.id
        ).all()

    elif current_user.role == "donor":
        statuses = db.session.query(DonationStatus, Recipient).join(Recipient).filter(
            DonationStatus.donor_id == current_user.id
        ).all()
    else:
        return jsonify({"error": "Unauthorized role"}), 403

    result = []
    for status, req in statuses:
        result.append({
            "status_id": status.status_id,
            "rid": status.rid,
            "donor_id": status.donor_id,
            "status": status.status,
            "food_item": req.food_item,
            "quantity": req.quantity,
            "location": req.location
        })
    return jsonify(result), 200

@app.route('/api/status/update/<int:status_id>', methods=["PUT"])
@login_required
def update_status(status_id):
    status_entry = db.session.get(DonationStatus, status_id)
    if not status_entry:
        return jsonify({"error": "Status not found"}), 404

    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    recipient_req = Recipient.query.get(status_entry.rid)

    if current_user.role == "recipient":
        # Recipient can only update to "Donation Accepted"
        if recipient_req.user_id != current_user.id:
            return jsonify({"error": "Unauthorized recipient"}), 403
        if new_status != "Donation Accepted":
            return jsonify({"error": "Recipients can only acknowledge"}), 403

    elif current_user.role == "donor":
        # Donor can update to "Donation Ongoing" only *after* recipient has acknowledged
        if status_entry.donor_id != current_user.id:
            return jsonify({"error": "Unauthorized donor"}), 403

        if new_status == "Donation Ongoing" and status_entry.status != "Donation Accepted":
            return jsonify({"error": "Donation must be acknowledged first"}), 400

        # Donor can't set to "Donation Accepted"
        if new_status == "Donation Accepted":
            return jsonify({"error": "Donors cannot set this status"}), 403

    else:
        return jsonify({"error": "Unauthorized role"}), 403

    # Update and save
    status_entry.status = new_status
    try:
        db.session.commit()
        return jsonify({"message": f"Status updated to '{new_status}'"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating status: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/status/delete/<int:rid>', methods=["DELETE"])
@login_required
def delete_status(rid):
    status_entry = DonationStatus.query.filter_by(rid=rid, donor_id=current_user.id).first()
    donor_status = DonorDetails.query.filter_by(rid=rid,donor_id = current_user.id).first()

    if not status_entry:
        return jsonify({"error": "Unauthorized or not found"}), 403

    try:
        db.session.delete(status_entry)
        db.session.delete(donor_status)
        db.session.commit()
        return jsonify({"message": "Donation status canceled"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting status: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/acknowledge_donation/<int:rid>', methods=["PUT"])
@login_required
def acknowledge_donation(rid):
    if current_user.role != "recipient":
        return jsonify({"error": "Only recipients can acknowledge donations"}), 403

    # Check if the recipient actually made this request
    request_entry = Recipient.query.filter_by(rid=rid, user_id=current_user.id).first()
    if not request_entry:
        return jsonify({"error": "Request not found or unauthorized"}), 404

    # Find the corresponding DonationStatus
    status_entry = DonationStatus.query.filter_by(rid=rid).first()
    if not status_entry:
        return jsonify({"error": "Donation status not found"}), 404

    # Only allow acknowledgement if status is "Acknowledgement Pending"
    if status_entry.status != "Acknowledgement Pending":
        return jsonify({"error": "Cannot acknowledge donation at this stage"}), 400

    status_entry.status = "Donation Ongoing"
    try:
        db.session.commit()
        recipient_user = DonorDetails.query.filter_by(rid=rid).first()
        msg = Message(
            subject="Your Donation has been Acknowledged",
            sender=app.config['MAIL_USERNAME'],
            recipients=[recipient_user.email]
        )
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Base styles */
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #ff6f61;
            font-size: 24px;
        }}
        p {{
            margin: 10px 0;
        }}
        .details {{
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #eee;
        }}
        .details p {{
            margin: 5px 0;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 14px;
            color: #ff6f61;
        }}
        .button {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}

        /* Responsive design for mobile devices */
        @media (max-width: 600px) {{
            .container {{
                padding: 15px;
            }}
            h1 {{
                font-size: 20px;
            }}
            .button {{
                width: 100%;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Donation Has Been Acknowledged!</h1>
        <p>Dear {recipient_user.email.split('@')[0]},</p>
        <p>We are pleased to inform you that your generous contribution of <strong>{request_entry.food_item}</strong> has been officially acknowledged by the recipient through DonateaDish. Your support plays a vital role in making a positive impact, and we are grateful for your compassionate gesture. You may continue to monitor the status of your donation through your dashboard. Thank you for embodying the spirit of giving and being an integral part of our mission.</p>
        <br>
        <br>
        <p>Please login to your dashboard at <a href="https://donateadish.onrender.com">DonateaDish</a> to proceed further.</p>

        <div class="footer">
            <p>Best Regards,<br>Team DonateaDish</p>
        </div>
    </div>
</body>
</html>
"""
        mail.send(msg)
        return jsonify({"message": "Acknowledged successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error acknowledging donation: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    
@app.route('/api/status/<int:rid>', methods=["GET"])
@login_required
def get_status_by_rid(rid):
    """Get donation status for a specific request ID"""
    status_entry = DonationStatus.query.filter_by(rid=rid).first()
    
    if status_entry:
        return jsonify({
            "status": status_entry.status,
            "donor_id": status_entry.donor_id
        }), 200
    else:
        return jsonify({
            "status": "Donation Request Listed"
        }), 200



@app.route('/api/accept_donation/<int:rid>', methods=["POST"])
@login_required
def accept_donation(rid):
    if current_user.role != "donor":
        return jsonify({"error": "Only donors can accept donations"}), 403

    data = request.get_json()
    donor_name = data.get("name")
    donor_email = data.get("email")
    donor_phone = data.get("phone")
    quantity_fulfilled = data.get("quantity")
    additional_notes = data.get("notes")

    # Validate required fields
    if not all([donor_name, donor_email, donor_phone, quantity_fulfilled]):
        return jsonify({"error": "All required fields must be filled"}), 400

    # Check if the request exists
    request_entry = Recipient.query.get(rid)
    if not request_entry:
        return jsonify({"error": "Request not found"}), 404

    # Create or update the donation status
    status_entry = DonationStatus.query.filter_by(rid=rid, donor_id=current_user.id).first()
    if not status_entry:
        status_entry = DonationStatus(
            rid=rid,
            donor_id=current_user.id,
            status="Acknowledgement Pending"
        )
        db.session.add(status_entry)
    else:
        status_entry.status = "Acknowledgement Pending"

    # Insert donor details into the new table
    donor_details = DonorDetails(
        rid=rid,
        donor_id=current_user.id,
        name=donor_name,
        email=donor_email,
        phone=donor_phone,
        quantity_fulfilled=quantity_fulfilled,
        notes=additional_notes
    )
    db.session.add(donor_details)

    try:
        db.session.commit()

        # Send email to the recipient
        recipient_user = Users.query.get(request_entry.user_id)
        msg = Message(
            subject="Your Donation Request Has Been Accepted",
            sender=app.config['MAIL_USERNAME'],
            recipients=[recipient_user.email]
        )
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Base styles */
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #ff6f61;
            font-size: 24px;
        }}
        p {{
            margin: 10px 0;
        }}
        .details {{
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #eee;
        }}
        .details p {{
            margin: 5px 0;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 14px;
            color: #ff6f61;
        }}
        .button {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}

        /* Responsive design for mobile devices */
        @media (max-width: 600px) {{
            .container {{
                padding: 15px;
            }}
            h1 {{
                font-size: 20px;
            }}
            .button {{
                width: 100%;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Donation Request Has Been Accepted!</h1>
        <p>Dear {recipient_user.email.split('@')[0]},</p>
        <p>Your donation request for <strong>{request_entry.food_item}</strong> has been accepted by a donor on DonateaDish.</p>

        <div class="details">
            <p><strong>Name of the Donor:</strong> {donor_name}</p>
            <p><strong>Email Address of the Donor:</strong> {donor_email}</p>
            <p><strong>Contact Information of the Donor:</strong> {donor_phone}</p>
            <p><strong>Quantity They Will Fulfill:</strong> {quantity_fulfilled}</p>
            <p><strong>A Note by the Donor:</strong> {additional_notes or 'None'}</p>
        </div>

        <p>Please login to your dashboard at <a href="https://donateadish.onrender.com">DonateaDish</a> to acknowledge the donor's request and proceed further.</p>

        <div class="footer">
            <p>Best Regards,<br>Team DonateaDish</p>
        </div>
    </div>
</body>
</html>
"""
        mail.send(msg)

        return jsonify({"message": "Donation accepted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error accepting donation: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    
@app.route('/api/markcomplete/<int:rid>', methods = ['PATCH'])
@login_required
def markcomplete(rid):
    if current_user.role != "recipient":
        return jsonify({"error": "Only recipients can mark donations as completed."}), 403
    updatedqty = DonorDetails.query.filter_by(rid=rid).first()
    req_list = Recipient.query.filter_by(rid=rid).first()
    status = DonationStatus.query.filter_by(rid=rid).first()

    qty = req_list.quantity
    qtyfulfill = updatedqty.quantity_fulfilled
    new_qty = qty - qtyfulfill

    if new_qty == 0:
        req_list.quantity = 0
    else:
        req_list.quantity = new_qty
    
    db.session.delete(status)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        # Debugging: Log form data
        logging.debug(f"Form data: {request.form}")

        # Validate form data
        if not email or not password or not role:
            flash("All fields are required.", "danger")
            return render_template('signup.html')

        if role not in ["donor", "recipient"]:
            flash("Invalid role selected.", "danger")
            return render_template('signup.html')

        # Check if user already exists
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        # Hash the password
        encpassword = generate_password_hash(password)

        new_user=Users(email=email,password=encpassword,role=role)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Signup Success! Please Login", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template('signup.html')

    return render_template('signup.html')


from flask_login import current_user

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ✅ If already logged in, redirect based on role
    if current_user.is_authenticated:
        role = session.get('role')
        if role == 'donor':
            return redirect(url_for('donor_dashboard'))
        elif role == 'recipient':
            return redirect(url_for('recipient_dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        user = Users.query.filter_by(email=email, role=role).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['role'] = user.role
            flash('Login successful!', 'success')

            if role == 'donor':
                return redirect(url_for('donor_dashboard'))
            elif role == 'recipient':
                return redirect(url_for('recipient_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # optional
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/test-db')
def test_db():
    try:
        # Use the text() function to wrap the SQL query
        db.session.execute(text("SELECT 1"))
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {str(e)}"

# Run Flask Server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)