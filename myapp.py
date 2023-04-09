import requests
import os
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField


app = Flask(__name__, template_folder='templates', static_url_path='/static')
app.secret_key = 'randomGeneratedKey'

class UploadForm(FlaskForm):
    image = FileField('Image')
    submit = SubmitField('Upload')
    
# @app.route('/')
# def home():
#     return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the user data from the form
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user exists in the cloud database
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


@app.route('/', methods=['GET', 'POST'])
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


@app.route('/download/<filename>')
def download_image(filename):
    return send_file(os.path.join(app.static_folder, filename), as_attachment=True)
if __name__ == '__main__':
    app.run(debug=True)