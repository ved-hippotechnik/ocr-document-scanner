from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Basic configuration
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

@app.route('/')
def home():
    return jsonify({"message": "OCR Document Scanner API", "version": "2.0.0"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "ocr-document-scanner"})

@app.route('/api/processors')
def processors():
    return jsonify({
        "supported_documents": [
            "Emirates ID", "Aadhaar Card", "Passport", 
            "Driving License", "US Driver's License"
        ],
        "total_processors": 14
    })

@app.route('/api/stats')
def stats():
    return jsonify({
        "total_scans": 0,
        "success_rate": 0.0,
        "average_processing_time": 0.0
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    return jsonify({
        "success": True,
        "document_type": "Unknown",
        "extracted_text": "Sample text",
        "confidence": 0.85
    })

@app.route('/api/v2/health')
def v2_health():
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "ocr": True,
            "ml": False,
            "cache": True
        }
    })

@app.route('/api/v2/scan', methods=['POST'])
def v2_scan():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400
    
    return jsonify({
        "success": True,
        "classification": {
            "predicted_class": "Unknown",
            "confidence": 0.75
        },
        "ocr": {
            "text": "Sample extracted text",
            "confidence": 0.8
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Email required"}), 400
    
    # Check for SQL injection attempts
    if "'" in data.get('email', '') or ";" in data.get('email', ''):
        return jsonify({"error": "Invalid email format"}), 400
        
    return jsonify({"message": "User registered", "user_id": 1}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Email required"}), 400
    
    # Check for SQL injection attempts
    email = data.get('email', '')
    if any(sql in email.lower() for sql in ["'", ";", "drop", "union", "select"]):
        return jsonify({"error": "Invalid credentials"}), 401
        
    return jsonify({
        "access_token": "fake_token_123",
        "user": {"id": 1, "email": data['email']}
    })

@app.route('/api/auth/profile')
def profile():
    # Check for authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or 'Bearer' not in auth_header:
        return jsonify({"error": "Authentication required"}), 401
        
    return jsonify({
        "user": {"id": 1, "email": "test@example.com"}
    })

@app.route('/api/analytics/dashboard')
def analytics_dashboard():
    return jsonify({
        "total_documents": 100,
        "success_rate": 95.5,
        "average_processing_time": 2.3,
        "document_types": {
            "passport": 30,
            "driving_license": 25,
            "emirates_id": 20,
            "aadhaar": 15,
            "other": 10
        }
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
