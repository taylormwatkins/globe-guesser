from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import firestore, credentials, db
import random
import os



app = Flask(__name__)
CORS(app)

# port = int(os.environ.get("PORT", 8080))
# app.run(host="0.0.0.0", port=port)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://globeguesser-56dad-default-rtdb.firebaseio.com/'
})


# convert database to list of countries
db = firestore.client()
countries_ref = db.collection('countries')
countries = countries_ref.stream()
countries_list = [country.to_dict() for country in countries]

# empty variable to hold target country
target_country = ""
    
# return a randomly selected country from the database
@app.route('/random_country', methods=['GET'])
def random_country():
    if countries_list:
        target_country = random.choice(countries_list)
        return target_country
    else:
        return jsonify({"error": "No countries found"}), 404
    


    
# check if guess is correct
@app.route('/check_guess', methods=['POST'])
def check_guess():

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
                response = {
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
                    
                response = {
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
            response = {
                'found': False,
                'message': f'Country not found in database',
            }
        return response, 200

    except Exception as e:
        print("Error processing request:", e)
        return jsonify({'error': 'Invalid input or server error'}), 400

    

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



if __name__ == '__main__':
    app.run(debug=True)