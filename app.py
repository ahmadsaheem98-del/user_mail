from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from io import BytesIO
from datetime import datetime
import openpyxl
import random

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================
app.secret_key = "saheem_secret_key"

# =========================
# DATABASE
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# EMAIL CONFIG
# =========================
# =========================
# EMAIL CONFIG
# =========================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# YOUR GMAIL
app.config['MAIL_USERNAME'] = 'ahmadsaheem98@gmail.com'

# GOOGLE APP PASSWORD
app.config['MAIL_PASSWORD'] = 'ocxqecmxunhkgafm'

mail = Mail(app)

# =========================
# USER TABLE
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)

    password = db.Column(db.String(200))

    role = db.Column(db.String(20), default='user')

# =========================
# FORM TABLE
# =========================
class MailForm(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    form_date = db.Column(db.String(50))

    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    employee_code = db.Column(db.String(100))
    contact_detail = db.Column(db.String(100))
    extn_no = db.Column(db.String(100))

    mobile = db.Column(db.String(100))
    joining_date = db.Column(db.String(100))
    department = db.Column(db.String(100))

    designation = db.Column(db.String(100))

    email_type = db.Column(db.String(100))
    mail_service = db.Column(db.String(100))
    created_by = db.Column(db.String(100))

    domain_name = db.Column(db.String(100))
    preferred_id = db.Column(db.String(200))

    it_name = db.Column(db.String(100))
    it_designation = db.Column(db.String(100))

    it_contact = db.Column(db.String(100))
    it_email = db.Column(db.String(100))

    remarks = db.Column(db.Text)

    status = db.Column(db.String(50), default='Pending')

    user_id = db.Column(db.Integer)

# =========================
# CREATE DATABASE
# =========================
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(username="Saheem@123").first()

    if not admin:
        admin_user = User(
            username="Saheem@123",
            email="admin@gmail.com",
            password=generate_password_hash("Saheem123"),
            role="admin"
        )

        db.session.add(admin_user)
        db.session.commit()

# =========================
# SEND EMAIL
# =========================
def send_email(to, subject, body):

    try:

        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[to]
        )

        msg.body = body

        mail.send(msg)

    except:
        print("Email not sent")

# =========================
# HOME
# =========================
@app.route('/')
def home():
    return redirect('/login')

# =========================
# REGISTER
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing:
            flash("User already exists")
            return redirect('/register')

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(new_user)
        db.session.commit()

        send_email(
            email,
            "Registration Success",
            "Your account has been created successfully."
        )

        flash("Registration Successful")

        return redirect('/login')

    return render_template('register.html')

# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username

            if user.role == 'admin':
                return redirect('/admin_dashboard')

            return redirect('/user_dashboard')

        else:
            flash("Invalid Login")

    return render_template('login.html')

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# =========================
# USER DASHBOARD
# =========================
@app.route('/user_dashboard')
def user_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    forms = MailForm.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'user_dashboard.html',
        forms=forms
    )

# =========================
# ADMIN DASHBOARD
# =========================
@app.route('/admin_dashboard')
def admin_dashboard():

    if 'role' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return redirect('/login')

    forms = MailForm.query.all()

    return render_template(
        'admin_dashboard.html',
        forms=forms
    )

# =========================
# CREATE FORM
# =========================
@app.route('/form', methods=['GET', 'POST'])
def form():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        new_form = MailForm(

            company_name=request.form['company_name'],
            location=request.form['location'],
            form_date=request.form['form_date'],

            first_name=request.form['first_name'],
            middle_name=request.form['middle_name'],
            last_name=request.form['last_name'],

            employee_code=request.form['employee_code'],
            contact_detail=request.form['contact_detail'],
            extn_no=request.form['extn_no'],

            mobile=request.form['mobile'],
            joining_date=request.form['joining_date'],
            department=request.form['department'],

            designation=request.form['designation'],

            email_type=request.form['email_type'],
            mail_service=request.form['mail_service'],
            created_by=request.form['created_by'],

            domain_name=request.form['domain_name'],
            preferred_id=request.form['preferred_id'],

            it_name=request.form['it_name'],
            it_designation=request.form['it_designation'],

            it_contact=request.form['it_contact'],
            it_email=request.form['it_email'],

            remarks=request.form['remarks'],

            user_id=session['user_id']
        )

        db.session.add(new_form)
        db.session.commit()

        flash("Form Submitted Successfully")

        return redirect('/user_dashboard')

    return render_template('form.html')

# =========================
# VIEW FORM
# =========================
@app.route('/view_form/<int:id>')
def view_form(id):

    if 'user_id' not in session:
        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    return render_template(
        'view_form.html',
        form=form
    )

# =========================
# APPROVE FORM
# =========================
@app.route('/approve/<int:id>')
def approve(id):

    if session.get('role') != 'admin':
        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    form.status = "Approved"

    db.session.commit()

    flash("Form Approved")

    return redirect('/admin_dashboard')

# =========================
# REJECT FORM
# =========================
@app.route('/reject/<int:id>')
def reject(id):

    if session.get('role') != 'admin':
        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    form.status = "Rejected"

    db.session.commit()

    flash("Form Rejected")

    return redirect('/admin_dashboard')

# =========================
# EXCEL EXPORT
# =========================
@app.route('/excel/<int:id>')
def excel(id):

    form = MailForm.query.get_or_404(id)

    wb = openpyxl.Workbook()

    ws = wb.active

    ws.title = "Mail Form"

    data = [

        ["Company Name", form.company_name],
        ["Location", form.location],
        ["Form Date", form.form_date],

        ["First Name", form.first_name],
        ["Middle Name", form.middle_name],
        ["Last Name", form.last_name],

        ["Employee Code", form.employee_code],
        ["Contact Detail", form.contact_detail],

        ["Mobile", form.mobile],
        ["Department", form.department],

        ["Designation", form.designation],

        ["Preferred ID", form.preferred_id],

        ["Status", form.status]

    ]

    for row in data:
        ws.append(row)

    file = BytesIO()

    wb.save(file)

    file.seek(0)

    return send_file(
        file,
        download_name='mail_form.xlsx',
        as_attachment=True
    )

# =========================
# RUN APP
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )