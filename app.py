import base64
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Fallback memory variable to store the latest evaluation of the intersection
intersection_status = "none"

# Fetch the secret token saved in Render's dashboard environment
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY")

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    # 1. Declare the global reference immediately at the top of the scope
    global intersection_status
    
    try:
        # 2. Catch the payload from the ESP32-CAM
        data = request.get_json()
        if not data or 'imageBase64' not in data:
            return jsonify({"error": "Missing image data"}), 400

        raw_base64 = data['imageBase64']

        if not ROBOFLOW_API_KEY:
            return jsonify({"error": "Roboflow API key is not configured on Render"}), 500

        # 3. Clean up formatting and whitespace issues before sending to Roboflow
        raw_base64 = raw_base64.replace(" ", "+").replace("\n", "").replace("\r", "")

        # 4. Configure Roboflow hosted API parameters
        url = "https://detect.roboflow.com/coco/3"
        params = {"api_key": ROBOFLOW_API_KEY}
        
        # 5. Execute the application/x-www-form-urlencoded POST
        response = requests.post(
            url, 
            params=params,
            data=raw_base64, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print(f"⚠️ Roboflow returned an error: {response.text}")
            return jsonify({"error": "Failed to communicate with Vision API"}), 500

        predictions = response.json().get('predictions', [])
        detected_labels = [p['class'].lower() for p in predictions]
        
        # Check your Render dashboard log streams to see what labels print here!
        print(f"👁️ AI Detections: {detected_labels}")

        # 6. Core System Logic mapping
        if "truck" in detected_labels or "bus" in detected_labels or "car" in detected_labels:
            intersection_status = "ambulance"
            print("🚨 Priority Vehicle Detected! Triggering Emergency Sequence.")
        else:
            intersection_status = "none"

        return jsonify({"status": "processed", "objects_found": detected_labels}), 200

    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    global intersection_status
    # Endpoint polled by hardware devices to read intersection state
    return jsonify({"vehicleType": intersection_status})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)