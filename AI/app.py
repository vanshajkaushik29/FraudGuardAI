from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from datetime import datetime
import pickle
from description_analyzer import analyzer

app = Flask(__name__)
CORS(app)

# Load original ML model
print("Loading fraud detection model...")
try:
    with open('model.pkl', 'rb') as f:
        model_data = pickle.load(f)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model_data = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'FraudGuard AI Service',
        'features': ['amount', 'location', 'time', 'description'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['amount', 'location', 'time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract features
        amount = float(data['amount'])
        location = data['location']
        timestamp = float(data['time'])
        description = data.get('description', '')
        
        # Convert time to features
        dt = datetime.fromtimestamp(timestamp / 1000)
        hour = dt.hour
        
        print(f"🔍 Analyzing: ₹{amount} at {location}, {hour}:00 - Desc: '{description}'")
        
        # Get description analysis
        desc_result = analyzer.predict(description, amount, hour)
        
        # Get original ML prediction (if model exists)
        original_fraud = False
        original_confidence = 0.3
        
        if model_data and 'location_encoder' in model_data:
            try:
                model = model_data['model']
                scaler = model_data['scaler']
                location_encoder = model_data['location_encoder']
                feature_names = model_data['feature_names']
                
                # Encode location
                try:
                    location_code = location_encoder.transform([location])[0]
                except:
                    location_code = len(location_encoder.classes_) // 2
                
                # Create feature vector
                features = pd.DataFrame([{
                    'amount': amount,
                    'location_code': location_code,
                    'hour': hour,
                    'day_of_week': dt.weekday(),
                    'is_weekend': 1 if dt.weekday() >= 5 else 0
                }])
                
                features = features[feature_names]
                features_scaled = scaler.transform(features)
                
                # Predict
                prediction = model.predict(features_scaled)[0]
                probabilities = model.predict_proba(features_scaled)[0]
                
                original_fraud = bool(prediction)
                original_confidence = float(probabilities[1]) if prediction == 1 else float(probabilities[0])
                
            except Exception as e:
                print(f"ML model error: {e}")
        
        # COMBINE PREDICTIONS
        # Weight: 60% original model, 40% description analysis
        combined_confidence = (
            original_confidence * 0.6 +
            desc_result['confidence'] * 0.4
        )
        
        # OVERRIDE RULES (These take priority)
        final_fraud = combined_confidence > 0.5
        final_confidence = combined_confidence
        
        # Rule: Healthcare is NEVER fraud
        if desc_result['features']['category'] == 'healthcare':
            final_fraud = False
            final_confidence = 0.05
            print("✅ Healthcare override - SAFE")
        
        # Rule: Transport at night with reasonable amount is SAFE (fixes cab problem!)
        if desc_result['features']['category'] == 'transport' and amount < 2000:
            final_fraud = False
            final_confidence = 0.1
            print("✅ Transport override - SAFE (cab/uber)")
        
        # Rule: Food delivery at night is SAFE
        if desc_result['features']['category'] == 'food' and amount < 1500:
            final_fraud = False
            final_confidence = 0.15
            print("✅ Food delivery override - SAFE")
        
        # Rule: High amount + fraud keywords = FRAUD
        if amount > 20000 and desc_result['features']['fraud_keyword_count'] >= 2:
            final_fraud = True
            final_confidence = 0.95
            print("🚨 High amount + fraud keywords - FRAUD")
        
        # Rule: Small amount + transport = always safe
        if amount < 1000 and desc_result['features']['category'] == 'transport':
            final_fraud = False
            final_confidence = 0.05
            
        # Rule: Small amount + food = always safe  
        if amount < 500 and desc_result['features']['category'] == 'food':
            final_fraud = False
            final_confidence = 0.05
        
        response = {
            'fraud': final_fraud,
            'confidence': round(final_confidence, 3),
            'description_analysis': desc_result,
            'original_prediction': {
                'fraud': original_fraud,
                'confidence': round(original_confidence, 3)
            }
        }
        
        print(f"📊 Result: {'🚨 FRAUD' if final_fraud else '✅ SAFE'} ({final_confidence:.1%})")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)