"""
widgets/map_canvas.py — Mapa interactivo de Colombia v2.

Funcionalidades:
  - Zoom in/out con rueda del mouse o botones +/-
  - Pan (arrastrar) con click izquierdo
  - Clic en ciudad → muestra popup con clima y selecciona ciudad
  - Clic derecho → menú contextual con ciudades
  - Buscar ciudad con autocompletado en tiempo real
  - Cambiar ciudad desde header mueve el marcador con animación
  - Callback on_city_select para notificar al orquestador
"""
import math
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


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
    "Montería":      ( 8.7575, -75.8876),
    "Villavicencio": ( 4.1420, -73.6266),
    "Neiva":         ( 2.9273, -75.2819),
    "Armenia":       ( 4.5339, -75.6811),
    "Popayán":       ( 2.4448, -76.6147),
    "Valledupar":    (10.4631, -73.2532),
}

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

# Límites base del mapa
LAT_MAX, LAT_MIN =  12.8, -4.8
LON_MIN, LON_MAX = -79.5, -65.5


class CityPopup(tk.Toplevel):
    """Mini popup que muestra info del clima al hacer clic en una ciudad."""

    def __init__(self, parent, city: str, wd: Optional[WeatherData],
                 on_select: Callable, rx: int, ry: int):
        super().__init__(parent)
        self.wm_overrideredirect(True)
        self.wm_geometry(f"+{rx+12}+{ry-10}")
        self.configure(bg=Theme.SURFACE)
        self.attributes("-topmost", True)

        outer = tk.Frame(self, bg=Theme.ACCENT, padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=Theme.SURFACE, padx=14, pady=10)
        inner.pack()

        # Nombre ciudad
        tk.Label(inner, text=city, font=(Theme.FONT_SANS, 11, "bold"),
                 fg=Theme.TEXT, bg=Theme.SURFACE).pack(anchor="w")

        if wd and wd.city.lower() == city.lower():
            tk.Frame(inner, bg=Theme.BORDER, height=1).pack(
                fill="x", pady=(4, 6))
            info = [
                (f"{round(wd.temp, 1)}°C", wd.description),
                (f"💧 {wd.humidity}%", f"💨 {round(wd.wind_speed)} km/h"),
            ]
            for line in info:
                row = tk.Frame(inner, bg=Theme.SURFACE)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=line[0], font=(Theme.FONT_MONO, 9),
                         fg=Theme.ACCENT, bg=Theme.SURFACE).pack(side="left")
                tk.Label(row, text=f"  {line[1]}", font=(Theme.FONT_MONO, 9),
                         fg=Theme.TEXT_SEC, bg=Theme.SURFACE).pack(side="left")
        else:
            tk.Label(inner, text="Clic para ver el clima",
                     font=(Theme.FONT_MONO, 8),
                     fg=Theme.TEXT_MUT, bg=Theme.SURFACE).pack(anchor="w")

        # Botón seleccionar
        tk.Button(inner, text=f"→  Ver clima de {city}",
                  font=(Theme.FONT_SANS, 9),
                  bg=Theme.ACCENT, fg="white",
                  relief="flat", padx=8, pady=4,
                  cursor="hand2",
                  command=lambda: (on_select(city), self.destroy())
                  ).pack(fill="x", pady=(8, 0))

        self.bind("<FocusOut>", lambda _: self.destroy())
        self.bind("<Escape>",   lambda _: self.destroy())
        self.after(5000, self._safe_destroy)

    def _safe_destroy(self):
        try: self.destroy()
        except Exception: pass


