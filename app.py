from flask import Flask, render_template, request, jsonify, send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import threading
import json
import os
from datetime import datetime

app = Flask(__name__)

# Email configuration
SENDER_EMAIL = "lokeshwaranb0406@gmail.com"
SENDER_PASSWORD = "wlafhbbbsmtkxqoc"
RECIPIENT_EMAIL = "lokeshwaranb0406@gmail.com"

# Absolute path for leads file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_FILE = os.path.join(BASE_DIR, 'leads.json')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

def save_lead_to_file(data, timestamp):
    leads = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    leads = json.loads(content)
        except Exception as e:
            print(f"Error reading leads file: {e}")
            leads = []
    
    data['timestamp'] = timestamp
    leads.append(data)
    
    try:
        with open(LEADS_FILE, 'w') as f:
            json.dump(leads, f, indent=4)
    except Exception as e:
        print(f"Error writing to leads file: {e}")
        raise e

def send_email_async(name, phone, age):
    try:
        subject = f"🚨 URGENT: New Star Health Lead - {name}"
        body = f"NEW LEAD RECEIVED\n\nName: {name}\nPhone: {phone}\nAge: {age}"
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg['X-Priority'] = '1 (Highest)'
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent for {name}")
    except Exception as email_err:
        print(f"❌ Email failed: {email_err}")

@app.route('/dashboard')
def dashboard():
    leads = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    leads = json.loads(content)
        except Exception:
            leads = []
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('dashboard.html', leads=reversed(leads), todaydate=today_date)

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    try:
        arrival_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Processing lead at {arrival_time}")

        if not request.is_json:
            return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Empty lead data"}), 400

        name = data.get('name')
        phone = data.get('phone')
        age = data.get('age')

        if not all([name, phone, age]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        # Save leads
        save_lead_to_file(data.copy(), arrival_time)

        # Background email
        email_thread = threading.Thread(target=send_email_async, args=(name, phone, age))
        email_thread.daemon = True
        email_thread.start()

        return jsonify({"status": "success", "message": "Lead submitted successfully"})

    except Exception as e:
        print(f"Critical Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Standard Flask run
    app.run(debug=True, host='0.0.0.0', port=5000)
