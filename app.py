from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
from io import BytesIO
import openpyxl
import random
import os

app = Flask(__name__)

# ======================
# CONFIG
# ======================
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# TWILIO CONFIG (WHATSAPP OTP)
# ======================
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_WHATSAPP_FROM")

def send_whatsapp_otp(phone, otp):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

        client.messages.create(
            from_=TWILIO_FROM,
            body=f"Your OTP is: {otp}",
            to=f"whatsapp:{phone}"
        )

        print("OTP SENT")

    except Exception as e:
        print("WhatsApp OTP Error:", e)

# ======================
# DATABASE MODELS
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default='user')


class MailForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    department = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Pending")
    user_id = db.Column(db.Integer)

# ======================
# INIT DB + ADMIN
# ======================
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# ======================
# ROUTES
# ======================
@app.route('/')
def home():
    return redirect('/login')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 🔥 CHECK EXISTING USER
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash("User already exists")
            return redirect('/register')

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(user)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Database error occurred")
            print(e)

        return redirect('/login')

    return render_template('register.html')
# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect('/admin_dashboard')

            return redirect('/user_dashboard')

        flash("Invalid login")

    return render_template('login.html')

# ---------- DASHBOARDS ----------
@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    forms = MailForm.query.all()
    return render_template('admin_dashboard.html', forms=forms)

# ---------- CREATE FORM ----------
@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':

        f = MailForm(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            department=request.form.get('department'),
            user_id=session.get('user_id')
        )

        db.session.add(f)
        db.session.commit()

        return redirect('/user_dashboard')

    return render_template('form.html')

# ---------- APPROVE ----------
@app.route('/approve/<int:id>')
def approve(id):
    form = MailForm.query.get(id)
    form.status = "Approved"
    db.session.commit()
    return redirect('/admin_dashboard')

# ---------- REJECT ----------
@app.route('/reject/<int:id>')
def reject(id):
    form = MailForm.query.get(id)
    form.status = "Rejected"
    db.session.commit()
    return redirect('/admin_dashboard')

# ---------- EXCEL ----------
@app.route('/excel/<int:id>')
def excel(id):

    form = MailForm.query.get(id)

    wb = openpyxl.Workbook()
    ws = wb.active

    ws.append(["ID", form.id])
    ws.append(["Name", form.first_name + " " + form.last_name])
    ws.append(["Department", form.department])
    ws.append(["Status", form.status])

    file = BytesIO()
    wb.save(file)
    file.seek(0)

    return send_file(file, as_attachment=True, download_name="form.xlsx")

# ======================
# FORGOT PASSWORD (WHATSAPP OTP)
# ======================
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        phone = request.form.get('phone')

        otp = str(random.randint(100000, 999999))

        session['otp'] = otp
        session['phone'] = phone

        send_whatsapp_otp(phone, otp)

        return redirect('/verify_otp')

    return render_template('forgot_password.html')

# ---------- VERIFY OTP ----------
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if request.method == 'POST':

        otp = request.form.get('otp')

        if otp == session.get('otp'):
            return redirect('/reset_password')

        flash("Invalid OTP")

    return render_template('verify_otp.html')

# ---------- RESET PASSWORD ----------
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():

    if request.method == 'POST':

        new_password = request.form.get('password')

        flash("Password Updated")
        return redirect('/login')

    return render_template('reset_password.html')

# ======================
# RUN (RENDER READY)
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))