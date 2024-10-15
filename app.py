from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask_migrate import Migrate

#  CLOUD IMAGE STORAGE
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# .ENV
from dotenv import load_dotenv
import os



app = Flask(__name__)

app.secret_key = 'servease-123-$%^-mad1-proj*'  

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///servease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

load_dotenv()
cloud_api_secret = os.getenv('CLOUD_API_SECRET')
cloud_api_key = os.getenv('CLOUD_API_KEY')
cloud_name = os.getenv('CLOUD_NAME')

cloudinary.config( 
    cloud_name = f"{cloud_name}", 
    api_key = f"{cloud_api_key}", 
    api_secret = f"{cloud_api_secret}", 
    secure=True
)


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
    image_url = db.Column(db.String(255), nullable=True)
    
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
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Service( name='{self.name}', price={self.price})>"

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
    return render_template('profile.html', address=address, pinCode=pinCode, ab = name[0],customerName=name, joinDate=joinDate,image_url=session.get('image_url'))


@app.route('/bookings')
def bookings():
    current_customer_id = session['user']  # Assuming session['user'] contains the user ID
    
    # Query the database for all service requests made by the current customer
    service_requests = ServiceRequest.query.filter_by(
        customer_id=current_customer_id
    ).all()
    return render_template('bookings.html', service_requests=service_requests,image_url=session.get('image_url'))

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
            if user.Role == 'customer':
                customer = Customer.query.filter_by(id=user.id).first()
                if customer:
                    if customer.is_blocked:
                        return redirect(url_for('login',message="This User is Blocked"))
                    else:
                        session['user'] = user.id
                        session['role'] = user.Role
                        if user.image_url:
                            session['image_url'] = user.image_url

                        return redirect(url_for('customer_dashboard',image_url=session.get('image_url')))
            elif user.Role == 'service':
                session['user'] = user.id
                session['role'] = user.Role
                if user.image_url:
                    session['image_url'] = user.image_url

                return redirect(url_for('service_dashboard',image_url=session.get('image_url')))
            
        else:
            return redirect(url_for('login',message="Invalid credentials"))


@app.route('/servEase/home',methods=['GET','POST'])
def customer_dashboard():
    services = Service.query.all()
    image_url = session.get('image_url')
    # print(request.method)
    if request.method == 'GET':
        # Get the search query from the form
        search_query = request.args.get('search', '').strip()
        # print(search_query)
        # print(type(search_query))
        # Query the database for services that match the search term
        services = Service.query.filter(Service.name.ilike(f'%{search_query}%')).all()
        # print(services)
    else:
        # If it's a GET request, fetch all services
        services = Service.query.all()
    return render_template('customerView.html',services=services,image_url=image_url)


@app.route('/servEase/home/seeall')
def customer_allView():
    services = Service.query.all()
    image_url = session.get('image_url')
    # print(request.method)
    if request.method == 'GET':
        # Get the search query from the form
        search_query = request.args.get('search', '').strip()
        
        # print(search_query)
        # print(type(search_query))
        
        # Query the database for services that match the search term
        services = Service.query.filter(Service.name.ilike(f'%{search_query}%')).all()
        print(services)
    else:
        # If it's a GET request, fetch all services
        services = Service.query.all()

    return render_template('customerViewall.html',services=services,image_url=session.get('image_url'))


# ! ------- CORE SERVICE EXPERT FUNCTIONALITY -----

@app.route('/serviceDashboard')
def service_dashboard():
    # TODO: ADD A GRAPH -------
    service_requests = ServiceRequest.query.filter(
    ServiceRequest.professional_id == current_user,
    ServiceRequest.service_status.in_(['requested', 'assigned'])
    ).all()
    num_requests = len(service_requests)
    return render_template('serviceDash.html',reqCount=num_requests)


@app.route('/serviceDashboard/editProfile')
def edit_service_prof():
    return render_template('editProf.html')


@app.route('/editProf',methods=['POST'])
def edit_service_prof_post():
    message = "PROFILE UPDATED"
    name = request.form.get('name')
    exp = request.form.get('exp')
    desc = request.form.get('desc')
    userID = session.get('user')

    servicePro = ServiceProfessional.query.filter_by(id=userID).first()

    if name:
        servicePro.name = name
    if exp:
        servicePro.experience = exp
    if desc:
        servicePro.description = desc

    db.session.commit()
    return render_template('editProf.html',message=message)


