
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_functions import https_fn
import functions_framework
from firebase_admin import initialize_app
import random
from flask import Flask, jsonify
from flask_cors import CORS


app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": ["https://globeguesser-56dad.web.app/", "http://localhost:3000"]}}, supports_credentials=True)  #Supports_credentials for cookies

# Initialize Firebase Admin SDK 
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Convert Firestore collection to list of countries
countries_ref = db.collection('countries')  # Reference to 'countries' collection
countries = countries_ref.stream()  # Stream the documents
countries_list = [country.to_dict() for country in countries]  # Convert to list of dictionaries


# Empty variable to hold target country
target_country = ""

# Randomly select a country from the database
@https_fn.on_request()
def random_country(request):
    if countries_list:
        target_country = random.choice(countries_list)
        response = jsonify(target_country)
        response.headers['Access-Control-Allow-Origin'] = 'https://globeguesser-56dad.web.app'
        return response
    else:
        response = jsonify({"error": "No countries found"})
        response.status_code = 404 
        return response


@https_fn.on_request()
def check_guess(request):
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({})  
        response.headers['Access-Control-Allow-Origin'] = 'https://globeguesser-56dad.web.app'
        response.headers['Access-Control-Allow-Methods'] = 'POST' 
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type' 
        response.headers['Access-Control-Max-Age'] = '3600' # cache preflight for one hour
        return response
    
    
    try:
        # parse the incoming JSON request
        data = request.json

        # get the guess field
        guess = data.get('guess', '')  
        target = data.get('target', '')

        # search for the country by name in the list
        matching_guess = [country for country in countries_list if country.get('name', '').lower() == guess.lower()]
        matching_target = [country for country in countries_list if country.get('name', '').lower() == target.lower()]

        if matching_guess and matching_target:
            guessed_country = matching_guess[0]
            target_country = matching_target[0] 
            
            # if guess is the target country, return correct
            if guessed_country == target_country:
                response_data = {
                    'found': True,
                    'correct': True,
                    'message': 'You got it! The country is ' + target_country.get('name', ''),
                }
            else:
            # if guessed country isn't correct, calculate the comparisons
            # calculate directional difference
                direction = get_direction(guessed_country.get('latitude', ''), guessed_country.get('longitude', ''), target_country.get('latitude', ''), target_country.get('longitude', ''))

                if (guessed_country.get('continent', '') == target_country.get('continent', '')):
                    continent = "Yep"
                else:
                    continent = "Nope"
                    
                response_data = {
                    'found': True,
                    'correct': False,
                    'name': guessed_country.get('name', ''),
                    'co2_difference': (target_country.get('co2_emissions', '') - guessed_country.get('co2_emissions', '')),
                    'climate_difference': (target_country.get('climate', '') - guessed_country.get('climate', '')), 
                    'land_area_difference': (target_country.get('area', '') - guessed_country.get('area', '')),
                    'continent': continent,
                    'direction': direction
                }
        # if country isn't in database
        else:
            response_data = {
                'found': False,
                'message': f'Country not found in database',
            }
            
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = 'https://globeguesser-56dad.web.app'
        return response

    except Exception as e:
        print("Error processing request:", e)
        response.status_code = 400 
        return response
    

# calculate direction from guessed country to target
def get_direction(guessed_country_lat, guessed_country_lon, target_country_lat, target_country_lon):
    
    # helper function to convert coordinates to decimal number
    def convert_to_decimal(degree_str):
        degree, _, direction = degree_str.split()
        degree = int(degree)
        if direction in ['S', 'W']:
            degree = -degree
        return degree

    # calling helper function
    guessed_lat = convert_to_decimal(guessed_country_lat)
    guessed_lon = convert_to_decimal(guessed_country_lon)
    target_lat = convert_to_decimal(target_country_lat)
    target_lon = convert_to_decimal(target_country_lon)

    # find the difference in latitude and longitude
    lat_diff = target_lat - guessed_lat
    lon_diff = target_lon - guessed_lon

    if abs(lat_diff) > abs(lon_diff):
        lat_dir = "N" if lat_diff > 0 else "S"
        lon_dir = "E" if lon_diff > 0 else "W" if lon_diff != 0 else ""
    else:
        lat_dir = "N" if lat_diff > 0 else "S" if lat_diff != 0 else ""
        lon_dir = "E" if lon_diff > 0 else "W"

    # combine directions for more specific indications (like NE, SW)
    if lat_dir and lon_dir:
        direction = lat_dir + lon_dir
    else:
        direction = lat_dir if lat_dir else lon_dir

    
    return direction




    
if __name__ == "__main__":
    app.run(debug=True)