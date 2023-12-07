from flask import Flask, render_template, request
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import requests

app = Flask(__name__)

def geocode_address(address, api_key):
    geocode_url = f'https://rsapi.goong.io/geocode?address={address}&api_key={api_key}'
    response = requests.get(geocode_url)
    data = response.json()

    if response.status_code == 200 and data.get('results'):
        location = data['results'][0]['geometry']['location']
        return f"{location['lat']},{location['lng']}"
    else:
        return None

def get_distance_matrix(origin_address, destination_address, vehicle='bike', api_key=''):
    origin_coordinates = geocode_address(origin_address, api_key)
    destination_coordinates = geocode_address(destination_address, api_key)

    if origin_coordinates and destination_coordinates:
        url = f'https://rsapi.goong.io/DistanceMatrix?origins={origin_coordinates}&destinations={destination_coordinates}&vehicle={vehicle}&api_key={api_key}'

        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data.get('rows') and data['rows'][0].get('elements'):
            distance_value = data['rows'][0]['elements'][0]['distance']['value'] / 1000
            duration_value = data['rows'][0]['elements'][0]['duration']['value']

            return distance_value, duration_value
        else:
            print('Error fetching data.')
            return None, None
    else:
        print('Error geocoding addresses.')
        return None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        origin_address = request.form['origin_address']
        destination_address = request.form['destination_address']
        api_key = 'DQtdTTXPtWvtuxat9LuwjnKn5gg96SZXWTjfwYqQ'
        central_area = int(request.form['central_area'])
        running_time = int(request.form['running_time'])

        distance_value, duration_value = get_distance_matrix(origin_address, destination_address, api_key=api_key)

        if distance_value is not None and duration_value is not None:
            new_data = pd.DataFrame([[distance_value, central_area, running_time]], columns=['km', 'central_area', 'running_time'])
            predicted_fare = model.predict(new_data)[0]
            predicted_fare = max(predicted_fare, 0)
            predicted_fare = predicted_fare*1000
            predicted_fare = round(predicted_fare)
            # Append new_data to the existing CSV file
            new_data['fare'] = predicted_fare  # Add the predicted fare to the DataFrame
            dataluu = new_data
            with open('new_data.csv', 'a', newline='') as file:
                dataluu.to_csv(file, header=False, index=False)
                file.write('\n')  # Add a new line after each set of data
            return render_template('index.html', predicted_fare=predicted_fare, show_result=True)

        else:
            return render_template('index.html', show_error=True)

    return render_template('index.html')

if __name__ == '__main__':
    data = pd.read_csv('your_dataset.csv', skiprows=1, names=['km', 'central_area', 'running_time', 'fare'])
    data['km'] = pd.to_numeric(data['km'], errors='coerce')
    data['central_area'] = pd.to_numeric(data['central_area'], errors='coerce')
    data['running_time'] = pd.to_numeric(data['running_time'], errors='coerce')
    data = data.dropna()

    X = data[['km', 'central_area', 'running_time']]
    y = data['fare']

    model = make_pipeline(StandardScaler(), LinearRegression())
    model.fit(X, y)

    app.run(debug=True)
