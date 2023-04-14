import requests
import os
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file, jsonify
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from google.cloud.sql.connector import Connector, IPTypes
import json, datetime
import logging

# Set up a specific logger with our desired output level
# set to critical mode to disable debug log (level=logging.CRITICAL)
# set to info mode to turn on debug log (level=logging.INFO)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s - %(message)s', datefmt='%y-%b-%d %H:%M:%S')

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

# email setting
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'chefmate839@gmail.com'
app.config['MAIL_PASSWORD'] = 'Cs839chefmate'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

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
    username = db.Column(db.String(16), db.ForeignKey("user.username"), primary_key=True,  nullable=False)
    id = db.Column(db.Integer, primary_key=True, nullable=False, index=True, autoincrement=True)
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
    return render_template('index.html', form = UploadForm())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the user data from the form
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists in the cloud database
        user = User.query.filter_by(username=username).first()
        if user is None:
            logging.info("There is no data with {}".format(username)) # debug
            flash('No data for this user', 'error')
            return redirect('/')
        elif user.password != password:
            logging.info("Incorrect password!") # debug
            flash('Invalid email or password', 'error')
            return redirect('/')
        else:
            session['username'] = username
            session['password'] = password
            logging.info("Login successful!") # debug
            flash('Welcome '+username, 'success')
            return redirect(url_for('dashboard'))

    # If the request method is GET, show the login form
    else:
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'username' in session and 'password' in session:
        return render_template('index.html', form = UploadForm())
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is not None:
            logging.info("User({}) exitst! Please try another username".format(username)) # debug
            flash('User exitst! Please try another username', 'error')
            return redirect('/')
        
        new_user = User(username=username, email=email, password=password, create_time=datetime.datetime.now())
        # Store the user data in the cloud database
        db.session.add(new_user)
        db.session.commit()

        # Handle the response
        user = User.query.filter_by(username=username).first()
        if user is None:
            logging.info('Register Failed')
            flash('Register Failed', 'error')
            return redirect(url_for('signup'))
        else:
            logging.info('Register Success')
            flash('Register Success', 'success')
            return redirect('/')

    # If the request method is GET, show the signup form
    else:
        return redirect('/')


@app.route('/uploadImg', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if 'username' in session:
        if form.validate_on_submit():
            image_file = form.image.data
            filename = image_file.filename
            image_file.save('static/images/' + filename)
            return redirect(url_for('display_image', filename=filename))
    else:
        flash('Please login', 'error')
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


@app.route('/recognition')
def object_recognition():
    test_list={
        'egg': 0,
        'ham': 9,
        'water': 2
    }
    username = session['username']
    food_list = Food_list.query.filter_by(username=username).order_by(Food_list.id.desc()).first()
    # it is first time for user to upload pantry
    if food_list is None:
        new_food = Food_list(username=username, food=test_list)
        db.session.add(new_food)
        db.session.commit()
        flash('This is your first pantry!', 'success')
        return redirect('/')
    # not the first time to upload pantry, will compare the difference and update the latest food list in database
    else:
        old_list = food_list.food
        keys1 = set(old_list.keys())
        keys2 = set(test_list.keys())
        diff1 = keys1 - keys2
        diff2 = keys2 - keys1
        common_keys = keys1 & keys2
        diff3 = {k: (old_list[k] - test_list[k]) for k in common_keys if old_list[k] != test_list[k]}
        difference = {}
        difference.update({k: old_list[k] for k in diff1})
        difference.update({k: test_list[k] for k in diff2})
        difference.update(diff3)
        
        user = User.query.filter_by(username=username).first()
        user_email = user.email
        message = json.dumps(difference)

        # send gmail with SMTP
        # msg = Message('Your Shopping List from ChefMate', sender = 'chefmate839@gmail.com', recipients = "ilai3@wisc.edu")
        # msg.body = json.dumps(difference)
        # mail.send(msg)

        # send email with mailgun
        send_simple_message("ilai3@wisc.edu", message)
        # send_simple_message(user_email, message)
        print(message)
        
        # update the database, if under testing, don't recover comment
        # new_food = Food_list(username=username, food=test_list)
        # db.session.add(new_food)
        # db.session.commit()
        # flash('Here is the difference: '+json.dumps(difference), 'success')
        return redirect('/')

def send_simple_message(recipients, txt):
	return requests.post(
		"https://api.mailgun.net/v3/sandboxf6cbbd6cf88246d495116184fc07d291.mailgun.org/messages",
		auth=("api", "f71b7c883f7997052282ee661f65cd9b-2cc48b29-dda92d69"),
		data={"from": "ChefMate <postmaster@sandboxf6cbbd6cf88246d495116184fc07d291.mailgun.org>",
			"to": recipients,
			"subject": "Your Shopping List from ChefMate ",
			"text": txt})

if __name__ == '__main__':
    app.run(debug=True)