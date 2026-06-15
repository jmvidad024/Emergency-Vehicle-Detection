from flask import Flask, request, jsonify
from ultralytics import YOLO
from PIL import Image
import base64
import io

app = Flask(__name__)

print("Loading YOLO model...")
model = YOLO("best.pt")
print("YOLO loaded!")

intersection_status = "none"

@app.route('/api/detect', methods=['POST'])
def detect_vehicle():
    global intersection_status

    try:
        data = request.get_json()

        if 'imageBase64' not in data:
            return jsonify({"error": "No image"}), 400

        img_data = base64.b64decode(data['imageBase64'])

        image = Image.open(io.BytesIO(img_data)).convert("RGB")

        results = model.predict(
            source=image,
            conf=0.25,
            verbose=False
        )

        vehicle_type = "none"

        if len(results[0].boxes) > 0:

            best_conf = 0

            for box in results[0].boxes:

                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if conf > best_conf:
                    best_conf = conf
                    vehicle_type = model.names[cls]

        intersection_status = vehicle_type

        print(f"Detected: {vehicle_type}")

        return jsonify({
            "vehicleType": vehicle_type
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    global intersection_status

    return jsonify({
        "vehicleType": intersection_status
    })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000
    )