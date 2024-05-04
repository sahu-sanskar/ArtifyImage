import cv2
import numpy as np
from cv2 import IMREAD_GRAYSCALE
import os
from flask import Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = 'users.db'


# Initialize database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

# Check if user exists
def check_user(username, password):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if user:
            if check_password_hash(user[2], password):
                return True
    return False

# Register new user
def register_user(username, password):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
        conn.commit()
        

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')


# Route for logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# Route for main page
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))
    

# Route for photo gallery
@app.route('/photo_gallery.html')
def display_uploaded_photos():
    if 'username' in session:
        image_list = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_url = f"{UPLOAD_FOLDER}/{filename}"
                image_list.append(image_url)
        return render_template('photo_gallery.html', image_list=image_list)
    else:
        return redirect(url_for('login'))
    

# Route for registering new user
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['new_username']
        password = request.form['new_password']
        register_user(username, password)
        return redirect(url_for('login'))




# Function to cartoonize an image
def cartoonize_image(image_path, method='color'):

    if 'username' in session:

        img = cv2.imread(image_path)

        if method == 'Cartoonize':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(img, 9, 250, 250)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            
        elif method == 'black_and_white':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cartoon = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)

        elif method == 'black_and_white_to_color':
            color_image = cv2.applyColorMap(img, cv2.COLORMAP_JET)
            cartoon = color_image

        elif method == 'grayscale':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cartoon = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        return cartoon

    else:
        return redirect(url_for('login'))



# Route for processing image cartoonization
@app.route('/cartoonize', methods=['POST'])
def cartoonize():

    if 'username' in session:
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']
        cartoon_method = request.form.get('method') 
        if file.filename == '':
            return "No selected file"



        if file:
            # Save the uploaded image to the server
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Perform cartoonization
            cartoon_image = cartoonize_image(file_path, method=cartoon_method)

            # Save the cartoonized image in the same folder
            cartoon_filename = 'cartoonized_' + filename
            cartoon_path = os.path.join(app.config['UPLOAD_FOLDER'], cartoon_filename)

            # Save the cartoonized image
            cv2.imwrite(cartoon_path, cartoon_image)
            cartoon_url = f"/uploads/{cartoon_filename}"
            original_url = f"/uploads/{filename}"
            return render_template('display_cartoon.html', cartoon_url=cartoon_url, original_url=original_url)
        

    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
