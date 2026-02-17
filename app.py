from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from models import db, User, Booking
import requests
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.exc import IntegrityError

# -------------------------------------------------
# GMAIL CONFIGURATION
# -------------------------------------------------
GMAIL_USER = "shaniyamugi19@gmail.com"
GMAIL_PASS = "hbxjpaajgcnlhiiq"
LPG_COMPANY_EMAIL = "shaniyamugi19@gmail.com"

# -------------------------------------------------
# Flask App Configuration
# -------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------------------------------------
# PHP API ENDPOINTS
# -------------------------------------------------
PHP_GAS_API = "http://esskay-012024.live/gasleve/get_gas_data.php"
PHP_GAS_HISTORY_API = "http://esskay-012024.live/gasleve/get_gas_history.php"

# -------------------------------------------------
# INIT DB & LOGIN MANAGER
# -------------------------------------------------
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------
# CREATE DB TABLES + DEFAULT ADMIN
# -------------------------------------------------
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@gmail.com",
            is_admin=True
        )
        admin.set_password("admin@123")
        db.session.add(admin)
        db.session.commit()

# -------------------------------------------------
# VALIDATION FUNCTIONS
# -------------------------------------------------

def is_valid_email(email):
    """
    Validates email.
    1. Professional emails must end with .ac.in or .co.in exactly
    2. Normal emails like gmail.com, yahoo.com, outlook.com are allowed
    """
    # professional_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(ac|co)\.in$'
    # normal_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    college_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(ac|co)\.in$'

    # Allowed public email providers (STRICT)
    public_pattern = r'^[A-Za-z0-9._%+-]+@(gmail|yahoo|outlook)\.com$'

    if re.match(college_pattern, email):
        return True
    elif re.match(public_pattern, email):
        return True
    else:
        return False

def is_valid_password(password):
    """
    Minimum 8 characters
    At least 1 special character
    """
    if len(password) < 8:
        return False
    special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
    special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
    return re.search(special_char_pattern, password)

def format_datetime(date_str):
    """
    Converts 'YYYY-MM-DD HH:MM:SS' to 'DD-MM-YYYY hh:mm AM/PM'
    """
    if not date_str:
        return "N/A"
    try:
        # Parse the string (assuming standard SQL format)
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        # Format to 12-hour format
        return dt.strftime('%d-%m-%Y %I:%M %p')
    except ValueError:
        return date_str  # Return original if parsing fails

# -------------------------------------------------
# EMAIL FUNCTIONS
# -------------------------------------------------

def send_lpg_booking_email(user, booking_date, cylinder_type):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = user.email
        msg["Cc"] = LPG_COMPANY_EMAIL
        msg["Subject"] = "New LPG Booking Request"

        body = f"""
New LPG Booking Request

Customer Name : {user.username}
Email         : {user.email}
Booking Date  : {booking_date}
Cylinder Type : {cylinder_type}
"""
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email Error:", e)


def send_registration_email(user):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = user.email
        msg["Cc"] = LPG_COMPANY_EMAIL
        msg["Subject"] = "Welcome to Esskay Gas Service"

        body = f"""
New User Registration

Username : {user.username}
Email    : {user.email}
Time     : {user.created_at}

Welcome to our service!
"""
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Registration Email Error:", e)

# -------------------------------------------------
# ROUTES
# -------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for your message!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password=request.form['confirm_password']

        # EMAIL VALIDATION
        if not is_valid_email(email):
            flash("Enter a valid email address. Example: abc@gmail.com or 22it043@drngpit.ac.in", "danger")
            return render_template('register.html', username=username, email=email)

        # PASSWORD VALIDATION
        if not is_valid_password(password):
            flash("Password must be at least 8 characters and contain at least one special character.", "danger")
            return render_template('register.html',username=username,email=email)
        # CONFIRM PASSWORD CHECK
        if password != confirm_password:
            flash("Password and Confirm Password must match", "danger")
            return render_template('register.html', username=username, email=email)


        # CHECK IF USERNAME OR EMAIL EXISTS
        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'danger')
            return render_template('register.html', username=username, email=email)

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already registered (concurrent)', 'danger')
            return render_template('register.html', username=username, email=email)

        send_registration_email(user)

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- USER LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        # EMAIL VALIDATION
        if not is_valid_email(email):
            flash("Enter a valid email address. Example: abc@gmail.com or 22it043@drngpit.ac.in", "danger")
            return render_template('login.html')

        user = User.query.filter_by(email=email, is_admin=False).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid email or password', 'danger')

    return render_template('login.html')


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        admin = User.query.filter_by(email=email, is_admin=True).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials', 'danger')

    return render_template('admin_login.html')


# ---------------- USER DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    try:
        res = requests.get(PHP_GAS_API, timeout=5)
        current_gas = res.json().get("data")

        if current_gas:
            current_gas["level"] = int(current_gas["level"])
            current_gas["leakage"] = int(current_gas["leakage"]) == 1
            # Override with current system time as requested
            current_gas["timestamp"] = datetime.now().strftime('%d-%m-%Y %I:%M %p')

        res2 = requests.get(PHP_GAS_HISTORY_API, timeout=5)
        gas_readings = res2.json()

        for i, r in enumerate(gas_readings):
            r["level"] = int(r["level"])
            r["leakage"] = int(r["leakage"]) == 1
            # Simulate recent history: each reading 30 mins apart
            recent_time = datetime.now() - timedelta(minutes=i*30)
            r["timestamp"] = recent_time.strftime('%d-%m-%Y %I:%M %p')

    except Exception as e:
        print("Gas API error:", e)
        current_gas = None
        gas_readings = []

    return render_template("dashboard.html",
                           current_gas=current_gas,
                           gas_readings=gas_readings)


# ---------------- BOOK LPG ----------------
@app.route('/book-lpg', methods=['POST'])
@login_required
def book_lpg():
    booking = Booking(
        user_id=current_user.id,
        booking_date=request.form['booking_date'],
        cylinder_type=request.form['cylinder_type']
    )
    db.session.add(booking)
    db.session.commit()

    send_lpg_booking_email(current_user,
                           booking.booking_date,
                           booking.cylinder_type)

    flash("LPG booking successful! Email sent to company.", "success")
    return redirect(url_for('dashboard'))


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("admin_dashboard.html", bookings=bookings)


# ---------------- UPDATE BOOKING STATUS (ADMIN) ----------------
@app.route('/admin/update-booking/<int:booking_id>', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    status = request.form.get('status')

    if status in ['Pending', 'Confirmed', 'Delivered']:
        booking.status = status
        db.session.commit()
        flash(f"Booking #{booking_id} status updated to {status}", "success")
    else:
        flash("Invalid status value", "danger")

    return redirect(url_for('admin_dashboard'))


# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)