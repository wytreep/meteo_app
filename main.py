"""
main.py — Punto de entrada de MeteoApp móvil.
Arquitectura: MDApp + MDNavigationBar (bottom nav) + ScreenManager.

Ejecución en escritorio (desarrollo):
    pip install kivymd requests matplotlib
    python main.py

Compilar para Android:
    pip install buildozer
    buildozer init
    buildozer android debug

Compilar para iOS (requiere Mac):
    pip install kivy-ios
    toolchain build kivy
"""
import threading
import random
from datetime import datetime, timedelta

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationbar import (
    MDNavigationBar, MDNavigationItem,
    MDNavigationItemIcon, MDNavigationItemLabel,
)
from kivymd.uix.snackbar import MDSnackbar

from config import Config, Palette
from core.weather_data import WeatherData
from core.weather_api  import WeatherAPI
from core.history      import History
from core.notifier     import Notifier
from screens.dashboard_screen import DashboardScreen
from screens.charts_screen    import ChartsScreen
from screens.map_screen       import MapScreen

# Simular pantalla móvil en escritorio durante desarrollo
Window.size = (390, 844)


class MeteoApp(MDApp):
    """
    Aplicación principal KivyMD.
    Orquesta el ciclo de datos y la navegación entre pantallas.
    """

    def build(self) -> MDBoxLayout:
        # Tema Material Design 3
        self.theme_cls.theme_style   = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style  = "M3"
        self.title = Config.APP_TITLE

        # Modelo
        self._history  = History()
        self._current  = WeatherData.demo()
        self._forecast: list[dict] = []
        self._busy     = False

        # Layout raíz: pantallas arriba + nav bar abajo
        root = MDBoxLayout(orientation="vertical")

        # ── Screen Manager ──────────────────────────────────────
        self._sm = ScreenManager(transition=NoTransition())
        self._dash   = DashboardScreen(self._history)
        self._charts = ChartsScreen(self._history)
        self._map    = MapScreen(on_city_select=self._on_map_city_selected)
        self._sm.add_widget(self._dash)
        self._sm.add_widget(self._charts)
        self._sm.add_widget(self._map)
        root.add_widget(self._sm)

        # ── Bottom Navigation Bar ───────────────────────────────
        nav = MDNavigationBar(on_switch_tabs=self._on_tab_switch)

        tabs = [
            ("dashboard", "home",         "Inicio"),
            ("charts",    "chart-line",   "Gráficos"),
            ("map",       "map-marker",   "Mapa"),
        ]
        for screen, icon, label in tabs:
            item = MDNavigationItem()
            item.add_widget(MDNavigationItemIcon(icon=f"mdi:{icon}"))
            item.add_widget(MDNavigationItemLabel(text=label))
            nav.add_widget(item)

        root.add_widget(nav)

        # ── Primer refresh ──────────────────────────────────────
        Clock.schedule_once(lambda dt: self._refresh(), 0.5)
        Clock.schedule_interval(
            lambda dt: self._refresh(), Config.INTERVAL)

        return root

    # ── Navegación ─────────────────────────────────────────────
    def _on_tab_switch(self, instance_navigation_bar,
                       instance_tab, instance_tab_label,
                       tab_text: str) -> None:
        screen_map = {
            "Inicio":    "dashboard",
            "Gráficos":  "charts",
            "Mapa":      "map",
        }
        target = screen_map.get(tab_text, "dashboard")
        self._sm.current = target

    # ── Ciclo de datos ─────────────────────────────────────────
    def _refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        key  = Config.API_KEY.strip()
        city = Config.CITY
        demo = not bool(key)
        threading.Thread(
            target=self._fetch,
            args=(key, city, demo),
            daemon=True,
        ).start()

    def _fetch(self, key: str, city: str, demo: bool) -> None:
        try:
            if demo or not key:
                wd   = WeatherData.demo(city.split(",")[0])
                fc   = self._demo_forecast(wd)
                mode = "DEMO"
            else:
                api  = WeatherAPI(key)
                wd   = api.fetch_current(city)
                fc   = api.fetch_forecast(city)
                mode = "API"

            self._current  = wd
            self._forecast = fc
            self._history.push(wd)

            threading.Thread(
                target=Notifier.evaluate, args=(wd,), daemon=True
            ).start()

            Clock.schedule_once(lambda dt: self._render(mode), 0)

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._show_error(str(e)), 0)
        finally:
            self._busy = False

    def _demo_forecast(self, base: WeatherData) -> list[dict]:
        now   = datetime.now()
        icons = ["01d","02d","03d","10d","09d","11d"]
        result = []
        for i in range(8):
            dt = now + timedelta(hours=3 * i)
            result.append({
                "hour":  "Ahora" if i == 0 else dt.strftime("%H:%M"),
                "temp":  round(base.temp + random.uniform(-3, 3), 1),
                "icon":  random.choice(icons),
                "humid": random.randint(55, 88),
                "wind":  round(random.uniform(8, 30), 1),
                "rain":  round(random.uniform(0, 3), 1),
            })
        return result

    def _on_map_city_selected(self, city: str) -> None:
        """Ciudad seleccionada en el mapa → actualizar Config y refrescar."""
        from config import Config
        if "," not in city:
            Config.CITY = f"{city},CO"
        else:
            Config.CITY = city
        self._refresh()

    # ── Render (hilo principal vía Clock) ──────────────────────
    def _render(self, mode: str) -> None:
        wd = self._current
        self._dash.refresh(wd)
        self._dash.update_forecast(self._forecast)
        self._charts.refresh(wd)
        self._map.refresh(wd)

    def _show_error(self, msg: str) -> None:
        snack = MDSnackbar(
            text=f"Error: {msg[:60]}",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            duration=4,
        )
        snack.open()


# ── Buildozer spec helpers ─────────────────────────────────────
if __name__ == "__main__":
    MeteoApp().run()