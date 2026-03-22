"""
widgets/compass_canvas.py — Brújula animada dibujada en Canvas.
No hereda de tk.Canvas para evitar conflictos con Python 3.13.
"""
import math
import tkinter as tk

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class CompassCanvas(BaseWidget):
    """
    Brújula que muestra la dirección del viento.
    Usa un tk.Canvas interno (composición, no herencia).
    Se redibuja automáticamente al redimensionar.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        self._angle = 0.0
        self._cv = tk.Canvas(self, bg=Theme.CARD,
                             highlightthickness=0)
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", lambda _: self._draw())

    def refresh(self, data: WeatherData) -> None:
        self._angle = data.wind_deg
        self._draw()

    def _draw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w // 2, h // 2
        r  = min(cx, cy) - 8
        r2 = r - 12

        # Anillos
        cv.create_oval(cx-r,  cy-r,  cx+r,  cy+r,
                       outline=Theme.BORDER_DARK, width=1.5,
                       fill=Theme.CARD_ALT)
        cv.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                       outline=Theme.BORDER, width=0.8, fill="")

        # Puntos cardinales
        for deg, lbl in [(0,"N"),(90,"E"),(180,"S"),(270,"O")]:
            rad   = math.radians(deg - 90)
            tx    = cx + (r - 10) * math.cos(rad)
            ty    = cy + (r - 10) * math.sin(rad)
            color = Theme.ACCENT if lbl == "N" else Theme.TEXT_MUT
            bold  = "bold" if lbl == "N" else "normal"
            cv.create_text(tx, ty, text=lbl, fill=color,
                           font=(Theme.FONT_MONO, 7, bold))

        # Ticks cada 45°
        for deg in range(0, 360, 45):
            rad = math.radians(deg - 90)
            x1  = cx + (r - 16) * math.cos(rad)
            y1  = cy + (r - 16) * math.sin(rad)
            x2  = cx + r2 * math.cos(rad)
            y2  = cy + r2 * math.sin(rad)
            cv.create_line(x1, y1, x2, y2,
                           fill=Theme.BORDER_DARK, width=0.8)

        # Aguja
        rad    = math.radians(self._angle - 90)
        ar     = r2 - 6
        tip_x  = cx + ar * math.cos(rad)
        tip_y  = cy + ar * math.sin(rad)
        tail_x = cx - (ar // 2) * math.cos(rad)
        tail_y = cy - (ar // 2) * math.sin(rad)
        perp   = math.radians(self._angle)
        wx_    = 5 * math.cos(perp)
        wy_    = 5 * math.sin(perp)

        # Mitad norte — azul
        cv.create_polygon(
            tip_x, tip_y, cx+wx_, cy+wy_,
            cx, cy, cx-wx_, cy-wy_,
            fill=Theme.ACCENT, outline="",
        )
        # Mitad sur — gris
        cv.create_polygon(
            tail_x, tail_y, cx+wx_, cy+wy_,
            cx, cy, cx-wx_, cy-wy_,
            fill=Theme.BORDER_DARK, outline="",
        )
        # Centro
        cv.create_oval(cx-5, cy-5, cx+5, cy+5,
                       fill=Theme.SURFACE,
                       outline=Theme.ACCENT, width=1.5)
