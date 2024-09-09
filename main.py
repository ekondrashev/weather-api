import argparse

from fastapi import FastAPI, HTTPException
from aiohttp import ClientSession

import local_backend

app = FastAPI()
parser = argparse.ArgumentParser()
parser.add_argument("--aws-backend", action="store_true",
					help="Use AWS S3 and DynamoDB as the backend for cache and events log")

# Configuration
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
API_KEY = "01572c89d3ca9de06928a54b69e523b9"

backend = local_backend
if __name__ == "__main__":
    args = parser.parse_args()
    if args.aws_backend:
        import aws_backend
        backend = aws_backend

async def fetch_weather_data(city: str) -> dict:
    params = {"q": city, "appid": API_KEY}
    async with ClientSession() as session:
        async with session.get(WEATHER_API_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise HTTPException(status_code=response.status, detail="Failed to fetch weather data")

@app.get("/weather")
async def get_weather(city: str):
    # Check cache first
    cached_data = await backend.get_cached_weather_data(city)
    if cached_data:
        return cached_data

    # Fetch weather data
    weather_data = await fetch_weather_data(city)

    # Store weather data
    filepath = await backend.store_weather_data(city, weather_data)

    # Log the event
    await backend.log_weather_event(city, filepath)

    return weather_data
