import { GoogleGenAI } from '@google/genai';

// A global in-memory variable to act as our temporary database state. 
// Note: In serverless, this resets when the function goes to sleep, 
// which is perfect for a live-updating miniature city flag!
global.emergencyState = global.emergencyState || { isEmergency: false, vehicleType: 'none' };

export default async function handler(req, res) {
  // Allow your ESP32-CAM to hit this endpoint from anywhere
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // --- ENDPOINT 1: THE ESP32-CAM SENDS THE IMAGE (POST) ---
  if (req.method === 'POST') {
    try {
      const { imageBase64 } = req.body; // Expecting raw base64 string from ESP32

      if (!imageBase64) {
        return res.status(400).json({ error: 'No image data received.' });
      }

      // Initialize Gemini with your environment variable API key
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

      const prompt = `
        Analyze this image from a traffic camera. Is there an emergency vehicle present (Ambulance, Fire Truck, or Police Car)?
        Respond strictly in this JSON format:
        {
          "isEmergency": true/false,
          "vehicleType": "ambulance" / "fire_truck" / "police" / "none"
        }
      `;

      // Call Gemini 3.5 Flash (optimized for speed and low cost)
      const response = await ai.models.generateContent({
        model: 'gemini-3.5-flash',
        contents: [
          prompt,
          {
            inlineData: {
              mimeType: 'image/jpeg',
              data: imageBase64
            }
          }
        ],
        // Force the AI to output parseable JSON
        config: { responseMimeType: "application/json" }
      });

      // Parse the AI response and update our global city state
      const result = JSON.parse(response.text);
      global.emergencyState = {
        isEmergency: result.isEmergency,
        vehicleType: result.vehicleType
      };

      return res.status(200).json({ message: "Processed successfully", status: global.emergencyState });

    } catch (error) {
      console.error("Gemini Error:", error);
      return res.status(500).json({ error: "Failed to process image." });
    }
  }

  // --- ENDPOINT 2: YOUR TRAFFIC LIGHTS CHECK THE STATUS (GET) ---
  if (req.method === 'GET') {
    return res.status(200).json(global.emergencyState);
  }

  return res.status(405).json({ error: 'Method not allowed' });
}