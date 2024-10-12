from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask_migrate import Migrate

app = Flask(__name__)

app.secret_key = 'servease-123-$%^-mad1-proj*'  

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///servease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    
    
# * --- User Table --- #
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Password = db.Column(db.String(256), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Role = db.Column(db.String(100), nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', uselist=False, backref='user')  # Refers to Customer class
    serviceProf = db.relationship('ServiceProfessional', uselist=False, backref='user')  # Refers to ServiceProfessional class

    def __repr__(self):
        return f"<{self.Name} | {self.Email} | {self.Role}>"
    

# * --- Service Professional Table --- #
class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    description = db.Column(db.String(255), nullable=True)
    service_type = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    reviews = db.relationship('Review', backref='professional', lazy=True)
    service_requests = db.relationship('ServiceRequest', backref='professional', lazy=True)

    def __repr__(self):
        return f"<name='{self.name}', service_type='{self.service_type}', experience={self.experience})>"


# * --- Customer Table --- #
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    address = db.Column(db.String(255), nullable=True)
    pin_code = db.Column(db.String(10), nullable=True)
    is_blocked = db.Column(db.Boolean, default=False)

    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='customer', lazy=True)

    def __repr__(self):
        return f"<name='{self.name}', address='{self.address}', pin_code='{self.pin_code}')>"

# * --- Service Table --- #
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)  # in minutes
    description = db.Column(db.String(255), nullable=True)
    service_requests = db.relationship('ServiceRequest', backref='service', lazy=True)

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}', price={self.price}, time_required={self.time_required})>"

# * --- Service Request Table --- #
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(50), nullable=False, default='requested')  # can be requested, assigned, closed
    remarks = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return (f"<ServiceRequest(id={self.id}, service_id={self.service_id}, customer_id={self.customer_id}, "
                f"professional_id={self.professional_id}, status='{self.service_status}')>")

# * --- Review Table --- #
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Assuming rating out of 5
    comment = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Review(id={self.id}, rating={self.rating}, comment='{self.comment}')>"

# * ------ GENERIC ROUTES -------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    message = request.args.get('message')
    return render_template('login.html',message=message)

@app.route('/signup')
def signup():
    return render_template('signup.html')

# * --------- PROFILE ----------
@app.route('/profile')
def profile():
    userId = session.get('user')
    customer = Customer.query.filter_by(id=userId).first()
    name = customer.name
    joinDate = customer.date_created.strftime("%d-%b-%Y")
    address = customer.address
    pinCode = customer.pin_code
    return render_template('profile.html', address=address, pinCode=pinCode, ab = name[0],customerName=name, joinDate=joinDate)

# * --------- AUTHENTICATION ----------
# ---- LOGOUT ----
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('login',message="Logged out successfully"))

# ------ REGISTERATION ------
@app.route('/registerUser', methods=['POST'])
def registerUser():
     if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        pwd = request.form.get('pwd')
        email = request.form.get('email')
        industry = request.form.get('industry')
        
        existing_user = User.query.filter_by(Email=email).first()
        if existing_user:
            return render_template('signup.html',msg=True)
        
        hashed_password = generate_password_hash(pwd, method='pbkdf2:sha256', salt_length=16)
        new_user = User(Name=name, Password=hashed_password, Email=email, Role=role)
        db.session.add(new_user)
        db.session.commit()
        print("==== NEW USER ADDED ==== ")
        
        if role == 'service' and industry != 'CUSTOMER':
            new_server = ServiceProfessional(name=name,id=new_user.id,service_type=industry,is_approved=False)
            db.session.add(new_server)
            db.session.commit()
            print("=== NEW SERVER ADDED ===")
    
        elif role == 'customer':
            new_cust = Customer(id=new_user.id,name=name)
            db.session.add(new_cust)
            db.session.commit()
            print("=== NEW CUSTOMER ADDED ===")
        
        return redirect(url_for('login',message="Registered successfully"))
        

