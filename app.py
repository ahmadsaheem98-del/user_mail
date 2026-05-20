from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import openpyxl
import random
import os

app = Flask(__name__)

# =========================
# CONFIG (RENDER SAFE)
# =========================
app.secret_key = os.environ.get("SECRET_KEY", "saheem_secret_key")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODELS
# =========================
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

# =========================
# INIT DB (SAFE ADMIN)
# =========================
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(username="admin").first()

    if not admin:
        try:
            admin_user = User(
                username="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
        except:
            db.session.rollback()

# =========================
# HOME
# =========================
@app.route('/')
def home():
    return redirect('/login')

# =========================
# REGISTER (NO DUPLICATE ERROR)
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash("All fields required")
            return redirect('/register')

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            flash("User already exists")
            return redirect('/register')

        try:
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role='user'
            )

            db.session.add(user)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print("DB ERROR:", e)

        return redirect('/login')

    return render_template('register.html')

# =========================
# LOGIN
# =========================
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

# =========================
# DASHBOARD
# =========================
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    forms = MailForm.query.filter_by(user_id=session['user_id']).all()
    return render_template('user_dashboard.html', forms=forms)


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    forms = MailForm.query.all()
    return render_template('admin_dashboard.html', forms=forms)

# =========================
# CREATE FORM
# =========================
@app.route('/form', methods=['GET', 'POST'])
def form():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        new_form = MailForm(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            department=request.form.get('department'),
            user_id=session['user_id']
        )

        db.session.add(new_form)
        db.session.commit()

        return redirect('/user_dashboard')

    return render_template('form.html')

# =========================
# APPROVE / REJECT
# =========================
@app.route('/approve/<int:id>')
def approve(id):
    form = MailForm.query.get(id)
    if form:
        form.status = "Approved"
        db.session.commit()
    return redirect('/admin_dashboard')


@app.route('/reject/<int:id>')
def reject(id):
    form = MailForm.query.get(id)
    if form:
        form.status = "Rejected"
        db.session.commit()
    return redirect('/admin_dashboard')

# =========================
# EXCEL DOWNLOAD
# =========================
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

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

# =========================
# RUN (RENDER READY)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)