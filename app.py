import streamlit as st
import pandas.io.sql as sqlio
import altair as alt
import folium
from streamlit_folium import st_folium
import pandas as pd
import pytz

from db import conn_str

st.title("Seattle Events")

df = sqlio.read_sql_query("SELECT * FROM events", conn_str)

# Convert 'date' from string to datetime format for easier manipulation
df['date'] = pd.to_datetime(df['date'])

# Charts
## 1. Most common categories of events
st.header("Most Common Categories of Events")
chart1 = alt.Chart(df).mark_bar().encode(
    x=alt.X('count()', title='Number of Events'),
    y=alt.Y('category', sort='-x', title='Category')
).properties(
    width=700,
    height=400
)
st.altair_chart(chart1, use_container_width=True)

## 2. What month has the most number of events?
st.header("Events Distribution by Month")
df['month'] = df['date'].dt.month
chart2 = alt.Chart(df).mark_bar().encode(
    x=alt.X('month', title='Month'),
    y=alt.Y('count()', title='Number of Events')
).properties(
    width=700,
    height=400
)
st.altair_chart(chart2, use_container_width=True)

## 3. What day of the week has the most number of events?
st.header("Events Distribution by Day of the Week")
df['day_of_week'] = df['date'].dt.day_name()
chart3 = alt.Chart(df).mark_bar().encode(
    x=alt.X('day_of_week', title='Day of the Week', sort=alt.EncodingSortField(field="day_of_week", op="count", order='descending')),
    y=alt.Y('count()', title='Number of Events')
).properties(
    width=700,
    height=400
)
st.altair_chart(chart3, use_container_width=True)

## 4. Where are events often held? (Using latitude and longitude)
st.header("Event Locations")
# Assuming latitude and longitude are stored as strings, convert them to float. Handle conversion errors.
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
m = folium.Map(location=[47.6062, -122.3321], zoom_start=12)
for _, row in df.iterrows():
    if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
        folium.Marker([row['latitude'], row['longitude']], popup=row['title']).add_to(m)
st_folium(m, width=725, height=500)

# Seattle's timezone for date localization
seattle_tz = pytz.timezone('America/Los_Angeles')

# Controls
st.sidebar.header("Filters")

# Add an "All" option to the dropdowns
category_options = ["All"] + sorted(df['category'].dropna().unique().tolist())
location_options = ["All"] + sorted(df['location'].dropna().unique().tolist())
weather_options = ["All"] + sorted(df['condition'].dropna().unique().tolist())

# Dropdown to filter category
category = st.sidebar.selectbox("Select a category", options=category_options, index=0)

# Date range selector for event date
date_range = st.sidebar.date_input("Event Date Range", [])

# Dropdown to filter location
location = st.sidebar.selectbox("Select a location", options=location_options, index=0)

# Dropdown to filter weather
weather = st.sidebar.selectbox("Select weather condition", options=weather_options, index=0)

# Filtering logic
filtered_df = df
if category != "All":
    filtered_df = filtered_df[filtered_df['category'] == category]
if location != "All":
    filtered_df = filtered_df[filtered_df['location'] == location]
if weather != "All":
    filtered_df = filtered_df[filtered_df['condition'] == weather]
if date_range:
    start_date, end_date = date_range
    start_datetime = pd.Timestamp(start_date).tz_localize(seattle_tz)
    end_datetime = (pd.Timestamp(end_date) + pd.Timedelta(days=1)).tz_localize(seattle_tz) - pd.Timedelta(seconds=1)
    filtered_df = filtered_df[(filtered_df['date'] >= start_datetime) & (filtered_df['date'] <= end_datetime)]

# Display filtered DataFrame
st.write(filtered_df)