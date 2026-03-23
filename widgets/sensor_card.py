"""
widgets/sensor_card.py — Tarjeta de sensor con interacciones completas.

Mejoras v2:
  - Iconos SVG dibujados en Canvas (no emojis de texto)
  - Hover con elevación y cambio de borde animado
  - Clic para expandir detalle con estadísticas de sesión
  - Tooltip informativo con descripción del sensor
  - Efecto ripple/scale en el clic
  - Barra de progreso animada con transición suave
"""
import tkinter as tk
import math
from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class SensorIcon(tk.Canvas):
    """Canvas que dibuja un icono vectorial para cada tipo de sensor."""
    SIZE = 28

    def __init__(self, parent, key: str, color: str, **kwargs):
        super().__init__(parent, width=self.SIZE, height=self.SIZE,
                         bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self._key   = key
        self._color = color
        self.after(10, self._draw)

    def set_color(self, color: str) -> None:
        self._color = color
        self._draw()

    def set_bg(self, bg: str) -> None:
        self.configure(bg=bg)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        s = self.SIZE
        c = self._color
        k = self._key
        if   k == "humid":    self._droplet(s, c)
        elif k == "pressure": self._gauge(s, c)
        elif k == "uv":       self._sun(s, c)
        elif k == "vis":      self._eye(s, c)
        elif k == "rain":     self._rain(s, c)
        elif k == "dew":      self._thermo(s, c)
        else:                 self._sun(s, c)

    def _droplet(self, s, c):
        pts = []
        for i in range(20):
            a = math.radians(i * 18)
            rx = 0.38 if a > math.pi else 0.30
            pts.extend([s/2 + s*rx*math.sin(a), s*0.72 - s*0.42*math.cos(a)])
        self.create_polygon(pts, fill=c, outline="", smooth=True)
        self.create_oval(s*0.40, s*0.08, s*0.60, s*0.28, fill=c, outline="")

    def _gauge(self, s, c):
        self.create_arc(s*0.10, s*0.15, s*0.90, s*0.85,
                        start=0, extent=180, style="arc", outline=c, width=2.5)
        angle = math.radians(140)
        cx, cy = s/2, s*0.5
        nx = cx + s*0.28 * math.cos(angle)
        ny = cy - s*0.28 * math.sin(angle)
        self.create_line(cx, cy, nx, ny, fill=c, width=2, capstyle="round")
        self.create_oval(cx-3, cy-3, cx+3, cy+3, fill=c, outline="")

    def _sun(self, s, c):
        cx, cy, r = s/2, s/2, s*0.22
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=c, outline="")
        for i in range(8):
            a = math.radians(i * 45)
            x1 = cx + (r+3)*math.cos(a); y1 = cy + (r+3)*math.sin(a)
            x2 = cx + (r+7)*math.cos(a); y2 = cy + (r+7)*math.sin(a)
            self.create_line(x1, y1, x2, y2, fill=c, width=2, capstyle="round")

    def _eye(self, s, c):
        pts = []
        for i in range(20):
            a = math.radians(i * 18)
            pts.extend([s/2 + s*0.38*math.cos(a), s/2 + s*0.20*math.sin(a)])
        self.create_polygon(pts, fill=Theme.CARD_ALT, outline=c, width=1.8, smooth=True)
        r = s*0.12
        self.create_oval(s/2-r, s/2-r, s/2+r, s/2+r, fill=c, outline="")
        self.create_oval(s/2-r*0.4, s/2-r*0.4, s/2+r*0.4, s/2+r*0.4, fill="white", outline="")

    def _rain(self, s, c):
        self.create_oval(s*0.18, s*0.12, s*0.55, s*0.45, fill=c, outline="")
        self.create_oval(s*0.38, s*0.06, s*0.78, s*0.46, fill=c, outline="")
        self.create_rectangle(s*0.18, s*0.30, s*0.78, s*0.46, fill=c, outline="")
        for x in [0.28, 0.48, 0.68]:
            y0 = s*0.52
            self.create_line(s*x, y0, s*x, y0+s*0.14, fill=c, width=2, capstyle="round")

    def _thermo(self, s, c):
        self.create_rectangle(s*0.43, s*0.10, s*0.57, s*0.65,
                              fill=Theme.CARD_ALT, outline=c, width=1.5)
        self.create_rectangle(s*0.45, s*0.35, s*0.55, s*0.65, fill=c, outline="")
        self.create_oval(s*0.35, s*0.60, s*0.65, s*0.88, fill=c, outline="")


