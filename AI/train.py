import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle
import os
from datetime import datetime

# Generate synthetic training data
def generate_training_data(n_samples=10000):
    np.random.seed(42)
    
    # Generate features
    amounts = np.random.exponential(100, n_samples)
    amounts = np.clip(amounts, 1, 10000)
    
    # Locations with different risk profiles
    locations = ['NY', 'LA', 'CHI', 'HOU', 'PHX', 'PHL', 'SA', 'SD', 'DAL', 'SJ']
    location_risk = {'NY': 0.3, 'LA': 0.4, 'CHI': 0.2, 'HOU': 0.3, 'PHX': 0.2,
                     'PHL': 0.3, 'SA': 0.2, 'SD': 0.1, 'DAL': 0.2, 'SJ': 0.1}
    
    # Times (in milliseconds since epoch, normalized)
    current_time = datetime.now().timestamp() * 1000
    times = np.random.uniform(current_time - 30*24*60*60*1000, current_time, n_samples)
    
    # Create location codes
    location_encoder = LabelEncoder()
    location_codes = location_encoder.fit_transform([np.random.choice(locations) for _ in range(n_samples)])
    
    # Generate fraud labels based on rules
    labels = []
    for i in range(n_samples):
        fraud_prob = 0.05  # base fraud rate
        
        # High amount increases fraud probability
        if amounts[i] > 500:
            fraud_prob += 0.2
        if amounts[i] > 1000:
            fraud_prob += 0.3
            
        # Location affects fraud probability
        location = location_encoder.inverse_transform([location_codes[i]])[0]
        fraud_prob += location_risk.get(location, 0.1)
        
        # Time features (late night transactions are riskier)
        hour = datetime.fromtimestamp(times[i] / 1000).hour
        if hour < 6 or hour > 23:
            fraud_prob += 0.15
            
        labels.append(1 if np.random.random() < min(fraud_prob, 0.95) else 0)
    
    # Create feature matrix
    X = pd.DataFrame({
        'amount': amounts,
        'location_code': location_codes,
        'hour': [datetime.fromtimestamp(t / 1000).hour for t in times],
        'day_of_week': [datetime.fromtimestamp(t / 1000).weekday() for t in times],
        'is_weekend': [1 if datetime.fromtimestamp(t / 1000).weekday() >= 5 else 0 for t in times]
    })
    
    return X, np.array(labels), location_encoder

print("Generating training data...")
X, y, location_encoder = generate_training_data(20000)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Training Random Forest model...")
# Train Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

# Evaluate model
train_score = model.score(X_train_scaled, y_train)
test_score = model.score(X_test_scaled, y_test)

print(f"Training accuracy: {train_score:.3f}")
print(f"Test accuracy: {test_score:.3f}")

# Save model and preprocessors
print("Saving model and preprocessors...")
with open('model.pkl', 'wb') as f:
    pickle.dump({
        'model': model,
        'scaler': scaler,
        'location_encoder': location_encoder,
        'feature_names': X.columns.tolist()
    }, f)

print("Model training complete!")