from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)

app.secret_key = 'servease-123-$%^-mad1-proj*'  

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///servease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ! ---------------- MODELS ---------------- #

# * --- Admin Table --- #
class Admin(db.Model):
    __tablename__ = 'admin'
    
    AdminID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(50), nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<{self.Username} | {self.Password} | {self.Email}>"
    

# * ------ GENERIC ROUTES -------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    pass
# ------ WRAPPER FUNCTIONS ------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or session['admin'] != True:
            return redirect(url_for('login', message='Must be logged in as an admin'))
        return f(*args, **kwargs)
    return decorated_function


# * ------------ ADMIN ROUTES ------------ #

@app.route('/admin')
def admin_login_page():
    return render_template('admin-login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # print(email,password)
        admin = Admin.query.filter_by(Email=email).first()
        if admin and password == admin.Password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "<h1>Invalid uname or pwd</h1>"


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin-dash.html')

# ''' RUN APP.PY '''
# Admin Details: name: admin, passwowrd: admin123
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5500)