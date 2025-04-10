from flask import Flask, render_template, request, redirect, url_for, g, flash, Blueprint, session
import os
import pymongo
import bcrypt
import bson
import qrcode
from PIL import Image
import io
import base64
import uuid
import shortuuid
from datetime import datetime
# Create separate blueprints with different prefixes
auth = Blueprint('auth', __name__, url_prefix='/auth')
dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')
qr = Blueprint('qr', __name__, url_prefix='/qr')

client = pymongo.MongoClient("localhost", 27017)
db = client.qr_database
usersCollection = db["users"]
qrCollection = db["qr_codes"]

app = Flask(__name__)
app.secret_key = 'dev'  # Make sure this is set for sessions to work

def root_dir():
    return os.path.dirname(os.path.abspath(__file__))

# Function to generate a short unique ID for QR codes
def generate_short_id():
    return shortuuid.uuid()[:8]  # 8 characters is enough for most use cases

@app.route('/')
def home_route():
    if g.user:
        return redirect(url_for('dashboard.home'))
    else:
        return redirect(url_for('auth.login'))

# QR code redirect endpoint - This handles when someone scans a QR code
@app.route('/q/<short_id>')
def qr_redirect(short_id):
    # Find the QR code by its short ID
    qr_code = qrCollection.find_one({"short_id": short_id})
    
    if qr_code:
        # Increment the scan count
        qrCollection.update_one(
            {"_id": qr_code["_id"]},
            {"$inc": {"scans": 1}}
        )
        
        # Check if the QR is active
        if qr_code.get("active", True):
            # Get the data to redirect to based on QR type
            qr_data = qr_code["data"]
            
            # For URL type, redirect directly
            if qr_code["type"] == "url":
                return redirect(qr_data)
            # For other types, show a page with the data
            else:
                return render_template("qr/scan.html", qr=qr_code)
        else:
            # QR code is deactivated
            return render_template("qr/inactive.html")
    else:
        # QR code not found
        return render_template("qr/not_found.html")

# Auth blueprint routes
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if usersCollection.find_one({"username": username}):
            flash('Username already exists!')
            return redirect(url_for('auth.register'))
        
        password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user into the database
        user_id = usersCollection.insert_one({"username": username, "email": email, "password": password}).inserted_id
        
        # Store the user ID in the session
        session['user_id'] = str(user_id)
        
        flash('Registration successful!')
        return redirect(url_for('auth.login'))

    return render_template("auth/register.html")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = usersCollection.find_one({"email": email})

        if user:
            try:
                matched_password = bcrypt.checkpw(
                    password.encode('utf-8'),
                    user['password'])


                if matched_password:
                    # Store the user ID in the session
                    session['user_id'] = str(user['_id'])
                    flash('Login successful!')
                    return redirect(url_for('dashboard.home'))
                else:
                    flash('Invalid password!')
                    return redirect(url_for('auth.login'))
            except ValueError as e:
                print(f"Password verification error: {e}")
                flash('Login error. Please try again.')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid email')
            return redirect(url_for('auth.login'))
        
    return render_template("auth/login.html")

@auth.route('/logout')
def logout():
    # Clear the user ID from the session
    session.clear()
    flash('You have been logged out!')
    return redirect(url_for('home_route'))

# Dashboard blueprint routes
@dashboard.route('/home')
def home():
    if g.user:
        return render_template("dashboard/home.html", user=g.user)
    else:
        flash('You need to log in first!')
        return redirect(url_for('auth.login'))
    

# QR code routes
@qr.route('/')
def index():
    if g.user:
        # Find all QR codes for the current user
        qr_codes = list(qrCollection.find({"user_id": g.user["_id"]}))
        
        # Process each QR code to format date and add image URL
        for qr_code in qr_codes:
            # Format the date (if it exists)
            if 'created_at' in qr_code:
                qr_code['created_at_formatted'] = qr_code['created_at'].strftime('%Y-%m-%d')
            else:
                qr_code['created_at_formatted'] = 'Unknown'
                
            # Add direct image data URL
            if 'image_data' in qr_code:
                qr_code['image_url'] = f"data:image/png;base64,{qr_code['image_data']}"
        
        return render_template("qr/index.html", qr_codes=qr_codes)
    else:
        flash('You need to log in first!')
        return redirect(url_for('auth.login'))
    
