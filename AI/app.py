from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load model and preprocessors
print("Loading model...")
with open('model.pkl', 'rb') as f:
    model_data = pickle.load(f)
    
model = model_data['model']
scaler = model_data['scaler']
location_encoder = model_data['location_encoder']
feature_names = model_data['feature_names']

print("Model loaded successfully!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'FraudGuard AI Service',
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
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract features
        amount = float(data['amount'])
        location = data['location']
        timestamp = float(data['time'])
        
        # Convert time to features
        dt = datetime.fromtimestamp(timestamp / 1000)
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Encode location
        try:
            location_code = location_encoder.transform([location])[0]
        except:
            # If location not seen in training, use median code
            location_code = len(location_encoder.classes_) // 2
        
        # Create feature vector
        features = pd.DataFrame([{
            'amount': amount,
            'location_code': location_code,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend
        }])
        
        # Ensure correct feature order
        features = features[feature_names]
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make prediction
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        # Get confidence score
        confidence = float(probabilities[1]) if prediction == 1 else float(probabilities[0])
        
        response = {
            'fraud': bool(prediction),
            'confidence': confidence,
            'features_used': feature_names,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/batch-predict', methods=['POST'])
def batch_predict():
    try:
        data = request.get_json()
        
        if 'transactions' not in data:
            return jsonify({'error': 'Missing transactions array'}), 400
            
        transactions = data['transactions']
        results = []
        
        for transaction in transactions:
            try:
                amount = float(transaction['amount'])
                location = transaction['location']
                timestamp = float(transaction['time'])
                
                dt = datetime.fromtimestamp(timestamp / 1000)
                hour = dt.hour
                day_of_week = dt.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                
                try:
                    location_code = location_encoder.transform([location])[0]
                except:
                    location_code = len(location_encoder.classes_) // 2
                
                features = pd.DataFrame([{
                    'amount': amount,
                    'location_code': location_code,
                    'hour': hour,
                    'day_of_week': day_of_week,
                    'is_weekend': is_weekend
                }])
                
                features = features[feature_names]
                features_scaled = scaler.transform(features)
                
                prediction = model.predict(features_scaled)[0]
                probabilities = model.predict_proba(features_scaled)[0]
                confidence = float(probabilities[1]) if prediction == 1 else float(probabilities[0])
                
                results.append({
                    'transaction_id': transaction.get('id', len(results)),
                    'fraud': bool(prediction),
                    'confidence': confidence
                })
            except Exception as e:
                results.append({
                    'transaction_id': transaction.get('id', len(results)),
                    'error': str(e)
                })
        
        return jsonify({
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)