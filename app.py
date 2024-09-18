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
    
    
@app.route('/')
def home():
    return render_template('index.html')


# ''' RUN APP.PY '''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5500)