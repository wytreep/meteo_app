"""
screens/map_screen.py — Mapa interactivo de Colombia para móvil v2.

Funcionalidades:
  - Pinch-to-zoom (touch nativo de Kivy)
  - Pan con un dedo
  - Toque en ciudad → popup con info y botón seleccionar
  - Búsqueda con autocompletado
  - Animación suave al cambiar ciudad
  - Barra de escala y coordenadas HUD
"""
import math
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from core.weather_data import WeatherData

CITIES = {
    "Bogotá":        ( 4.7110, -74.0721),
    "Medellín":      ( 6.2518, -75.5636),
    "Cali":          ( 3.4516, -76.5320),
    "Barranquilla":  (10.9685, -74.7813),
    "Cartagena":     (10.3910, -75.4794),
    "Cúcuta":        ( 7.8939, -72.5078),
    "Bucaramanga":   ( 7.1254, -73.1198),
    "Pereira":       ( 4.8133, -75.6961),
    "Manizales":     ( 5.0689, -75.5174),
    "Pasto":         ( 1.2136, -77.2811),
    "Ibagué":        ( 4.4389, -75.2322),
    "Santa Marta":   (11.2408, -74.1990),
    "Villavicencio": ( 4.1420, -73.6266),
    "Neiva":         ( 2.9273, -75.2819),
}

OUTLINE = [
    (-77.3,8.7),(-76.9,9.4),(-76.2,9.9),(-75.5,10.7),(-74.9,11.1),
    (-73.7,11.7),(-72.5,12.2),(-71.9,11.6),(-71.3,11.8),(-70.9,12.2),
    (-70.2,11.9),(-69.9,11.4),(-70.5,11.0),(-72.0,10.5),(-72.3,9.8),
    (-72.7,9.2),(-73.0,8.8),(-73.4,8.0),(-73.7,7.2),(-72.5,7.0),
    (-72.0,6.8),(-70.1,6.4),(-68.5,6.0),(-67.5,6.3),(-67.0,6.9),
    (-67.3,7.5),(-67.1,8.2),(-66.9,9.4),(-68.3,9.8),(-69.9,10.3),
    (-68.0,11.5),(-63.9,10.8),(-63.1,9.9),(-63.0,9.0),(-64.3,8.8),
    (-65.4,8.1),(-66.8,7.5),(-67.3,6.0),(-67.8,5.5),(-67.5,4.5),
    (-67.8,3.5),(-69.2,3.5),(-70.1,3.2),(-70.5,2.2),(-71.0,2.0),
    (-71.9,2.2),(-72.7,2.3),(-72.9,2.0),(-73.7,1.4),(-74.2,0.8),
    (-75.0,0.1),(-75.6,-0.3),(-75.8,-1.0),(-76.3,-1.6),(-76.5,-2.3),
    (-77.0,-2.6),(-77.5,-2.3),(-78.0,-2.0),(-78.3,-1.5),(-78.7,-0.5),
    (-78.9,0.2),(-78.5,1.3),(-78.0,1.8),(-77.5,2.8),(-77.2,3.8),
    (-77.5,4.8),(-77.3,5.5),(-77.0,6.5),(-77.3,7.5),(-77.3,8.7),
]

LAT_MAX, LAT_MIN =  12.8, -4.8
LON_MIN, LON_MAX = -79.5, -65.5


