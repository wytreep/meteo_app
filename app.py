"""
app.py — Ventana principal y orquestador de la aplicación.
Responsabilidad: conectar el modelo (core/) con las vistas (views/).
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import random
from datetime import datetime, timedelta

from config import Config, Theme
from core.weather_data import WeatherData
from core.weather_api  import WeatherAPI
from core.history      import History
from core.data_logger  import DataLogger
from core.notifier     import Notifier
from views.dashboard_view import DashboardView
from views.charts_view    import ChartsView


class RippleButton(tk.Button):
    """Botón con efecto de escala (ripple) al presionar."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._orig_relief = kwargs.get("relief", "flat")
        self.bind("<ButtonPress-1>",   self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _press(self, _=None):
        self.configure(relief="sunken")
        orig_pad = self.cget("padx")
        try:
            self.configure(padx=max(0, int(orig_pad)-1))
        except Exception:
            pass

    def _release(self, _=None):
        self.configure(relief=self._orig_relief)
        orig_pad = self.cget("padx")
        try:
            self.configure(padx=int(orig_pad)+1)
        except Exception:
            pass


class WeatherStation(tk.Tk):
    """
    Ventana principal de la aplicación.
    Orquesta el ciclo de datos y coordina las vistas.

    Flujo:
      _refresh()  → hilo _fetch()  → after() → _render()
    """

    def __init__(self):
        super().__init__()
        self.title(Config.WIN_TITLE)
        self.geometry(Config.WIN_SIZE)
        self.minsize(1000, 640)
        self.configure(bg=Theme.BG)

        # ── Modelo ────────────────────────────────────────────
        self._history  = History()
        self._logger   = DataLogger()
        self._current  = WeatherData.demo()
        self._forecast: list[dict] = []

        # ── Estado UI ────────────────────────────────────────
        self._var_key    = tk.StringVar(value=Config.API_KEY)
        self._var_city   = tk.StringVar(value=Config.CITY)
        self._var_demo   = tk.BooleanVar(value=(Config.API_KEY == ""))
        self._var_notif  = tk.BooleanVar(value=True)
        self._var_status = tk.StringVar(value="Iniciando…")
        self._var_upd    = tk.StringVar(value="—")
        self._busy       = False
        self._running    = True

        # ── Construcción ─────────────────────────────────────
        self._build_header()
        self._build_notebook()
        self._build_statusbar()
        self._apply_ttk_style()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(300, self._refresh)
        self._schedule()

    # ══════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DE UI
    # ══════════════════════════════════════════════════════════

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=Theme.SURFACE,
                       highlightthickness=1,
                       highlightbackground=Theme.BORDER)
        hdr.pack(fill="x", side="top")

        # Logo
        lf = tk.Frame(hdr, bg=Theme.SURFACE)
        lf.pack(side="left", padx=16, pady=10)
        tk.Label(lf, text="◈", font=("", 20),
                 fg=Theme.ACCENT,
                 bg=Theme.SURFACE).pack(side="left")
        tf = tk.Frame(lf, bg=Theme.SURFACE)
        tf.pack(side="left", padx=8)
        tk.Label(tf, text="Estación Meteorológica",
                 font=(Theme.FONT_SANS, 13, "bold"),
                 fg=Theme.TEXT,
                 bg=Theme.SURFACE).pack(anchor="w")
        self._city_lbl = tk.Label(tf, text=Config.CITY,
                                  font=(Theme.FONT_MONO, 8),
                                  fg=Theme.TEXT_MUT,
                                  bg=Theme.SURFACE)
        self._city_lbl.pack(anchor="w")

        # Controles
        rf = tk.Frame(hdr, bg=Theme.SURFACE)
        rf.pack(side="right", padx=16, pady=10)

        self._live_lbl = tk.Label(rf, text="● EN VIVO",
                                  font=(Theme.FONT_MONO, 9),
                                  fg=Theme.SUCCESS,
                                  bg=Theme.SURFACE)
        self._live_lbl.pack(side="right", padx=10)

        # Separador
        tk.Frame(rf, bg=Theme.BORDER, width=1,
                 height=24).pack(side="right", padx=8)

        # Botones — explícitos para evitar lambda closure bug en loops
        RippleButton(rf, text="↺  Actualizar",
                  font=(Theme.FONT_SANS, 9),
                  bg=Theme.ACCENT, fg=Theme.TEXT_INV,
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  activebackground=Theme.ACCENT_DARK,
                  activeforeground=Theme.TEXT_INV,
                  highlightthickness=1,
                  highlightbackground=Theme.BORDER,
                  command=self._refresh).pack(side="right", padx=3)

        RippleButton(rf, text="↓  CSV",
                  font=(Theme.FONT_SANS, 9),
                  bg=Theme.CARD, fg=Theme.SUCCESS,
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  activebackground=Theme.CARD_ALT,
                  activeforeground=Theme.SUCCESS,
                  highlightthickness=1,
                  highlightbackground=Theme.BORDER,
                  command=lambda: self._logger.export(self)
                  ).pack(side="right", padx=3)

        tk.Frame(rf, bg=Theme.BORDER, width=1,
                 height=24).pack(side="right", padx=8)

        # Checkboxes
        for text, var in [("Alertas", self._var_notif),
                          ("Demo",    self._var_demo)]:
            tk.Checkbutton(rf, text=text, variable=var,
                           font=(Theme.FONT_SANS, 9),
                           fg=Theme.TEXT_SEC,
                           bg=Theme.SURFACE,
                           selectcolor=Theme.ACCENT_LIGHT,
                           activebackground=Theme.SURFACE,
                           activeforeground=Theme.TEXT).pack(
                               side="right", padx=4)

        tk.Frame(rf, bg=Theme.BORDER, width=1,
                 height=24).pack(side="right", padx=8)

        # Entradas
        for var, w_, show in [
            (self._var_city,  10, False),
            (self._var_key,   24, True),
        ]:
            e = tk.Entry(rf, textvariable=var, width=w_,
                         show="*" if show else "",
                         font=(Theme.FONT_MONO, 9),
                         bg=Theme.CARD, fg=Theme.TEXT,
                         relief="flat",
                         highlightthickness=1,
                         highlightcolor=Theme.ACCENT,
                         highlightbackground=Theme.BORDER,
                         insertbackground=Theme.TEXT)
            e.pack(side="right", padx=2)

        tk.Label(rf, text="API Key:",
                 font=(Theme.FONT_SANS, 9),
                 fg=Theme.TEXT_MUT,
                 bg=Theme.SURFACE).pack(side="right", padx=(0, 2))

    def _build_notebook(self) -> None:
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True,
                      padx=6, pady=(4, 0))

        t1 = tk.Frame(self._nb, bg=Theme.BG)
        t2 = tk.Frame(self._nb, bg=Theme.BG)
        self._nb.add(t1, text="  Dashboard  ")
        self._nb.add(t2, text="  Gráficos avanzados  ")

        self._dashboard = DashboardView(t1, self._history)
        self._dashboard.pack(fill="both", expand=True)
        self._dashboard.set_city_callback(self._on_map_city_selected)

        self._charts = ChartsView(t2, self._history)
        self._charts.pack(fill="both", expand=True)

    def _build_statusbar(self) -> None:
        sb = tk.Frame(self, bg=Theme.SURFACE,
                      highlightthickness=1,
                      highlightbackground=Theme.BORDER,
                      height=24)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, textvariable=self._var_status,
                 font=(Theme.FONT_MONO, 8),
                 fg=Theme.TEXT_MUT,
                 bg=Theme.SURFACE,
                 anchor="w").pack(side="left", padx=10)
        tk.Label(sb, textvariable=self._var_upd,
                 font=(Theme.FONT_MONO, 8),
                 fg=Theme.TEXT_MUT,
                 bg=Theme.SURFACE,
                 anchor="e").pack(side="right", padx=10)

    # ══════════════════════════════════════════════════════════
    #  CICLO DE DATOS
    # ══════════════════════════════════════════════════════════

    def _refresh(self) -> None:
        """Lanza una actualización si no hay una en curso."""
        if self._busy:
            return
        self._busy = True
        self._var_status.set("⟳  Actualizando…")
        # Bug fix: leer StringVars en hilo principal antes de lanzar el hilo
        key  = self._var_key.get().strip()
        city = self._var_city.get().strip() or Config.CITY
        demo = self._var_demo.get()
        threading.Thread(
            target=self._fetch, args=(key, city, demo),
            daemon=True).start()

    def _fetch(self, key: str, city: str, demo: bool) -> None:
        """Corre en hilo secundario. Obtiene datos y llama _render."""
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
            self._logger.log(wd)

            if self._var_notif.get():
                threading.Thread(target=Notifier.evaluate,
                                 args=(wd,), daemon=True).start()

            self.after(0, lambda: self._render(mode))

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))
        finally:
            self._busy = False

    def _demo_forecast(self, base: WeatherData) -> list[dict]:
        """Genera pronóstico simulado de 8 intervalos."""
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

    # ══════════════════════════════════════════════════════════
    #  RENDER
    # ══════════════════════════════════════════════════════════

    def _on_map_city_selected(self, city: str) -> None:
        """El usuario hizo clic en una ciudad del mapa → actualizar datos."""
        # Actualizar el campo ciudad en el header
        if "," not in city:
            city_api = f"{city},CO"
        else:
            city_api = city
        self._var_city.set(city_api)
        self._var_demo.set(False)   # cambiar a API si hay key
        self._refresh()

    def _render(self, mode: str) -> None:
        """Actualiza todas las vistas con los datos más recientes."""
        wd = self._current
        self._dashboard.refresh(wd)
        self._dashboard.update_forecast(self._forecast)
        self._charts.refresh(wd)
        self._city_lbl.config(text=f"{wd.city}, {wd.country}")

        ts = datetime.now().strftime("%H:%M:%S")
        self._var_upd.set(f"Actualizado: {ts}  [{mode}]")
        self._var_status.set(
            f"✓  {wd.city}, {wd.country}  —  {wd.description}")

        # Parpadeo del indicador EN VIVO
        self._live_lbl.config(fg=Theme.ACCENT)
        self.after(600, lambda: self._live_lbl.config(fg=Theme.SUCCESS))

    def _on_error(self, msg: str) -> None:
        self._var_status.set(f"✗  Error: {msg}")
        messagebox.showerror("Error al obtener datos", msg, parent=self)

    # ══════════════════════════════════════════════════════════
    #  AUTO-REFRESH
    # ══════════════════════════════════════════════════════════

    def _schedule(self) -> None:
        if self._running:
            self.after(Config.INTERVAL * 1000, self._auto_tick)

    def _auto_tick(self) -> None:
        self._refresh()
        self._schedule()

    # ══════════════════════════════════════════════════════════
    #  ESTILOS Y CIERRE
    # ══════════════════════════════════════════════════════════

    def _apply_ttk_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",
                    background=Theme.BG,
                    borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=Theme.CARD_ALT,
                    foreground=Theme.TEXT_SEC,
                    font=(Theme.FONT_SANS, 9),
                    padding=[14, 6],
                    borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", Theme.SURFACE)],
              foreground=[("selected", Theme.ACCENT)])

    def _on_close(self) -> None:
        self._running = False
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        self.destroy()