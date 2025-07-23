# app.py
from flask import Flask, request, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import math

try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    # Fallback distance calculation using Haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon/2) * math.sin(dLon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

app = Flask(__name__)

# Load and preprocess data
try:
    df = pd.read_csv('corn_data.csv')
    # Clean data - handle missing values
    df['Acreage'] = df['Acreage'].fillna(df['Acreage'].median())
    df['Fertilizer amount'] = df['Fertilizer amount'].fillna(df['Fertilizer amount'].median())

    # Feature engineering
    df['Yield_per_acre'] = df['Yield'] / df['Acreage']
    df['Surplus_score'] = df['Yield'] - (df['Household size'] * 50)  # Assuming 50kg per person annual need

    # Train yield prediction model
    X = df[['Acreage', 'Fertilizer amount', 'Laborers', 'Household size']]
    y = df['Yield']
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    joblib.dump(model, 'yield_model.pkl')
except Exception as e:
    print(f"Error during initialization: {str(e)}")
    df = pd.DataFrame()  # Empty dataframe as fallback

@app.route('/predict_yield', methods=['POST'])
def predict_yield():
    try:
        data = request.json
        model = joblib.load('yield_model.pkl')
        prediction = model.predict([[data['acreage'], data['fertilizer'], data['laborers'], data['household_size']]])
        return jsonify({'predicted_yield': prediction[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/find_surplus', methods=['GET'])
def find_surplus():
    try:
        surplus_farmers = df[df['Surplus_score'] > 0]
        surplus_farmers = surplus_farmers.sort_values('Surplus_score', ascending=False)
        return jsonify(surplus_farmers[['Farmer', 'Yield', 'Household size', 'Surplus_score', 'Latitude', 'Longitude']].to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/optimize_routes', methods=['POST'])
def optimize_routes():
    try:
        locations = request.json['locations']
        center = (-3.45, 38.35)  # Central point in Taita Taveta
        
        if GEOPY_AVAILABLE:
            locations.sort(key=lambda loc: geodesic(center, (loc['lat'], loc['lon'])).km)
        else:
            locations.sort(key=lambda loc: haversine(center[0], center[1], loc['lat'], loc['lon']))
            
        return jsonify({'optimized_route': locations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)