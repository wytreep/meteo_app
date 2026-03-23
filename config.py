"""
config.py — Configuración global de la app móvil.
"""


class Config:
    API_KEY     = "2262ff91362f26070bb08c849bbe9856"          # ← pega tu API key aquí
    CITY        = "Cali,CO"
    UNITS       = "metric"
    INTERVAL    = 30          # segundos entre auto-refresh
    HISTORY_LEN = 60
    APP_TITLE   = "MeteoApp"

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


class Palette:
    """Colores Material Design 3 para la app."""
    # Primarios
    PRIMARY       = "#1565C0"   # Azul oscuro
    PRIMARY_LIGHT = "#E3F2FD"   # Azul muy claro
    ON_PRIMARY    = "#FFFFFF"

    # Superficie
    SURFACE       = "#FFFFFF"
    SURFACE_VAR   = "#F5F7FA"
    BACKGROUND    = "#F0F4F8"
    ON_SURFACE    = "#1A2332"
    ON_SURFACE_V  = "#5A6578"

    # Semánticos
    SUCCESS       = "#2E7D32"
    SUCCESS_BG    = "#E8F5E9"
    WARNING       = "#E65100"
    WARNING_BG    = "#FFF3E0"
    DANGER        = "#C62828"
    DANGER_BG     = "#FFEBEE"
    INFO          = "#01579B"
    INFO_BG       = "#E1F5FE"

    # Bordes y divisores
    OUTLINE       = "#DDE1E7"
    OUTLINE_VAR   = "#C5CAD3"

    # Chart
    CHART_BG      = "#FFFFFF"
    GRID          = "#F1F3F6"
    SERIES        = ["#1565C0", "#2E7D32", "#E65100", "#6A1B9A"]