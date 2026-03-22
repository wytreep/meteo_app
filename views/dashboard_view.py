"""
views/dashboard_view.py — Vista principal del dashboard.
Compone: hero de temperatura, sensores, mapa, gráfico, pronóstico y alertas.
"""
import tkinter as tk

from config import Theme
from core.history      import History
from core.weather_data import WeatherData
from widgets.base_widget    import BaseWidget
from widgets.sensor_card    import SensorCard
from widgets.compass_canvas import CompassCanvas
from widgets.map_canvas     import MapCanvas
from widgets.mini_chart     import MiniChart
from widgets.forecast_bar   import ForecastBar
from widgets.alert_panel    import AlertPanel


class DashboardView(BaseWidget):
    """
    Vista principal con 3 columnas:
      Izquierda  — Hero de temperatura + brújula
      Centro     — Sensores grid + gráfico histórico
      Derecha    — Mapa + pronóstico + alertas
    """

    def __init__(self, parent, history: History):
        super().__init__(parent, bg=Theme.BG)
        self._history = history
        self._sensors: dict[str, SensorCard] = {}
        self._build()

    def _build(self) -> None:
        body = tk.Frame(self, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        self._build_left(body)
        self._build_center(body)
        self._build_right(body)

    # ── Columna izquierda: hero ────────────────────────────────
    def _build_left(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=Theme.CARD,
                        highlightthickness=1,
                        highlightbackground=Theme.BORDER,
                        width=185)
        card.pack(side="left", fill="y", padx=(0, 8))
        card.pack_propagate(False)

        pad = tk.Frame(card, bg=Theme.CARD, padx=16, pady=14)
        pad.pack(fill="both", expand=True)

        self._hero_icon = tk.Label(pad, text="☀",
                                   font=("", 32), fg=Theme.ACCENT,
                                   bg=Theme.CARD)
        self._hero_icon.pack()

        temp_row = tk.Frame(pad, bg=Theme.CARD)
        temp_row.pack(pady=(4, 0))
        self._hero_temp = tk.Label(temp_row, text="—",
                                   font=(Theme.FONT_MONO, 38, "bold"),
                                   fg=Theme.TEXT, bg=Theme.CARD)
        self._hero_temp.pack(side="left")
        tk.Label(temp_row, text="°C",
                 font=(Theme.FONT_SANS, 14),
                 fg=Theme.ACCENT, bg=Theme.CARD).pack(
                     side="left", anchor="n", pady=10)

        self._hero_feels = tk.Label(pad, text="Sensación: —",
                                    font=(Theme.FONT_MONO, 8),
                                    fg=Theme.TEXT_MUT, bg=Theme.CARD)
        self._hero_feels.pack()

        self._hero_trend = tk.Label(pad, text="→ Estable",
                                    font=(Theme.FONT_SANS, 10),
                                    fg=Theme.TEXT_SEC, bg=Theme.CARD)
        self._hero_trend.pack(pady=(4, 0))

        self._hero_desc = tk.Label(pad, text="—",
                                   font=(Theme.FONT_SANS, 10),
                                   fg=Theme.TEXT_SEC, bg=Theme.CARD,
                                   wraplength=155)
        self._hero_desc.pack(pady=(2, 0))

        self._hero_mm = tk.Label(pad, text="↓—  ↑—",
                                 font=(Theme.FONT_MONO, 9),
                                 fg=Theme.TEXT_MUT, bg=Theme.CARD)
        self._hero_mm.pack(pady=(4, 0))

        tk.Frame(pad, bg=Theme.BORDER, height=1).pack(
            fill="x", pady=10)

        # Brújula
        self._compass = CompassCanvas(pad)
        self._compass.pack(fill="x", ipady=50)

        self._wind_spd = tk.Label(pad, text="— km/h",
                                  font=(Theme.FONT_MONO, 11, "bold"),
                                  fg=Theme.ACCENT, bg=Theme.CARD)
        self._wind_spd.pack(pady=(4, 0))

        self._wind_lbl = tk.Label(pad, text="—",
                                  font=(Theme.FONT_MONO, 9),
                                  fg=Theme.TEXT_SEC, bg=Theme.CARD)
        self._wind_lbl.pack()

    # ── Columna centro: sensores + gráfico ────────────────────
    def _build_center(self, parent: tk.Frame) -> None:
        col = tk.Frame(parent, bg=Theme.BG)
        col.pack(side="left", fill="both", expand=True,
                 padx=(0, 8))

        # Grid 2×3 de sensores
        grid = tk.Frame(col, bg=Theme.BG)
        grid.pack(fill="x", pady=(0, 8))

        sensors = [
            ("humid",    "💧", "Humedad",     "%",     Theme.INFO,      True),
            ("pressure", "⬤",  "Presión",      " hPa",  Theme.SERIES[2], False),
            ("uv",       "◉",  "Índice UV",    "",      Theme.WARNING,   True),
            ("vis",      "◎",  "Visibilidad",  " km",   Theme.SUCCESS,   True),
            ("rain",     "▼",  "Lluvia 1h",    " mm",   Theme.INFO,      True),
            ("dew",      "◈",  "Punto rocío",  "°C",    Theme.SERIES[0], False),
        ]
        for i, (key, icon, lbl, unit, color, bar) in enumerate(sensors):
            r, c = divmod(i, 2)
            card = SensorCard(grid, icon, lbl, unit, color, bar)
            card.grid(row=r, column=c,
                      padx=(0 if c == 0 else 6, 0),
                      pady=(0 if r == 0 else 6, 0),
                      sticky="nsew")
            grid.columnconfigure(c, weight=1)
            self._sensors[key] = card

        # Gráfico histórico
        chart_card = tk.Frame(col, bg=Theme.CARD,
                              highlightthickness=1,
                              highlightbackground=Theme.BORDER)
        chart_card.pack(fill="both", expand=True)
        self._mini_chart = MiniChart(chart_card, self._history)
        self._mini_chart.pack(fill="both", expand=True)

    # ── Columna derecha: mapa + pronóstico + alertas ──────────
    def _build_right(self, parent: tk.Frame) -> None:
        col = tk.Frame(parent, bg=Theme.BG, width=290)
        col.pack(side="left", fill="y")
        col.pack_propagate(False)

        # Mapa
        map_card = tk.Frame(col, bg=Theme.CARD,
                            highlightthickness=1,
                            highlightbackground=Theme.BORDER)
        map_card.pack(fill="both", expand=True, pady=(0, 8))

        map_hdr = tk.Frame(map_card, bg=Theme.CARD)
        map_hdr.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(map_hdr, text="UBICACIÓN",
                 font=(Theme.FONT_MONO, 8),
                 fg=Theme.TEXT_MUT, bg=Theme.CARD).pack(side="left")
        self._map_city = tk.Label(map_hdr, text="—",
                                  font=(Theme.FONT_MONO, 8),
                                  fg=Theme.ACCENT, bg=Theme.CARD)
        self._map_city.pack(side="right")

        self._map = MapCanvas(map_card)
        self._map.pack(fill="both", expand=True, padx=6, pady=(4, 8))

        # Pronóstico
        fc_card = tk.Frame(col, bg=Theme.CARD,
                           highlightthickness=1,
                           highlightbackground=Theme.BORDER)
        fc_card.pack(fill="x", pady=(0, 8))
        tk.Label(fc_card, text="PRONÓSTICO  3H",
                 font=(Theme.FONT_MONO, 8),
                 fg=Theme.TEXT_MUT, bg=Theme.CARD,
                 pady=6, padx=12).pack(anchor="w")
        self._forecast = ForecastBar(fc_card)
        self._forecast.pack(fill="x", padx=6, pady=(0, 6))

        # Alertas
        al_card = tk.Frame(col, bg=Theme.CARD,
                           highlightthickness=1,
                           highlightbackground=Theme.BORDER)
        al_card.pack(fill="x")
        tk.Label(al_card, text="ALERTAS",
                 font=(Theme.FONT_MONO, 8),
                 fg=Theme.TEXT_MUT, bg=Theme.CARD,
                 pady=6, padx=12).pack(anchor="w")
        self._alerts = AlertPanel(al_card)
        self._alerts.pack(fill="x", padx=6, pady=(0, 6))

    # ── Actualización ─────────────────────────────────────────
    def refresh(self, data: WeatherData) -> None:
        self._update_hero(data)
        self._update_sensors(data)
        self._map.refresh(data)
        self._map_city.config(text=f"{data.city}, {data.country}")
        self._mini_chart.refresh(data)
        self._alerts.refresh(data)

    def update_forecast(self, items: list[dict]) -> None:
        self._forecast.update_forecast(items)

    def _update_hero(self, data: WeatherData) -> None:
        self._hero_icon.config(text=data.emoji)
        self._hero_temp.config(text=str(round(data.temp, 1)))
        self._hero_feels.config(
            text=f"Sensación: {round(data.feels_like, 1)}°C")

        trend = self._history.trend()
        trend_map = {
            "up":     ("↑ Subiendo", Theme.DANGER),
            "down":   ("↓ Bajando",  Theme.INFO),
            "stable": ("→ Estable",  Theme.TEXT_MUT),
        }
        txt, col = trend_map[trend]
        self._hero_trend.config(text=txt, fg=col)
        self._hero_desc.config(text=data.description)
        self._hero_mm.config(
            text=f"↓{round(data.temp_min):.0f}°   ↑{round(data.temp_max):.0f}°")

        self._compass.refresh(data)
        self._wind_spd.config(
            text=f"{round(data.wind_speed, 1)} km/h")
        self._wind_lbl.config(
            text=f"{data.wind_dir}  |  ráfaga {round(data.wind_gust, 1)}")

    def _update_sensors(self, data: WeatherData) -> None:
        from config import Theme
        self._sensors["humid"].set_value(
            str(data.humidity), data.humidity / 100)
        self._sensors["pressure"].set_value(str(data.pressure))
        uv_col = Theme.uv_color(data.uv_index)
        self._sensors["uv"].set_value(
            f"{data.uv_index}  {Theme.uv_label(data.uv_index)}",
            data.uv_index / 11, uv_col)
        self._sensors["vis"].set_value(
            str(round(data.visibility, 1)),
            min(1.0, data.visibility / 20))
        self._sensors["rain"].set_value(
            str(round(data.rain_1h, 1)),
            min(1.0, data.rain_1h / 20))
        self._sensors["dew"].set_value(
            str(round(data.dew_point, 1)))
