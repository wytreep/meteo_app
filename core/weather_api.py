"""
core/weather_api.py — Cliente HTTP para OpenWeatherMap API.
Responsabilidad única: obtener datos de la red.
"""
from config import Config
from core.weather_data import WeatherData

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


class WeatherAPI:
    """
    Encapsula todas las llamadas a la API de OpenWeatherMap.
    Lanza excepciones en caso de error HTTP o de red.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str):
        if not REQUESTS_OK:
            raise RuntimeError(
                "El módulo 'requests' no está instalado.\n"
                "Ejecuta: pip install requests"
            )
        self._key = api_key

    def _get(self, endpoint: str, **params) -> dict:
        """Realiza un GET y devuelve el JSON. Lanza si hay error."""
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(
            url,
            params={
                "appid":  self._key,
                "units":  Config.UNITS,
                "lang":   "es",
                **params,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def fetch_current(self, city: str) -> WeatherData:
        """Obtiene el clima actual para una ciudad."""
        raw = self._get("weather", q=city)
        return WeatherData.from_api(raw)

    def fetch_forecast(self, city: str, count: int = 8) -> list[dict]:
        """
        Obtiene el pronóstico en intervalos de 3h.
        Devuelve una lista de dicts con keys:
          hour, temp, icon, humid, wind, rain
        """
        raw    = self._get("forecast", q=city, cnt=count)
        result = []
        from datetime import datetime

        for i, item in enumerate(raw.get("list", [])):
            dt   = datetime.fromtimestamp(item["dt"])
            main = item.get("main", {})
            wx   = item.get("weather", [{}])[0]
            wind = item.get("wind", {})
            result.append({
                "hour":  "Ahora" if i == 0 else dt.strftime("%H:%M"),
                "temp":  round(main.get("temp", 0), 1),
                "icon":  wx.get("icon", "01d"),
                "humid": main.get("humidity", 0),
                "wind":  round(wind.get("speed", 0) * 3.6, 1),
                "rain":  item.get("rain", {}).get("3h", 0),
            })
        return result