# ------ LOGIN USER ------
@app.route('/loginUser', methods=['POST'])
def loginUser():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        user = User.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, pwd):
            session['user'] = user.id
            session['role'] = user.Role
            if user.Role == 'customer':
                customer = Customer.query.filter_by(id=user.id).first()
                if customer:
                    if customer.is_blocked:
                        return redirect(url_for('login',message="This User is Blocked"))
                    else:
                        return redirect(url_for('customer_dashboard'))
            elif user.Role == 'service':
                return redirect(url_for('service_dashboard'))
            
        else:
            return redirect(url_for('login',message="Invalid credentials"))


@app.route('/servEase/home')
def customer_dashboard():
    return render_template('customerView.html')

@app.route('/serviceDashboard')
def service_dashboard():
    return render_template('serviceDash.html')

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

# * ------------ CHANGE PASSWORD --------------
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        userId = session.get('user')
        user = User.query.filter_by(id=userId).first()
        if new_password == confirm_password:
            user.Password = new_password
            db.session.commit()
            print("======= PASSWORD CHANGED SUCCESSFULLY ======= ")
            return redirect(url_for('profile'))
        else:
            return "<h1>Passwords do not match</h1>"

# * ------------ EDIT ADDRESS --------------
@app.route('/edit_address', methods=['GET', 'POST'])
def edit_address():
    if request.method == 'POST':
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        userId = session.get('user')
        # print(userId)
        customer = Customer.query.filter_by(id=userId).first()
        customer.address = address
        customer.pin_code = pincode
        db.session.commit()
        print("======= ADDRESS EDITED SUCCESSFULLY =======")
        return redirect(url_for('profile'))


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin')
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()
    custCount = Customer.query.count()
    expCount = ServiceProfessional.query.filter_by(is_approved=True).count()
    return render_template('admin-dash.html',custCount=custCount,expCount=expCount,reqCount=reqCount)

#* -----  ADMIN FUNCTIONALITY  -----

# ------------------------------ MANAGE CUSTOMERS ------------------------------ 
@app.route('/admin/dashboard/customers')
@admin_required
def manage_customers():
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()
    customers = Customer.query.all()
    return render_template('adminCust-dash.html',reqCount=reqCount,customers=customers)

@app.route('/toggle_block_customer/<int:customer_id>', methods=['POST'])
def toggle_block_customer(customer_id):
    # Fetch the customer by ID
    customer = Customer.query.get(customer_id)
    if customer:
        # Toggle the is_blocked status
        if customer.is_blocked:
            customer.is_blocked = False
        else:
            customer.is_blocked = True
        # Commit changes to the database
        db.session.commit()
    return redirect(url_for('manage_customers'))

#! -----  CORE ADMIN FUNCTIONALITY  -----
@app.route('/admin/dashboard/service')
@admin_required
def manage_service():
    servicePro = ServiceProfessional.query.filter_by(is_approved=True).all()
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()
    return render_template('adminserv-dash.html',reqCount=reqCount, service_professionals=servicePro)


@app.route('/block_service_professional/<int:professional_id>', methods=['POST'])
def block_service_professional(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_approved = False
        db.session.commit()
    return redirect(url_for('manage_service'))

# ------------------------------ MANAGE SERVICE PROF. REQUESTS ------------------------------ 
@app.route('/admin/dashboard/reviews')
@admin_required
def manage_reviews():
    unapproved = ServiceProfessional.query.filter_by(is_approved=False).all()
    # print(unapproved)
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()
    # print(reqCount)
    return render_template('adminReq-dash.html',reqCount=reqCount, service_professionals=unapproved)

@app.route('/approve/<int:professional_id>', methods=['POST'])
def approve_service_professional(professional_id):
    # Logic to approve the service professional
    service_professional = ServiceProfessional.query.get(professional_id)
    if service_professional:
        service_professional.is_approved = True
        db.session.commit()
    return redirect(url_for('manage_reviews'))  # Redirect to the relevant page

@app.route('/deny/<int:professional_id>', methods=['POST'])
def deny_service_professional(professional_id):
    # Logic to deny the service professional
    service_professional = ServiceProfessional.query.get(professional_id)
    if service_professional:
        service_professional.is_approved = False
        db.session.commit()
    return redirect(url_for('manage_reviews'))  # Redirect to the relevant page

# ------------------------------------------------------------------


# ''' RUN APP.PY '''
#! Admin Details: email: admin@gmail.com, password: admin123

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5500)