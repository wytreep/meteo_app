"""
screens/dashboard_screen.py — Pantalla principal del Dashboard.
Muestra: hero de temperatura, sensores, pronóstico y alertas.
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
# MDSnackbar moved — errors handled by parent app

from config import Config, Palette
from core.weather_data import WeatherData
from core.history import History
from widgets.weather_card import (
    HeroCard, SensorCard, InfoRow, ForecastCard
)


class DashboardScreen(MDScreen):
    """
    Pantalla principal. Scroll vertical con:
      1. HeroCard — temperatura grande
      2. InfoRow  — viento, amanecer, puesta
      3. Grid 2x3 — sensores individuales
      4. Pronóstico 3h (scroll horizontal)
      5. Panel de alertas
    """

    def __init__(self, history: History, **kwargs):
        super().__init__(name="dashboard", **kwargs)
        self._history = history
        self._sensors: dict[str, SensorCard] = {}
        self._forecast_row = None
        self._alerts_box   = None
        self._build()

    # ── Construcción ──────────────────────────────────────────
    def _build(self) -> None:
        scroll = ScrollView()
        root   = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(16), dp(16), dp(16), dp(80)],
            size_hint_y=None,
        )
        root.bind(minimum_height=root.setter("height"))

        # 1. Hero
        self._hero = HeroCard()
        root.add_widget(self._hero)

        # 2. Info rápida: viento, amanecer, puesta, nubosidad
        self._info_row = InfoRow([
            ("wind",    "rain",     "Viento"),
            ("sunrise", "uv",       "Amanecer"),
            ("sunset",  "uv",       "Atardecer"),
            ("clouds",  "pressure", "Nubosidad"),
        ])
        root.add_widget(self._info_row)

        # 3. Grid sensores 2 columnas
        root.add_widget(self._section_label("SENSORES"))
        grid = MDGridLayout(
            cols=2, spacing=dp(10),
            size_hint_y=None, height=dp(380),
            adaptive_height=False,
        )
        sensors = [
            ("humid",    "humid",    "Humedad",     "%",    Palette.SERIES[2], True),
            ("pressure", "pressure", "Presión",      "hPa",  Palette.SERIES[3], False),
            ("uv",       "uv",       "Índice UV",    "",     Palette.SERIES[2], True),
            ("vis",      "vis",      "Visibilidad",  "km",   Palette.SERIES[1], True),
            ("rain",     "rain",     "Lluvia 1h",    "mm",   Palette.SERIES[0], True),
            ("dew",      "dew",      "Punto rocío",  "°C",   Palette.SERIES[0], False),
        ]
        for key, icon_key, lbl, unit, color, bar in sensors:
            rgba = self._hex_to_rgba(color)
            card = SensorCard(key, icon_key, lbl, unit, rgba, bar)
            grid.add_widget(card)
            self._sensors[key] = card
        root.add_widget(grid)

        # 4. Pronóstico 3h
        root.add_widget(self._section_label("PRONÓSTICO  3H"))
        fc_scroll = ScrollView(size_hint_y=None, height=dp(130),
                               do_scroll_y=False)
        self._forecast_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_x=None,
            padding=[0, dp(4), 0, dp(4)],
        )
        self._forecast_row.bind(
            minimum_width=self._forecast_row.setter("width"))
        fc_scroll.add_widget(self._forecast_row)
        root.add_widget(fc_scroll)

        # 5. Alertas
        root.add_widget(self._section_label("ALERTAS"))
        self._alerts_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            adaptive_height=True,
        )
        root.add_widget(self._alerts_box)

        scroll.add_widget(root)
        self.add_widget(scroll)

    def _section_label(self, text: str) -> MDLabel:
        return MDLabel(
            text=text,
            font_style="Label",
            role="medium",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(20),
        )

    # ── Actualización ─────────────────────────────────────────
    def refresh(self, data: WeatherData) -> None:
        """Actualiza todos los widgets con nuevos datos."""
        self._update_hero(data)
        self._update_info_row(data)
        self._update_sensors(data)
        self._update_alerts(data)

    def update_forecast(self, items: list[dict]) -> None:
        self._forecast_row.clear_widgets()
        self._forecast_row.width = dp(0)
        for fc in items[:8]:
            card = ForecastCard(
                hour=fc["hour"],
                icon_key=fc.get("icon", "01d"),
                temp=f"{round(fc['temp']):.0f}°",
                humid=f"💧{fc['humid']}%",
            )
            self._forecast_row.add_widget(card)

    def _update_hero(self, data: WeatherData) -> None:
        trend = self._history.trend()
        self._hero.update(
            city=f"{data.city}, {data.country}",
            temp=round(data.temp, 1),
            feels=round(data.feels_like, 1),
            desc=data.description,
            icon_key=data.icon_code,
            trend=trend,
            t_min=round(data.temp_min),
            t_max=round(data.temp_max),
        )

    def _update_info_row(self, data: WeatherData) -> None:
        self._info_row.set("wind",
            f"{round(data.wind_speed)} km/h {data.wind_dir}")
        self._info_row.set("sunrise", data.sunrise_str)
        self._info_row.set("sunset",  data.sunset_str)
        self._info_row.set("clouds",  f"{data.clouds}%")

    def _update_sensors(self, data: WeatherData) -> None:
        uv_color = self._hex_to_rgba(self._uv_color(data.uv_index))
        uv_label = self._uv_label(data.uv_index)

        self._sensors["humid"].set_value(
            str(data.humidity), data.humidity / 100)
        self._sensors["pressure"].set_value(str(data.pressure))
        self._sensors["uv"].set_value(
            f"{data.uv_index}  {uv_label}",
            data.uv_index / 11, uv_color)
        self._sensors["vis"].set_value(
            str(round(data.visibility, 1)),
            min(1.0, data.visibility / 20))
        self._sensors["rain"].set_value(
            str(round(data.rain_1h, 1)),
            min(1.0, data.rain_1h / 20))
        self._sensors["dew"].set_value(str(round(data.dew_point, 1)))

    def _update_alerts(self, data: WeatherData) -> None:
        self._alerts_box.clear_widgets()
        alerts = self._evaluate_alerts(data)
        for icon, msg, bg in alerts:
            row = MDCard(
                style="filled",
                radius=[dp(10)],
                padding=[dp(12), dp(8)],
                size_hint_y=None,
                height=dp(44),
                md_bg_color=bg,
            )
            content = MDBoxLayout(orientation="horizontal",
                                  spacing=dp(10))
            content.add_widget(MDLabel(
                text=icon, size_hint_x=None, width=dp(24),
                halign="center"))
            content.add_widget(MDLabel(
                text=msg, font_style="Body", role="medium"))
            row.add_widget(content)
            self._alerts_box.add_widget(row)

    def _evaluate_alerts(self, wd: WeatherData) -> list[tuple]:
        a = Config.ALERT
        results = []

        def add(icon, msg, bg):
            results.append((icon, msg, bg))

        if wd.uv_index >= a["uv_extreme"]:
            add("⚠", f"UV Extremo ({wd.uv_index})",
                self._hex_to_rgba(Palette.DANGER_BG))
        elif wd.uv_index >= a["uv_high"]:
            add("⚠", f"UV Alto ({wd.uv_index}) — usa protector",
                self._hex_to_rgba(Palette.WARNING_BG))
        if wd.wind_speed >= a["wind_storm"]:
            add("💨", f"Viento de tormenta: {round(wd.wind_speed)} km/h",
                self._hex_to_rgba(Palette.DANGER_BG))
        elif wd.wind_speed >= a["wind_strong"]:
            add("💨", f"Vientos fuertes: {round(wd.wind_speed)} km/h",
                self._hex_to_rgba(Palette.WARNING_BG))
        if wd.rain_1h >= a["rain_heavy"]:
            add("🌧", f"Lluvia intensa: {wd.rain_1h} mm/h",
                self._hex_to_rgba(Palette.INFO_BG))
        if wd.temp >= a["temp_hot"]:
            add("🌡", f"Temperatura alta: {wd.temp}°C",
                self._hex_to_rgba(Palette.DANGER_BG))

        if not results:
            add("✓", "Sin alertas — condiciones normales",
                self._hex_to_rgba(Palette.SUCCESS_BG))
        return results

    # ── Helpers ───────────────────────────────────────────────
    @staticmethod
    def _hex_to_rgba(hex_color: str) -> list[float]:
        h = hex_color.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
            return [r/255, g/255, b/255, 1.0]
        return [0.5, 0.5, 0.5, 1.0]

    @staticmethod
    def _uv_color(uv: float) -> str:
        if uv < 3:  return Palette.SUCCESS
        if uv < 6:  return Palette.WARNING
        if uv < 8:  return "#E64A19"
        if uv < 11: return Palette.DANGER
        return "#6A1B9A"

    @staticmethod
    def _uv_label(uv: float) -> str:
        if uv < 3:  return "Bajo"
        if uv < 6:  return "Moderado"
        if uv < 8:  return "Alto"
        if uv < 11: return "Muy alto"
        return "Extremo"