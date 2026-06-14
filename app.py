import base64
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Fallback memory variable to store the latest evaluation of the intersection
intersection_status = "none"

# Fetch the secret token we just saved in Render's dashboard environment
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY")

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    global intersection_status
    try:
        # 1. Catch the JSON payload from the ESP32-CAM
        data = request.get_json()
        if not data or 'imageBase64' not in data:
            return jsonify({"error": "Missing image data"}), 400

        # Extract just the raw base64 text from the JSON object
        raw_base64 = data['imageBase64']

        if not ROBOFLOW_API_KEY:
            return jsonify({"error": "Roboflow API key is not configured on Render"}), 500

        # 2. Set up the Roboflow endpoint URL
        url = "https://detect.roboflow.com/coco/3"
        params = {"api_key": ROBOFLOW_API_KEY}
        
        # 3. Post the raw string data to Roboflow
        # We pass the raw string directly into the data parameter
        response = requests.post(
            url, 
            params=params,
            data=raw_base64, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # 4. Handle response errors from Roboflow gracefully
        if response.status_code != 200:
            print(f"⚠️ Roboflow returned an error: {response.text}")
            return jsonify({"error": "Failed to communicate with Vision API"}), 500

        predictions = response.json().get('predictions', [])
        detected_labels = [p['class'].lower() for p in predictions]
        print(f"☁️ Roboflow Cloud Vision identified: {detected_labels}")

        # 5. Core Traffic Rules: Look for priority vehicles
        if "truck" in detected_labels or "bus" in detected_labels:
            intersection_status = "ambulance"
            print("🚨 Emergency vehicle declared! Changing status memory.")
        else:
            intersection_status = "none"

        return jsonify({"status": "processed", "objects_found": detected_labels}), 200

    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    global intersection_status
    # This is the lightweight endpoint your hardware devices hit to check state
    return jsonify({"vehicleType": intersection_status})


if __name__ == '__main__':
    # Render binds automatically to port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)