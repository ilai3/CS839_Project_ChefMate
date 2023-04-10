import requests
import os
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField

from flask_sqlalchemy import SQLAlchemy
from google.cloud.sql.connector import Connector, IPTypes
import json, datetime

# Python Connector database connection function
def getconn():
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector with Automatic IAM Database Authentication.
    """
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.
    info = {}
    with open('secret.json', "r") as f:
        info = json.loads(f.read())
  
    # initialize Cloud SQL Python Connector object
    instance_connection_name = info["INSTANCE_CONNECTION_NAME"]  # e.g. 'project:region:instance'
    db_iam_user = info["DB_IAM_USER"]  # e.g. 'sa-name@project-id.iam'
    db_name = info["DB_NAME"]  # e.g. 'my-database'
    ip_type = IPTypes.PUBLIC

    with Connector() as connector:
        conn = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_iam_user,
            enable_iam_auth=True,
            db=db_name,
            ip_type= ip_type
        )
        return conn

app = Flask(__name__, template_folder='templates', static_url_path='/static')
app.secret_key = 'randomGeneratedKey'

# The Cloud SQL Python Connector can be used with SQLAlchemy
# using the 'creator' argument to 'create_engine'
# configure Flask-SQLAlchemy to use Python Connector
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "creator": getconn
}

db = SQLAlchemy(app)

# database table schema
class User(db.Model):
    username = db.Column(db.String(16), primary_key=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    create_time = db.Column(db.DateTime)
    """
    def __repr__(self):
        return '<User %r>' % self.username
    """

class Food_list(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, index=True)
    food = db.Column(db.JSON)
    """
    def __repr__(self):
        return '<Category %r>' % self.name
    """

class UploadForm(FlaskForm):
    image = FileField('Image')
    submit = SubmitField('Upload')
    
@app.route('/')
def home():
    form = UploadForm()
    return render_template('index.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the user data from the form
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists in the cloud database
        """
        url = 'http://your-database-api-url'
        data = {
            'email': email,
            'password': password
        }
        response = requests.get(url, params=data)

        # Handle the response
        if response.status_code == 200:
            # Set the user's data in the session
            session['email'] = email
            session['password'] = password
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect('/')
        """
        user = User.query.filter_by(username=username).first()
        if user is None:
            print("There is no data with {}".format(username)) # debug
            flash('No data for this user', 'error')
            return redirect('/')
        elif user.password != password:
            print("Incorrect password!") # debug
            flash('Invalid email or password', 'error')
            return redirect('/')
        else:
            session['username'] = username
            session['password'] = password
            print("Login successful!") # debug
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))

    # If the request method is GET, show the login form
    else:
        return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'email' in session and 'password' in session:
        return render_template('index.html')
    else:
        flash('You need to log in first', 'error')
        return redirect('/')

@app.route('/logout')
def logout():
    # Clear the session and log the user out
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get the user data from the form
        email = request.form['email']
        password = request.form['password']

        # Store the user data in the cloud database
        url = 'http://your-database-api-url'
        data = {
            'email': email,
            'password': password
        }
        response = requests.post(url, json=data)

        # Handle the response
        if response.status_code != 200:
            return render_template('index.html')
        else:
            flash('Register Failed', 'error')
            return redirect('/')
    # If the request method is GET, show the signup form
    else:
        return render_template('index.html')


@app.route('/uploadImg', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if form.validate_on_submit():
        image_file = form.image.data
        filename = image_file.filename
        image_file.save('static/images/' + filename)
        return redirect(url_for('display_image', filename=filename))
    return render_template('index.html', form=form)

@app.route('/display/<filename>')
def display_image(filename):
    latest_image = get_latest_image()
    return render_template('index.html', latest_image=latest_image)

def get_latest_image():
    images_dir = os.path.join(app.static_folder, 'images')
    if not os.path.isdir(images_dir):
        return None
    images = [f for f in os.listdir(images_dir) if f.endswith('.jpg') or f.endswith('.png') or f.endswith('.jpeg')]
    if not images:
        return None
    latest_image = sorted(images, key=lambda f: os.path.getmtime(os.path.join(images_dir, f)), reverse=True)[0]
    return latest_image


# @app.route('/recognition')
# def object_recognition():
#     if first time upload 
#        query to db, but get nothing
#        return home page
#     else 
#     compare the difference between uploaded photo and photo in db
#     update db with latest photo