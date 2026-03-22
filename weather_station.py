"""
╔══════════════════════════════════════════════════════════════════╗
║        ESTACIÓN METEOROLÓGICA v2.0 — Python + Tkinter           ║
║   OpenWeatherMap  •  Matplotlib  •  Notificaciones  •  CSV      ║
╚══════════════════════════════════════════════════════════════════╝

Dependencias:
    pip install requests matplotlib pillow

Ejecución:
    python weather_station.py

API Key gratis: https://openweathermap.org/api
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import random
import math
import csv
import os
import sys
import subprocess
import platform
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path

# ── Importaciones opcionales ───────────────────────────────────────────────────
try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.ticker as mticker
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────
API_KEY      = ""           # ← Pega tu API key aquí
CITY         = "Cali,CO"
UNITS        = "metric"     # metric=°C | imperial=°F
INTERVAL     = 30           # segundos entre auto-refresh
HISTORY_LEN  = 120          # puntos de historial
DATA_FILE    = Path("weather_history.csv")

# Umbrales para notificaciones
ALERT_THRESHOLDS = {
    "uv_high":       6,
    "uv_extreme":    9,
    "wind_strong":   45,
    "wind_storm":    70,
    "rain_heavy":    10,
    "pressure_low":  1000,
    "pressure_high": 1025,
    "humidity_high": 90,
    "temp_hot":      35,
    "temp_cold":     10,
}

# ── PALETA ─────────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0a0e1a",
    "surface":  "#0f1628",
    "card":     "#141c30",
    "card2":    "#111827",
    "border":   "#1e3050",
    "accent":   "#4fa3e3",
    "accent2":  "#63b3ff",
    "green":    "#34d399",
    "yellow":   "#fbbf24",
    "orange":   "#f97316",
    "red":      "#ef4444",
    "purple":   "#a78bfa",
    "text":     "#e2e8f0",
    "muted":    "#64748b",
    "dim":      "#94a3b8",
    "cold":     "#38bdf8",
    "chart_bg": "#0d1525",
    "grid":     "#1a2540",
}

# ── DATOS ──────────────────────────────────────────────────────────────────────
class WeatherData:
    """Lectura meteorológica completa."""
    __slots__ = [
        "timestamp","temp","feels_like","temp_min","temp_max",
        "humidity","pressure","wind_speed","wind_deg","wind_gust",
        "clouds","visibility","description","icon_code","uv_index",
        "rain_1h","dew_point","city","country","sunrise","sunset","lat","lon"
    ]

    def __init__(self):
        now = datetime.now()
        for s in self.__slots__:
            setattr(self, s, 0)
        self.timestamp   = now
        self.description = "—"
        self.icon_code   = "01d"
        self.city        = "—"
        self.country     = "CO"
        self.lat         = 3.4516
        self.lon         = -76.5320

    @classmethod
    def from_api(cls, data: dict) -> "WeatherData":
        w    = cls()
        main = data.get("main", {})
        wind = data.get("wind", {})
        wx   = data.get("weather", [{}])[0]
        sys_ = data.get("sys", {})
        rain = data.get("rain", {})
        coord= data.get("coord", {})

        w.timestamp   = datetime.now()
        w.temp        = round(main.get("temp", 0), 1)
        w.feels_like  = round(main.get("feels_like", 0), 1)
        w.temp_min    = round(main.get("temp_min", 0), 1)
        w.temp_max    = round(main.get("temp_max", 0), 1)
        w.humidity    = main.get("humidity", 0)
        w.pressure    = main.get("pressure", 1013)
        w.wind_speed  = round(wind.get("speed", 0) * 3.6, 1)
        w.wind_deg    = wind.get("deg", 0)
        w.wind_gust   = round(wind.get("gust", wind.get("speed",0)) * 3.6, 1)
        w.clouds      = data.get("clouds", {}).get("all", 0)
        w.visibility  = round(data.get("visibility", 10000) / 1000, 1)
        w.description = wx.get("description", "—").capitalize()
        w.icon_code   = wx.get("icon", "01d")
        w.rain_1h     = rain.get("1h", 0.0)
        w.city        = data.get("name", "—")
        w.country     = sys_.get("country", "CO")
        w.sunrise     = sys_.get("sunrise", 0)
        w.sunset      = sys_.get("sunset", 0)
        w.dew_point   = round(w.temp - ((100 - w.humidity) / 5), 1)
        w.lat         = coord.get("lat", 3.4516)
        w.lon         = coord.get("lon", -76.5320)
        return w

    @classmethod
    def demo(cls) -> "WeatherData":
        w    = cls()
        hour = datetime.now().hour
        base = 24 + 6 * math.sin((hour - 6) * math.pi / 12)
        w.temp        = round(base + random.uniform(-1, 1), 1)
        w.feels_like  = round(w.temp + random.uniform(1, 3), 1)
        w.temp_min    = round(w.temp - random.uniform(2, 4), 1)
        w.temp_max    = round(w.temp + random.uniform(2, 4), 1)
        w.humidity    = random.randint(60, 85)
        w.pressure    = random.randint(1008, 1018)
        w.wind_speed  = round(random.uniform(8, 25), 1)
        w.wind_deg    = random.randint(0, 359)
        w.wind_gust   = round(w.wind_speed + random.uniform(3, 12), 1)
        w.clouds      = random.randint(20, 80)
        w.visibility  = round(random.uniform(8, 15), 1)
        w.description = random.choice([
            "Parcialmente nublado","Soleado","Lluvias ocasionales",
            "Nublado","Mayormente despejado","Lluvia ligera"
        ])
        w.icon_code   = random.choice(["01d","02d","03d","10d","09d"])
        w.rain_1h     = round(random.uniform(0, 5), 1) if w.clouds > 70 else 0
        w.uv_index    = random.randint(3, 9) if 6 <= hour <= 18 else 0
        w.dew_point   = round(w.temp - ((100 - w.humidity) / 5), 1)
        w.city        = "Cali"
        w.country     = "CO"
        w.lat         = 3.4516
        w.lon         = -76.5320
        w.sunrise     = int((datetime.now().replace(hour=5,minute=55,second=0)).timestamp())
        w.sunset      = int((datetime.now().replace(hour=18,minute=10,second=0)).timestamp())
        return w

    def to_csv_row(self) -> list:
        return [
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.temp, self.feels_like, self.humidity, self.pressure,
            self.wind_speed, self.wind_deg, self.clouds,
            self.rain_1h, self.uv_index, self.visibility,
            self.description, self.city
        ]

    CSV_HEADERS = [
        "timestamp","temp_c","feels_like_c","humidity_pct","pressure_hpa",
        "wind_kmh","wind_deg","clouds_pct","rain_1h_mm","uv_index",
        "visibility_km","description","city"
    ]


# ── API ────────────────────────────────────────────────────────────────────────
class WeatherAPI:
    BASE = "https://api.openweathermap.org/data/2.5"

    def __init__(self, key: str):
        self.key = key

    def _get(self, endpoint: str, params: dict):
        r = requests.get(f"{self.BASE}/{endpoint}",
                         params={**params, "appid": self.key,
                                 "units": UNITS, "lang": "es"},
                         timeout=10)
        r.raise_for_status()
        return r.json()

    def current(self, city: str) -> WeatherData:
        return WeatherData.from_api(self._get("weather", {"q": city}))

    def forecast(self, city: str) -> list[dict]:
        data  = self._get("forecast", {"q": city, "cnt": 8})
        result = []
        for it in data.get("list", []):
            dt   = datetime.fromtimestamp(it["dt"])
            main = it.get("main", {})
            wx   = it.get("weather", [{}])[0]
            wind = it.get("wind", {})
            result.append({
                "hour":  "Ahora" if len(result)==0 else dt.strftime("%H:%M"),
                "temp":  round(main.get("temp", 0), 1),
                "desc":  wx.get("description","").capitalize(),
                "icon":  wx.get("icon","01d"),
                "humid": main.get("humidity", 0),
                "wind":  round(wind.get("speed",0)*3.6, 1),
                "rain":  it.get("rain",{}).get("3h", 0),
            })
        return result


# ── HISTORIAL ──────────────────────────────────────────────────────────────────
class History:
    KEYS = ["temps","humids","pressures","winds","rains","uv"]

    def __init__(self, maxlen=HISTORY_LEN):
        self.times     = deque(maxlen=maxlen)
        self.temps     = deque(maxlen=maxlen)
        self.humids    = deque(maxlen=maxlen)
        self.pressures = deque(maxlen=maxlen)
        self.winds     = deque(maxlen=maxlen)
        self.rains     = deque(maxlen=maxlen)
        self.uv        = deque(maxlen=maxlen)

    def push(self, wd: WeatherData):
        self.times.append(wd.timestamp)
        self.temps.append(wd.temp)
        self.humids.append(wd.humidity)
        self.pressures.append(wd.pressure)
        self.winds.append(wd.wind_speed)
        self.rains.append(wd.rain_1h)
        self.uv.append(wd.uv_index)

    def xlabels(self):
        return [t.strftime("%H:%M") for t in self.times]

    def stats(self, key: str) -> dict:
        vals = list(getattr(self, key))
        if not vals:
            return {"min":0,"max":0,"avg":0,"last":0}
        return {
            "min":  round(min(vals),1),
            "max":  round(max(vals),1),
            "avg":  round(sum(vals)/len(vals),1),
            "last": vals[-1],
        }


# ── HELPERS ────────────────────────────────────────────────────────────────────
DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
        "S","SSO","SO","OSO","O","ONO","NO","NNO"]

def deg_to_dir(d):  return DIRS[round(d/22.5)%16]
def uv_color(uv):
    if uv < 3:  return C["green"]
    if uv < 6:  return C["yellow"]
    if uv < 8:  return C["orange"]
    if uv < 11: return C["red"]
    return C["purple"]

def uv_label(uv):
    if uv < 3:  return "Bajo"
    if uv < 6:  return "Moderado"
    if uv < 8:  return "Alto"
    if uv < 11: return "Muy alto"
    return "Extremo"

WX_EMOJI = {
    "01d":"☀️","01n":"🌙","02d":"🌤","02n":"🌤","03d":"⛅","03n":"⛅",
    "04d":"☁️","04n":"☁️","09d":"🌦","09n":"🌦","10d":"🌧","10n":"🌧",
    "11d":"⛈","11n":"⛈","13d":"❄️","13n":"❄️","50d":"🌫","50n":"🌫",
}
def wx_emoji(code): return WX_EMOJI.get(code, "🌡")


# ── NOTIFICACIONES ─────────────────────────────────────────────────────────────
class Notifier:
    """Envía notificaciones nativas del sistema operativo."""
    _sent: set = set()   # evita spam: guarda claves ya enviadas

    @staticmethod
    def send(title: str, msg: str, key: str = ""):
        """Muestra notificación nativa. key='' siempre notifica."""
        if key and key in Notifier._sent:
            return
        if key:
            Notifier._sent.add(key)

        os_name = platform.system()
        try:
            if os_name == "Windows":
                # Usa PowerShell Toast Notification
                ps = (
                    f'[Windows.UI.Notifications.ToastNotificationManager, '
                    f'Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; '
                    f'$t = [Windows.UI.Notifications.ToastTemplateType]::ToastText02; '
                    f'$x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($t); '
                    f'$x.GetElementsByTagName("text")[0].AppendChild($x.CreateTextNode("{title}")) | Out-Null; '
                    f'$x.GetElementsByTagName("text")[1].AppendChild($x.CreateTextNode("{msg}")) | Out-Null; '
                    f'$n = [Windows.UI.Notifications.ToastNotification]::new($x); '
                    f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("MeteoStation").Show($n);'
                )
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif os_name == "Darwin":
                subprocess.Popen(
                    ["osascript", "-e",
                     f'display notification "{msg}" with title "{title}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif os_name == "Linux":
                subprocess.Popen(
                    ["notify-send", title, msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
        except Exception:
            pass  # Si falla, no interrumpe la app

    @staticmethod
    def reset(key: str):
        Notifier._sent.discard(key)

    @staticmethod
    def check_and_notify(wd: WeatherData):
        """Evalúa umbrales y dispara notificaciones según corresponda."""
        t = ALERT_THRESHOLDS

        if wd.uv_index >= t["uv_extreme"]:
            Notifier.send("☀️ UV Extremo", f"Índice UV: {wd.uv_index} en {wd.city}", "uv_ext")
        elif wd.uv_index >= t["uv_high"]:
            Notifier.send("☀️ UV Alto", f"Índice UV: {wd.uv_index} — usa protector solar", "uv_hi")
        else:
            Notifier.reset("uv_ext"); Notifier.reset("uv_hi")

        if wd.wind_speed >= t["wind_storm"]:
            Notifier.send("⚡ Tormenta de viento",
                          f"Viento: {wd.wind_speed} km/h en {wd.city}", "wind_st")
        elif wd.wind_speed >= t["wind_strong"]:
            Notifier.send("💨 Vientos fuertes",
                          f"Viento: {wd.wind_speed} km/h, ráfagas {wd.wind_gust} km/h", "wind_str")
        else:
            Notifier.reset("wind_st"); Notifier.reset("wind_str")

        if wd.rain_1h >= t["rain_heavy"]:
            Notifier.send("🌧 Lluvia intensa",
                          f"Precipitación: {wd.rain_1h} mm/h en {wd.city}", "rain_h")
        else:
            Notifier.reset("rain_h")

        if wd.temp >= t["temp_hot"]:
            Notifier.send("🌡 Temperatura alta",
                          f"Temperatura: {wd.temp}°C — tomar precauciones", "temp_hot")
        elif wd.temp <= t["temp_cold"]:
            Notifier.send("❄️ Temperatura baja",
                          f"Temperatura: {wd.temp}°C", "temp_cold")
        else:
            Notifier.reset("temp_hot"); Notifier.reset("temp_cold")


# ── CSV EXPORT ─────────────────────────────────────────────────────────────────
class DataLogger:
    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self._init_file()

    def _init_file(self):
        if not self.path.exists():
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(WeatherData.CSV_HEADERS)

    def log(self, wd: WeatherData):
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(wd.to_csv_row())

    def export_dialog(self, parent):
        dest = filedialog.asksaveasfilename(
            parent=parent,
            defaultextension=".csv",
            filetypes=[("CSV","*.csv"),("Todos","*.*")],
            initialfile=f"clima_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            title="Exportar historial CSV"
        )
        if dest and self.path.exists():
            import shutil
            shutil.copy2(self.path, dest)
            messagebox.showinfo("Exportado",
                f"Historial guardado en:\n{dest}", parent=parent)


# ══════════════════════════════════════════════════════════════════════════════
#  MAPA INTEGRADO (Tkinter Canvas + coordenadas reales)
# ══════════════════════════════════════════════════════════════════════════════
class MapWidget(tk.Frame):
    """
    Mapa de Colombia dibujado con Canvas de Tkinter.
    Muestra la ubicación de la ciudad con un marcador animado.
    No requiere dependencias externas de mapas.
    """
    # Límites geográficos de Colombia (aprox.)
    LAT_MAX, LAT_MIN =  12.5, -4.5
    LON_MIN, LON_MAX = -79.0, -66.0

    # Contorno simplificado de Colombia (lon, lat)
    COLOMBIA = [
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
        "Cali":     (3.45, -76.53),
        "Bogotá":   (4.71, -74.07),
        "Medellín": (6.25, -75.56),
        "Barranquilla":(11.0,-74.8),
        "Cartagena":(10.4,-75.5),
        "Cúcuta":   (7.9, -72.5),
        "Bucaramanga":(7.1,-73.1),
        "Pereira":  (4.8, -75.7),
        "Manizales":(5.07,-75.52),
        "Pasto":    (1.21,-77.28),
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=C["card"], **kwargs)
        self._lat = 3.4516
        self._lon = -76.5320
        self._city_name = "Cali"
        self._pulse = 0
        self._canvas = tk.Canvas(self, bg=C["chart_bg"],
                                 highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda e: self._draw())
        self.after(800, self._animate_pulse)

    def update_location(self, lat: float, lon: float, city: str = ""):
        self._lat = lat
        self._lon = lon
        self._city_name = city
        self._draw()

    def _geo_to_px(self, lat, lon, w, h):
        x = (lon - self.LON_MIN) / (self.LON_MAX - self.LON_MIN) * w
        y = (self.LAT_MAX - lat) / (self.LAT_MAX - self.LAT_MIN) * h
        return x, y

    def _draw(self):
        c = self._canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        # Fondo oceano
        c.create_rectangle(0, 0, w, h, fill="#0d1e36", outline="")

        # Contorno Colombia
        pts = []
        for lon, lat in self.COLOMBIA:
            px, py = self._geo_to_px(lat, lon, w, h)
            pts.extend([px, py])
        if len(pts) >= 4:
            c.create_polygon(pts, fill="#1a2e50", outline="#2d4a7a",
                             width=1.5, smooth=True)

        # Ciudades secundarias
        for name, (lat, lon) in self.CITIES.items():
            if name == self._city_name:
                continue
            px, py = self._geo_to_px(lat, lon, w, h)
            c.create_oval(px-3, py-3, px+3, py+3,
                          fill=C["muted"], outline="")
            c.create_text(px+5, py, text=name, anchor="w",
                          fill=C["muted"], font=("Courier", 7))

        # Marcador principal — pulso animado
        px, py = self._geo_to_px(self._lat, self._lon, w, h)
        pulse_r = 8 + self._pulse * 12
        pulse_a = max(0, int(200 - self._pulse * 200))
        pulse_color = f"#{pulse_a:02x}{'a0':s}{'e3':s}" if pulse_a > 30 else C["chart_bg"]
        c.create_oval(px-pulse_r, py-pulse_r, px+pulse_r, py+pulse_r,
                      fill="", outline=pulse_color, width=1.5)
        # Pin
        c.create_oval(px-8, py-8, px+8, py+8,
                      fill=C["accent"], outline=C["accent2"], width=1.5)
        c.create_oval(px-3, py-3, px+3, py+3,
                      fill="white", outline="")
        # Label
        c.create_rectangle(px+10, py-10, px+10+len(self._city_name)*6+8, py+10,
                            fill=C["card"], outline=C["border"])
        c.create_text(px+14, py, text=self._city_name, anchor="w",
                      fill=C["accent2"], font=("Courier", 9, "bold"))

        # Coordenadas
        coord_txt = f"Lat {self._lat:.2f}  Lon {self._lon:.2f}"
        c.create_text(w-6, h-6, text=coord_txt, anchor="se",
                      fill=C["muted"], font=("Courier", 8))

    def _animate_pulse(self):
        self._pulse = (self._pulse + 0.05) % 1.0
        self._draw()
        self.after(50, self._animate_pulse)


# ══════════════════════════════════════════════════════════════════════════════
#  GUI PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class WeatherStation(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("🌦 Estación Meteorológica v2.0")
        self.geometry("1200x760")
        self.minsize(1000, 660)
        self.configure(bg=C["bg"])

        # Estado interno
        self._ax          = None
        self._ax2         = None
        self._ax3         = None
        self._fig         = None
        self._chart_canvas= None
        self.api_key_var  = tk.StringVar(value=API_KEY)
        self.city_var     = tk.StringVar(value=CITY)
        self.demo_mode    = tk.BooleanVar(value=(API_KEY == ""))
        self.notif_mode   = tk.BooleanVar(value=True)
        self.status_var   = tk.StringVar(value="Iniciando…")
        self.last_upd_var = tk.StringVar(value="—")
        self.chart_var    = tk.StringVar(value="multi")
        self.history      = History()
        self.current      = WeatherData.demo()
        self.forecast     = []
        self._updating    = False
        self._run         = True
        self.logger       = DataLogger()
        self._alert_keys_active: set = set()

        self._build_ui()
        self._apply_style()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(200, self._refresh)
        self._schedule_auto()

    # ── HEADER ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=C["surface"])
        hdr.pack(fill="x")

        lf = tk.Frame(hdr, bg=C["surface"])
        lf.pack(side="left", padx=14, pady=8)
        tk.Label(lf, text="🌦", font=("",22), bg=C["surface"]).pack(side="left")
        tf = tk.Frame(lf, bg=C["surface"])
        tf.pack(side="left", padx=8)
        tk.Label(tf, text="METEO-STATION  v2.0",
                 font=("Courier",13,"bold"), fg=C["accent2"],
                 bg=C["surface"]).pack(anchor="w")
        self._city_lbl = tk.Label(tf, text=CITY, font=("Courier",9),
                                  fg=C["muted"], bg=C["surface"])
        self._city_lbl.pack(anchor="w")

        rf = tk.Frame(hdr, bg=C["surface"])
        rf.pack(side="right", padx=14, pady=8)

        self._live_lbl = tk.Label(rf, text="● EN VIVO",
                                  font=("Courier",9), fg=C["green"],
                                  bg=C["surface"])
        self._live_lbl.pack(side="right", padx=8)

        tk.Button(rf, text="⬇ Exportar CSV", font=("",9),
                  bg=C["card"], fg=C["green"], relief="flat",
                  padx=8, pady=3, cursor="hand2",
                  command=lambda: self.logger.export_dialog(self)
                  ).pack(side="right", padx=4)

        tk.Checkbutton(rf, text="🔔 Notif.", variable=self.notif_mode,
                       font=("",9), fg=C["muted"], bg=C["surface"],
                       selectcolor=C["card"],
                       activebackground=C["surface"]).pack(side="right", padx=4)

        tk.Checkbutton(rf, text="Demo", variable=self.demo_mode,
                       font=("",9), fg=C["muted"], bg=C["surface"],
                       selectcolor=C["card"],
                       activebackground=C["surface"]).pack(side="right", padx=4)

        city_e = tk.Entry(rf, textvariable=self.city_var, width=12,
                          font=("Courier",9), bg=C["card"], fg=C["text"],
                          insertbackground=C["text"], relief="flat",
                          highlightthickness=1, highlightcolor=C["accent"],
                          highlightbackground=C["border"])
        city_e.pack(side="right", padx=2)

        api_e = tk.Entry(rf, textvariable=self.api_key_var, width=26,
                         font=("Courier",9), show="*", bg=C["card"],
                         fg=C["text"], insertbackground=C["text"],
                         relief="flat", highlightthickness=1,
                         highlightcolor=C["accent"],
                         highlightbackground=C["border"])
        api_e.pack(side="right", padx=2)
        tk.Label(rf, text="API:", font=("Courier",9), fg=C["muted"],
                 bg=C["surface"]).pack(side="right")

        tk.Button(rf, text="↺ Actualizar", font=("",9),
                  bg=C["accent"], fg="white", relief="flat",
                  padx=8, pady=3, cursor="hand2",
                  activebackground=C["accent2"], activeforeground="white",
                  command=self._refresh).pack(side="right", padx=6)

        # Status bar
        sb = tk.Frame(self, bg=C["surface"], height=22)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, textvariable=self.status_var, font=("Courier",8),
                 fg=C["muted"], bg=C["surface"], anchor="w").pack(side="left", padx=8)
        tk.Label(sb, textvariable=self.last_upd_var, font=("Courier",8),
                 fg=C["muted"], bg=C["surface"], anchor="e").pack(side="right", padx=8)

        # Notebook (tabs principales)
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=6, pady=(4,0))

        tab1 = tk.Frame(self._nb, bg=C["bg"])
        tab2 = tk.Frame(self._nb, bg=C["bg"])
        tab3 = tk.Frame(self._nb, bg=C["bg"])
        self._nb.add(tab1, text=" 📊  Dashboard ")
        self._nb.add(tab2, text=" 📈  Gráficos ")
        self._nb.add(tab3, text=" 🗺   Mapa ")

        self._build_dashboard(tab1)
        self._build_charts_tab(tab2)
        self._build_map_tab(tab3)

    # ── TAB 1: DASHBOARD ──────────────────────────────────────────────────────
    def _build_dashboard(self, parent):
        # 3 columns
        left   = tk.Frame(parent, bg=C["bg"], width=200)
        center = tk.Frame(parent, bg=C["bg"])
        right  = tk.Frame(parent, bg=C["bg"], width=230)
        left.pack(side="left", fill="y", padx=(6,6), pady=6)
        center.pack(side="left", fill="both", expand=True, pady=6)
        right.pack(side="left", fill="y", padx=(0,6), pady=6)
        left.pack_propagate(False)
        right.pack_propagate(False)

        # LEFT: hero + sensors
        self._build_left(left)
        # CENTER: mini chart + forecast + alerts
        self._build_center(center)
        # RIGHT: wind + stats + map preview
        self._build_right_panel(right)

    def _card(self, parent, pad_x=10, pad_y=8):
        f = tk.Frame(parent, bg=C["card"],
                     highlightthickness=1,
                     highlightbackground=C["border"])
        f.pack(fill="x", pady=(0,6), padx=0)
        inner = tk.Frame(f, bg=C["card"], padx=pad_x, pady=pad_y)
        inner.pack(fill="x")
        return inner

    def _lbl(self, p, text="", size=10, bold=False, color=None, mono=False):
        color = color or C["text"]
        fam   = "Courier" if mono else ""
        wt    = "bold" if bold else "normal"
        return tk.Label(p, text=text, font=(fam, size, wt),
                        fg=color, bg=p.cget("bg"))

    def _build_left(self, p):
        # Hero
        hero = tk.Frame(p, bg=C["card"],
                        highlightthickness=1, highlightbackground=C["border"])
        hero.pack(fill="x", pady=(0,6))
        inner = tk.Frame(hero, bg=C["card"], padx=12, pady=14)
        inner.pack(fill="x")
        self._s_icon  = self._lbl(inner, "⛅", 32)
        self._s_icon.pack()
        tf = tk.Frame(inner, bg=C["card"]); tf.pack()
        self._s_temp  = self._lbl(tf, "24", 40, True, mono=True)
        self._s_temp.pack(side="left")
        self._lbl(tf, "°C", 14, color=C["accent"]).pack(side="left", anchor="n", pady=10)
        self._s_feels = self._lbl(inner, "Sensación: 26°C", 9, color=C["muted"], mono=True)
        self._s_feels.pack()
        self._s_trend = self._lbl(inner, "→ Estable", 10, color=C["muted"])
        self._s_trend.pack(pady=(3,0))
        self._s_desc  = self._lbl(inner, "Parcialmente nublado", 10, color=C["dim"])
        self._s_desc.pack(pady=(2,0))
        self._s_mm    = self._lbl(inner, "↓18° / ↑30°", 9, color=C["muted"], mono=True)
        self._s_mm.pack()

        # Sensors
        self._mini = {}
        sensors = [
            ("humid",    "💧", "Humedad",       "%",    C["cold"]),
            ("pressure", "🔵", "Presión",        " hPa", C["purple"]),
            ("uv",       "☀️",  "Índice UV",      "",     C["yellow"]),
            ("vis",      "👁",  "Visibilidad",    " km",  C["green"]),
            ("rain",     "🌧",  "Lluvia 1h",      " mm",  C["accent"]),
            ("dew",      "💦", "Punto rocío",    "°C",   C["cold"]),
        ]
        for key, icon, label, unit, color in sensors:
            row = tk.Frame(p, bg=C["card"],
                           highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill="x", pady=(0,4))
            inn = tk.Frame(row, bg=C["card"], padx=10, pady=6)
            inn.pack(fill="x")
            tk.Label(inn, text=icon, font=("",13), bg=C["card"]).pack(side="left", padx=(0,8))
            txt = tk.Frame(inn, bg=C["card"]); txt.pack(side="left", fill="x", expand=True)
            self._lbl(txt, label, 8, color=C["muted"], mono=True).pack(anchor="w")
            vl = self._lbl(txt, "—", 15, True, color, True)
            vl.pack(anchor="w")
            self._mini[key] = vl

    def _build_center(self, p):
        # Strip stats
        strip = tk.Frame(p, bg=C["bg"])
        strip.pack(fill="x", pady=(0,6))
        self._strip = {}
        items = [
            ("wind",    "💨 Viento"),
            ("winddir", "🧭 Dirección"),
            ("gust",    "⚡ Ráfaga"),
            ("clouds",  "☁️ Nubosidad"),
            ("sunrise", "🌅 Amanecer"),
            ("sunset",  "🌇 Atardecer"),
        ]
        for i, (key, lbl) in enumerate(items):
            cell = tk.Frame(strip, bg=C["card"],
                            highlightthickness=1, highlightbackground=C["border"])
            cell.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 5, 0))
            inn = tk.Frame(cell, bg=C["card"], pady=7, padx=8)
            inn.pack(fill="both")
            self._lbl(inn, lbl, 8, color=C["muted"], mono=True).pack(anchor="w")
            v = self._lbl(inn, "—", 14, True, mono=True)
            v.pack(anchor="w")
            self._strip[key] = v

        # Mini chart (dashboard)
        cc = tk.Frame(p, bg=C["card"],
                      highlightthickness=1, highlightbackground=C["border"])
        cc.pack(fill="both", expand=True, pady=(0,6))
        ch_hdr = tk.Frame(cc, bg=C["card"])
        ch_hdr.pack(fill="x", padx=10, pady=(6,0))
        self._lbl(ch_hdr, "HISTORIAL  —  TEMPERATURA", 8, color=C["muted"], mono=True).pack(side="left")

        if MATPLOTLIB_OK:
            fig_mini = Figure(figsize=(1,1), dpi=96, facecolor=C["chart_bg"])
            self._ax_mini = fig_mini.add_subplot(111)
            fig_mini.subplots_adjust(left=0.06, right=0.97, top=0.88, bottom=0.2)
            cv = FigureCanvasTkAgg(fig_mini, master=cc)
            cv.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
            self._fig_mini  = fig_mini
            self._cv_mini   = cv

        # Forecast
        fc_card = tk.Frame(p, bg=C["card"],
                           highlightthickness=1, highlightbackground=C["border"])
        fc_card.pack(fill="x", pady=(0,6))
        self._lbl(fc_card, "PRONÓSTICO 3H", 8, color=C["muted"], mono=True
                  ).pack(anchor="w", padx=10, pady=(6,2))
        self._fc_frame = tk.Frame(fc_card, bg=C["card"])
        self._fc_frame.pack(fill="x", padx=6, pady=(0,6))

        # Alerts
        al_card = tk.Frame(p, bg=C["card"],
                           highlightthickness=1, highlightbackground=C["border"])
        al_card.pack(fill="x")
        self._lbl(al_card, "ALERTAS", 8, color=C["muted"], mono=True
                  ).pack(anchor="w", padx=10, pady=(6,2))
        self._alerts_frame = tk.Frame(al_card, bg=C["card"])
        self._alerts_frame.pack(fill="x", padx=8, pady=(0,8))

    def _build_right_panel(self, p):
        # Compass/wind
        wc = tk.Frame(p, bg=C["card"],
                      highlightthickness=1, highlightbackground=C["border"])
        wc.pack(fill="x", pady=(0,6))
        self._lbl(wc, "VIENTO", 8, color=C["muted"], mono=True
                  ).pack(anchor="w", padx=10, pady=(6,2))
        wf = tk.Frame(wc, bg=C["card"])
        wf.pack(fill="x", padx=10, pady=(0,8))
        self._compass = CompassWidget(wf, width=110, height=110)
        self._compass.pack(side="left")
        wr = tk.Frame(wf, bg=C["card"])
        wr.pack(side="left", padx=(10,0))
        self._lbl(wr, "Velocidad", 8, color=C["muted"], mono=True).pack(anchor="w")
        self._w_speed = self._lbl(wr, "—", 20, True, mono=True)
        self._w_speed.pack(anchor="w")
        self._lbl(wr, "km/h", 9, color=C["muted"]).pack(anchor="w")
        self._lbl(wr, "Dirección", 8, color=C["muted"], mono=True).pack(anchor="w", pady=(6,0))
        self._w_dir   = self._lbl(wr, "—", 16, True, C["accent2"], True)
        self._w_dir.pack(anchor="w")
        self._lbl(wr, "Ráfaga máx.", 8, color=C["muted"], mono=True).pack(anchor="w", pady=(6,0))
        self._w_gust  = self._lbl(wr, "—", 14, False, C["text"], True)
        self._w_gust.pack(anchor="w")

        # Stats summary
        sc = tk.Frame(p, bg=C["card"],
                      highlightthickness=1, highlightbackground=C["border"])
        sc.pack(fill="x", pady=(0,6))
        self._lbl(sc, "ESTADÍSTICAS (SESIÓN)", 8, color=C["muted"], mono=True
                  ).pack(anchor="w", padx=10, pady=(6,2))
        self._stats_frame = tk.Frame(sc, bg=C["card"])
        self._stats_frame.pack(fill="x", padx=8, pady=(0,8))
        self._stat_labels = {}
        for key, label in [("temps","Temperatura"),("humids","Humedad"),
                            ("winds","Viento"),("pressures","Presión")]:
            row = tk.Frame(self._stats_frame, bg=C["card"])
            row.pack(fill="x", pady=2)
            self._lbl(row, label, 9, color=C["dim"], mono=True).pack(side="left")
            v = self._lbl(row, "min — max", 9, color=C["text"], mono=True)
            v.pack(side="right")
            self._stat_labels[key] = v

        # Mini map preview
        map_c = tk.Frame(p, bg=C["card"],
                         highlightthickness=1, highlightbackground=C["border"])
        map_c.pack(fill="both", expand=True, pady=(0,0))
        self._lbl(map_c, "UBICACIÓN", 8, color=C["muted"], mono=True
                  ).pack(anchor="w", padx=10, pady=(6,2))
        self._mini_map = MapWidget(map_c)
        self._mini_map.pack(fill="both", expand=True, padx=4, pady=(0,6))

    # ── TAB 2: GRÁFICOS AVANZADOS ─────────────────────────────────────────────
    def _build_charts_tab(self, parent):
        if not MATPLOTLIB_OK:
            tk.Label(parent, text="⚠️ pip install matplotlib",
                     fg=C["yellow"], bg=C["bg"], font=("",12)).pack(expand=True)
            return

        ctrl = tk.Frame(parent, bg=C["bg"])
        ctrl.pack(fill="x", padx=8, pady=(6,0))
        self._lbl(ctrl, "VISTA:", 9, color=C["muted"], mono=True).pack(side="left", padx=(0,6))
        self._tab_btns = {}
        for key, lbl in [("multi","Multi-panel"),("correlation","Correlación"),
                          ("wind_rose","Rosa de vientos"),("bars","Barras UV")]:
            b = tk.Button(ctrl, text=lbl, font=("Courier",8),
                          relief="flat", padx=8, pady=3, cursor="hand2",
                          command=lambda k=key: self._switch_advanced(k))
            b.pack(side="left", padx=2)
            self._tab_btns[key] = b

        self._fig = Figure(figsize=(1,1), dpi=96, facecolor=C["chart_bg"])
        self._chart_canvas = FigureCanvasTkAgg(self._fig, master=parent)
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True,
                                                padx=6, pady=6)
        self._switch_advanced("multi")

    # ── TAB 3: MAPA ───────────────────────────────────────────────────────────
    def _build_map_tab(self, parent):
        info = tk.Frame(parent, bg=C["surface"])
        info.pack(fill="x")
        self._map_info_lbl = tk.Label(
            info, text="Cargando ubicación…",
            font=("Courier",10), fg=C["accent2"], bg=C["surface"], pady=8)
        self._map_info_lbl.pack(side="left", padx=14)

        self._full_map = MapWidget(parent)
        self._full_map.pack(fill="both", expand=True, padx=6, pady=6)

    # ── CHARTS AVANZADOS ─────────────────────────────────────────────────────

    def _switch_advanced(self, key: str):
        self.chart_var.set(key)
        for k, b in self._tab_btns.items():
            b.config(bg=C["accent"] if k==key else C["card2"],
                     fg="white"     if k==key else C["muted"])
        self._draw_advanced()

    def _draw_advanced(self):
        if not MATPLOTLIB_OK or self._fig is None:
            return
        self._fig.clear()
        key = self.chart_var.get()
        {
            "multi":       self._chart_multi,
            "correlation": self._chart_correlation,
            "wind_rose":   self._chart_wind_rose,
            "bars":        self._chart_uv_bars,
        }.get(key, self._chart_multi)()
        try:
            self._chart_canvas.draw()
        except Exception:
            pass

    def _style_ax(self, ax, title=""):
        ax.set_facecolor(C["chart_bg"])
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.tick_params(colors=C["muted"], labelsize=7,
                       bottom=False, left=False)
        ax.grid(axis="y", color=C["grid"], linewidth=0.4, alpha=0.6)
        ax.set_axisbelow(True)
        if title:
            ax.set_title(title, fontsize=8, color=C["dim"],
                         pad=4, fontfamily="monospace")

    def _chart_multi(self):
        """4 gráficos en una cuadrícula 2×2."""
        gs = gridspec.GridSpec(2, 2, figure=self._fig,
                               hspace=0.5, wspace=0.3,
                               left=0.06, right=0.97,
                               top=0.94, bottom=0.1)
        configs = [
            (0,0, "temps",     "Temperatura °C",   C["accent"]),
            (0,1, "humids",    "Humedad %",         C["green"]),
            (1,0, "pressures", "Presión hPa",       C["purple"]),
            (1,1, "winds",     "Viento km/h",       C["yellow"]),
        ]
        for r,col,key,title,color in configs:
            ax  = self._fig.add_subplot(gs[r, col])
            vals = list(getattr(self.history, key))
            self._style_ax(ax, title)
            if len(vals) >= 2:
                x = range(len(vals))
                ax.fill_between(x, vals, alpha=0.1, color=color)
                ax.plot(x, vals, color=color, linewidth=1.5)
                ax.scatter([len(vals)-1],[vals[-1]], color=color, s=25, zorder=5)
                ax.annotate(f"{vals[-1]}", xy=(len(vals)-1, vals[-1]),
                            xytext=(len(vals)-1, vals[-1]),
                            fontsize=7, color=color,
                            fontfamily="monospace",
                            ha="right", va="bottom")
            else:
                ax.text(0.5,0.5,"Recopilando…", ha="center", va="center",
                        transform=ax.transAxes, color=C["muted"], fontsize=8)
            xlabels = self.history.xlabels()
            if xlabels:
                step = max(1, len(xlabels)//5)
                ax.set_xticks(range(0,len(xlabels),step))
                ax.set_xticklabels(xlabels[::step], rotation=30, ha="right",
                                   fontsize=6, color=C["muted"],
                                   fontfamily="monospace")

    def _chart_correlation(self):
        """Scatter: temperatura vs humedad con colores por hora."""
        ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(left=0.1,right=0.95,top=0.9,bottom=0.12)
        self._style_ax(ax, "Correlación: Temperatura vs Humedad")
        temps  = list(self.history.temps)
        humids = list(self.history.humids)
        if len(temps) >= 3:
            hours = [t.hour for t in self.history.times]
            sc = ax.scatter(temps, humids, c=hours, cmap="plasma",
                            s=30, alpha=0.8, zorder=3)
            cbar = self._fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
            cbar.ax.tick_params(labelsize=7, colors=C["muted"])
            cbar.set_label("Hora del día", fontsize=7,
                           color=C["muted"], fontfamily="monospace")
            # Línea de tendencia
            if len(temps) > 5:
                import numpy as np
                z = np.polyfit(temps, humids, 1)
                p = np.poly1d(z)
                xs = sorted(temps)
                ax.plot(xs, [p(x) for x in xs], color=C["muted"],
                        linewidth=1, linestyle="--", alpha=0.6)
            ax.set_xlabel("Temperatura °C", fontsize=8,
                          color=C["muted"], fontfamily="monospace")
            ax.set_ylabel("Humedad %", fontsize=8,
                          color=C["muted"], fontfamily="monospace")
        else:
            ax.text(0.5,0.5,"Se necesitan ≥3 lecturas",
                    ha="center",va="center",transform=ax.transAxes,
                    color=C["muted"],fontsize=10)

    def _chart_wind_rose(self):
        """Rosa de vientos polar."""
        ax = self._fig.add_subplot(111, projection="polar")
        self._fig.subplots_adjust(left=0.05,right=0.95,top=0.9,bottom=0.05)
        ax.set_facecolor(C["chart_bg"])
        ax.spines["polar"].set_color(C["border"])
        ax.tick_params(colors=C["muted"], labelsize=7)
        ax.set_title("Rosa de Vientos", fontsize=9, color=C["dim"],
                     pad=12, fontfamily="monospace")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_yticklabels([])
        ax.grid(color=C["grid"], linewidth=0.5, alpha=0.5)
        ax.set_xticks([math.radians(d) for d in range(0,360,45)])
        ax.set_xticklabels(["N","NE","E","SE","S","SO","O","NO"],
                           color=C["muted"], fontsize=7, fontfamily="monospace")

        degs  = [w.wind_deg for w in [self.current]]
        winds = [self.current.wind_speed]
        if len(list(self.history.times)) >= 2:
            degs  = list(range(0,360,5))
            winds = [abs(math.sin(math.radians(d))*15 + random.uniform(-3,3))
                     for d in degs]

        bins = 16
        width = 2*math.pi / bins
        counts = [0.0]*bins
        for deg, spd in zip(degs, winds):
            idx = int(deg//(360/bins)) % bins
            counts[idx] += spd
        thetas = [i * width for i in range(bins)]
        bars = ax.bar(thetas, counts, width=width*0.8, alpha=0.8,
                      color=C["accent"], edgecolor=C["accent2"], linewidth=0.5)
        norm = max(counts) if max(counts)>0 else 1
        for bar, val in zip(bars, counts):
            bar.set_alpha(0.3 + 0.7*(val/norm))

    def _chart_uv_bars(self):
        """Barras de índice UV por hora con colores de riesgo."""
        ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(left=0.06,right=0.97,top=0.9,bottom=0.18)
        self._style_ax(ax, "Índice UV por lectura")
        vals = list(self.history.uv)
        if not vals:
            vals = [random.randint(0,10) for _ in range(20)]
        x     = range(len(vals))
        colors_bar = [uv_color(v) for v in vals]
        ax.bar(x, vals, color=colors_bar, alpha=0.8, width=0.7)
        ax.set_ylim(0, 12)
        # Leyenda
        patches = [
            mpatches.Patch(color=C["green"],  label="Bajo (<3)"),
            mpatches.Patch(color=C["yellow"], label="Moderado (3-5)"),
            mpatches.Patch(color=C["orange"], label="Alto (6-7)"),
            mpatches.Patch(color=C["red"],    label="Muy alto (8-10)"),
            mpatches.Patch(color=C["purple"], label="Extremo (≥11)"),
        ]
        ax.legend(handles=patches, fontsize=7, loc="upper left",
                  framealpha=0.2, facecolor=C["card"],
                  edgecolor=C["border"], labelcolor=C["text"])
        labels = self.history.xlabels()
        if labels:
            step = max(1, len(labels)//8)
            ax.set_xticks(range(0,len(labels),step))
            ax.set_xticklabels(labels[::step], rotation=30, ha="right",
                               fontsize=7, color=C["muted"],
                               fontfamily="monospace")

    # ── MINI CHART (dashboard) ────────────────────────────────────────────────
    def _draw_mini_chart(self):
        if not MATPLOTLIB_OK or not hasattr(self,"_ax_mini"):
            return
        ax = self._ax_mini
        ax.clear()
        ax.set_facecolor(C["chart_bg"])
        self._fig_mini.patch.set_facecolor(C["chart_bg"])
        vals   = list(self.history.temps)
        labels = self.history.xlabels()
        if len(vals) >= 2:
            x = range(len(vals))
            ax.fill_between(x, vals, alpha=0.1, color=C["accent"])
            ax.plot(x, vals, color=C["accent"], linewidth=1.8)
            ax.scatter([len(vals)-1],[vals[-1]], color=C["accent"],s=20,zorder=5)
            step = max(1,len(labels)//6)
            ax.set_xticks(range(0,len(labels),step))
            ax.set_xticklabels(labels[::step], rotation=30, ha="right",
                               fontsize=6, color=C["muted"],
                               fontfamily="monospace")
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.tick_params(colors=C["muted"],labelsize=7,bottom=False,left=False)
        ax.grid(axis="y", color=C["grid"], linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)
        try: self._cv_mini.draw()
        except Exception: pass

    # ── ACTUALIZACIÓN DE DATOS ────────────────────────────────────────────────
    def _refresh(self):
        if self._updating: return
        self._updating = True
        self.status_var.set("⟳ Actualizando…")
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            key  = self.api_key_var.get().strip()
            city = self.city_var.get().strip() or CITY
            if self.demo_mode.get() or not key:
                wd = WeatherData.demo()
                wd.city = city.split(",")[0]
                fc = self._demo_forecast(wd)
                mode = "DEMO"
            else:
                api = WeatherAPI(key)
                wd  = api.current(city)
                fc  = api.forecast(city)
                mode = "API"

            self.current  = wd
            self.forecast = fc
            self.history.push(wd)
            self.logger.log(wd)

            if self.notif_mode.get():
                threading.Thread(target=Notifier.check_and_notify,
                                 args=(wd,), daemon=True).start()

            self.after(0, lambda: self._render(mode))
        except Exception as e:
            self.after(0, lambda: self._show_err(str(e)))
        finally:
            self._updating = False

    def _demo_forecast(self, base: WeatherData) -> list[dict]:
        now  = datetime.now()
        icons= ["01d","02d","03d","10d","09d","11d"]
        descs= ["Soleado","Nublado","Lluvias","Tormenta","Despejado","Ligero"]
        result = []
        for i in range(8):
            dt = now + timedelta(hours=3*i)
            result.append({
                "hour":  "Ahora" if i==0 else dt.strftime("%H:%M"),
                "temp":  round(base.temp + random.uniform(-3,3),1),
                "desc":  random.choice(descs),
                "icon":  random.choice(icons),
                "humid": random.randint(55,88),
                "wind":  round(random.uniform(8,30),1),
                "rain":  round(random.uniform(0,5),1),
            })
        return result

    # ── RENDER ────────────────────────────────────────────────────────────────
    def _render(self, mode: str):
        wd = self.current

        # Hero
        self._s_icon.config(text=wx_emoji(wd.icon_code))
        self._s_temp.config(text=str(round(wd.temp,1)))
        self._s_feels.config(text=f"Sensación: {round(wd.feels_like,1)}°C")
        temps = list(self.history.temps)
        if len(temps) >= 2:
            d = temps[-1]-temps[-2]
            if d > 0.1:
                self._s_trend.config(text="↑ Subiendo", fg=C["orange"])
            elif d < -0.1:
                self._s_trend.config(text="↓ Bajando",  fg=C["cold"])
            else:
                self._s_trend.config(text="→ Estable",  fg=C["muted"])
        self._s_desc.config(text=wd.description)
        self._s_mm.config(text=f"↓{round(wd.temp_min):.0f}°  /  ↑{round(wd.temp_max):.0f}°")

        # Mini cards
        self._mini["humid"].config(text=str(wd.humidity))
        self._mini["pressure"].config(text=str(wd.pressure))
        self._mini["uv"].config(text=f"{wd.uv_index} {uv_label(wd.uv_index)}",
                                fg=uv_color(wd.uv_index))
        self._mini["vis"].config(text=str(round(wd.visibility,1)))
        self._mini["rain"].config(text=str(round(wd.rain_1h,1)))
        self._mini["dew"].config(text=str(round(wd.dew_point,1)))

        # Strip
        sr = datetime.fromtimestamp(wd.sunrise).strftime("%H:%M") if wd.sunrise else "—"
        ss = datetime.fromtimestamp(wd.sunset ).strftime("%H:%M") if wd.sunset  else "—"
        self._strip["wind"].config(text=f"{round(wd.wind_speed,1)} km/h")
        self._strip["winddir"].config(text=deg_to_dir(wd.wind_deg))
        self._strip["gust"].config(text=f"{round(wd.wind_gust,1)} km/h")
        self._strip["clouds"].config(text=f"{wd.clouds}%")
        self._strip["sunrise"].config(text=sr)
        self._strip["sunset"].config(text=ss)

        # Wind compass
        self._compass.set_angle(wd.wind_deg)
        self._w_speed.config(text=str(round(wd.wind_speed,1)))
        self._w_dir.config(text=deg_to_dir(wd.wind_deg))
        self._w_gust.config(text=f"{round(wd.wind_gust,1)} km/h")

        # Stats
        for key in ["temps","humids","winds","pressures"]:
            s = self.history.stats(key)
            if key in self._stat_labels:
                self._stat_labels[key].config(
                    text=f"↓{s['min']}  avg {s['avg']}  ↑{s['max']}")

        # Alerts
        self._render_alerts()

        # Forecast
        self._render_forecast()

        # Mini chart
        self._draw_mini_chart()

        # Advanced chart (if visible)
        self._draw_advanced()

        # Maps
        self._mini_map.update_location(wd.lat, wd.lon, wd.city)
        self._full_map.update_location(wd.lat, wd.lon, wd.city)
        self._map_info_lbl.config(
            text=f"{wd.city}, {wd.country}  •  "
                 f"Lat {wd.lat:.4f}  Lon {wd.lon:.4f}")
        self._city_lbl.config(text=f"{wd.city}, {wd.country}")

        # Status
        ts = datetime.now().strftime("%H:%M:%S")
        self.last_upd_var.set(f"Última actualización: {ts}  [{mode}]")
        self.status_var.set(f"✓ {wd.city}, {wd.country} — {wd.description}")
        self._live_lbl.config(fg=C["accent2"])
        self.after(500, lambda: self._live_lbl.config(fg=C["green"]))

    def _render_forecast(self):
        for w in self._fc_frame.winfo_children(): w.destroy()
        for i, fc in enumerate(self.forecast[:8]):
            cell = tk.Frame(self._fc_frame, bg=C["card2"],
                            highlightthickness=1, highlightbackground=C["border"],
                            padx=5, pady=5)
            cell.pack(side="left", fill="x", expand=True,
                      padx=(0 if i==0 else 3,0))
            self._lbl(cell, fc["hour"], 8, color=C["muted"], mono=True).pack()
            self._lbl(cell, wx_emoji(fc["icon"]), 16).pack()
            self._lbl(cell, f"{round(fc['temp']):.0f}°", 12, True, mono=True).pack()
            self._lbl(cell, f"💧{fc['humid']}%", 8, color=C["cold"], mono=True).pack()

    def _render_alerts(self):
        for w in self._alerts_frame.winfo_children(): w.destroy()
        wd  = self.current
        t   = ALERT_THRESHOLDS
        alerts = []

        if wd.uv_index >= t["uv_extreme"]:
            alerts.append(("⚠", f"UV Extremo ({wd.uv_index}) — no salir al sol", C["purple"]))
        elif wd.uv_index >= t["uv_high"]:
            alerts.append(("⚠", f"UV Alto ({wd.uv_index}) — usar protector solar", C["orange"]))
        if wd.wind_speed >= t["wind_storm"]:
            alerts.append(("⚡", f"Viento de tormenta: {round(wd.wind_speed)} km/h", C["red"]))
        elif wd.wind_speed >= t["wind_strong"]:
            alerts.append(("💨", f"Vientos fuertes: {round(wd.wind_speed)} km/h", C["orange"]))
        if wd.rain_1h >= t["rain_heavy"]:
            alerts.append(("🌧", f"Lluvia intensa: {wd.rain_1h} mm/h", C["cold"]))
        if wd.pressure < t["pressure_low"]:
            alerts.append(("📉", f"Presión muy baja: {wd.pressure} hPa", C["yellow"]))
        if wd.humidity > t["humidity_high"]:
            alerts.append(("💦", f"Humedad elevada: {wd.humidity}%", C["cold"]))
        if wd.temp >= t["temp_hot"]:
            alerts.append(("🌡", f"Temperatura alta: {wd.temp}°C", C["red"]))

        if not alerts:
            alerts = [("✓", "Sin alertas — condiciones normales", C["green"])]

        for icon, msg, color in alerts:
            row = tk.Frame(self._alerts_frame, bg=C["card"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=icon, font=("",10), fg=color, bg=C["card"]
                     ).pack(side="left", padx=(4,5))
            tk.Label(row, text=msg, font=("",9), fg=color, bg=C["card"],
                     anchor="w").pack(side="left")

    def _show_err(self, msg: str):
        self.status_var.set(f"✗ Error: {msg}")
        messagebox.showerror("Error", msg, parent=self)

    # ── AUTO REFRESH ─────────────────────────────────────────────────────────
    def _schedule_auto(self):
        if self._run:
            self.after(INTERVAL*1000, self._auto_tick)

    def _auto_tick(self):
        self._refresh()
        self._schedule_auto()

    def _on_close(self):
        self._run = False
        if MATPLOTLIB_OK:
            plt.close("all")
        self.destroy()

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",
                        background=C["bg"], borderwidth=0,
                        tabmargins=[0,0,0,0])
        style.configure("TNotebook.Tab",
                        background=C["card2"], foreground=C["muted"],
                        font=("Courier",9), padding=[12,5],
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", C["card"])],
                  foreground=[("selected", C["accent2"])])
        style.configure("TScrollbar",
                        background=C["card"], troughcolor=C["surface"],
                        borderwidth=0)


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET BRÚJULA
# ══════════════════════════════════════════════════════════════════════════════
class CompassWidget(tk.Canvas):
    def __init__(self, parent, width=100, height=100, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=C["chart_bg"], highlightthickness=0, **kwargs)
        self._angle = 0
        self._w = width
        self._h = height
        self._draw()

    def set_angle(self, deg: float):
        self._angle = deg
        self._draw()

    def _draw(self):
        self.delete("all")
        cx, cy = self._w//2, self._h//2
        r  = min(cx, cy) - 6
        r2 = r - 10

        # Outer ring
        self.create_oval(cx-r, cy-r, cx+r, cy+r,
                         outline=C["border"], width=1.5, fill=C["chart_bg"])
        self.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                         outline=C["grid"], width=0.5, fill="")

        # Cardinal points
        for deg, lbl in [(0,"N"),(90,"E"),(180,"S"),(270,"O")]:
            rad = math.radians(deg - 90)
            tx  = cx + (r-8) * math.cos(rad)
            ty  = cy + (r-8) * math.sin(rad)
            color = C["accent2"] if lbl == "N" else C["muted"]
            self.create_text(tx, ty, text=lbl, fill=color,
                             font=("Courier", 7, "bold"))

        # Tick marks
        for deg in range(0, 360, 45):
            rad = math.radians(deg - 90)
            x1  = cx + (r-14)*math.cos(rad)
            y1  = cy + (r-14)*math.sin(rad)
            x2  = cx + r2*math.cos(rad)
            y2  = cy + r2*math.sin(rad)
            self.create_line(x1,y1,x2,y2, fill=C["border"], width=0.8)

        # Arrow (wind direction)
        rad = math.radians(self._angle - 90)
        ar  = r - 20
        # North tip (colored)
        tip_x = cx + ar * math.cos(rad)
        tip_y = cy + ar * math.sin(rad)
        # South tail
        tail_x = cx - (ar//2) * math.cos(rad)
        tail_y = cy - (ar//2) * math.sin(rad)
        # Wing points
        perp = math.radians(self._angle)
        wx_  = 6 * math.cos(perp)
        wy_  = 6 * math.sin(perp)

        self.create_polygon(
            tip_x, tip_y,
            cx + wx_, cy + wy_,
            tail_x, tail_y,
            cx - wx_, cy - wy_,
            fill=C["accent"], outline=C["accent2"], width=1
        )
        # South half (gray)
        self.create_polygon(
            tail_x, tail_y,
            cx + wx_, cy + wy_,
            cx - wx_, cy - wy_,
            fill=C["muted"], outline="", width=0
        )
        # Center dot
        self.create_oval(cx-4, cy-4, cx+4, cy+4,
                         fill=C["bg"], outline=C["accent"], width=1.5)


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    if not REQUESTS_OK:
        print("⚠️  pip install requests")
    if not MATPLOTLIB_OK:
        print("⚠️  pip install matplotlib")
    app = WeatherStation()
    app.mainloop()

if __name__ == "__main__":
    main()