class MapCanvas(BaseWidget):
    """
    Mapa interactivo de Colombia con zoom, pan, clic en ciudades
    y búsqueda con autocompletado.
    """

    def __init__(self, parent, on_city_select: Callable = None):
        super().__init__(parent, bg=Theme.CARD)
        self._on_city_select = on_city_select or (lambda c: None)

        # Estado de posición
        self._lat    = 3.4516
        self._lon    = -76.5320
        self._city   = "Cali"
        self._wd     : Optional[WeatherData] = None
        self._pulse  = 0.0

        # Estado de animación de movimiento
        self._anim_lat = 3.4516
        self._anim_lon = -76.5320
        self._moving   = False

        # Estado de zoom y pan
        self._zoom   = 1.0          # 1.0 = vista completa
        self._zoom_min = 0.8
        self._zoom_max = 6.0
        self._pan_x  = 0.0          # offset de pan en píxeles del mapa base
        self._pan_y  = 0.0
        self._drag_start = None

        # Popup activo
        self._popup  = None

        self._build()

    def _build(self):
        # Barra de búsqueda
        search_bar = tk.Frame(self, bg=Theme.CARD, pady=4, padx=6)
        search_bar.pack(fill="x")

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        search_entry = tk.Entry(
            search_bar, textvariable=self._search_var,
            font=(Theme.FONT_MONO, 9),
            bg=Theme.CARD_ALT, fg=Theme.TEXT,
            relief="flat", highlightthickness=1,
            highlightcolor=Theme.ACCENT,
            highlightbackground=Theme.BORDER,
            insertbackground=Theme.TEXT
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        search_entry.insert(0, "Buscar ciudad...")
        search_entry.bind("<FocusIn>",  self._search_focus_in)
        search_entry.bind("<FocusOut>", self._search_focus_out)
        search_entry.bind("<Return>",   self._search_enter)
        search_entry.bind("<Down>",     lambda e: self._suggest_lb.focus())
        self._search_entry = search_entry

        # Botones zoom
        zoom_f = tk.Frame(search_bar, bg=Theme.CARD)
        zoom_f.pack(side="right", padx=(6, 0))
        for txt, fn in [("+", self._zoom_in), ("−", self._zoom_out),
                        ("⌂", self._zoom_reset)]:
            tk.Button(zoom_f, text=txt, font=("", 10, "bold"),
                      bg=Theme.CARD_ALT, fg=Theme.ACCENT,
                      relief="flat", width=2, cursor="hand2",
                      highlightthickness=1,
                      highlightbackground=Theme.BORDER,
                      command=fn).pack(side="left", padx=1)

        # Canvas del mapa
        self._cv = tk.Canvas(self, bg=Theme.ACCENT_LIGHT,
                             highlightthickness=0, cursor="crosshair")
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>",     lambda _: self._draw())
        self._cv.bind("<ButtonPress-1>", self._on_press)
        self._cv.bind("<B1-Motion>",     self._on_drag)
        self._cv.bind("<ButtonRelease-1>", self._on_release)
        self._cv.bind("<MouseWheel>",    self._on_wheel)       # Windows
        self._cv.bind("<Button-4>",      self._on_wheel_up)    # Linux
        self._cv.bind("<Button-5>",      self._on_wheel_down)  # Linux
        self._cv.bind("<ButtonPress-3>", self._on_right_click)
        self._cv.bind("<Motion>",        self._on_motion)

        # Dropdown de sugerencias
        self._suggest_frame = tk.Frame(self, bg=Theme.SURFACE,
                                       highlightthickness=1,
                                       highlightbackground=Theme.BORDER)
        self._suggest_lb = tk.Listbox(
            self._suggest_frame,
            font=(Theme.FONT_MONO, 9),
            bg=Theme.SURFACE, fg=Theme.TEXT,
            selectbackground=Theme.ACCENT,
            selectforeground="white",
            relief="flat", borderwidth=0,
            activestyle="none", height=6
        )
        self._suggest_lb.pack(fill="both", expand=True)
        self._suggest_lb.bind("<<ListboxSelect>>", self._on_suggest_select)
        self._suggest_lb.bind("<Return>",           self._on_suggest_select)
        self._suggest_lb.bind("<Escape>",
                              lambda _: self._suggest_frame.place_forget())
        self._suggest_visible = False

        self.after(60, self._tick)

    # ── Coordenadas geo ↔ píxel ─────────────────────────────────────────
    def _geo_to_px(self, lat: float, lon: float) -> tuple[float, float]:
        w = self._cv.winfo_width()
        h = self._cv.winfo_height()
        if w < 10 or h < 10:
            return 0, 0
        lat_range = LAT_MAX - LAT_MIN
        lon_range = LON_MAX - LON_MIN
        base_x = (lon - LON_MIN) / lon_range * w
        base_y = (LAT_MAX - lat) / lat_range * h
        cx, cy = w / 2, h / 2
        x = cx + (base_x - cx + self._pan_x) * self._zoom
        y = cy + (base_y - cy + self._pan_y) * self._zoom
        return x, y

    def _px_to_geo(self, px: float, py: float) -> tuple[float, float]:
        w = self._cv.winfo_width()
        h = self._cv.winfo_height()
        cx, cy = w / 2, h / 2
        base_x = (px - cx) / self._zoom + cx - self._pan_x
        base_y = (py - cy) / self._zoom + cy - self._pan_y
        lon = base_x / w * (LON_MAX - LON_MIN) + LON_MIN
        lat = LAT_MAX - base_y / h * (LAT_MAX - LAT_MIN)
        return lat, lon

    # ── Ciudad más cercana a un punto ──────────────────────────────────
    def _nearest_city(self, px: float, py: float,
                      threshold: float = 18) -> Optional[str]:
        best_name = None
        best_dist = float("inf")
        for name, (lat, lon) in CITIES.items():
            cx, cy = self._geo_to_px(lat, lon)
            d = math.hypot(px - cx, py - cy)
            if d < best_dist:
                best_dist = d
                best_name = name
        return best_name if best_dist <= threshold else None

    # ── Zoom ────────────────────────────────────────────────────────────
    def _zoom_in(self, factor: float = 1.4):
        self._zoom = min(self._zoom_max, self._zoom * factor)
        self._draw()

    def _zoom_out(self, factor: float = 1.4):
        self._zoom = max(self._zoom_min, self._zoom / factor)
        self._draw()

    def _zoom_reset(self):
        self._zoom  = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._draw()

    def _on_wheel(self, event):
        factor = 1.15 if event.delta > 0 else 1/1.15
        # Zoom centrado en el cursor
        w = self._cv.winfo_width()
        h = self._cv.winfo_height()
        cx, cy = w/2, h/2
        self._pan_x += (event.x - cx) * (1/self._zoom - 1/(self._zoom*factor))
        self._pan_y += (event.y - cy) * (1/self._zoom - 1/(self._zoom*factor))
        self._zoom = max(self._zoom_min, min(self._zoom_max, self._zoom * factor))
        self._draw()

    def _on_wheel_up(self, _):   self._zoom_in(1.15)
    def _on_wheel_down(self, _): self._zoom_out(1.15)

    # ── Pan ─────────────────────────────────────────────────────────────
    def _on_press(self, event):
        self._drag_start  = (event.x, event.y)
        self._drag_moved  = False
        self._drag_pan_x  = self._pan_x
        self._drag_pan_y  = self._pan_y
        self._cv.configure(cursor="fleur")

    def _on_drag(self, event):
        if not self._drag_start:
            return
        dx = (event.x - self._drag_start[0]) / self._zoom
        dy = (event.y - self._drag_start[1]) / self._zoom
        if abs(dx) > 2 or abs(dy) > 2:
            self._drag_moved = True
        self._pan_x = self._drag_pan_x + dx
        self._pan_y = self._drag_pan_y + dy
        self._draw()

    def _on_release(self, event):
        self._cv.configure(cursor="crosshair")
        if not self._drag_moved:
            self._handle_click(event.x, event.y)
        self._drag_start  = None
        self._drag_moved  = False

    # ── Hover cursor ────────────────────────────────────────────────────
    def _on_motion(self, event):
        city = self._nearest_city(event.x, event.y, threshold=16)
        self._cv.configure(cursor="hand2" if city else "crosshair")

    # ── Clic en ciudad ──────────────────────────────────────────────────
    def _handle_click(self, px: float, py: float):
        city = self._nearest_city(px, py, threshold=20)
        if city:
            if self._popup:
                try: self._popup.destroy()
                except Exception: pass
            rx = self._cv.winfo_rootx() + int(px)
            ry = self._cv.winfo_rooty() + int(py)
            self._popup = CityPopup(
                self, city, self._wd,
                self._on_city_select_internal, rx, ry
            )

    def _on_right_click(self, event):
        """Menú contextual con lista de ciudades."""
        menu = tk.Menu(self, tearoff=0,
                       bg=Theme.SURFACE, fg=Theme.TEXT,
                       font=(Theme.FONT_MONO, 9),
                       activebackground=Theme.ACCENT,
                       activeforeground="white",
                       relief="flat", borderwidth=1)
        menu.add_command(label="── Ir a ciudad ──", state="disabled")
        for name in sorted(CITIES):
            menu.add_command(
                label=f"  {name}",
                command=lambda n=name: self._on_city_select_internal(n))
        menu.add_separator()
        menu.add_command(label="  Restablecer zoom ⌂",
                         command=self._zoom_reset)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_city_select_internal(self, city: str):
        """Selección desde popup o menú → anima el marcador y notifica."""
        if city in CITIES:
            lat, lon = CITIES[city]
            self._animate_to(lat, lon, city)
        self._on_city_select(city)

    # ── Animación suave al cambiar ciudad ───────────────────────────────
    def _animate_to(self, target_lat: float, target_lon: float,
                    city: str):
        self._city = city
        self._target_lat = target_lat
        self._target_lon = target_lon
        self._moving = True
        self._move_step()

    def _move_step(self):
        if not self._moving:
            return
        dlat = self._target_lat - self._anim_lat
        dlon = self._target_lon - self._anim_lon
        if abs(dlat) < 0.005 and abs(dlon) < 0.005:
            self._anim_lat = self._target_lat
            self._anim_lon = self._target_lon
            self._lat = self._target_lat
            self._lon = self._target_lon
            self._moving = False
        else:
            self._anim_lat += dlat * 0.12
            self._anim_lon += dlon * 0.12
        self._draw()
        if self._moving:
            self.after(16, self._move_step)

    # ── Búsqueda con autocompletado ─────────────────────────────────────
    def _search_focus_in(self, _=None):
        if self._search_var.get() == "Buscar ciudad...":
            self._search_entry.delete(0, "end")
            self._search_entry.configure(fg=Theme.TEXT)

    def _search_focus_out(self, _=None):
        if not self._search_var.get().strip():
            self._search_entry.insert(0, "Buscar ciudad...")
            self._search_entry.configure(fg=Theme.TEXT_MUT)
            self._hide_suggestions()

    def _on_search_change(self, *_):
        q = self._search_var.get().strip().lower()
        if not q or q == "buscar ciudad...":
            self._hide_suggestions()
            return
        matches = [n for n in CITIES if q in n.lower()]
        # También buscar ciudades fuera de Colombia por nombre
        extra = [n for n in [
            "Bogota,CO","Medellin,CO","Cali,CO","Barranquilla,CO",
            "Miami,US","Madrid,ES","Buenos Aires,AR","Lima,PE",
            "Ciudad de Mexico,MX","Santiago,CL","Caracas,VE"
        ] if q in n.lower() and n not in matches]
        matches.extend(extra)
        if matches:
            self._show_suggestions(matches)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, items: list):
        self._suggest_lb.delete(0, "end")
        for item in items[:8]:
            self._suggest_lb.insert("end", f"  {item}")
        h = min(len(items), 6) * 22 + 4
        self._suggest_frame.place(
            x=6, y=32, width=self._cv.winfo_width() - 12, height=h)
        self._suggest_frame.lift()
        self._suggest_visible = True

    def _hide_suggestions(self):
        self._suggest_frame.place_forget()
        self._suggest_visible = False

    def _on_suggest_select(self, _=None):
        sel = self._suggest_lb.curselection()
        if not sel:
            return
        city = self._suggest_lb.get(sel[0]).strip()
        self._search_entry.delete(0, "end")
        self._search_entry.insert(0, city)
        self._hide_suggestions()
        self._on_city_select_internal(city)

    def _search_enter(self, _=None):
        q = self._search_var.get().strip()
        if not q or q == "Buscar ciudad...":
            return
        # Buscar coincidencia exacta primero
        for name in CITIES:
            if q.lower() == name.lower():
                self._on_city_select_internal(name)
                return
        # Si no hay coincidencia, enviar directamente a la API
        self._hide_suggestions()
        self._on_city_select(q)

    # ── Dibujo ──────────────────────────────────────────────────────────
    def _draw(self):
        cv = self._cv
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 10 or h < 10:
            return

        # Fondo océano
        cv.create_rectangle(0, 0, w, h, fill="#DDEEFF", outline="")

        # Contorno Colombia
        pts = []
        for lon, lat in OUTLINE:
            px, py = self._geo_to_px(lat, lon)
            pts.extend([px, py])
        if len(pts) >= 4:
            cv.create_polygon(pts, fill=Theme.CARD,
                              outline=Theme.BORDER_DARK,
                              width=1.2, smooth=True)

        # Ciudades secundarias
        cur_lat = self._anim_lat if self._moving else self._lat
        cur_lon = self._anim_lon if self._moving else self._lon

        for name, (lat, lon) in CITIES.items():
            px, py = self._geo_to_px(lat, lon)
            is_active = (name == self._city)
            r = 5 if is_active else 3
            color = Theme.ACCENT if is_active else Theme.BORDER_DARK
            cv.create_oval(px-r, py-r, px+r, py+r,
                           fill=color, outline=Theme.SURFACE, width=1)
            # Etiqueta — solo si zoom suficiente o es ciudad activa
            if self._zoom >= 1.5 or is_active:
                font_size = max(6, min(9, int(7 * self._zoom)))
                cv.create_text(px+6, py, text=name, anchor="w",
                               fill=Theme.ACCENT if is_active else Theme.TEXT_MUT,
                               font=(Theme.FONT_MONO, font_size,
                                     "bold" if is_active else "normal"))

        # Marcador principal con pulso
        mpx, mpy = self._geo_to_px(cur_lat, cur_lon)
        pr  = 8 + self._pulse * 16
        opa = max(0, int(220 * (1 - self._pulse)))
        if opa > 15:
            hex_a  = f"{opa:02x}"
            pcolor = f"#{hex_a}7fb3d3"
            cv.create_oval(mpx-pr, mpy-pr, mpx+pr, mpy+pr,
                           fill="", outline=pcolor, width=1.5)

        cv.create_oval(mpx-10, mpy-10, mpx+10, mpy+10,
                       fill=Theme.ACCENT,
                       outline=Theme.ACCENT_DARK, width=2)
        cv.create_oval(mpx-4, mpy-4, mpx+4, mpy+4,
                       fill=Theme.SURFACE, outline="")

        # Etiqueta ciudad activa
        lw = len(self._city) * 6 + 18
        cv.create_rectangle(mpx+13, mpy-10, mpx+13+lw, mpy+10,
                            fill=Theme.SURFACE,
                            outline=Theme.ACCENT, width=1)
        cv.create_text(mpx+17, mpy, text=self._city, anchor="w",
                       fill=Theme.ACCENT,
                       font=(Theme.FONT_MONO, 9, "bold"))

        # HUD: zoom + coordenadas
        zoom_pct = int(self._zoom * 100)
        cv.create_text(8, h-6, anchor="sw",
                       text=f"Zoom {zoom_pct}%   "
                            f"Lat {cur_lat:.3f}  Lon {cur_lon:.3f}",
                       fill=Theme.TEXT_MUT,
                       font=(Theme.FONT_MONO, 7))

        # Escala visual
        self._draw_scale(cv, w, h)

    def _draw_scale(self, cv, w, h):
        """Barra de escala en km."""
        # 1° lat ≈ 111 km
        lat_range = LAT_MAX - LAT_MIN
        km_per_px = (lat_range * 111) / (h * self._zoom)
        scale_km  = 100  # objetivo
        scale_px  = scale_km / km_per_px
        x0, y0    = 10, h - 22
        x1        = x0 + scale_px
        cv.create_line(x0, y0, x1, y0, fill=Theme.TEXT_SEC, width=1.5)
        cv.create_line(x0, y0-4, x0, y0+4, fill=Theme.TEXT_SEC, width=1.5)
        cv.create_line(x1, y0-4, x1, y0+4, fill=Theme.TEXT_SEC, width=1.5)
        cv.create_text((x0+x1)/2, y0-7, text=f"{scale_km} km",
                       font=(Theme.FONT_MONO, 7),
                       fill=Theme.TEXT_SEC)

    # ── API pública ──────────────────────────────────────────────────────
    def refresh(self, data: WeatherData) -> None:
        self._wd = data
        if data.city != self._city:
            if data.city in CITIES:
                lat, lon = CITIES[data.city]
            else:
                lat, lon = data.lat, data.lon
            self._animate_to(lat, lon, data.city)
        else:
            self._lat  = data.lat
            self._lon  = data.lon

    def set_city_external(self, city: str, lat: float, lon: float):
        """Llamado desde el header cuando el usuario cambia la ciudad."""
        CITIES[city] = (lat, lon)   # agregar si es nueva
        self._animate_to(lat, lon, city)

    # ── Tick de animación ────────────────────────────────────────────────
    def _tick(self):
        self._pulse = (self._pulse + 0.035) % 1.0
        if not self._moving:
            self._draw()
        self.after(60, self._tick)