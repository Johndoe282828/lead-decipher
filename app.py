from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import re
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Uploads folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirect to login if not authenticated
login_manager.init_app(app)

# User class for login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Fake user for demonstration
users = {"admin": "password123"}

# Store the leads in a global variable
all_leads = []  # Renamed to avoid confusion with function names

# Regex patterns for extracting leads
email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
phone_pattern = re.compile(r'\b\d{7,15}\b')

# Load user
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Extract lead information from text
def extract_lead_info(text):
    lead = {
        "name": None,
        "email": None,
        "phone": None,
        "job": None,
        "notes": ""
    }

    email = email_pattern.search(text)
    phone = phone_pattern.search(text)
    if email:
        lead['email'] = email.group()
        text = text.replace(lead['email'], '')
    if phone:
        lead['phone'] = phone.group()
        text = text.replace(lead['phone'], '')

    parts = [p.strip() for p in text.split() if p.strip()]
    if len(parts) >= 2:
        lead['name'] = f"{parts[0]} {parts[1]}"
        if len(parts) > 2:
            lead['job'] = ' '.join(parts[2:3])
            lead['notes'] = ' '.join(parts[3:])
    elif len(parts) == 1:
        lead['name'] = parts[0]

    return lead

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            user = User(username)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Upload file route
# Route to handle file upload
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    ext = os.path.splitext(file.filename)[1].lower()
    path = os.path.join('uploads', file.filename)
    file.save(path)

    if ext == '.txt':
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_leads.append(extract_lead_info(line.strip()))  # Appending to all_leads
    elif ext == '.xlsx':
        df = pd.read_excel(path, header=None)
        for _, row in df.iterrows():
            combined = ' '.join(str(cell) for cell in row if pd.notna(cell))
            all_leads.append(extract_lead_info(combined.strip()))  # Appending to all_leads

    return redirect(url_for('show_leads'))  # Redirect to leads page after upload


# Show leads route
# Route to display extracted leads
@app.route('/leads')
@login_required
def show_leads():
    return render_template('leads.html', leads=all_leads)  # Pass 'all_leads' to the template



# Edit lead route
@app.route('/edit_lead/<int:index>', methods=['GET', 'POST'])
@login_required
def edit_lead(index):
    lead = all_leads[index]
    if request.method == 'POST':
        lead['name'] = request.form['name']
        lead['email'] = request.form['email']
        lead['phone'] = request.form['phone']
        lead['job'] = request.form['job']
        lead['notes'] = request.form['notes']
        return redirect(url_for('show_leads'))
    return render_template('edit_lead.html', lead=lead, index=index)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)