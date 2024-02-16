import re
import json
import datetime
from zoneinfo import ZoneInfo
import html

import requests



URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'

def list_links():
    res = requests.get(URL + '1/')
    last_page_no = int(re.findall(r'bpn-last-page-link"><a href=".+?/page/(\d+?)/.+" title="Navigate to last page">', res.text)[0])

    links = []
    for page_no in range(1, last_page_no + 1):
        res = requests.get(URL + str(page_no) + '/')
        links.extend(re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">.+?</a></h3>', res.text))

    json.dump(links, open(URL_LIST_FILE, 'w'))

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        try:
            row = {}
            res = requests.get(link)
            row['title'] = html.unescape(re.findall(r'<h1 class="page-title" itemprop="headline">(.+?)</h1>', res.text)[0])
            datetime_venue = re.findall(r'<h4><span>(.+?)</span> \| <span>(.+?)</span></h4>', res.text)[0]
            row['date'] = datetime_venue[0]            
            row['venue'] = datetime_venue[1].strip() # remove leading/trailing whitespaces
            metas = re.findall(r'<a href=".+?" class="button big medium black category">(.+?)</a>', res.text)
            row['category'] = html.unescape(metas[0])
            row['location'] = metas[1]
            data.append(row)
        except IndexError as e:
            print(f'Error: {e}')
            print(f'Link: {link}')
    json.dump(data, open(URL_DETAIL_FILE, 'w'))

def update_geolocation():
    def geocode_location(location):
        base_url = "https://nominatim.openstreetmap.org/search.php"
        params = {
            "q": location,
            "format": "jsonv2"
        }
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200 and len(response.json()) > 0:
                data = response.json()[0]
                return data['lat'], data['lon']
            else:
                return 'N/A', 'N/A'
        except Exception as e:
            print(f"Error fetching location data for {location}: {e}")
            return 'Error', 'Error'

    # Load the data.json file
    with open(URL_DETAIL_FILE, 'r') as file:
        data = json.load(file)

    # Update each row with latitude and longitude
    for row in data:
        if 'venue' in row and row['venue'] not in ['N/A', 'Error', '']:  # Check if venue exists and is valid
            lat, lon = geocode_location(row['venue'])
            row['latitude'] = lat
            row['longitude'] = lon

    # Save the updated data back to the same JSON file
    with open(URL_DETAIL_FILE, 'w') as file:
        json.dump(data, file, indent=4)

    
# Function to parse the event date and return the last date if it's a range
def parse_event_date(date_str):
    # Handle special cases like "Ongoing"
    if date_str.lower() == 'ongoing':
        # Return today's date for ongoing events
        return datetime.today()
    elif 'through' in date_str:
        # Parse the last date from the range "Now through MM/DD/YYYY"
        last_date_str = date_str.split(' ')[-1]
    else:
        last_date_str = date_str
    
    try:
        # Convert to datetime object
        return datetime.strptime(last_date_str, "%m/%d/%Y")
    except ValueError:
        # Handle other unexpected formats
        print(f"Unrecognized date format: {date_str}")
        # Return a default date or handle as needed
        return datetime.today()  # Or any other default date
    
def insert_date():
    with open(URL_DETAIL_FILE, 'r') as file:
        data = json.load(file)
    
    
    for row in data:
        event_date = parse_event_date(row['date'])
        event_date = event_date.replace(tzinfo=ZoneInfo('America/Los_Angeles'))
        row['date'] = event_date.isoformat()
    
    with open(URL_DETAIL_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def get_wind_chill(temperature, wind_speed):
    """
    Calculate wind chill based on temperature (F) and wind speed (mph).
    Applicable for temperatures at or below 50°F and wind speeds above 3 mph.
    """
    if temperature <= 50 and wind_speed > 3:
        wind_chill = 35.74 + (0.6215 * temperature) - 35.75 * (wind_speed ** 0.16) + (0.4275 * temperature * (wind_speed ** 0.16))
        return round(wind_chill, 2)
    else:
        return None

def parse_wind_speed(wind_speed_str):
    """
    Parse wind speed string to extract the average wind speed in mph.
    """
    parts = wind_speed_str.split()
    if "to" in wind_speed_str:
        low, high = map(int, parts[0::2])
        return (low + high) / 2
    else:
        return int(parts[0])    
    
def get_short_forecast(latitude, longitude, event_date):
    formatted_date = event_date.strftime("%Y-%m-%d")
    weather_api_url = f"http://api.weather.gov/points/{latitude},{longitude}"
    try:
        res = requests.get(weather_api_url)
        res.raise_for_status()
        forecast_url = res.json().get('properties', {}).get('forecast')
        if forecast_url:
            forecast_res = requests.get(forecast_url)
            forecast_res.raise_for_status()
            forecasts = forecast_res.json().get('properties', {}).get('periods', [])
            for forecast in forecasts:
                if formatted_date in forecast['startTime']:
                    condition = forecast['shortForecast']
                    temperature = forecast['temperature']
                    wind_speed_str = forecast['windSpeed']
                    wind_speed = parse_wind_speed(wind_speed_str)
                    wind_chill = get_wind_chill(temperature, wind_speed)
                    return {
                        'condition': condition,
                        'temperature': temperature,
                        'windChill': wind_chill
                    }
            return 'Weather forecast not available'
        else:
            return 'Forecast URL not found'
    except requests.exceptions.RequestException as e:
        return f'Error fetching weather data: {e}'

def get_weather_forecast():
    with open(URL_DETAIL_FILE, 'r') as file:
        data = json.load(file)
    
    for row in data:
        event_date = parse_event_date(row['date'])
        if row['latitude'] != 'N/A' and row['longitude'] != 'N/A':
            weather_forecast = get_short_forecast(row['latitude'], row['longitude'], event_date)
            row['weather'] = weather_forecast
        else:
            row['weather'] = 'Location not available'
    
    with open(URL_DETAIL_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    


if __name__ == '__main__':
    list_links()
    get_detail_page()
    update_geolocation()
    insert_date()
    get_weather_forecast()