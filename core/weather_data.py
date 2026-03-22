"""
core/weather_data.py — Modelo de datos de una lectura meteorológica.
Incluye constructores de fábrica: from_api() y demo().
"""
import math
import random
from datetime import datetime

from config import Config


class WeatherData:
    """
    Snapshot inmutable de una lectura meteorológica.
    No contiene lógica de red ni de UI.
    """

    CSV_HEADERS = [
        "timestamp", "temp_c", "feels_like_c", "humidity_pct",
        "pressure_hpa", "wind_kmh", "wind_deg", "clouds_pct",
        "rain_1h_mm", "uv_index", "visibility_km", "description", "city",
    ]

    WIND_DIRS = [
        "N","NNE","NE","ENE","E","ESE","SE","SSE",
        "S","SSO","SO","OSO","O","ONO","NO","NNO",
    ]

    WX_EMOJI = {
        "01d":"☀","01n":"☽","02d":"⛅","02n":"⛅",
        "03d":"☁","03n":"☁","04d":"☁","04n":"☁",
        "09d":"🌦","09n":"🌦","10d":"🌧","10n":"🌧",
        "11d":"⛈","11n":"⛈","13d":"❄","13n":"❄",
        "50d":"≋","50n":"≋",
    }

    def __init__(self):
        self.timestamp   = datetime.now()
        self.temp        = 0.0
        self.feels_like  = 0.0
        self.temp_min    = 0.0
        self.temp_max    = 0.0
        self.humidity    = 0
        self.pressure    = 1013
        self.wind_speed  = 0.0
        self.wind_deg    = 0
        self.wind_gust   = 0.0
        self.clouds      = 0
        self.visibility  = 10.0
        self.description = "—"
        self.icon_code   = "01d"
        self.uv_index    = 0
        self.rain_1h     = 0.0
        self.dew_point   = 0.0
        self.city        = Config.CITY.split(",")[0]
        self.country     = "CO"
        self.sunrise     = 0
        self.sunset      = 0
        self.lat         = 3.4516
        self.lon         = -76.5320

    # ── Constructores de fábrica ──────────────────────────────────
    @classmethod
    def from_api(cls, raw: dict) -> "WeatherData":
        """Crea una instancia desde la respuesta JSON de OpenWeatherMap."""
        w     = cls()
        main  = raw.get("main", {})
        wind  = raw.get("wind", {})
        wx    = raw.get("weather", [{}])[0]
        sys_  = raw.get("sys", {})
        coord = raw.get("coord", {})
        rain  = raw.get("rain", {})

        w.timestamp   = datetime.now()
        w.temp        = round(main.get("temp", 0), 1)
        w.feels_like  = round(main.get("feels_like", 0), 1)
        w.temp_min    = round(main.get("temp_min", 0), 1)
        w.temp_max    = round(main.get("temp_max", 0), 1)
        w.humidity    = main.get("humidity", 0)
        w.pressure    = main.get("pressure", 1013)
        w.wind_speed  = round(wind.get("speed", 0) * 3.6, 1)
        w.wind_deg    = wind.get("deg", 0)
        w.wind_gust   = round(wind.get("gust", wind.get("speed", 0)) * 3.6, 1)
        w.clouds      = raw.get("clouds", {}).get("all", 0)
        w.visibility  = round(raw.get("visibility", 10000) / 1000, 1)
        w.description = wx.get("description", "—").capitalize()
        w.icon_code   = wx.get("icon", "01d")
        w.rain_1h     = rain.get("1h", 0.0)
        w.city        = raw.get("name", "—")
        w.country     = sys_.get("country", "CO")
        w.sunrise     = sys_.get("sunrise", 0)
        w.sunset      = sys_.get("sunset", 0)
        w.dew_point   = round(w.temp - ((100 - w.humidity) / 5), 1)
        w.lat         = coord.get("lat", 3.4516)
        w.lon         = coord.get("lon", -76.5320)
        return w

    @classmethod
    def demo(cls, city: str = "Cali") -> "WeatherData":
        """Genera datos simulados realistas para demostración."""
        w    = cls()
        hour = datetime.now().hour
        base = 24 + 6 * math.sin((hour - 6) * math.pi / 12)

        w.temp        = round(base + random.uniform(-1, 1), 1)
        w.feels_like  = round(w.temp + random.uniform(1, 3), 1)
        w.temp_min    = round(w.temp - random.uniform(2, 4), 1)
        w.temp_max    = round(w.temp + random.uniform(2, 4), 1)
        w.humidity    = random.randint(60, 85)
        w.pressure    = random.randint(1008, 1018)
        w.wind_speed  = round(random.uniform(8, 25), 1)
        w.wind_deg    = random.randint(0, 359)
        w.wind_gust   = round(w.wind_speed + random.uniform(3, 12), 1)
        w.clouds      = random.randint(20, 80)
        w.visibility  = round(random.uniform(8, 15), 1)
        w.description = random.choice([
            "Parcialmente nublado", "Soleado", "Lluvias ocasionales",
            "Mayormente despejado", "Lluvia ligera", "Nublado",
        ])
        w.icon_code   = random.choice(["01d","02d","03d","10d","09d"])
        w.rain_1h     = round(random.uniform(0, 5), 1) if w.clouds > 70 else 0
        w.uv_index    = random.randint(3, 9) if 6 <= hour <= 18 else 0
        w.dew_point   = round(w.temp - ((100 - w.humidity) / 5), 1)
        w.city        = city
        w.country     = "CO"
        w.sunrise     = int(datetime.now().replace(
            hour=5, minute=55, second=0).timestamp())
        w.sunset      = int(datetime.now().replace(
            hour=18, minute=10, second=0).timestamp())
        return w

    # ── Propiedades calculadas ────────────────────────────────────
    @property
    def wind_dir(self) -> str:
        return self.WIND_DIRS[round(self.wind_deg / 22.5) % 16]

    @property
    def emoji(self) -> str:
        return self.WX_EMOJI.get(self.icon_code, "●")

    @property
    def sunrise_str(self) -> str:
        return (datetime.fromtimestamp(self.sunrise).strftime("%H:%M")
                if self.sunrise else "—")

    @property
    def sunset_str(self) -> str:
        return (datetime.fromtimestamp(self.sunset).strftime("%H:%M")
                if self.sunset else "—")

    # ── Serialización ─────────────────────────────────────────────
    def to_csv_row(self) -> list:
        return [
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.temp, self.feels_like, self.humidity, self.pressure,
            self.wind_speed, self.wind_deg, self.clouds,
            self.rain_1h, self.uv_index, self.visibility,
            self.description, self.city,
        ]

    def __repr__(self) -> str:
        return (f"WeatherData(city={self.city!r}, temp={self.temp}, "
                f"humid={self.humidity}, ts={self.timestamp:%H:%M:%S})")