class Tooltip:
    """Tooltip descriptivo con delay de 600ms."""
    DESCRIPTIONS = {
        "humid":    "Humedad relativa del aire.\n100% = aire saturado de vapor.",
        "pressure": "Presión atmosférica en hPa.\nNormal: 1013 hPa al nivel del mar.",
        "uv":       "Índice de radiación ultravioleta.\n6+ = usar protector solar SPF 30+.",
        "vis":      "Distancia máxima de visibilidad.\nMenor a 1 km indica niebla densa.",
        "rain":     "Precipitación acumulada en 1 hora.\n10+ mm/h = lluvia intensa.",
        "dew":      "Temperatura de punto de rocío.\nCerca de la temp. = humedad alta.",
    }

    def __init__(self, widget: tk.Widget, key: str):
        self._widget  = widget
        self._text    = self.DESCRIPTIONS.get(key, "")
        self._win     = None
        self._job     = None
        widget.bind("<Enter>",        self._schedule, add="+")
        widget.bind("<Leave>",        self._hide,     add="+")
        widget.bind("<ButtonPress>",  self._hide,     add="+")

    def _schedule(self, _=None):
        if self._job: self._widget.after_cancel(self._job)
        self._job = self._widget.after(600, self._show)

    def _show(self):
        if self._win: return
        x = self._widget.winfo_rootx() + self._widget.winfo_width() + 6
        y = self._widget.winfo_rooty()
        self._win = tk.Toplevel(self._widget)
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        self._win.configure(bg=Theme.TEXT)
        f = tk.Frame(self._win, bg=Theme.TEXT, padx=10, pady=8)
        f.pack()
        tk.Label(f, text=self._text, font=(Theme.FONT_MONO, 9),
                 fg=Theme.SURFACE, bg=Theme.TEXT, justify="left").pack()

    def _hide(self, _=None):
        if self._job: self._widget.after_cancel(self._job); self._job = None
        if self._win: self._win.destroy(); self._win = None


class DetailPopup(tk.Toplevel):
    """Ventana flotante con estadísticas de sesión del sensor."""
    LABELS = {
        "humid":    ("Humedad",        "%"),
        "pressure": ("Presión",        " hPa"),
        "uv":       ("Índice UV",      ""),
        "vis":      ("Visibilidad",    " km"),
        "rain":     ("Lluvia 1h",      " mm"),
        "dew":      ("Punto de rocío", "°C"),
    }

    def __init__(self, parent, key, stats, color):
        super().__init__(parent)
        name, unit = self.LABELS.get(key, (key, ""))
        self.title(f"Detalle — {name}")
        self.resizable(False, False)
        self.configure(bg=Theme.SURFACE)
        self.attributes("-topmost", True)
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        self.geometry(f"240x210+{px+10}+{py-220}")

        hdr = tk.Frame(self, bg=color, padx=14, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=name, font=(Theme.FONT_SANS, 12, "bold"),
                 fg="white", bg=color).pack(anchor="w")
        tk.Label(hdr, text="Estadísticas de sesión",
                 font=(Theme.FONT_MONO, 8), fg="white", bg=color).pack(anchor="w")

        body = tk.Frame(self, bg=Theme.SURFACE, padx=16, pady=12)
        body.pack(fill="both", expand=True)
        for label, val in [
            ("Actual",   f"{stats['last']}{unit}"),
            ("Mínimo",   f"{stats['min']}{unit}"),
            ("Máximo",   f"{stats['max']}{unit}"),
            ("Promedio", f"{stats['avg']}{unit}"),
        ]:
            row = tk.Frame(body, bg=Theme.SURFACE)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=(Theme.FONT_MONO, 9),
                     fg=Theme.TEXT_SEC, bg=Theme.SURFACE,
                     width=10, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=(Theme.FONT_MONO, 11, "bold"),
                     fg=color, bg=Theme.SURFACE).pack(side="right")
        tk.Label(body, text="Cierra en 4 s…",
                 font=(Theme.FONT_MONO, 7), fg=Theme.TEXT_MUT,
                 bg=Theme.SURFACE).pack(pady=(6, 0))
        self.after(4000, self.destroy)


