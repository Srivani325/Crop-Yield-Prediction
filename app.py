from flask import Flask, render_template, request, redirect , url_for, session, flash
import pickle
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['crop_yield_db']
users = db['users']
history = db['history']

# Load the trained models and label encoders
with open('linear_model.pkl', 'rb') as f:
    linear_model = pickle.load(f)

with open('random_forest.pkl', 'rb') as f:
    random_forest = pickle.load(f)

with open('label_encoders.pkl', 'rb') as encoder_file:
    label_encoders = pickle.load(encoder_file)

     
# Load R² scores
with open('metadata.pkl', 'rb') as f:
    metadata = pickle.load(f)

@app.route('/')
def home():
    return render_template('index.html')


# SIGNUP FORM
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))

        existing_user = users.find_one({'email': email})
        if existing_user:
            flash('Email already exists!', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)
        users.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


# LOGIN FORM
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']  # Store username in session
            print("success")
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')



@app.route('/result', methods=['POST'])
def result():
    if request.method == 'POST':
      try:
            # Get user inputs
            region = request.form['region']
            soil = request.form['soil_type']
            crop = request.form['crop']
            rainfall = float(request.form['rainfall'])
            temperature = float(request.form['temperature'])

            # Define allowed values for validation
            VALID_REGIONS = label_encoders['region'].classes_.tolist()
            VALID_SOIL_TYPES = label_encoders['soil_type'].classes_.tolist()
            VALID_CROPS = label_encoders['crop'].classes_.tolist()

            # Validate input values before encoding
            if region not in VALID_REGIONS:
                flash(f"Invalid region: '{region}'. Allowed values: {VALID_REGIONS}", 'error')
                return redirect(url_for('home'))
            if soil not in VALID_SOIL_TYPES:
                flash(f"Invalid soil type: '{soil}'. Allowed values: {VALID_SOIL_TYPES}", 'error')
                return redirect(url_for('home'))
            if crop not in VALID_CROPS:
                flash(f"Invalid crop: '{crop}'. Allowed values: {VALID_CROPS}", 'error')
                return redirect(url_for('home'))

            # Encode categorical data using the label encoder
            region_code = label_encoders['region'].transform([region])[0]
            soil_code = label_encoders['soil_type'].transform([soil])[0]
            crop_code = label_encoders['crop'].transform([crop])[0]
           
            # Prepare input for prediction
            input_data = np.array([[region_code, soil_code, crop_code, rainfall, temperature]])

            # Predict crop yield
            linear_pred = linear_model.predict(input_data)[0]
            random_pred = random_forest.predict(input_data)[0]
        
      
            r2_linear = metadata['r2_linear']
            r2_random = metadata['r2_random']
   
            # Compute dynamic weights based on R² scores
            weight_linear = r2_linear / (r2_linear + r2_random)
            weight_random = r2_random / (r2_linear + r2_random)

            print(f"Linear Model Weight: {weight_linear:.2f}")
            print(f"Random Forest Weight: {weight_random:.2f}")

            combined_pred = (linear_pred *weight_linear + random_pred * weight_random)
            
            # Save to history only if user is logged in
            if 'email' in session:   
                history.insert_one({
                   'email': session['email'],
                   'region': region,
                   'soil': soil,
                   'crop': crop,
                   'rainfall': rainfall,
                   'temperature': temperature,
                   'prediction': round(combined_pred, 2),
                   "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                })

            # Return the result to the result page
            return render_template('result.html',
                               region=region,
                               soil=soil,
                               crop=crop,
                               rainfall=rainfall,
                               temperature=temperature,
                               result=round(combined_pred, 2))

      except Exception as e:
            flash(f"Error: {e}", 'error')
            return redirect(url_for('home'))

    return redirect(url_for('home'))  

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


@app.route('/history',methods=['GET'])
def history_view():
    if 'email' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    # Convert MongoDB cursor to list
    records = list(history.find({'email': session['email']}))

    for record in records:
        timestamp_str = record.get('timestamp')
        try:
            # Parse the timestamp string and convert to datetime object
            timestamp_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            # Localize to IST (just to ensure consistency)
            ist_time = timestamp_obj.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            record['timestamp'] = ist_time.strftime('%d-%m-%Y %I:%M %p')  # Example: 07-04-2025 04:45 PM
        except Exception as e:
            record['timestamp'] = timestamp_str  # Fallback in case of error

    return render_template('history.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)
