import { GoogleGenAI } from '@google/genai';

// Safe initialization of global state
if (!global.emergencyState) {
  global.emergencyState = { isEmergency: false, vehicleType: 'none' };
}

export default async function handler(req, res) {
  // Setup CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // --- GET METHOD: TRAFFIC LIGHTS POLL STATUS ---
  if (req.method === 'GET') {
    return res.status(200).json(global.emergencyState);
  }

  // --- POST METHOD: ESP32-CAM SENDS IMAGE ---
  if (req.method === 'POST') {
    try {
      // Check for API key right away before running heavy code
      if (!process.env.GEMINI_API_KEY) {
        console.error("Missing GEMINI_API_KEY environment variable.");
        return res.status(500).json({ error: "Server Configuration Error: Missing API Key" });
      }

      const { imageBase64 } = req.body || {};

      if (!imageBase64) {
        return res.status(400).json({ error: 'No image data received in request body.' });
      }

      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

      const prompt = `
        Analyze this image from a traffic camera. Is there an emergency vehicle present (Ambulance, Fire Truck, or Police Car)?
        Respond strictly in this JSON format:
        {
          "isEmergency": true/false,
          "vehicleType": "ambulance" / "fire_truck" / "police" / "none"
        }
      `;

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
        config: { responseMimeType: "application/json" }
      });

      const result = JSON.parse(response.text);
      
      // Update state safely
      global.emergencyState = {
        isEmergency: !!result.isEmergency,
        vehicleType: result.vehicleType || 'none'
      };

      return res.status(200).json({ message: "Processed successfully", status: global.emergencyState });

    } catch (error) {
      console.error("Runtime Exception:", error);
      return res.status(500).json({ error: "Internal processing crash", details: error.message });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}