"""
widgets/alert_panel.py — Panel de alertas meteorológicas.
Evalúa los umbrales y muestra filas con color semántico.
"""
import tkinter as tk

from config import Config, Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class AlertPanel(BaseWidget):
    """
    Muestra alertas activas según los umbrales de Config.ALERT.
    Si no hay alertas, muestra un mensaje verde de "todo normal".
    """

    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)

    def refresh(self, data: WeatherData) -> None:
        for w in self.winfo_children():
            w.destroy()
        for icon, msg, color, bg in self._evaluate(data):
            row = tk.Frame(self, bg=bg, pady=4, padx=10)
            row.pack(fill="x", pady=(0, 2))
            tk.Label(row, text=icon, font=("", 10),
                     fg=color, bg=bg).pack(side="left", padx=(0, 8))
            tk.Label(row, text=msg, font=("", 9),
                     fg=color, bg=bg, anchor="w").pack(side="left")

    def _evaluate(self, wd: WeatherData) -> list[tuple]:
        """Devuelve lista de (icon, mensaje, color_texto, color_fondo)."""
        a       = Config.ALERT
        results = []

        def add(icon, msg, color, bg):
            results.append((icon, msg, color, bg))

        if wd.uv_index >= a["uv_extreme"]:
            add("●", f"UV Extremo ({wd.uv_index}) — evitar exposición",
                Theme.DANGER, "#FEF2F2")
        elif wd.uv_index >= a["uv_high"]:
            add("●", f"UV Alto ({wd.uv_index}) — usa protector solar",
                Theme.WARNING, "#FFFBEB")

        if wd.wind_speed >= a["wind_storm"]:
            add("●", f"Viento de tormenta: {round(wd.wind_speed)} km/h",
                Theme.DANGER, "#FEF2F2")
        elif wd.wind_speed >= a["wind_strong"]:
            add("●", f"Vientos fuertes: {round(wd.wind_speed)} km/h",
                Theme.WARNING, "#FFFBEB")

        if wd.rain_1h >= a["rain_heavy"]:
            add("●", f"Lluvia intensa: {wd.rain_1h} mm/h",
                Theme.INFO, "#F0F9FF")

        if wd.pressure < a["pressure_low"]:
            add("●", f"Presión baja: {wd.pressure} hPa",
                Theme.WARNING, "#FFFBEB")

        if wd.humidity > a["humidity_high"]:
            add("●", f"Humedad muy alta: {wd.humidity}%",
                Theme.INFO, "#F0F9FF")

        if wd.temp >= a["temp_hot"]:
            add("●", f"Temperatura alta: {wd.temp}°C",
                Theme.DANGER, "#FEF2F2")

        if not results:
            add("✓", "Sin alertas — condiciones normales",
                Theme.SUCCESS, "#F0FDF4")

        return results
