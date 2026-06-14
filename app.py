import base64
import io
import os
import threading
import time
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

app = Flask(__name__)

# Initialize the Gemini Client using the server environment variable
# The SDK automatically checks for GEMINI_API_KEY in your system environment variables
client = genai.Client()

# Define the structured data schema for Gemini 2.5 Flash
class TrafficAnalysis(BaseModel):
    isEmergency: bool
    vehicleType: str

# Shared continuous global application state
emergency_state = {
    "isEmergency": False,
    "vehicleType": "none"
}

def auto_reset_state():
    """Clears out the emergency status after 10 seconds."""
    global emergency_state
    time.sleep(10)
    emergency_state = {"isEmergency": False, "vehicleType": "none"}
    print("System Clear: Resetting traffic system back to normal state.")

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    global emergency_state
    try:
        data = request.get_json()
        if not data or 'imageBase64' not in data:
            return jsonify({"error": "Missing image string payload"}), 400
        
        # Extract and decode image buffer stream
        image_bytes = base64.b64decode(data['imageBase64'])
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = (
            "Analyze this traffic intersection image. Check if there is an active, "
            "approaching emergency vehicle (like an ambulance, fire truck, or police car). "
            "Output matching the required JSON schema."
        )
        
        # Run vision processing via the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TrafficAnalysis,
                temperature=0.1
            ),
        )
        
        import json
        result = json.loads(response.text)
        
        emergency_state = {
            "isEmergency": bool(result.get("isEmergency", False)),
            "vehicleType": str(result.get("vehicleType", "none")).lower()
        }
        
        # Trigger background automatic clearance timer
        if emergency_state["isEmergency"]:
            threading.Thread(target=auto_reset_state, daemon=True).start()
            
        return jsonify({"message": "Processed successfully", "status": emergency_state}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/detect', methods=['GET'])
def get_status():
    """Polled continuously by the Arduino Uno to read current intersection state."""
    return jsonify(emergency_state), 200

if __name__ == '__main__':
    # Grab the dynamic port given by the cloud provider, default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)