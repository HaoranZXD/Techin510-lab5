import json
from dateutil.parser import parse
from db import get_db_conn
import logging

# Setup logging
logging.basicConfig(filename='insert_to_pg.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def insert_to_pg():
    q_create_table = '''
    CREATE TABLE IF NOT EXISTS events (
        url TEXT PRIMARY KEY,
        title TEXT,
        date TIMESTAMP WITH TIME ZONE,
        venue TEXT,
        category TEXT,
        location TEXT,
        latitude TEXT,
        longitude TEXT,
        condition TEXT,
        mintemperature FLOAT,
        maxtemperature FLOAT,
        windChill FLOAT
    );
    '''
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(q_create_table)
    
    urls = json.load(open('./data/links.json', 'r'))
    data = json.load(open('./data/data.json', 'r'))
    
    for url, row in zip(urls, data):
        try:
            # Check if weather data is a dictionary and contains the expected keys
            if isinstance(row['weather'], dict) and 'condition' in row['weather'] and 'temperature' in row['weather'] and 'windChill' in row['weather']:
                weather_condition = row['weather']['condition']
                mintemperature = row['weather']['temperature']
                maxtemperature = row['weather']['temperature']  # Assuming the same temperature for min and max
                windChill = row['weather']['windChill']
            else:
                # Default values for missing or incorrect weather data
                weather_condition = 'Not available'
                mintemperature = None
                maxtemperature = None
                windChill = None

            q_insert = '''
            INSERT INTO events (url, title, date, venue, category, location, latitude, longitude, condition, mintemperature, maxtemperature, windChill)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            '''
            cur.execute(q_insert, (
                url, 
                row['title'], 
                parse(row['date']), 
                row['venue'], 
                row['category'], 
                row['location'], 
                row['latitude'], 
                row['longitude'], 
                weather_condition, 
                mintemperature, 
                maxtemperature, 
                windChill
            ))
        except Exception as e:
            logging.error(f'Error processing URL {url}: {e}')

    conn.commit()  # Commit the transaction
    cur.close()
    conn.close()  # Close the database connection

if __name__ == '__main__':
    insert_to_pg()
