"""
core/history.py — Historial en memoria de lecturas meteorológicas.
Usa deque para mantener una ventana deslizante de tamaño fijo.
"""
from collections import deque
from config import Config
from core.weather_data import WeatherData


class History:
    """
    Almacena el historial de lecturas de la sesión actual.
    Cada deque mantiene exactamente HISTORY_LEN puntos.
    """

    def __init__(self, maxlen: int = Config.HISTORY_LEN):
        self._maxlen   = maxlen
        self.times     = deque(maxlen=maxlen)
        self.temps     = deque(maxlen=maxlen)
        self.humids    = deque(maxlen=maxlen)
        self.pressures = deque(maxlen=maxlen)
        self.winds     = deque(maxlen=maxlen)
        self.rains     = deque(maxlen=maxlen)
        self.uv        = deque(maxlen=maxlen)

    def push(self, wd: WeatherData) -> None:
        """Agrega una nueva lectura al historial."""
        self.times.append(wd.timestamp)
        self.temps.append(wd.temp)
        self.humids.append(wd.humidity)
        self.pressures.append(wd.pressure)
        self.winds.append(wd.wind_speed)
        self.rains.append(wd.rain_1h)
        self.uv.append(wd.uv_index)

    def xlabels(self) -> list[str]:
        """Etiquetas de tiempo para el eje X de los gráficos."""
        return [t.strftime("%H:%M") for t in self.times]

    VALID_KEYS = {"temps", "humids", "pressures", "winds", "rains", "uv"}

    def stats(self, key: str) -> dict:
        """Devuelve min, max, avg y last de una serie."""
        if key not in self.VALID_KEYS:
            raise ValueError(f"History.stats: key inválida '{key}'. "
                             f"Válidas: {self.VALID_KEYS}")
        vals = list(getattr(self, key))
        if not vals:
            return {"min": 0, "max": 0, "avg": 0, "last": 0}
        return {
            "min":  round(min(vals), 1),
            "max":  round(max(vals), 1),
            "avg":  round(sum(vals) / len(vals), 1),
            "last": round(vals[-1], 1),
        }

    def trend(self) -> str:
        """
        Calcula la tendencia de temperatura.
        Retorna: 'up' | 'down' | 'stable'
        """
        vals = list(self.temps)
        if len(vals) < 2:
            return "stable"
        delta = vals[-1] - vals[-2]
        if delta > 0.15:  return "up"
        if delta < -0.15: return "down"
        return "stable"

    def __len__(self) -> int:
        return len(self.times)