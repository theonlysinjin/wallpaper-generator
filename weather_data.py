"""
How to run this script:

1. With prompt generation:
   python weather_data.py --city "City Name"

2. Without prompt generation (weather data only):
   python weather_data.py --city "City Name" --no-prompt

3. With forecast:
   python weather_data.py --city "City Name" --forecast

Replace "City Name" with the name of the city you want to fetch weather data for.
"""

import requests
import argparse
from openai import OpenAI
import json
import configparser
import os
from datetime import datetime, timezone

def fetch_weather(city, use_forecast=False):
    """Fetch current weather data for a specified city using Open-Meteo API."""
    base_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        location_data = response.json()
        
        if location_data["results"]:
            lat = location_data["results"][0]["latitude"]
            lon = location_data["results"][0]["longitude"]
            
            weather_url = f"https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "temperature_unit": "celsius",
                "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
                "timezone": "auto",
                "forecast_days": 1
            }
            
            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            if use_forecast:
                forecast_weather = {
                    "temperature_min": weather_data['daily']['temperature_2m_min'][0],
                    "temperature_max": weather_data['daily']['temperature_2m_max'][0],
                    "weathercode": weather_data['daily']['weathercode'][0],
                    "country": location_data['results'][0]['country'],
                    "season": get_astronomical_season(datetime.now(timezone.utc), lat)
                }
                forecast_weather['weather_description'] = get_weather_description(forecast_weather['weathercode'])
                return forecast_weather
            else:
                current_weather = weather_data['current_weather']
                current_weather['country'] = location_data['results'][0]['country']
                current_weather['weather_description'] = get_weather_description(current_weather['weathercode'])
                current_weather['season'] = get_astronomical_season(datetime.now(timezone.utc), lat)
                return current_weather
        else:
            print(f"Error: Could not find location data for {city}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_weather_description(weathercode):
    """Convert Open-Meteo weather code to a description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        95: "Thunderstorm",
    }
    return weather_codes.get(weathercode, "Unknown")

def generate_gpt4_prompt(client, weather_data, use_forecast=None):
    """Generate a prompt using GPT-4 based on the weather data."""

    # Read the weather option from config.ini
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)
    weather_option = config['Weather']['weather']

    # Use passed in forecast information if provided, otherwise use config
    if use_forecast is None:
        use_forecast = weather_option.lower() == 'forecast'

    forecast_text = "forecasted" if use_forecast else "current"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a creative assistant specialized in generating unique and captivating prompts for wallpaper creation based on weather conditions."},
            {"role": "user", "content": f"The prompt should be suitable for creating a stunning desktop wallpaper that reflects the {forecast_text} weather conditions in an artistic and visually appealing manner."},
            {"role": "user", "content": f"Generate a long one line prompt, ensure the image contains no text and try not include any known landmarks or places."},
            {"role": "user", "content": f"{weather_data}."}
        ]
    )
    return response.choices[0].message.content

def get_astronomical_season(date=None, latitude=None):
    if date is None:
        date = datetime.now(timezone.utc)
    elif date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    if latitude is None:
        raise ValueError("Latitude must be provided to determine hemisphere")

    # Approximate dates for solstices and equinoxes (times are rough estimates)
    spring_equinox = datetime(date.year, 3, 20, 5, 0, tzinfo=timezone.utc)
    summer_solstice = datetime(date.year, 6, 21, 5, 0, tzinfo=timezone.utc)
    autumn_equinox = datetime(date.year, 9, 22, 5, 0, tzinfo=timezone.utc)
    winter_solstice = datetime(date.year, 12, 21, 5, 0, tzinfo=timezone.utc)

    is_northern_hemisphere = latitude >= 0

    if spring_equinox <= date < summer_solstice:
        return "Spring" if is_northern_hemisphere else "Autumn"
    elif summer_solstice <= date < autumn_equinox:
        return "Summer" if is_northern_hemisphere else "Winter"
    elif autumn_equinox <= date < winter_solstice:
        return "Autumn" if is_northern_hemisphere else "Spring"
    else:
        return "Winter" if is_northern_hemisphere else "Summer"

def main():
    print("Starting weather data fetching and prompt generation...")
    parser = argparse.ArgumentParser(description="Fetch weather data and generate a wallpaper prompt")
    parser.add_argument("--city", type=str, required=True, help="City name for weather data")
    parser.add_argument("--no-prompt", action="store_true", help="Skip AI prompt generation and output weather data only")
    parser.add_argument("--forecast", action="store_true", help="Use forecast weather data")
    args = parser.parse_args()

    use_forecast = args.forecast

    print(f"Fetching {'forecast' if use_forecast else 'current'} weather data for {args.city}...")
    weather_data = fetch_weather(args.city, use_forecast)
    if weather_data:
        print("Weather data successfully fetched.")
        if args.no_prompt:
            print("Weather Data:")
            print(json.dumps(weather_data, indent=2))
        else:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
            config.read(config_path)
            openai_api_key = config['OpenAI']['api_key']
            
            client = OpenAI(api_key=openai_api_key)
            print("Generating prompt using GPT-4...")
            prompt = generate_gpt4_prompt(client, weather_data, use_forecast)
            print("Generated Prompt:")
            print(prompt)
    else:
        print("Failed to fetch weather data.")

if __name__ == "__main__":
    main()