@app.route('/serviceDashboard/reviews')
def service_reviews():
    pass
    # current_user = session['user']
    # print(current_user)
    # service_professional = ServiceProfessional.query.filter_by(user_id=current_user).first()
    # print(service_professional)
    #     # Fetch the service requests assigned to this professional
    # service_requests = ServiceRequest.query.filter_bky(professional_id=service_professional.id, service_status='requested').all()
    # print(service_requests)
    # return render_template('serviceRequests.html', service_requests=service_requests)


@app.route('/accept_service_request/<int:request_id>', methods=['POST'])
def accept_service_request(request_id):
    # Fetch the service request
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Update the service status to 'assigned'
    service_request.service_status = 'assigned'
    db.session.commit()
    
    # Redirect back to the service requests page
    return redirect(url_for('service_requests'))


@app.route('/ignore_service_request/<int:request_id>', methods=['POST'])
def ignore_service_request(request_id):
    # Fetch the service request
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Optionally, you could update the status to 'ignored' or perform other actions
    service_request.service_status = 'ignored'
    db.session.commit()
    
    # Redirect back to the service requests page
    return redirect(url_for('service_requests'))



@app.route('/complete_service_request/<int:request_id>', methods=['POST'])
def complete_service_request(request_id):
    # Fetch the service request
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Update the service status to 'closed' and set the date of completion
    service_request.service_status = 'closed'
    service_request.date_of_completion = datetime.now()
    db.session.commit()
    
    # Redirect back to the service requests page
    return redirect(url_for('service_requests'))


@app.route('/serviceDashboard/requests')
def service_requests():
    current_user = session['user']
    print(current_user)
    service_professional = ServiceProfessional.query.filter_by(id=current_user).first()
    print(service_professional)
    #     # Fetch the service requests assigned to this professional
    service_requests = ServiceRequest.query.filter(
    ServiceRequest.professional_id == current_user,
    ServiceRequest.service_status.in_(['requested', 'assigned'])
    ).all()
    num_requests = len(service_requests)

    service_requests2 = ServiceRequest.query.filter_by(
        professional_id=current_user, 
        service_status='closed'
    ).all()

    compReq = len(service_requests2)
    # print(service_requests)
    # return render_template('serviceRequests.html')
    return render_template('serviceRequests.html', service_requests=service_requests,reqCount=num_requests,compReq=compReq)


@app.route('/serviceDashboard/completed')
def service_completed():
    # Get the current logged-in user ID
    current_user_id = session['user']  # Assuming session['user'] contains the user ID
    
    # Query the database for closed service requests for the current professional
    service_requests = ServiceRequest.query.filter_by(
        professional_id=current_user_id, 
        service_status='closed'
    ).all()

    compReq = len(service_requests)

    service_requests2 = ServiceRequest.query.filter(
    ServiceRequest.professional_id == current_user_id,
    ServiceRequest.service_status.in_(['requested', 'assigned'])
    ).all()
    num_requests = len(service_requests2)
    
    # Render the template and pass the retrieved service requests
    return render_template('serviceCompleted.html', service_requests=service_requests, compReq=compReq, reqCount=num_requests)


# ------ WRAPPER FUNCTIONS ------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or session['admin'] != True:
            return redirect(url_for('login', message='Must be logged in as an admin'))
        return f(*args, **kwargs)
    return decorated_function


def service_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'service':
            return redirect(url_for('login', message='Must be logged in as an service prof'))
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'customer':
            return redirect(url_for('login', message='Must be logged in as an customer'))
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



# ! -------------- CORE CUSTOMER FUNCTIONALITY --------------

@app.route('/servEase/bookService/<int:service_id>/<int:price>/<string:desc>', methods=['GET', 'POST'])
def bookService(service_id, price, desc):
    # Get the service by ID
    message = request.args.get('message')
    service = Service.query.get(service_id)
    service_name = service.name if service else None

    # Format service name to match the format stored in 'service_type'
    service_pro_name = service_name.lower().replace(' ', '_') if len(service_name.split()) > 1 else service_name.lower()
    
    # Query all service professionals who offer this service type
    service_pros = ServiceProfessional.query.filter_by(service_type=service_pro_name).all()
    # Get the reviews for each service professional
    professionals_with_reviews = []
    for pro in service_pros:
        reviews = Review.query.filter_by(professional_id=pro.id).all()
        # Add the professional and their reviews to the list
        professionals_with_reviews.append({
            'professional': pro,
            'reviews': reviews
        })

    # If a service is found, get the image URL
    image_url = service.image_url if service else None
    
    # Pass the list of service professionals with their reviews, service name, image URL, price, and description to the template
    return render_template(
        'book.html',
        service_name=service_name,
        price=price,
        desc=desc,
        professionals_with_reviews=professionals_with_reviews,
        service_image_url=image_url,
        image_url=session.get('image_url'),
        service_id=service_id,
        message=message
    )


