"""
widgets/mini_chart.py — Gráfico sparkline embebido con tabs.
Muestra el historial de la sesión para 4 métricas.
"""
import tkinter as tk

from config import Theme
from core.history import History
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget

try:
    import matplotlib.ticker as mticker
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class MiniChart(BaseWidget):
    """
    Gráfico de historial con 4 pestañas:
    Temperatura | Humedad | Presión | Viento
    """

    CHART_META = {
        "temps":     ("Temperatura", "°C",    0),
        "humids":    ("Humedad",     "%",      1),
        "pressures": ("Presión",     " hPa",   2),
        "winds":     ("Viento",      " km/h",  3),
    }

    def __init__(self, parent, history: History):
        super().__init__(parent, bg=Theme.CARD)
        self._history  = history
        self._active   = "temps"
        self._tab_btns: dict[str, tk.Button] = {}
        self._fig      = None
        self._ax       = None
        self._mpl_cv   = None
        self._build()

    def _build(self) -> None:
        # Cabecera con tabs
        hdr = tk.Frame(self, bg=Theme.CARD)
        hdr.pack(fill="x", padx=12, pady=(8, 0))
        self.label("HISTORIAL", 8, color=Theme.TEXT_MUT,
                   parent=hdr, mono=True).pack(side="left")

        tabs_f = tk.Frame(hdr, bg=Theme.CARD)
        tabs_f.pack(side="right")

        tab_labels = {
            "temps":     "Temp",
            "humids":    "Humedad",
            "pressures": "Presión",
            "winds":     "Viento",
        }
        for key, lbl in tab_labels.items():
            b = tk.Button(tabs_f, text=lbl,
                          font=(Theme.FONT_MONO, 8),
                          relief="flat", padx=8, pady=3,
                          cursor="hand2",
                          command=lambda k=key: self._switch(k))
            b.pack(side="left", padx=2)
            self._tab_btns[key] = b

        # Área del gráfico
        if MATPLOTLIB_OK:
            self._fig = Figure(figsize=(1, 1), dpi=96,
                               facecolor=Theme.CHART_BG)
            self._ax  = self._fig.add_subplot(111)
            self._fig.subplots_adjust(
                left=0.06, right=0.97, top=0.88, bottom=0.22)
            self._mpl_cv = FigureCanvasTkAgg(self._fig, master=self)
            self._mpl_cv.get_tk_widget().pack(
                fill="both", expand=True, padx=6, pady=6)
        else:
            self.label("pip install matplotlib", 10,
                       color=Theme.WARNING).pack(expand=True)

        self._switch("temps")

    def _switch(self, key: str) -> None:
        self._active = key
        for k, b in self._tab_btns.items():
            active = k == key
            b.config(
                bg=Theme.ACCENT   if active else Theme.CARD_ALT,
                fg=Theme.TEXT_INV if active else Theme.TEXT_SEC,
            )
        self.draw()

    def refresh(self, data: WeatherData) -> None:
        self.draw()

    def draw(self) -> None:
        if not MATPLOTLIB_OK or self._ax is None:
            return

        label, unit, series_idx = self.CHART_META[self._active]
        color  = Theme.SERIES[series_idx]
        vals   = list(getattr(self._history, self._active))
        labels = self._history.xlabels()

        ax = self._ax
        ax.clear()
        ax.set_facecolor(Theme.CHART_BG)
        self._fig.patch.set_facecolor(Theme.CHART_BG)

        if len(vals) >= 2:
            x = range(len(vals))
            ax.fill_between(x, vals, alpha=0.08, color=color)
            ax.plot(x, vals, color=color, linewidth=1.8,
                    solid_capstyle="round")
            ax.scatter([len(vals)-1], [vals[-1]],
                       color=color, s=22, zorder=5)
            ax.annotate(
                f"{vals[-1]}{unit}",
                xy=(len(vals)-1, vals[-1]),
                fontsize=7, color=color,
                fontfamily=Theme.FONT_MONO,
                ha="right", va="bottom",
            )
            step = max(1, len(labels) // 7)
            ax.set_xticks(range(0, len(labels), step))
            ax.set_xticklabels(
                labels[::step], rotation=30, ha="right",
                fontsize=6, color=Theme.TEXT_MUT,
                fontfamily=Theme.FONT_MONO,
            )
        else:
            ax.text(0.5, 0.5, "Recopilando datos…",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color=Theme.TEXT_MUT, fontsize=9)

        ax.set_title(label, fontsize=8, color=Theme.TEXT_SEC,
                     pad=4, fontfamily=Theme.FONT_MONO)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.tick_params(colors=Theme.TEXT_MUT, labelsize=6,
                       bottom=False, left=False)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"{v:.0f}{unit}"))
        ax.tick_params(axis="y", labelsize=6,
                       labelcolor=Theme.TEXT_MUT)
        ax.grid(axis="y", color=Theme.GRID,
                linewidth=0.5, alpha=0.8)
        ax.set_axisbelow(True)

        try:
            self._mpl_cv.draw()
        except Exception:
            pass
