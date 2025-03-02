import os
import socket
import qrcode
import base64
import io
from flask import Flask, request, send_from_directory, send_file, jsonify, render_template_string
from werkzeug.utils import secure_filename
from datetime import datetime

# Base upload folder (Mounted Suite Studio Path)
BASE_UPLOAD_FOLDER = "/Volumes/Suite"

# Ensure the base directory exists
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

# 🔹 Get Local IP Address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# 🔹 Generate QR Code and return as Base64 JSON API
@app.route("/generate_qr", methods=["GET"])
def generate_qr_api():
    server_ip = get_local_ip()
    server_url = f"http://{server_ip}:8080"
    
    qr = qrcode.make(server_url)
    img_io = io.BytesIO()
    qr.save(img_io, format="PNG")
    img_io.seek(0)

    # Encode image as base64
    qr_base64 = base64.b64encode(img_io.read()).decode("utf-8")

    return jsonify({"qr_code": qr_base64, "server_url": server_url})

# 🔹 Generate QR Code and return as an Image Response (Triggers Download)
@app.route("/generate_qr_image", methods=["GET"])
def generate_qr_image():
    server_ip = get_local_ip()
    server_url = f"http://{server_ip}:8080"

    qr = qrcode.make(server_url)
    img_io = io.BytesIO()
    qr.save(img_io, format="PNG")
    img_io.seek(0)

    # This sets the `Content-Disposition` header to force download
    return send_file(img_io, mimetype="image/png", as_attachment=True, download_name="qr_code.png")

# 🔹 Get Uploaded File Count Per Project
def get_uploaded_files_count():
    project_counts = {}
    if os.path.exists(BASE_UPLOAD_FOLDER):
        for project in sorted(os.listdir(BASE_UPLOAD_FOLDER)):  # Sort to maintain order
            project_path = os.path.join(BASE_UPLOAD_FOLDER, project)
            if os.path.isdir(project_path) and not project.startswith("."):  # Ignore hidden folders
                file_count = len(os.listdir(project_path))
                project_counts[project] = file_count
    return project_counts

# 🔹 Homepage: Show uploaded file count & upload form
@app.route("/")
def home():
    project_counts = get_uploaded_files_count()
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload Photos</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background: #f8f9fa;
                font-family: Arial, sans-serif;
            }
            .container {
                max-width: 500px;
                margin: 50px auto;
                text-align: center;
            }
            .upload-btn {
                width: 100%;
                font-size: 24px;
                padding: 15px;
                border-radius: 10px;
            }
            input[type="file"] {
                display: none;
            }
            .file-count {
                font-size: 26px;
                font-weight: bold;
                color: #007bff;
                margin-top: 20px;
            }
            .success-message {
                font-size: 28px;
                font-weight: bold;
                color: green;
                margin-top: 20px;
                display: none;
            }
            .project-list {
                margin-top: 20px;
                font-size: 20px;
                text-align: left;
            }
        </style>
        <script>
            function updateFileCount() {
                let files = document.getElementById("file-input").files;
                let countDisplay = document.getElementById("file-count");
                if (files.length > 0) {
                    countDisplay.innerText = "📂 " + files.length + " files selected for upload";
                } else {
                    countDisplay.innerText = "";
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h2 class="text-primary mb-4">Upload Your Photos</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="project_name" placeholder="Name the project" class="form-control mb-3" required>
                <label class="btn btn-lg btn-primary upload-btn">
                    Select Files <input type="file" name="file" id="file-input" multiple accept="image/*,video/*,.heic,.jpeg,.jpg,.png,.mp4,.mov,.pdf" onchange="updateFileCount()">
                </label>
                <p id="file-count" class="file-count"></p>
                <button type="submit" class="btn btn-lg btn-success upload-btn mt-3">Upload</button>
            </form>
            
            <!-- Show uploaded file count -->
            <div class="project-list">
                <h3>📂 Available albums to upload:</h3>
                <ul>
                    {% for project, count in project_counts.items() %}
                        <li><b>{{ project }}</b>: {{ count }} files</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """, project_counts=project_counts)

# 🔹 Upload endpoint: Saves files inside Suite Studio with project name
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files or "project_name" not in request.form:
        return "<h2 style='color:red; font-size:28px;'>❌ Missing file or project name</h2>", 400

    project_name = request.form["project_name"].strip()
    if not project_name:
        return "<h2 style='color:red; font-size:28px;'>❌ Project name cannot be empty</h2>", 400

    # Create a project-specific directory inside Suite Studio
    project_folder = os.path.join(BASE_UPLOAD_FOLDER, secure_filename(project_name))
    os.makedirs(project_folder, exist_ok=True)

    files = request.files.getlist("file")  # Get all uploaded files
    if not files or files[0].filename == "":
        return "<h2 style='color:red; font-size:28px;'>❌ No selected files</h2>", 400

    uploaded_files = []
    for file in files:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(f"{timestamp}_{file.filename}")
        file_path = os.path.join(project_folder, filename)

        try:
            file.save(file_path)
            uploaded_files.append(filename)
        except Exception as e:
            return f"<h2 style='color:red; font-size:28px;'>❌ Error saving file: {str(e)}</h2>", 500

    return "<script>window.location.href='/'</script>"  # Redirect to home page after upload

# 🔹 Serve Uploaded Files
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(BASE_UPLOAD_FOLDER, filename)

# 🔹 Start Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
