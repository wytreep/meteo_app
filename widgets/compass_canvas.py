"""
widgets/compass_canvas.py — Brújula con rotación suave animada.

Mejoras v2:
  - Rotación interpolada (easing) al cambiar la dirección del viento
  - Anillos de grados con marcas cada 30°
  - Aguja con sombra para profundidad
  - Ícono de viento en el centro
  - Hover muestra el ángulo exacto
"""
import math
import tkinter as tk

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class CompassCanvas(BaseWidget):
    """Brújula animada con interpolación suave al actualizar el viento."""

    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        self._target  = 0.0    # ángulo destino
        self._current = 0.0    # ángulo actual (interpolado)
        self._animating = False
        self._hovered   = False

        self._cv = tk.Canvas(self, bg=Theme.CARD, highlightthickness=0)
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", lambda _: self._draw())
        self._cv.bind("<Enter>",     self._on_enter)
        self._cv.bind("<Leave>",     self._on_leave)

    def refresh(self, data: WeatherData) -> None:
        # Calcular camino más corto (evitar giro largo)
        diff = (data.wind_deg - self._target + 180) % 360 - 180
        self._target = self._current + diff
        if not self._animating:
            self._animating = True
            self._step()

    def _step(self) -> None:
        diff = self._target - self._current
        if abs(diff) < 0.3:
            self._current = self._target % 360
            self._animating = False
        else:
            self._current += diff * 0.12   # easing exponencial
        self._draw()
        if self._animating:
            self.after(16, self._step)     # ~60 fps

    def _on_enter(self, _=None):
        self._hovered = True
        self._draw()

    def _on_leave(self, _=None):
        self._hovered = False
        self._draw()

    def _draw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w / 2, h / 2
        r      = min(cx, cy) - 6
        r_inner = r - 14
        angle   = self._current % 360

        # ── Fondo del disco ──────────────────────────────────
        cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=Theme.CARD_ALT,
                       outline=Theme.BORDER_DARK, width=1.5)

        # ── Marcas de grados cada 30° ──────────────────────
        for deg in range(0, 360, 30):
            rad  = math.radians(deg - 90)
            long = deg % 90 == 0   # cardinales más largas
            r1   = r - (18 if long else 12)
            r2   = r - 4
            x1   = cx + r1 * math.cos(rad)
            y1   = cy + r1 * math.sin(rad)
            x2   = cx + r2 * math.cos(rad)
            y2   = cy + r2 * math.sin(rad)
            cv.create_line(x1, y1, x2, y2,
                           fill=Theme.BORDER_DARK if not long else Theme.TEXT_MUT,
                           width=1.5 if long else 0.8)

        # ── Anillo interior ───────────────────────────────
        cv.create_oval(cx-r_inner, cy-r_inner,
                       cx+r_inner, cy+r_inner,
                       outline=Theme.BORDER, width=0.6, fill="")

        # ── Puntos cardinales ─────────────────────────────
        for deg, lbl in [(0,"N"),(90,"E"),(180,"S"),(270,"O")]:
            rad   = math.radians(deg - 90)
            tx    = cx + (r - 10) * math.cos(rad)
            ty    = cy + (r - 10) * math.sin(rad)
            is_n  = lbl == "N"
            cv.create_text(tx, ty, text=lbl,
                           fill=Theme.ACCENT if is_n else Theme.TEXT_MUT,
                           font=(Theme.FONT_MONO, 7, "bold" if is_n else "normal"))

        # ── Aguja — sombra ───────────────────────────────
        rad    = math.radians(angle - 90)
        ar     = r_inner - 8
        tip_x  = cx + ar * math.cos(rad) + 1
        tip_y  = cy + ar * math.sin(rad) + 1
        tail_x = cx - (ar // 2) * math.cos(rad) + 1
        tail_y = cy - (ar // 2) * math.sin(rad) + 1
        perp   = math.radians(angle)
        wx_    = 5 * math.cos(perp)
        wy_    = 5 * math.sin(perp)
        cv.create_polygon(
            tip_x, tip_y, cx+wx_+1, cy+wy_+1,
            tail_x, tail_y, cx-wx_+1, cy-wy_+1,
            fill=Theme.BORDER, outline="", stipple="gray50"
        )

        # ── Aguja — mitad norte (azul) ────────────────────
        tip_x  = cx + ar * math.cos(rad)
        tip_y  = cy + ar * math.sin(rad)
        tail_x = cx - (ar // 2) * math.cos(rad)
        tail_y = cy - (ar // 2) * math.sin(rad)
        cv.create_polygon(
            tip_x, tip_y, cx+wx_, cy+wy_,
            cx, cy, cx-wx_, cy-wy_,
            fill=Theme.ACCENT, outline=Theme.ACCENT_DARK, width=0.5
        )
        # Mitad sur (gris)
        cv.create_polygon(
            tail_x, tail_y, cx+wx_, cy+wy_,
            cx, cy, cx-wx_, cy-wy_,
            fill=Theme.BORDER_DARK, outline=""
        )

        # ── Centro ────────────────────────────────────────
        cv.create_oval(cx-6, cy-6, cx+6, cy+6,
                       fill=Theme.SURFACE,
                       outline=Theme.ACCENT, width=2)
        cv.create_oval(cx-2, cy-2, cx+2, cy+2,
                       fill=Theme.ACCENT, outline="")

        # ── Ángulo en hover ───────────────────────────────
        if self._hovered:
            deg_str = f"{int(angle % 360)}°"
            cv.create_text(cx, cy + r + 14,
                           text=deg_str,
                           font=(Theme.FONT_MONO, 8),
                           fill=Theme.TEXT_SEC)