@app.route('/book_service/<int:service_id>/<int:professional_id>/<int:price>/<string:desc>',methods=['POST'])
def book_service(service_id, professional_id, price, desc):
    date = request.form.get('date')
    customer_id = session.get('user')
    service_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=professional_id,
        date_of_request=date
    )
    db.session.add(service_request)
    db.session.commit()
    return redirect(url_for('bookService',message=True,price=price,desc=desc,service_id=service_id))




# ------------ CHANGE PASSWORD --------------
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


# ------------ EDIT ADDRESS --------------
@app.route('/edit_address', methods=['GET', 'POST'])
def edit_address():
    if request.method == 'POST':
        image = request.files['image']
        image_urlFinal = None
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        userId = session.get('user')
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')
            if image_url:
                image_urlFinal = image_url
                session['image_url'] = image_urlFinal
                user = User.query.filter_by(id=userId).first()
                user.image_url = image_urlFinal

        
        # print(userId)
        customer = Customer.query.filter_by(id=userId).first()
        if address:
            customer.address = address
        if pincode:
            customer.pin_code = pincode
        
        db.session.commit()
        print("======= PROFILE UPDATED SUCCESSFULLY =======")
        print(image_urlFinal)
        return redirect(url_for('profile',image_url=image_urlFinal))


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


#! -----  CORE ADMIN FUNCTIONALITY  -----

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


# ------------------------------------------------------------ 


# ------------------------------ MANAGE SERVICE PROF. ------------------------------

@app.route('/block_service_professional/<int:professional_id>', methods=['POST'])
def block_service_professional(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_approved = False
        db.session.commit()
    return redirect(url_for('manage_service'))

# SEARCH AND DISPLAY PROFESSIONALS
@app.route('/admin/dashboard/serviceExpert', methods=['GET'])
@admin_required
def manage_service():
    query = request.args.get('query', '').strip()

    # Filter based on the search query if provided, otherwise fetch all approved professionals
    if query:
        servicePro = ServiceProfessional.query.filter(
            (ServiceProfessional.name.ilike(f'%{query}%')) | 
            (ServiceProfessional.service_type.ilike(f'%{query}%'))
        ).filter(ServiceProfessional.is_approved == True).all()
    else:
        servicePro = ServiceProfessional.query.filter_by(is_approved=True).all()
    
    # Get the count of service professionals with pending approval requests
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()

    # Render the template with the filtered list of professionals and request count
    return render_template('adminserv-dash.html', reqCount=reqCount, service_professionals=servicePro)

# ------------------------------------------------------------ 


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


# ------------------------------ MANAGE SERVICES ------------------------------ 
@app.route('/admin/dashboard/services')
@admin_required
def manage_services():
    services = Service.query.all()
    reqCount = ServiceProfessional.query.filter_by(is_approved=False).count()
    return render_template('admservices.html',reqCount=reqCount, services=services)


@app.route('/update_service', methods=['POST'])
def update_service():
    service_id = request.form.get('service_id')
    service = Service.query.get(service_id)
    if service:
        service.name = request.form.get('name')
        service.price = request.form.get('price')
        service.time_required = request.form.get('time_required')
        service.description = request.form.get('description')
        image = request.files['image']
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')
            service.image_url = image_url
        db.session.commit()
    return redirect(url_for('manage_services'))


@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    # Find the service by ID
    service = Service.query.get(service_id)
    
    if service:
        db.session.delete(service)
        db.session.commit()
        print('Service deleted successfully!')
    else:
        print('Service not found.', 'error')
    return redirect(url_for('manage_services'))  


@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        # Get data from the form
        name = request.form.get('name')
        price = request.form.get('price')
        time_required = request.form.get('timereq')
        description = request.form.get('description')
        image = request.files['image']
        imgUrl = None
        if image:
            upload_result = cloudinary.uploader.upload(image)
            imgUrl = upload_result.get('secure_url')
        # Create a new service instance
        new_service = Service(name=name, price=float(price), time_required=int(time_required), description=description, image_url=imgUrl)

        # Add to the database
        db.session.add(new_service)
        db.session.commit()

        print('Service added successfully')
        return redirect(url_for('manage_services'))  # Replace with your actual dashboard view
    
    # Render the add service form (for GET requests)
    return render_template('admnservices.html')  # Create a template for adding a service

# ------------------------------------------------------------ 



# ''' RUN APP.PY '''
#! Admin Details: email: admin@gmail.com, password: admin123



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5500)