from fastapi import FastAPI, HTTPException
from aiohttp import ClientSession
import aiofiles
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
from aiofiles.os import wrap
from fcntl import flock, LOCK_EX, LOCK_UN

app = FastAPI()

# Configuration
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
API_KEY = "01572c89d3ca9de06928a54b69e523b9"
CACHE_DIR = Path("./weather_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_EXPIRY = timedelta(minutes=5)
LOG_FILE = "weather_log.json"

async def fetch_weather_data(city: str) -> dict:
    params = {"q": city, "appid": API_KEY}
    async with ClientSession() as session:
        async with session.get(WEATHER_API_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise HTTPException(status_code=response.status, detail="Failed to fetch weather data")

async def store_weather_data(city: str, data: dict) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{city}_{timestamp}.json"
    filepath = CACHE_DIR / filename
    async with aiofiles.open(filepath, "w") as file:
        await file.write(json.dumps(data))
    return str(filepath)


@wrap
def file_lock(file, operation):
    return flock(file.fileno(), operation)

async def log_weather_event(city: str, filepath: str):
    log_file = LOG_FILE
    event = {
        "city": city,
        "timestamp": datetime.utcnow().isoformat(),
        "filepath": filepath
    }
    if os.path.exists(log_file):
        async with aiofiles.open(log_file, "r+") as file:
            await file_lock(file, LOCK_EX)
            await file.seek(0)
            content = await file.read()
            log_data = json.loads(content) if content else []
            log_data.append(event)
            await file.seek(0)
            await file.write(json.dumps(log_data))
            await file.truncate()
            await file_lock(file, LOCK_UN)
    else:
        async with aiofiles.open(log_file, "w") as file:
            await file_lock(file, LOCK_EX)
            await file.write(json.dumps([event]))
            await file_lock(file, LOCK_UN)

async def get_cached_weather_data(city: str) -> dict:
    now = datetime.utcnow()
    for file in CACHE_DIR.glob(f"{city}_*.json"):
        timestamp_str = file.stem.split("_")[1]
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        if now - timestamp < CACHE_EXPIRY:
            async with aiofiles.open(file, "r") as f:
                return json.loads(await f.read())
    return None

@app.get("/weather")
async def get_weather(city: str):
    # Check cache first
    cached_data = await get_cached_weather_data(city)
    if cached_data:
        return cached_data

    # Fetch weather data
    weather_data = await fetch_weather_data(city)

    # Store weather data
    filepath = await store_weather_data(city, weather_data)

    # Log the event
    await log_weather_event(city, filepath)

    return weather_data