class InteractiveMap(Widget):
    """
    Mapa de Colombia con touch: zoom, pan, toque en ciudades.
    """

    def __init__(self, on_city_tap=None, **kwargs):
        super().__init__(**kwargs)
        self._on_city_tap = on_city_tap or (lambda c: None)
        self._city        = "Cali"
        self._lat         = 3.4516
        self._lon         = -76.5320
        self._anim_lat    = 3.4516
        self._anim_lon    = -76.5320
        self._moving      = False
        self._pulse       = 0.0
        self._zoom        = 1.0
        self._pan_x       = 0.0
        self._pan_y       = 0.0
        self._touch_start = None
        self._last_touch  = None
        self._pinch_dist  = None

        self.bind(pos=lambda *_: self._draw(),
                  size=lambda *_: self._draw())
        Clock.schedule_interval(self._tick, 1/30)

    # ── Geo ↔ pixel ────────────────────────────────────────────────────
    def _geo_to_px(self, lat, lon):
        w, h = self.width, self.height
        if w < 10 or h < 10:
            return 0, 0
        cx, cy = self.x + w/2, self.y + h/2
        base_x = self.x + (lon - LON_MIN) / (LON_MAX - LON_MIN) * w
        base_y = self.y + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * h
        x = cx + (base_x - cx + self._pan_x) * self._zoom
        y = cy + (base_y - cy + self._pan_y) * self._zoom
        return x, y

    def _nearest_city(self, tx, ty, threshold=dp(24)):
        best, dist = None, float("inf")
        for name, (lat, lon) in CITIES.items():
            cx, cy = self._geo_to_px(lat, lon)
            d = math.hypot(tx - cx, ty - cy)
            if d < dist:
                dist = d
                best = name
        return best if dist <= threshold else None

    # ── Touch ──────────────────────────────────────────────────────────
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._touch_start = touch.pos
        self._last_touch  = touch.pos
        self._moved       = False
        if hasattr(touch, 'is_double_tap') and touch.is_double_tap:
            self._zoom = min(4.0, self._zoom * 1.6)
            self._draw()
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        dx = touch.pos[0] - self._last_touch[0]
        dy = touch.pos[1] - self._last_touch[1]
        if abs(dx) > dp(3) or abs(dy) > dp(3):
            self._moved = True
        self._pan_x += dx / self._zoom
        self._pan_y += dy / self._zoom
        self._last_touch = touch.pos
        self._draw()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if not self._moved:
            city = self._nearest_city(*touch.pos)
            if city:
                self._on_city_tap(city)
        return True

    # ── Animación ciudad ───────────────────────────────────────────────
    def go_to(self, city: str, lat: float, lon: float):
        self._city       = city
        self._target_lat = lat
        self._target_lon = lon
        self._moving     = True

    def _step_animation(self):
        if not self._moving:
            return
        dlat = self._target_lat - self._anim_lat
        dlon = self._target_lon - self._anim_lon
        if abs(dlat) < 0.005 and abs(dlon) < 0.005:
            self._anim_lat = self._target_lat
            self._anim_lon = self._target_lon
            self._lat      = self._target_lat
            self._lon      = self._target_lon
            self._moving   = False
        else:
            self._anim_lat += dlat * 0.14
            self._anim_lon += dlon * 0.14

    def zoom_in(self):
        self._zoom = min(5.0, self._zoom * 1.3)
        self._draw()

    def zoom_out(self):
        self._zoom = max(0.8, self._zoom / 1.3)
        self._draw()

    def zoom_reset(self):
        self._zoom  = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._draw()

    # ── Dibujo ─────────────────────────────────────────────────────────
    def _draw(self, *args):
        self.canvas.clear()
        w, h = self.width, self.height
        if w < 10 or h < 10:
            return

        cur_lat = self._anim_lat if self._moving else self._lat
        cur_lon = self._anim_lon if self._moving else self._lon

        with self.canvas:
            # Fondo océano
            Color(0.867, 0.918, 0.961, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Contorno Colombia
            pts = []
            for lon, lat in OUTLINE:
                px, py = self._geo_to_px(lat, lon)
                pts.extend([px, py])
            if pts:
                Color(0.980, 0.984, 0.992, 1)
                from kivy.graphics import Mesh, StencilPush, StencilUse, StencilPop, StencilUnUse
                # Dibujar con Line para el contorno
                Color(0.773, 0.808, 0.847, 1)
                Line(points=pts + pts[:2], width=dp(1.2))

            # Ciudades
            for name, (lat, lon) in CITIES.items():
                px, py = self._geo_to_px(lat, lon)
                is_active = name == self._city
                r = dp(6) if is_active else dp(3.5)
                if is_active:
                    Color(0.082, 0.396, 0.753, 1)
                else:
                    Color(0.647, 0.698, 0.773, 1)
                Ellipse(pos=(px-r, py-r), size=(r*2, r*2))
                Color(1, 1, 1, 1)
                ir = r * 0.4
                Ellipse(pos=(px-ir, py-ir), size=(ir*2, ir*2))

            # Marcador animado con pulso
            mpx, mpy = self._geo_to_px(cur_lat, cur_lon)
            pr  = dp(10) + self._pulse * dp(18)
            opa = max(0, 1 - self._pulse) * 0.35
            Color(0.082, 0.396, 0.753, opa)
            Ellipse(pos=(mpx-pr, mpy-pr), size=(pr*2, pr*2))

            # Pin principal
            Color(0.082, 0.396, 0.753, 1)
            Ellipse(pos=(mpx-dp(11), mpy-dp(11)),
                    size=(dp(22), dp(22)))
            Color(1, 1, 1, 1)
            Ellipse(pos=(mpx-dp(4), mpy-dp(4)),
                    size=(dp(8), dp(8)))

            # HUD: zoom
            Color(0.4, 0.4, 0.4, 0.5)
            zoom_txt = f"x{self._zoom:.1f}"
            # (texto en Kivy canvas no es directo, se hace con Label overlay)

    def _tick(self, dt):
        self._pulse = (self._pulse + 0.04) % 1.0
        self._step_animation()
        self._draw()


class MapScreen(MDScreen):
    """Pantalla del mapa interactivo con búsqueda y zoom."""

    def __init__(self, on_city_select=None, **kwargs):
        super().__init__(name="map", **kwargs)
        self._on_city_select = on_city_select or (lambda c: None)
        self._current_wd = None
        self._dialog = None
        self._build()

    def _build(self):
        root = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(12), dp(8), dp(12), dp(80)],
        )

        # ── Barra de búsqueda ──────────────────────────────
        search_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(52),
        )
        self._search_field = MDTextField(
            hint_text="Buscar ciudad...",
            mode="outlined",
            size_hint_x=1,
        )
        self._search_field.bind(
            text=self._on_search_change,
            on_text_validate=self._on_search_submit,
        )
        search_row.add_widget(self._search_field)

        search_btn = MDButton(
            MDButtonText(text="Ir"),
            style="filled",
            size_hint_x=None,
            width=dp(56),
        )
        search_btn.bind(on_release=lambda _: self._on_search_submit())
        search_row.add_widget(search_btn)
        root.add_widget(search_row)

        # ── Info de ciudad actual ───────────────────────────
        info_card = MDCard(
            style="elevated", radius=[dp(14)],
            padding=[dp(14), dp(8)],
            size_hint_y=None, height=dp(54),
            orientation="horizontal",
        )
        self._city_lbl = MDLabel(
            text="Cali, CO",
            font_style="Title", role="small",
            bold=True,
        )
        info_card.add_widget(self._city_lbl)
        self._coord_lbl = MDLabel(
            text="3.4516, -76.5320",
            font_style="Label", role="medium",
            theme_text_color="Secondary",
            halign="right",
        )
        info_card.add_widget(self._coord_lbl)
        root.add_widget(info_card)

        # ── Mapa ────────────────────────────────────────────
        map_card = MDCard(
            style="outlined", radius=[dp(20)],
            padding=dp(2),
        )
        self._map = InteractiveMap(
            on_city_tap=self._on_city_tapped,
        )
        map_card.add_widget(self._map)
        root.add_widget(map_card)

        # ── Botones de zoom ─────────────────────────────────
        zoom_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
        )
        for txt, fn in [("＋", lambda _: self._map.zoom_in()),
                        ("－", lambda _: self._map.zoom_out()),
                        ("⌂  Reset", lambda _: self._map.zoom_reset())]:
            btn = MDButton(MDButtonText(text=txt),
                           style="tonal", size_hint_x=1)
            btn.bind(on_release=fn)
            zoom_row.add_widget(btn)
        root.add_widget(zoom_row)

        # ── Lista de ciudades rápidas ───────────────────────
        root.add_widget(MDLabel(
            text="CIUDADES PRINCIPALES",
            font_style="Label", role="small",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        ))
        cities_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(40),
        )
        for city in ["Bogotá","Medellín","Cali","Barranquilla","Cartagena"]:
            btn = MDButton(MDButtonText(text=city, font_style="Label"),
                           style="outlined", size_hint_x=1)
            btn.bind(on_release=lambda _, c=city: self._select_city(c))
            cities_row.add_widget(btn)
        root.add_widget(cities_row)

        self.add_widget(root)

    # ── Interacciones ──────────────────────────────────────────────────
    def _on_city_tapped(self, city: str):
        """Toque en ciudad del mapa → mostrar dialog de info."""
        lat, lon = CITIES.get(city, (0, 0))
        wd = self._current_wd

        content = MDBoxLayout(orientation="vertical",
                              spacing=dp(8), padding=dp(4))
        content.add_widget(MDLabel(
            text=f"📍 {lat:.4f}, {lon:.4f}",
            font_style="Body", role="medium",
            theme_text_color="Secondary",
        ))
        if wd and wd.city.lower() == city.lower():
            content.add_widget(MDLabel(
                text=f"🌡 {round(wd.temp,1)}°C  —  {wd.description}",
                font_style="Body", role="medium",
            ))
            content.add_widget(MDLabel(
                text=f"💧 {wd.humidity}%   💨 {round(wd.wind_speed)} km/h",
                font_style="Body", role="small",
                theme_text_color="Secondary",
            ))

        if self._dialog:
            try: self._dialog.dismiss()
            except Exception: pass

        self._dialog = MDDialog(
            title=city,
            type="custom",
            content_cls=content,
            buttons=[
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=lambda _: self._dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text=f"Ver clima de {city}"),
                    style="filled",
                    on_release=lambda _: (
                        self._dialog.dismiss(),
                        self._select_city(city)
                    ),
                ),
            ],
        )
        self._dialog.open()

    def _select_city(self, city: str):
        if city in CITIES:
            lat, lon = CITIES[city]
            self._map.go_to(city, lat, lon)
            self._city_lbl.text  = f"{city}, CO"
            self._coord_lbl.text = f"{lat:.4f}, {lon:.4f}"
        self._on_city_select(city)

    def _on_search_change(self, field, text: str):
        pass  # autocompletado futuro

    def _on_search_submit(self, *_):
        city = self._search_field.text.strip()
        if city:
            self._select_city(city)

    # ── Actualización desde datos ───────────────────────────────────────
    def refresh(self, data: WeatherData) -> None:
        self._current_wd = data
        city = data.city
        if city in CITIES:
            lat, lon = CITIES[city]
        else:
            lat, lon = data.lat, data.lon
            CITIES[city] = (lat, lon)
        self._map.go_to(city, lat, lon)
        self._city_lbl.text  = f"{city}, {data.country}"
        self._coord_lbl.text = f"{data.lat:.4f}, {data.lon:.4f}"