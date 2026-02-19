import re

class DescriptionFraudAnalyzer:
    def __init__(self):
        # Fraudulent keywords (scams)
        self.fraud_keywords = [
            'urgent', 'verify', 'account', 'claim', 'prize', 'lottery',
            'inheritance', 'prince', 'wire', 'overseas', 'cryptocurrency',
            'bitcoin', 'gift card', 'western union', 'money gram', 'confirm',
            'security', 'bank details', 'password', 'otp', 'winning',
            'congratulations', 'selected', 'award', 'million', 'billion',
            'transfer to unknown', 'suspicious', 'verify now', 'action required'
        ]
        
        # Legitimate keywords (safe transactions)
        self.legitimate_keywords = [
            'uber', 'ola', 'rapido', 'taxi', 'cab', 'auto',  # Transport
            'swiggy', 'zomato', 'restaurant', 'cafe', 'dinner', 'lunch', 'breakfast', 'food',  # Food
            'amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'mall',  # Shopping
            'bigbasket', 'grofers', 'zepto', 'blinkit', 'grocery',  # Grocery
            'netflix', 'prime', 'hotstar', 'sony liv', 'spotify', 'youtube',  # Entertainment
            'electricity', 'water', 'gas', 'bill', 'rent', 'maintenance',  # Bills
            'hospital', 'clinic', 'doctor', 'medicine', 'pharmacy', 'medical',  # Healthcare
            'school', 'college', 'university', 'fees', 'tuition', 'education',  # Education
            'salary', 'emi', 'loan', 'insurance',  # Financial
            'petrol', 'fuel', 'toll', 'parking', 'metro', 'bus', 'train'  # Travel
        ]
        
        # Merchant category mapping
        self.merchant_categories = {
            'transport': ['uber', 'ola', 'taxi', 'cab', 'auto', 'rapido', 'metro', 'bus', 'train'],
            'food': ['swiggy', 'zomato', 'restaurant', 'cafe', 'pizza', 'burger', 'food'],
            'shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'mall', 'shopping'],
            'grocery': ['bigbasket', 'grofers', 'zepto', 'blinkit', 'grocery'],
            'entertainment': ['netflix', 'prime', 'hotstar', 'spotify', 'youtube'],
            'bills': ['electricity', 'water', 'gas', 'bill', 'rent', 'maintenance'],
            'healthcare': ['hospital', 'clinic', 'doctor', 'medicine', 'pharmacy', 'medical'],
            'education': ['school', 'college', 'university', 'tuition', 'fees'],
            'travel': ['petrol', 'fuel', 'toll', 'parking', 'flight', 'hotel']
        }
    
    def extract_features(self, description):
        """Extract features from transaction description"""
        if not description or not isinstance(description, str):
            return {
                'desc_length': 0,
                'word_count': 0,
                'fraud_keyword_count': 0,
                'legit_keyword_count': 0,
                'has_numbers': 0,
                'has_special_chars': 0,
                'is_all_caps': 0,
                'category': 'unknown'
            }
        
        description_lower = description.lower()
        words = description_lower.split()
        
        features = {
            'desc_length': len(description),
            'word_count': len(words),
            'fraud_keyword_count': 0,
            'legit_keyword_count': 0,
            'has_numbers': 1 if re.search(r'\d+', description) else 0,
            'has_special_chars': 1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', description) else 0,
            'is_all_caps': 1 if description.isupper() and len(description) > 3 else 0,
            'category': 'unknown'
        }
        
        # Count keywords
        for kw in self.fraud_keywords:
            if kw in description_lower:
                features['fraud_keyword_count'] += 1
        
        for kw in self.legitimate_keywords:
            if kw in description_lower:
                features['legit_keyword_count'] += 1
        
        # Determine category
        for category, keywords in self.merchant_categories.items():
            if any(kw in description_lower for kw in keywords):
                features['category'] = category
                break
        
        return features
    
    def predict(self, description, amount, hour):
        """Predict fraud based on description + amount + time"""
        features = self.extract_features(description)
        
        # Base fraud score
        fraud_score = 0.0
        reasons = []
        
        # Rule 1: Fraud keywords increase score
        if features['fraud_keyword_count'] > 0:
            fraud_score += min(0.3, features['fraud_keyword_count'] * 0.15)
            reasons.append(f"⚠️ Contains {features['fraud_keyword_count']} suspicious keyword(s)")
        
        # Rule 2: Legitimate keywords decrease score
        if features['legit_keyword_count'] > 0:
            fraud_score -= min(0.4, features['legit_keyword_count'] * 0.1)
            reasons.append(f"✅ Contains {features['legit_keyword_count']} legitimate keyword(s)")
        
        # Rule 3: ALL CAPS text (scammy)
        if features['is_all_caps']:
            fraud_score += 0.2
            reasons.append("⚠️ Message in ALL CAPS")
        
        # Rule 4: Transport at night is SAFE (solves cab problem!)
        if features['category'] == 'transport':
            fraud_score = max(0, fraud_score - 0.4)
            reasons.append("✅ Transportation expense")
            if hour < 6:
                reasons.append("   • Late night transport is normal (cab/uber)")
        
        # Rule 5: Healthcare is ALWAYS safe
        if features['category'] == 'healthcare':
            fraud_score = max(0, fraud_score - 0.5)
            reasons.append("✅ Healthcare expense - legitimate")
        
        # Rule 6: Food delivery at night is normal
        if features['category'] == 'food' and amount < 1000:
            fraud_score = max(0, fraud_score - 0.3)
            reasons.append("✅ Food delivery expense")
        
        # Rule 7: High amount + no description = risky
        if amount > 10000 and features['word_count'] == 0:
            fraud_score += 0.25
            reasons.append("⚠️ High amount with no description")
        
        # Rule 8: Bills and education are safe
        if features['category'] in ['bills', 'education']:
            fraud_score = max(0, fraud_score - 0.3)
            reasons.append(f"✅ Regular {features['category']} payment")
        
        # Rule 9: Small amount + transport = always safe
        if amount < 1000 and features['category'] == 'transport':
            fraud_score = 0.05
            reasons = ["✅ Small transport expense - completely safe"]
        
        # Rule 10: Hospital at any time = safe
        if features['category'] == 'healthcare':
            fraud_score = 0.05
            reasons = ["✅ Medical expense - completely safe"]
        
        # Clamp between 0 and 1
        fraud_score = max(0, min(1, fraud_score))
        
        # Determine if fraud
        is_fraud = fraud_score > 0.5
        
        return {
            'is_fraud': is_fraud,
            'confidence': fraud_score,
            'features': features,
            'reasons': reasons
        }

# Create global instance
analyzer = DescriptionFraudAnalyzer()