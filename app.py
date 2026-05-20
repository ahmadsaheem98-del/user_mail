from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from io import BytesIO
import openpyxl
import random

app = Flask(__name__)

# =====================
# CONFIG
# =====================
app.secret_key = "saheem_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =====================
# MAIL CONFIG (OTP)
# =====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yourgmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

mail = Mail(app)

# =====================
# MODELS
# =====================
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
    status = db.Column(db.String(50), default='Pending')

    user_id = db.Column(db.Integer)

# =====================
# INIT DB + ADMIN
# =====================
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@gmail.com").first()

    if not admin:
        admin_user = User(
            username="admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()

# =====================
# HOME
# =====================
@app.route('/')
def home():
    return redirect('/login')

# =====================
# LOGIN
# =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form.get('username', '')
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and password and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['role'] = user.role

            return redirect('/admin_dashboard' if user.role == 'admin' else '/user_dashboard')

        flash("Invalid login")

    return render_template('login.html')

# =====================
# REGISTER
# =====================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("All fields required")
            return redirect('/register')

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# =====================
# USER DASHBOARD
# =====================
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    forms = MailForm.query.filter_by(user_id=session['user_id']).all()
    return render_template('user_dashboard.html', forms=forms)

# =====================
# ADMIN DASHBOARD (FIXED COUNTS)
# =====================
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    forms = MailForm.query.all()

    total_forms = len(forms)
    approved_forms = len([f for f in forms if f.status == "Approved"])
    rejected_forms = len([f for f in forms if f.status == "Rejected"])
    pending_forms = len([f for f in forms if f.status == "Pending"])

    return render_template(
        'admin_dashboard.html',
        forms=forms,
        total_forms=total_forms,
        approved_forms=approved_forms,
        rejected_forms=rejected_forms,
        pending_forms=pending_forms
    )

# =====================
# CREATE FORM (FIXED ROUTE)
# =====================
@app.route('/form', methods=['GET', 'POST'])
def form():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        new_form = MailForm(
            first_name=request.form.get('first_name', ''),
            last_name=request.form.get('last_name', ''),
            department=request.form.get('department', ''),
            user_id=session['user_id']
        )

        db.session.add(new_form)
        db.session.commit()

        flash("Form submitted successfully")
        return redirect('/user_dashboard')

    return render_template('form.html')

# =====================
# VIEW FORM
# =====================
@app.route('/view_form/<int:id>')
def view_form(id):
    if 'user_id' not in session:
        return redirect('/login')

    form = MailForm.query.get_or_404(id)
    return render_template('view_form.html', form=form)

# =====================
# APPROVE
# =====================
@app.route('/approve/<int:id>')
def approve(id):
    if session.get('role') != 'admin':
        return redirect('/login')

    form = MailForm.query.get_or_404(id)
    form.status = "Approved"

    db.session.commit()
    flash("Approved")
    return redirect('/admin_dashboard')

# =====================
# REJECT
# =====================
@app.route('/reject/<int:id>')
def reject(id):
    if session.get('role') != 'admin':
        return redirect('/login')

    form = MailForm.query.get_or_404(id)
    form.status = "Rejected"

    db.session.commit()
    flash("Rejected")
    return redirect('/admin_dashboard')

# =====================
# EXCEL EXPORT (FIXED)
# =====================
@app.route('/excel/<int:id>')
def excel(id):
    form = MailForm.query.get_or_404(id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Form Data"

    data = [
        ["First Name", form.first_name],
        ["Last Name", form.last_name],
        ["Department", form.department],
        ["Status", form.status]
    ]

    for row in data:
        ws.append(row)

    file = BytesIO()
    wb.save(file)
    file.seek(0)

    return send_file(file, as_attachment=True, download_name="form.xlsx")

# =====================
# FORGOT PASSWORD OTP
# =====================
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':

        email = request.form.get('email', '')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not found")
            return redirect('/forgot_password')

        otp = str(random.randint(100000, 999999))

        session['otp'] = otp
        session['email'] = email

        msg = Message(
            "OTP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Your OTP is {otp}"
        mail.send(msg)

        return redirect('/verify_otp')

    return render_template('forgot_password.html')

# =====================
# VERIFY OTP
# =====================
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':

        otp = request.form.get('otp', '')

        if otp == session.get('otp'):
            return redirect('/reset_password')

        flash("Invalid OTP")

    return render_template('verify_otp.html')

# =====================
# RESET PASSWORD
# =====================
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':

        password = request.form.get('password', '')

        user = User.query.filter_by(email=session.get('email')).first()

        if user:
            user.password = generate_password_hash(password)
            db.session.commit()

        session.clear()
        return redirect('/login')

    return render_template('reset_password.html')

# =====================
# LOGOUT
# =====================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)