import os
from flask import Flask, request, jsonify, send_file, redirect, session, url_for,g
from flask_session import Session
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import io
from google import genai
from google.genai import types
import pathlib
import httpx
from datetime import datetime
import json
# from werkzeug import secure_filename
import string, random, requests
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = "itsasecret"

app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Azure Storage configuration
CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

# Google OAuth Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8080/login/callback"

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)

# In-memory user store (for demo purposes)
users = {}

class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)



# We'll get the container name when initializing the service
class BlobStorageService:
    def __init__(self, connection_string):
        if not connection_string:
            raise ValueError("Azure Storage connection string is not configured")
            
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # List available containers
        containers = list(self.blob_service_client.list_containers())
        if not containers:
            raise ValueError("No containers found in storage account")
            
        # Use the first container by default
        self.container_name = containers[0].name
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        print(f"Connected to container: {self.container_name}")

    def upload_file(self, user_id, file):
        """Upload a file to blob storage under user's directory"""
        try:
            blob_path = f"{user_id}/{file.filename}"
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(file, overwrite=True)
            return blob_client.url
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def download_file(self, user_id, filename):
        """Download a file from blob storage"""
        try:
            blob_path = f"{user_id}/{filename}"
            blob_client = self.container_client.get_blob_client(blob_path)
            
            if not blob_client.exists():
                raise FileNotFoundError("File not found")
                
            blob_data = blob_client.download_blob()
            return io.BytesIO(blob_data.readall())
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def list_files(self, user_id):
        """List all files for a specific user"""
        try:
            prefix = f"{user_id}/"
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            return [blob.name.replace(prefix, '') for blob in blobs]
        except Exception as e:
            raise Exception(f"List operation failed: {str(e)}")

try:
    # Initialize blob storage service
    blob_service = BlobStorageService(CONNECTION_STRING)
except Exception as e:
    print(f"Failed to initialize Blob Storage Service: {str(e)}")
    raise

# @app.route("/api/upload", methods=["POST"])
# def upload_file():
#     """API endpoint to upload a file"""
#     if "file" not in request.files or "user_id" not in request.form:
#         return jsonify({"error": "Missing file or user_id"}), 400

#     file = request.files["file"]
#     user_id = request.form["user_id"]

#     if not file.filename:
#         return jsonify({"error": "Invalid file"}), 400

#     try:
#         file_url = blob_service.upload_file(user_id, file)
#         return jsonify({
#             "message": "File uploaded successfully",
#             "file_url": file_url
#         }), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def landing_page():
    return ""

@app.route('/api/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        fileextension = filename.rsplit('.',1)[1]
        Randomfilename = id_generator()
        filename = Randomfilename + '.' + fileextension
        print(filename, fileextension)

        try:
            # blob_service.create_blob_from_stream('hackylticsdata', filename, file)
            # print('user id' + current_user)
            print('userid' + global_current_user_id)
            blob_service.upload_file(global_current_user_id, file)
        except Exception:
            print(global_current_user_id)
            pass
        ref =  'http://'+AZURE_STORAGE_ACCOUNT_NAME+'.blob.core.windows.net/' + AZURE_STORAGE_CONTAINER_NAME+'/' + filename
        return '''
        <!doctype html>
        <title>File Link</title>
        <h1>Uploaded File Link</h1>
        <p>''' + ref + '''</p>
        <img src="'''+ ref +'''">
        '''
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route("/api/list_files/<user_id>", methods=["GET"])
def list_files(user_id):
    """API endpoint to list all files for a user"""
    try:
        files = blob_service.list_files(user_id)
        return jsonify({
            "user_id": user_id,
            "files": files
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<user_id>/<filename>", methods=["GET"])
def download_file(user_id, filename):
    """API endpoint to download a file and save it locally"""
    try:
        print(f"Downloading file: {filename} for user: {user_id}")
        file_stream = blob_service.download_file(user_id, filename)
        
        # Create a directory for downloads if it doesn't exist
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        # Create user directory inside downloads
        user_dir = os.path.join(download_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Full path for saving the file
        file_path = os.path.join(user_dir, filename)
        
        # Save the file locally
        with open(file_path, 'wb') as f:
            f.write(file_stream.getvalue())
            
        print(f"File saved locally at: {file_path}")
        
        return jsonify({
            "message": "File downloaded successfully",
            "file_path": file_path
        }), 200
        
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


### AUTHENTICATION ROUTES ###
@app.route("/login", methods=["GET"])
def login():
    """Redirects user to Google's OAuth login page."""
    print(GOOGLE_CLIENT_ID)
    print(REDIRECT_URI)
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    print(google_auth_url)
    return redirect(google_auth_url)

@app.route("/login/callback", methods=["GET"])
def login_callback():
    """Handles Google OAuth callback and logs in the user."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    # Exchange code for access token
    token_data = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).json()

    print(token_data)

    if "id_token" not in token_data:
        return jsonify({"error": "Failed to obtain ID token"}), 400

    try:
        # Verify token
        id_info = id_token.verify_oauth2_token(token_data["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID)

        user_id = id_info["sub"]  # Unique ID from Google
        email = id_info["email"]
        name = id_info.get("name", "Unknown User")

        print(user_id, email,name)
        # Register user if not exists
        if user_id not in users:
            users[user_id] = User(user_id, name, email)
        global global_current_user_id
        global_current_user_id=user_id
        login_user(users[user_id])
        print(users)

        return jsonify({
            "message": "Login successful",
            "user_id": user_id,
            "name": name,
            "email": email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logs out the user."""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route("/api/me", methods=["GET"])
@login_required
def get_me():
    return jsonify({
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }), 200

@app.route("/debug/session")
def debug_session():
    return jsonify(session)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)