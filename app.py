from flask import Flask, render_template
from flask import request, redirect
from flask import session
from flask import make_response

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from flask_mail import Mail, Message

from waitress import serve

import random
import os

# =====================================================
# APP
# =====================================================

app = Flask(__name__)

app.secret_key = "secret_key"

# =====================================================
# DATABASE
# =====================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DB_PATH = os.path.join(BASE_DIR, "mail_system.db")

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + DB_PATH

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =====================================================
# MAIL CONFIG
# =====================================================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# CHANGE THIS
app.config['MAIL_USERNAME'] = 'yourgmail@gmail.com'

# CHANGE THIS
app.config['MAIL_PASSWORD'] = 'your_app_password'

mail = Mail(app)

# =====================================================
# USER TABLE
# =====================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True
    )

    email = db.Column(
        db.String(200),
        unique=True
    )

    password = db.Column(
        db.String(300)
    )

    role = db.Column(
        db.String(20)
    )

# =====================================================
# FORM TABLE
# =====================================================

class MailForm(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    form_date = db.Column(db.String(100))

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

    domain = db.Column(db.String(100))
    preferred_id = db.Column(db.String(200))

    it_name = db.Column(db.String(100))
    it_designation = db.Column(db.String(100))
    it_contact = db.Column(db.String(100))
    it_email = db.Column(db.String(100))

    remarks = db.Column(db.Text)

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    created_by_user = db.Column(
        db.String(100)
    )

# =====================================================
# DATABASE CREATE
# =====================================================

with app.app_context():

    db.create_all()

    admin = User.query.filter_by(
        username="Saheem@123"
    ).first()

    if not admin:

        admin_user = User(

            username="Saheem@123",

            email="admin@system.com",

            password=generate_password_hash(
                "Saheem123"
            ),

            role="admin"
        )

        db.session.add(admin_user)

        db.session.commit()

# =====================================================
# LOGIN
# =====================================================

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form.get('username')

        password = request.form.get('password')

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user'] = username

            session['role'] = user.role

            if user.role == 'admin':

                return redirect('/admin')

            return redirect('/dashboard')

        return "Invalid Username or Password"

    return render_template('login.html')

# =====================================================
# REGISTER
# =====================================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

        check_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if check_user:

            return "User already exists"

        new_user = User(

            username=username,

            email=email,

            password=password,

            role='user'
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# =====================================================
# FORGOT PASSWORD
# =====================================================

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']

        user = User.query.filter_by(email=email).first()

        if not user:
            return "Email not found"

        otp = str(random.randint(100000, 999999))

        session['otp'] = otp
        session['reset_email'] = email

        msg = Message(
            'OTP Verification',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.body = f'Your OTP is: {otp}'

        mail.send(msg)

        return redirect('/verify_otp')

    return render_template('forgot_password.html')

# =====================================================
# VERIFY OTP
# =====================================================

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if request.method == 'POST':

        otp = request.form['otp']

        if otp == session.get('otp'):

            return redirect('/reset_password')

        return "Invalid OTP"

    return render_template('verify_otp.html')

# =====================================================
# RESET PASSWORD
# =====================================================

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():

    if request.method == 'POST':

        password = generate_password_hash(
            request.form['password']
        )

        user = User.query.filter_by(
            email=session.get('reset_email')
        ).first()

        user.password = password

        db.session.commit()

        return redirect('/login')

    return render_template('reset_password.html')

# =====================================================
# USER DASHBOARD
# =====================================================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/login')

    forms = MailForm.query.filter_by(

        created_by_user=session['user']

    ).all()

    return render_template(

        'user_dashboard.html',

        forms=forms
    )

# =====================================================
# CREATE FORM
# =====================================================

@app.route('/create', methods=['GET', 'POST'])
def create():

    if 'user' not in session:

        return redirect('/login')

    if request.method == 'POST':

        form = MailForm(

            company_name=request.form.get('company_name'),
            location=request.form.get('location'),
            form_date=request.form.get('form_date'),

            first_name=request.form.get('first_name'),
            middle_name=request.form.get('middle_name'),
            last_name=request.form.get('last_name'),

            employee_code=request.form.get('employee_code'),
            contact_detail=request.form.get('contact_detail'),
            extn_no=request.form.get('extn_no'),

            mobile=request.form.get('mobile'),
            joining_date=request.form.get('joining_date'),
            department=request.form.get('department'),

            designation=request.form.get('designation'),

            email_type=request.form.get('email_type'),
            mail_service=request.form.get('mail_service'),
            created_by=request.form.get('created_by'),

            domain=request.form.get('domain'),
            preferred_id=request.form.get('preferred_id'),

            it_name=request.form.get('it_name'),
            it_designation=request.form.get('it_designation'),
            it_contact=request.form.get('it_contact'),
            it_email=request.form.get('it_email'),

            remarks=request.form.get('remarks'),

            created_by_user=session['user']
        )

        db.session.add(form)

        db.session.commit()

        return redirect('/dashboard')

    return render_template('form.html')

# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route('/admin')
def admin():

    if session.get('role') != 'admin':

        return redirect('/login')

    forms = MailForm.query.order_by(
        MailForm.id.desc()
    ).all()

    total_forms = MailForm.query.count()

    approved_forms = MailForm.query.filter_by(
        status="Approved"
    ).count()

    pending_forms = MailForm.query.filter_by(
        status="Pending"
    ).count()

    rejected_forms = MailForm.query.filter_by(
        status="Rejected"
    ).count()

    return render_template(

        'admin_dashboard.html',

        forms=forms,

        total_forms=total_forms,

        approved_forms=approved_forms,

        pending_forms=pending_forms,

        rejected_forms=rejected_forms
    )

# =====================================================
# VIEW FORM
# =====================================================

@app.route('/view/<int:id>')
def view(id):

    if session.get('role') != 'admin':

        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    return render_template(
        'view_form.html',
        form=form
    )

# =====================================================
# APPROVE
# =====================================================

@app.route('/approve/<int:id>')
def approve(id):

    if session.get('role') != 'admin':

        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    form.status = "Approved"

    db.session.commit()

    return redirect('/admin')

# =====================================================
# REJECT
# =====================================================

@app.route('/reject/<int:id>')
def reject(id):

    if session.get('role') != 'admin':

        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    form.status = "Rejected"

    db.session.commit()

    return redirect('/admin')

# =====================================================
# DOWNLOAD
# =====================================================

@app.route('/download/<int:id>')
def download(id):

    if session.get('role') != 'admin':

        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    html = render_template(
        'view_form.html',
        form=form
    )

    response = make_response(html)

    response.headers['Content-Type'] = 'text/html'

    response.headers['Content-Disposition'] = (
        f'attachment; filename=form_{id}.html'
    )

    return response

# =====================================================
# EXPORT EXCEL
# =====================================================

@app.route('/export_excel/<int:id>')
def export_excel(id):

    if session.get('role') != 'admin':

        return redirect('/login')

    form = MailForm.query.get_or_404(id)

    html = render_template(
        'view_form.html',
        form=form
    )

    response = make_response(html)

    response.headers['Content-Type'] = (
        'application/vnd.ms-excel'
    )

    response.headers['Content-Disposition'] = (
        f'attachment; filename=form_{id}.xls'
    )

    return response

# =====================================================
# LOGOUT
# =====================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )