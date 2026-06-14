import base64
import io
import os
from flask import Flask, request, jsonify
from PIL import Image
from transformers import pipeline

app = Flask(__name__)

# System memory state
intersection_status = "none"

print("⏳ Loading local AI Vision Pipeline into server memory...")
# Initialize a free, high-speed vision captioning engine locally
try:
    vision_engine = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    print("🟢 Local Vision Engine successfully loaded and ready!")
except Exception as err:
    print(f"❌ Failed to load model: {str(err)}")
    vision_engine = None

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    global intersection_status
    try:
        data = request.get_json()
        if not data or 'imageBase64' not in data:
            return jsonify({"error": "Missing image data"}), 400

        raw_base64 = data['imageBase64']

        if vision_engine is None:
            return jsonify({"error": "AI Vision engine failed to initialize on boot"}), 500

        # Clean the base64 string layout data
        if "," in raw_base64:
            raw_base64 = raw_base64.split(",")[1]
        raw_base64 = raw_base64.replace(" ", "+").replace("\n", "").replace("\r", "")

        # Decode base64 directly into system bytes and open as a PIL Image
        image_bytes = base64.b64decode(raw_base64)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Run local inference processing
        predictions = vision_engine(pil_image)
        description = predictions[0].get("generated_text", "").lower()
        
        print(f"👁️ Local AI Scene Evaluation: '{description}'")

        # Contextual verification checks
        emergency_keywords = ["ambulance", "truck", "fire", "bus", "car", "vehicle"]
        
        if any(word in description for word in emergency_keywords):
            intersection_status = "ambulance"
            print("🚨 Target vehicle confirmed! Setting intersection status to HIGH.")
        else:
            intersection_status = "none"

        return jsonify({"status": "processed", "ai_saw": description}), 200

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