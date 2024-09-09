# Weather API

A simple Weather Fast API based application using openweathermap.org as a source.

## How to run

```bash
docker compose build
docker compose up
```

## Testing
### Manual
The application will run on 8089 port by default:
```bash
curl --silent http://localhost:8089/weather?city=odessa | jq
```

Example output
```bash
{
  "coord": {
    "lon": 30.7326,
    "lat": 46.4775
  },
  "weather": [
    {
      "id": 800,
      "main": "Clear",
      "description": "clear sky",
      "icon": "01d"
    }
  ],
  "base": "stations",
  "main": {
    "temp": 296.28,
    "feels_like": 295.64,
    "temp_min": 296.28,
    "temp_max": 296.28,
    "pressure": 1013,
    "humidity": 38,
    "sea_level": 1013,
    "grnd_level": 1010
  },
  "visibility": 10000,
  "wind": {
    "speed": 3.77,
    "deg": 103,
    "gust": 4.3
  },
  "clouds": {
    "all": 0
  },
  "dt": 1725877735,
  "sys": {
    "country": "UA",
    "sunrise": 1725852462,
    "sunset": 1725898879
  },
  "timezone": 10800,
  "id": 698740,
  "name": "Odesa",
  "cod": 200
}
```

### Unit tests
Run this once to install test dependencies
```bash
pip install -r requirements.test.txt
```

And then
```bash
pytest -v
```
