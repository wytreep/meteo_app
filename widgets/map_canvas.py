"""
widgets/map_canvas.py — Mapa de Colombia dibujado en Canvas.
Sin dependencias externas de mapas.
Muestra la ubicación actual con un marcador animado.
"""
import math
import tkinter as tk

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class MapCanvas(BaseWidget):
    """
    Mapa simplificado de Colombia.
    Animación de pulso en el marcador de la ciudad actual.
    """

    # Límites geográficos de Colombia
    LAT_MAX, LAT_MIN =  12.5, -4.5
    LON_MIN, LON_MAX = -79.0, -66.0

    # Contorno simplificado (lon, lat)
    OUTLINE = [
        (-77.3,8.7),(-76.9,9.4),(-76.2,9.9),(-75.5,10.7),(-74.9,11.1),
        (-73.7,11.7),(-72.5,12.2),(-71.9,11.6),(-71.3,11.8),(-70.9,12.2),
        (-70.2,11.9),(-69.9,11.4),(-70.5,11.0),(-72.0,10.5),(-72.3,9.8),
        (-72.7,9.2),(-73.0,8.8),(-73.4,8.0),(-73.7,7.2),(-72.5,7.0),
        (-72.0,6.8),(-70.1,6.4),(-68.5,6.0),(-67.5,6.3),(-67.0,6.9),
        (-67.3,7.5),(-67.1,8.2),(-66.9,9.4),(-68.3,9.8),(-69.9,10.3),
        (-68.0,11.5),(-67.2,11.2),(-66.6,11.0),(-67.5,12.1),(-67.0,11.5),
        (-63.9,10.8),(-63.1,9.9),(-63.0,9.0),(-64.3,8.8),(-65.4,8.1),
        (-66.8,7.5),(-67.3,6.0),(-67.8,5.5),(-67.5,4.5),(-67.8,3.5),
        (-69.2,3.5),(-70.1,3.2),(-70.5,2.2),(-71.0,2.0),(-71.9,2.2),
        (-72.7,2.3),(-72.9,2.0),(-73.7,1.4),(-74.2,0.8),(-75.0,0.1),
        (-75.6,-0.3),(-75.8,-1.0),(-76.3,-1.6),(-76.5,-2.3),(-77.0,-2.6),
        (-77.5,-2.3),(-78.0,-2.0),(-78.3,-1.5),(-78.7,-0.5),(-78.9,0.2),
        (-78.5,1.3),(-78.0,1.8),(-77.5,2.8),(-77.2,3.8),(-77.5,4.8),
        (-77.3,5.5),(-77.0,6.5),(-77.3,7.5),(-77.3,8.7),
    ]

    CITIES = {
        "Bogotá":       ( 4.71, -74.07),
        "Medellín":     ( 6.25, -75.56),
        "Barranquilla": (11.00, -74.80),
        "Cartagena":    (10.40, -75.50),
        "Cali":         ( 3.45, -76.53),
        "Bucaramanga":  ( 7.10, -73.10),
        "Pereira":      ( 4.80, -75.70),
        "Manizales":    ( 5.07, -75.52),
        "Pasto":        ( 1.21, -77.28),
    }

    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        self._lat   = 3.4516
        self._lon   = -76.5320
        self._city  = "Cali"
        self._pulse = 0.0
        self._cv    = tk.Canvas(self, bg=Theme.CARD,
                                highlightthickness=0)
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", lambda _: self._draw())
        self.after(60, self._tick)

    def refresh(self, data: WeatherData) -> None:
        self._lat  = data.lat
        self._lon  = data.lon
        self._city = data.city
        self._draw()

    # ── Conversión geo → píxel ─────────────────────────────────
    def _geo(self, lat: float, lon: float,
             w: int, h: int) -> tuple[float, float]:
        x = (lon - self.LON_MIN) / (self.LON_MAX - self.LON_MIN) * w
        y = (self.LAT_MAX - lat) / (self.LAT_MAX - self.LAT_MIN) * h
        return x, y

    # ── Renderizado ────────────────────────────────────────────
    def _draw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 10 or h < 10:
            return

        # Fondo oceáno
        cv.create_rectangle(0, 0, w, h,
                            fill=Theme.ACCENT_LIGHT, outline="")

        # Contorno Colombia
        pts = []
        for lon, lat in self.OUTLINE:
            px, py = self._geo(lat, lon, w, h)
            pts.extend([px, py])
        if len(pts) >= 4:
            cv.create_polygon(pts,
                              fill=Theme.CARD,
                              outline=Theme.BORDER_DARK,
                              width=1.2, smooth=True)

        # Ciudades secundarias
        for name, (lat, lon) in self.CITIES.items():
            if name == self._city:
                continue
            px, py = self._geo(lat, lon, w, h)
            cv.create_oval(px-3, py-3, px+3, py+3,
                           fill=Theme.BORDER_DARK, outline="")
            cv.create_text(px+5, py, text=name, anchor="w",
                           fill=Theme.TEXT_MUT,
                           font=(Theme.FONT_MONO, 7))

        # Marcador con pulso animado
        px, py = self._geo(self._lat, self._lon, w, h)
        pr  = 8 + self._pulse * 14
        opa = int(200 * (1 - self._pulse))
        if opa > 20:
            hex_a  = f"{opa:02x}"
            pcolor = f"#{hex_a}8eb4"
            cv.create_oval(px-pr, py-pr, px+pr, py+pr,
                           fill="", outline=pcolor, width=1.5)

        cv.create_oval(px-9, py-9, px+9, py+9,
                       fill=Theme.ACCENT,
                       outline=Theme.ACCENT_DARK, width=1.5)
        cv.create_oval(px-3, py-3, px+3, py+3,
                       fill=Theme.SURFACE, outline="")

        # Etiqueta ciudad
        lw = len(self._city) * 6 + 14
        cv.create_rectangle(px+12, py-9, px+12+lw, py+9,
                            fill=Theme.SURFACE,
                            outline=Theme.BORDER, width=0.8)
        cv.create_text(px+16, py, text=self._city, anchor="w",
                       fill=Theme.ACCENT,
                       font=(Theme.FONT_MONO, 8, "bold"))

        # Coordenadas
        cv.create_text(w-6, h-6,
                       text=f"{self._lat:.2f}, {self._lon:.2f}",
                       anchor="se", fill=Theme.TEXT_MUT,
                       font=(Theme.FONT_MONO, 7))

    def _tick(self) -> None:
        self._pulse = (self._pulse + 0.04) % 1.0
        self._draw()
        self.after(60, self._tick)
