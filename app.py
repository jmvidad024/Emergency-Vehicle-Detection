import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Fallback memory variable to store the latest evaluation of the intersection
intersection_status = "none"

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    global intersection_status
    try:
        data = request.get_json()
        if not data or 'imageBase64' not in data:
            return jsonify({"error": "Missing image data"}), 400

        raw_base64 = data['imageBase64']

        # Clean up any weird data prefixes or newlines from the web payload
        if "," in raw_base64:
            raw_base64 = raw_base64.split(",")[1]
        raw_base64 = raw_base64.replace(" ", "+").replace("\n", "").replace("\r", "")

        # Format the image into a clean Data URL structure for the vision engine
        image_data_url = f"data:image/jpeg;base64,{raw_base64}"

        # Setup the Pollinations AI Endpoint
        url = "https://text.pollinations.ai/"
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this traffic camera frame. Determine if an emergency response "
                                "vehicle (like an ambulance, fire truck, or police car) is visible. "
                                "Respond with exactly one word in lowercase: 'ambulance' if present, "
                                "or 'none' if it is a normal car, empty road, glare, or screen frame."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            "model": "openai-large"  # High-accuracy vision interpreter
        }

        # Fire request to the free, uncapped Pollinations cloud engine
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"⚠️ Vision engine returned an error: {response.text}")
            return jsonify({"error": "Failed to communicate with Vision API"}), 500

        # Parse out the single-word context response text directly
        ai_decision = response.text.strip().lower()
        print(f"👁️ Free Cloud Vision Intelligence Evaluation: '{ai_decision}'")

        # Core Traffic Control Logic
        if "ambulance" in ai_decision:
            intersection_status = "ambulance"
            print("🚨 Emergency vehicle validated! Triggering hardware green light sequence.")
        else:
            intersection_status = "none"

        return jsonify({"status": "processed", "vision_saw": ai_decision}), 200

    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    global intersection_status
    return jsonify({"vehicleType": intersection_status})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)