class SensorCard(BaseWidget):
    """
    Tarjeta de sensor con hover, tooltip, clic-detalle y barra animada.
    """

    def __init__(self, parent, key: str, icon_key: str, label: str,
                 unit: str, color: str, show_bar: bool = True):
        super().__init__(parent, bg=Theme.CARD)
        self.configure(highlightthickness=1,
                       highlightbackground=Theme.BORDER,
                       cursor="hand2")
        self._key      = key
        self._color    = color
        self._show_bar = show_bar
        self._pct      = 0.0
        self._pct_cur  = 0.0
        self._stats    = {"min": 0, "max": 0, "avg": 0, "last": 0}
        self._popup    = None
        self._hovering = False

        self._build(icon_key, label, unit)
        self._bind_all()
        Tooltip(self, key)

    def _build(self, icon_key, label, unit):
        pad = tk.Frame(self, bg=Theme.CARD, padx=12, pady=10)
        pad.pack(fill="both", expand=True)

        top = tk.Frame(pad, bg=Theme.CARD)
        top.pack(fill="x")
        self._icon = SensorIcon(top, icon_key, self._color)
        self._icon.pack(side="left", padx=(0, 8))
        self.label(label, 8, color=Theme.TEXT_MUT, parent=top).pack(side="left", anchor="w")

        self._val_lbl = self.label("—", 20, bold=True, color=self._color, mono=True)
        self._val_lbl.pack(anchor="w", pady=(2, 0))
        if unit:
            self.label(unit, 9, color=Theme.TEXT_SEC).pack(anchor="w")

        if self._show_bar:
            bg_bar = tk.Frame(pad, bg=Theme.BORDER, height=4)
            bg_bar.pack(fill="x", pady=(8, 0))
            self._bar = tk.Frame(bg_bar, bg=self._color, height=4)
            self._bar.place(x=0, y=0, relheight=1, relwidth=0)
            self._animate_bar()
        else:
            self._bar = None

    def _all_widgets(self):
        result = [self]
        def r(w):
            for c in w.winfo_children():
                result.append(c); r(c)
        r(self)
        return result

    def _bind_all(self):
        for w in self._all_widgets():
            w.bind("<Enter>",           self._on_enter,   add="+")
            w.bind("<Leave>",           self._on_leave,   add="+")
            w.bind("<ButtonPress-1>",   self._on_press,   add="+")
            w.bind("<ButtonRelease-1>", self._on_release, add="+")

    def _on_enter(self, _=None):
        self._hovering = True
        self.configure(highlightbackground=self._color, highlightthickness=2)
        self._set_bg(Theme.ACCENT_LIGHT)

    def _on_leave(self, _=None):
        self._hovering = False
        self.configure(highlightbackground=Theme.BORDER, highlightthickness=1)
        self._set_bg(Theme.CARD)

    def _set_bg(self, bg):
        for w in self._all_widgets():
            try:
                if isinstance(w, SensorIcon): w.set_bg(bg)
                elif not isinstance(w, tk.Canvas): w.configure(bg=bg)
            except tk.TclError: pass

    def _on_press(self, _=None):
        self.configure(highlightthickness=3)

    def _on_release(self, _=None):
        self.configure(highlightthickness=2 if self._hovering else 1)
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        else:
            self._popup = DetailPopup(self, self._key, self._stats, self._color)

    def refresh(self, data: WeatherData) -> None:
        pass

    def set_value(self, val: str, pct: float = 0.0,
                  color: str = None, stats: dict = None) -> None:
        self._val_lbl.config(text=val)
        if color:
            self._color = color
            self._val_lbl.config(fg=color)
            if self._bar: self._bar.config(bg=color)
            self._icon.set_color(color)
        self._pct = max(0.0, min(1.0, pct))
        if stats: self._stats = stats

    def _animate_bar(self):
        if self._bar is None: return
        diff = self._pct - self._pct_cur
        self._pct_cur += diff * 0.15 if abs(diff) > 0.002 else diff
        try:
            self._bar.place(relwidth=self._pct_cur)
        except tk.TclError: return
        self.after(16, self._animate_bar)