@qr.route('/create', methods=['GET', 'POST'])
def create_qr():
    if g.user:
        if request.method == 'POST':
            # Get QR code details from form
            qr_name = request.form['qr_name']
            qr_type = request.form['qr_type']
            
            # Generate a unique short ID for this QR code
            short_id = generate_short_id()
            
            # Store the actual content based on QR type
            original_data = ""
            if qr_type == 'url':
                original_data = request.form['url_content']
            elif qr_type == 'text':
                original_data = request.form['text_content']
            elif qr_type == 'email':
                email = request.form['email_address']
                subject = request.form['email_subject']
                body = request.form['email_body']
                original_data = f"mailto:{email}?subject={subject}&body={body}"
            elif qr_type == 'phone':
                original_data = f"tel:{request.form['phone_number']}"
            elif qr_type == 'sms':
                phone = request.form['sms_number']
                message = request.form['sms_message']
                original_data = f"sms:{phone}?body={message}"
            elif qr_type == 'wifi':
                ssid = request.form['wifi_ssid']
                password = request.form['wifi_password']
                encryption = request.form['wifi_encryption']
                hidden = 'true' if 'wifi_hidden' in request.form else 'false'
                original_data = f"WIFI:S:{ssid};T:{encryption};P:{password};H:{hidden};;"
            elif qr_type == 'vcard':
                name = request.form['vcard_name']
                company = request.form['vcard_company']
                title = request.form['vcard_title']
                phone = request.form['vcard_phone']
                email = request.form['vcard_email']
                website = request.form['vcard_website']
                address = request.form['vcard_address']
                original_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{name}\nORG:{company}\nTITLE:{title}\nTEL:{phone}\nEMAIL:{email}\nURL:{website}\nADR:{address}\nEND:VCARD"
            
            # The actual QR code points to our redirection URL
            # Generate the full URL including the server name
            server_name = request.host_url.rstrip('/')
            qr_data = f"{server_name}/q/{short_id}"
            
            # Get QR code colors
            qr_color = request.form['qr_color']
            qr_background = request.form['qr_background']
            
            # Create QR code
            qr_img = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            # Add data to QR code - this uses our redirection URL
            qr_img.add_data(qr_data)
            qr_img.make(fit=True)
            
            # Convert hex colors to RGB tuples
            fill_color = tuple(int(qr_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            back_color = tuple(int(qr_background.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            # Create the QR code image
            img = qr_img.make_image(fill_color=fill_color, back_color=back_color)
            
            # Save image to in-memory file
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
            
            # Create a timestamp for the created_at field
            created_at = datetime.now()
            
            # Store QR code in database
            qr_code_data = {
                "name": qr_name,
                "type": qr_type,
                "short_id": short_id,
                "data": original_data,  # The actual content
                "redirect_url": qr_data,  # The URL in the QR code
                "image_data": img_data,
                "color": qr_color,
                "background": qr_background,
                "user_id": g.user["_id"],
                "created_at": created_at,
                "scans": 0,
                "active": True  # QR is active by default
            }
            
            # Insert into database
            qrCollection.insert_one(qr_code_data)
            
            flash('QR code created successfully!')
            return redirect(url_for('qr.index'))
        
        # For GET requests, just display the form
        return render_template("qr/create.html")
    else:
        flash('You need to log in first!')
        return redirect(url_for('auth.login'))

# Toggle QR code active status
@qr.route('/toggle/<id>', methods=['POST'])
def toggle_qr(id):
    if g.user:
        # Find the QR code and make sure it belongs to the current user
        qr_code = qrCollection.find_one({"_id": bson.ObjectId(id), "user_id": g.user["_id"]})
        
        if qr_code:
            # Toggle the active status
            new_status = not qr_code.get("active", True)
            qrCollection.update_one(
                {"_id": qr_code["_id"]},
                {"$set": {"active": new_status}}
            )
            
            status_msg = "activated" if new_status else "deactivated"
            flash(f'QR code {status_msg} successfully!')
        else:
            flash('QR code not found!')
            
        return redirect(url_for('qr.index'))
    else:
        flash('You need to log in first!')
        return redirect(url_for('auth.login'))

@qr.route('/delete/<id>', methods=['POST'])
def delete_qr(id):
    if g.user:
        try:
            # Make sure the QR code exists and belongs to the current user
            qr_code = qrCollection.find_one({
                "_id": bson.ObjectId(id), 
                "user_id": g.user["_id"]
            })
            
            if qr_code:
                # Delete the QR code
                result = qrCollection.delete_one({
                    "_id": bson.ObjectId(id),
                    "user_id": g.user["_id"]
                })
                
                if result.deleted_count > 0:
                    flash('QR code deleted successfully!')
                else:
                    flash('Failed to delete QR code.')
            else:
                flash('QR code not found or you do not have permission to delete it.')
                
        except bson.errors.InvalidId:
            flash('Invalid QR code ID.')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            
        return redirect(url_for('qr.index'))
    else:
        flash('You need to log in first!')
        return redirect(url_for('auth.login'))

# Register all blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(qr)

# Add a before_request handler to load the user from the session
@app.before_request
def load_logged_in_user():
    g.user = None
    user_id = session.get('user_id')
    if user_id:
        # Convert the string ID back to ObjectId for MongoDB query
        try:
            g.user = usersCollection.find_one({"_id": bson.ObjectId(user_id)})
        except:
            # Handle invalid session ID
            session.clear()