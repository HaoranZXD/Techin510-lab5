# Techin510-lab5
An interactive data visualization app for events in Seattle using Streamlit. This app allows users to explore various events happening around Seattle through dynamic charts and filters, providing insights into event categories, dates, locations, and weather conditions.

## How to Run

To run this app, follow these steps in your terminal:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py
```

## What's Included

- `app.py`: The main application file containing Streamlit code to render the app and handle user interactions.
- `requirements.txt`: A list of Python package dependencies required to run the app.

## How It Works

- The app queries a PostgreSQL database for event data, then uses Pandas for data manipulation and filtering based on user selections.
- Altair is utilized for generating charts, while Folium handles the mapping of event locations.

## Lessons Learned

- Gained practical experience in building interactive web apps with Streamlit, showcasing the power of Python in data manipulation and visualization.
- Developed proficiency in integrating Python with SQL databases to fetch and display data dynamically.
- Learned to use Folium for mapping and Altair for chart creation, enhancing the app's interactivity and user engagement.
- Explored advanced Streamlit features, such as sidebar controls and dynamic chart updates, to create a responsive and user-friendly interface.

## Questions

- How can we optimize SQL queries for performance in Streamlit apps, especially when dealing with large datasets?
- What are the best practices for deploying Streamlit apps in production environments, ensuring scalability and security?
- How can we incorporate machine learning models into Streamlit apps to predict future trends in event data?
