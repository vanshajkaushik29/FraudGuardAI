
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

# ============================================
# THRESHOLDS AND RULES CONFIGURATION
# ============================================

THRESHOLDS = {
    # Amount thresholds (in ₹)
    'EXTREME_AMOUNT': 200000,      # > ₹2,00,000 = automatic FRAUD
    'VERY_HIGH_AMOUNT': 100000,     # > ₹1,00,000 = high risk
    'HIGH_AMOUNT': 50000,           # > ₹50,000 = medium-high risk
    'MEDIUM_AMOUNT': 25000,         # > ₹25,000 = needs scrutiny
    'LOW_AMOUNT': 10000,            # < ₹10,000 = generally safe
    
    # Time thresholds (hour in 24h format)
    'LATE_NIGHT_START': 0,           # 12:00 AM
    'LATE_NIGHT_END': 5,             # 5:00 AM
    'EARLY_MORNING_END': 7,          # 7:00 AM
    'EVENING_START': 22,              # 10:00 PM
    
    # Confidence thresholds
    'FRAUD_CONFIDENCE_HIGH': 0.85,    # 85% - definite fraud
    'FRAUD_CONFIDENCE_MEDIUM': 0.75,  # 75% - likely fraud
    'FRAUD_CONFIDENCE_LOW': 0.60,     # 60% - suspicious
    'SAFE_CONFIDENCE_HIGH': 0.90,     # 90% - definite safe
    'SAFE_CONFIDENCE_MEDIUM': 0.70,   # 70% - likely safe
    
    # Risk multipliers
    'LATE_NIGHT_RISK': 0.3,           # +30% risk for late night
    'NO_DESCRIPTION_RISK': 0.25,      # +25% risk for no description
    'SUSPICIOUS_KEYWORD_RISK': 0.4,   # +40% risk for suspicious words
    'URGENT_KEYWORD_RISK': 0.35,      # +35% risk for urgency words
    
    # Safety overrides
    'HEALTHCARE_MAX_SAFE': 100000,    # Healthcare transactions up to ₹1L can be safe
    'TRANSPORT_MAX_SAFE': 5000,       # Transport up to ₹5,000 is safe
    'FOOD_MAX_SAFE': 3000,            # Food up to ₹3,000 is safe
    'BILLS_MAX_SAFE': 50000,          # Bills up to ₹50,000 are safe
}

# Keywords that indicate FRAUD
SUSPICIOUS_KEYWORDS = [
    'urgent', 'verify', 'account', 'claim', 'prize', 'lottery',
    'inheritance', 'prince', 'wire', 'overseas', 'cryptocurrency',
    'bitcoin', 'gift card', 'western union', 'money gram', 'confirm',
    'security', 'bank details', 'password', 'otp', 'winning',
    'congratulations', 'selected', 'award', 'million', 'billion',
    'transfer to unknown', 'verify now', 'action required', 'click here',
    'limited time', 'expires today', 'last chance', 'act now'
]

# Keywords that indicate SAFE transactions
SAFE_KEYWORDS = {
    'healthcare': ['hospital', 'apollo', 'max', 'fortis', 'aiims', 'clinic', 'doctor', 'medicine', 'pharmacy', 'medical', 'health', 'dental', 'eye', 'chemist'],
    'transport': ['uber', 'ola', 'rapido', 'taxi', 'cab', 'auto', 'metro', 'bus', 'train', 'flight', 'petrol', 'fuel', 'toll'],
    'food': ['swiggy', 'zomato', 'restaurant', 'cafe', 'dinner', 'lunch', 'breakfast', 'food', 'pizza', 'burger', 'mcdonalds', 'dominos'],
    'bills': ['electricity', 'water', 'gas', 'bill', 'rent', 'maintenance', 'society', 'broadband', 'internet', 'phone'],
    'education': ['school', 'college', 'university', 'tuition', 'fees', 'education', 'class'],
    'shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'mall', 'store'],
    'grocery': ['bigbasket', 'grofers', 'zepto', 'blinkit', 'grocery', 'vegetables', 'milk'],
    'entertainment': ['netflix', 'prime', 'hotstar', 'sony liv', 'spotify', 'youtube', 'movie', 'cinema']
}

