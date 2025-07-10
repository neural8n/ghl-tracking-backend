from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return "✅ GHL Tracking Backend is running."

@app.route('/process-tracking', methods=['POST'])
def process_tracking():
    try:
        data = request.json
        contact = data.get('contact', {})
        file_url = contact.get('custom_fields', {}).get('tracking_file')
        contact_email = contact.get('email', 'unknown@example.com')

        if not file_url:
            return jsonify({'error': 'No tracking file URL provided'}), 400

        # Download the file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        input_path = os.path.join(UPLOAD_DIR, f'input_{timestamp}.xlsx')
        output_path = os.path.join(UPLOAD_DIR, f'updated_{timestamp}.xlsx')

        r = requests.get(file_url)
        with open(input_path, 'wb') as f:
            f.write(r.content)

        # Read and process Excel file
        df = pd.read_excel(input_path)

        if 'Tracking Number' not in df.columns:
            return jsonify({'error': 'Excel file must have a "Tracking Number" column'}), 400

        # Simulate tracking check
        df['Status'] = df['Tracking Number'].apply(lambda x: "Delivered" if str(x).endswith('1') else "In Transit")

        df.to_excel(output_path, index=False)

        download_url = f"http://localhost:5000/download/{os.path.basename(output_path)}"

        return jsonify({
            "status": "done",
            "download_link": download_url,
            "email": contact_email
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
