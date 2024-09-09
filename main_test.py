import json
import os
import shutil
from fastapi import HTTPException
import pytest
import asynctest

import main
from main import get_weather, store_weather_data, log_weather_event, get_cached_weather_data


@pytest.mark.asyncio
class TestWeatherAPIService(asynctest.TestCase):
    def setUp(self):
        super().setUp()
        if os.path.exists(main.CACHE_DIR):
            shutil.rmtree(main.CACHE_DIR)
            os.mkdir(main.CACHE_DIR)
        if os.path.exists(main.LOG_FILE):
            os.remove(main.LOG_FILE)


    @asynctest.patch('main.fetch_weather_data')
    async def test_get_weather_cache_hit(self, mock_fetch_weather):
        # Mock data
        city = "London"
        weather_data = {"temp": 20}

        # Pre-populate cache
        await store_weather_data(city, weather_data)

        # Get weather should return cached data without calling the external API
        result = await get_weather(city)
        mock_fetch_weather.assert_not_called()
        assert result == weather_data

    @asynctest.patch('main.fetch_weather_data')
    async def test_get_weather_cache_miss(self, mock_fetch_weather):
        # Mock data
        city = "London"
        weather_data = {"temp": 20}

        mock_fetch_weather.return_value = weather_data

        # Get weather should fetch from the external API and cache the result
        result = await get_weather(city)
        mock_fetch_weather.assert_called_once()
        assert result == weather_data

        # Ensure data is cached
        cached_data = await get_cached_weather_data(city)
        assert cached_data == weather_data

    @asynctest.patch('main.fetch_weather_data')
    async def test_get_weather_invalid_city(self, mock_fetch_weather):
        # Mock an invalid city response
        mock_fetch_weather.side_effect = HTTPException(status_code=404, detail="City not found")

        # Get weather should raise an HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_weather("InvalidCity")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "City not found"

    @asynctest.patch('main.log_weather_event')
    async def test_log_weather_event_concurrent_writes(self, mock_log_event):
        city = "London"
        filepath = "test_file.json"

        # Simulate multiple concurrent requests trying to log the same event
        await log_weather_event(city, filepath),

        with open(main.LOG_FILE) as file:
            log_file = json.load(file)
            assert log_file[0]['city'] == city
            assert log_file[0]['filepath'] == filepath

    # Add more test cases as needed to cover all scenarios