# Emergency services (these can be trusted even at night)
EMERGENCY_SERVICES = ['hospital', 'ambulance', 'police', 'fire', 'emergency']

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'FraudGuard AI Service',
        'thresholds': THRESHOLDS,
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
        description = data.get('description', '').strip()
        
        # Convert time to features
        dt = datetime.fromtimestamp(timestamp / 1000)
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        print(f"\n{'='*60}")
        print(f"🔍 ANALYZING TRANSACTION")
        print(f"{'='*60}")
        print(f"💰 Amount: ₹{amount:,.2f}")
        print(f"📍 Location: {location}")
        print(f"⏰ Time: {hour:02d}:00 ({'LATE NIGHT' if hour < 5 or hour > 23 else 'DAYTIME'})")
        print(f"📝 Description: '{description if description else 'NO DESCRIPTION'}'")
        
        # Get description analysis
        desc_result = analyzer.predict(description, amount, hour)
        
        # Get original ML prediction
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
                    'day_of_week': day_of_week,
                    'is_weekend': is_weekend
                }])
                
                features = features[feature_names]
                features_scaled = scaler.transform(features)
                
                # Predict
                prediction = model.predict(features_scaled)[0]
                probabilities = model.predict_proba(features_scaled)[0]
                
                original_fraud = bool(prediction)
                original_confidence = float(probabilities[1]) if prediction == 1 else float(probabilities[0])
                
                print(f"🤖 ML Model: {'🚨 FRAUD' if original_fraud else '✅ SAFE'} ({original_confidence:.1%})")
                
            except Exception as e:
                print(f"⚠️ ML model error: {e}")
        
        # ============================================
        # ENHANCED FRAUD DETECTION LOGIC
        # ============================================
        
        reasons = []
        fraud_score = original_confidence
        is_fraud = original_fraud
        
        # Check if description has suspicious keywords
        suspicious_count = 0
        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword in description.lower():
                suspicious_count += 1
                reasons.append(f"⚠️ Suspicious keyword: '{keyword}'")
        
        # Check if description has safe keywords
        safe_category = None
        for category, keywords in SAFE_KEYWORDS.items():
            if any(kw in description.lower() for kw in keywords):
                safe_category = category
                reasons.append(f"✅ Recognized as: {category}")
                break
        
        # Check if it's an emergency service
        is_emergency = any(emergency in description.lower() for emergency in EMERGENCY_SERVICES)
        if is_emergency:
            reasons.append(f"🏥 Emergency service detected")
        
        # ============================================
        # RULE 1: EXTREME AMOUNT (> ₹2,00,000)
        # ============================================
        if amount > THRESHOLDS['EXTREME_AMOUNT']:
            is_fraud = True
            fraud_score = max(fraud_score, THRESHOLDS['FRAUD_CONFIDENCE_HIGH'])
            reasons.append(f"🚨 EXTREME AMOUNT: ₹{amount:,.2f} (> ₹2,00,000)")
            print(f"🚨 RULE 1 TRIGGERED: Extreme amount")
        
        # ============================================
        # RULE 2: VERY HIGH AMOUNT (> ₹1,00,000) + LATE NIGHT
        # ============================================
        elif amount > THRESHOLDS['VERY_HIGH_AMOUNT'] and (hour < THRESHOLDS['LATE_NIGHT_END'] or hour > THRESHOLDS['EVENING_START']):
            is_fraud = True
            fraud_score = max(fraud_score, THRESHOLDS['FRAUD_CONFIDENCE_MEDIUM'])
            reasons.append(f"🚨 Very high amount (₹{amount:,.2f}) during late night")
            print(f"🚨 RULE 2 TRIGGERED: High amount + late night")
        
        # ============================================
        # RULE 3: HIGH AMOUNT (> ₹50,000) + SUSPICIOUS KEYWORDS
        # ============================================
        elif amount > THRESHOLDS['HIGH_AMOUNT'] and suspicious_count > 0:
            is_fraud = True
            fraud_score = max(fraud_score, THRESHOLDS['FRAUD_CONFIDENCE_MEDIUM'])
            reasons.append(f"🚨 High amount + {suspicious_count} suspicious keyword(s)")
            print(f"🚨 RULE 3 TRIGGERED: High amount + suspicious keywords")
        
        # ============================================
        # RULE 4: HIGH AMOUNT (> ₹50,000) + NO DESCRIPTION
        # ============================================
        elif amount > THRESHOLDS['HIGH_AMOUNT'] and not description:
            is_fraud = True
            fraud_score = max(fraud_score, THRESHOLDS['FRAUD_CONFIDENCE_LOW'])
            reasons.append(f"⚠️ High amount with no description")
            print(f"⚠️ RULE 4 TRIGGERED: High amount + no description")
        
        # ============================================
        # RULE 5: MEDIUM AMOUNT (> ₹25,000) + LATE NIGHT + SUSPICIOUS
        # ============================================
        elif amount > THRESHOLDS['MEDIUM_AMOUNT'] and (hour < THRESHOLDS['LATE_NIGHT_END'] or hour > THRESHOLDS['EVENING_START']) and suspicious_count > 0:
            is_fraud = True
            fraud_score = max(fraud_score, THRESHOLDS['FRAUD_CONFIDENCE_LOW'])
            reasons.append(f"⚠️ Medium amount + late night + suspicious keywords")
            print(f"⚠️ RULE 5 TRIGGERED: Medium amount + late night + suspicious")
        
        # ============================================
        # RULE 6: HEALTHCARE OVERRIDE (with limits)
        # ============================================
        if safe_category == 'healthcare' or is_emergency:
            # Check if it's genuine healthcare with reasonable amount
            if amount <= THRESHOLDS['HEALTHCARE_MAX_SAFE']:
                # Genuine healthcare - SAFE
                is_fraud = False
                fraud_score = min(fraud_score, 0.1)
                reasons.append(f"✅ Genuine healthcare expense (₹{amount:,.2f})")
                print(f"✅ RULE 6: Healthcare override - SAFE")
            else:
                # Healthcare claim but amount too high - still FRAUD
                is_fraud = True
                fraud_score = max(fraud_score, 0.7)
                reasons.append(f"🚨 Healthcare claim but amount too high: ₹{amount:,.2f}")
                print(f"🚨 RULE 6: Healthcare claim but amount exceeds limit")
        
        # ============================================
        # RULE 7: TRANSPORT OVERRIDE (Uber/Ola safe at any time)
        # ============================================
        elif safe_category == 'transport':
            if amount <= THRESHOLDS['TRANSPORT_MAX_SAFE']:
                # Normal transport - SAFE
                is_fraud = False
                fraud_score = min(fraud_score, 0.1)
                reasons.append(f"✅ Transport expense (cab/uber)")
                print(f"✅ RULE 7: Transport override - SAFE")
            else:
                # Transport but amount too high - suspicious
                reasons.append(f"⚠️ Transport expense with unusually high amount")
                print(f"⚠️ RULE 7: Transport but amount high - keeping ML prediction")
        
        # ============================================
        # RULE 8: FOOD DELIVERY OVERRIDE
        # ============================================
        elif safe_category == 'food':
            if amount <= THRESHOLDS['FOOD_MAX_SAFE']:
                is_fraud = False
                fraud_score = min(fraud_score, 0.1)
                reasons.append(f"✅ Food delivery expense")
                print(f"✅ RULE 8: Food override - SAFE")
        
        # ============================================
        # RULE 9: BILLS OVERRIDE
        # ============================================
        elif safe_category == 'bills':
            if amount <= THRESHOLDS['BILLS_MAX_SAFE']:
                is_fraud = False
                fraud_score = min(fraud_score, 0.15)
                reasons.append(f"✅ Bill payment")
                print(f"✅ RULE 9: Bills override - SAFE")
        
        # ============================================
        # RULE 10: SUSPICIOUS KEYWORDS (even with safe categories)
        # ============================================
        if suspicious_count >= 2:
            is_fraud = True
            fraud_score = max(fraud_score, 0.8)
            reasons.append(f"🚨 Multiple suspicious keywords detected")
            print(f"🚨 RULE 10: Multiple suspicious keywords - FORCING FRAUD")
        
        # ============================================
        # FINAL SAFETY CHECKS
        # ============================================
        
        # Cap confidence between 0 and 1
        fraud_score = max(0, min(1, fraud_score))
        
        # Very small amounts (< ₹1000) are almost never fraud
        if amount < 1000 and not is_fraud:
            fraud_score = min(fraud_score, 0.1)
        
        # Log final decision
        print(f"\n{'='*60}")
        print(f"📊 FINAL DECISION")
        print(f"{'='*60}")
        print(f"Result: {'🚨 FRAUD' if is_fraud else '✅ SAFE'}")
        print(f"Confidence: {fraud_score:.1%}")
        print(f"Reasons:")
        for reason in reasons[-3:]:  # Show last 3 reasons
            print(f"  • {reason}")
        print(f"{'='*60}\n")
        
        # Prepare response
        response = {
            'fraud': is_fraud,
            'confidence': round(fraud_score, 3),
            'description_analysis': {
                'reasons': reasons,
                'features': desc_result.get('features', {}),
                'category': safe_category
            },
            'original_prediction': {
                'fraud': original_fraud,
                'confidence': round(original_confidence, 3)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🚀 FraudGuard AI Service Starting...")
    print(f"📊 Active Thresholds:")
    for key, value in THRESHOLDS.items():
        print(f"   • {key}: {value}")
    print("\n" + "="*60)
    app.run(host='0.0.0.0', port=5001, debug=True)

