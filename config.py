"""
config.py — Configuración global de la aplicación.
Todas las constantes en un solo lugar.
"""
from pathlib import Path


class Config:
    API_KEY     = "2262ff91362f26070bb08c849bbe9856"            # ← pega tu API key aquí
    CITY        = "Cali,CO"
    UNITS       = "metric"      # metric=°C | imperial=°F
    INTERVAL    = 30            # segundos entre auto-refresh
    HISTORY_LEN = 120
    DATA_FILE   = Path("weather_history.csv")
    WIN_SIZE    = "1200x750"
    WIN_TITLE   = "Estación Meteorológica"

    ALERT = {
        "uv_high":       6,
        "uv_extreme":    9,
        "wind_strong":   45,
        "wind_storm":    70,
        "rain_heavy":    10,
        "pressure_low":  1000,
        "humidity_high": 90,
        "temp_hot":      35,
        "temp_cold":     10,
    }


class Theme:
    # Fondos
    BG           = "#F4F5F7"
    SURFACE      = "#FFFFFF"
    CARD         = "#FFFFFF"
    CARD_ALT     = "#F8F9FB"

    # Bordes
    BORDER       = "#DDE1E7"
    BORDER_DARK  = "#C5CAD3"

    # Texto
    TEXT         = "#1A2332"
    TEXT_SEC     = "#5A6578"
    TEXT_MUT     = "#8C96A5"
    TEXT_INV     = "#FFFFFF"

    # Acento — azul clásico
    ACCENT       = "#2563EB"
    ACCENT_DARK  = "#1D4ED8"
    ACCENT_LIGHT = "#EFF6FF"

    # Semánticos
    SUCCESS      = "#16A34A"
    WARNING      = "#D97706"
    DANGER       = "#DC2626"
    INFO         = "#0891B2"

    # Gráficos
    CHART_BG     = "#FFFFFF"
    GRID         = "#F1F3F6"
    SERIES       = ["#2563EB", "#16A34A", "#D97706", "#7C3AED"]

    # Fuentes
    FONT_MONO    = "Courier"
    FONT_SANS    = ""

    @staticmethod
    def uv_color(uv: float) -> str:
        if uv < 3:  return Theme.SUCCESS
        if uv < 6:  return Theme.WARNING
        if uv < 8:  return "#EA580C"
        if uv < 11: return Theme.DANGER
        return "#7C3AED"

    @staticmethod
    def uv_label(uv: float) -> str:
        if uv < 3:  return "Bajo"
        if uv < 6:  return "Moderado"
        if uv < 8:  return "Alto"
        if uv < 11: return "Muy alto"
        return "Extremo"
