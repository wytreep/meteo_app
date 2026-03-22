"""
views/charts_view.py — Vista de gráficos avanzados multi-panel.
3 modos: todos los sensores, correlación Temp/Humedad, barras UV.
"""
import tkinter as tk

from config import Theme
from core.history      import History
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget

try:
    import matplotlib.gridspec as gridspec
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class ChartsView(BaseWidget):
    """
    Pestaña de gráficos avanzados con 3 vistas seleccionables.
    """

    MODES = [
        ("multi",       "Todos los sensores"),
        ("correlation", "Temp vs Humedad"),
        ("uv_bars",     "Índice UV"),
    ]

    def __init__(self, parent, history: History):
        super().__init__(parent, bg=Theme.BG)
        self._history  = history
        self._mode     = "multi"
        self._fig      = None
        self._mpl_cv   = None
        self._tab_btns: dict[str, tk.Button] = {}
        self._build()

    def _build(self) -> None:
        # Barra de modos
        ctrl = tk.Frame(self, bg=Theme.BG)
        ctrl.pack(fill="x", padx=10, pady=(8, 0))
        self.label("VISTA:", 9, color=Theme.TEXT_MUT,
                   parent=ctrl, mono=True).pack(side="left", padx=(0, 8))

        for key, lbl in self.MODES:
            b = tk.Button(ctrl, text=lbl,
                          font=(Theme.FONT_MONO, 8),
                          relief="flat", padx=10, pady=4,
                          cursor="hand2",
                          command=lambda k=key: self._switch(k))
            b.pack(side="left", padx=(0, 4))
            self._tab_btns[key] = b

        # Área matplotlib
        if MATPLOTLIB_OK:
            self._fig  = Figure(figsize=(1, 1), dpi=96,
                                facecolor=Theme.CHART_BG)
            self._mpl_cv = FigureCanvasTkAgg(self._fig, master=self)
            self._mpl_cv.get_tk_widget().pack(
                fill="both", expand=True, padx=10, pady=8)
        else:
            self.label("pip install matplotlib", 12,
                       color=Theme.WARNING).pack(expand=True)

        self._switch("multi")

    def _switch(self, key: str) -> None:
        self._mode = key
        for k, b in self._tab_btns.items():
            active = k == key
            b.config(
                bg=Theme.ACCENT   if active else Theme.CARD,
                fg=Theme.TEXT_INV if active else Theme.TEXT_SEC,
            )
        self.draw()

    def refresh(self, data: WeatherData) -> None:
        self.draw()

    def draw(self) -> None:
        if not MATPLOTLIB_OK or self._fig is None:
            return
        self._fig.clear()
        {
            "multi":       self._draw_multi,
            "correlation": self._draw_correlation,
            "uv_bars":     self._draw_uv,
        }[self._mode]()
        try:
            self._mpl_cv.draw()
        except Exception:
            pass

    # ── Helpers ───────────────────────────────────────────────
    def _style_ax(self, ax, title: str = "") -> None:
        ax.set_facecolor(Theme.CHART_BG)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.tick_params(colors=Theme.TEXT_MUT, labelsize=6,
                       bottom=False, left=False)
        ax.grid(axis="y", color=Theme.GRID,
                linewidth=0.4, alpha=0.8)
        ax.set_axisbelow(True)
        if title:
            ax.set_title(title, fontsize=8, color=Theme.TEXT_SEC,
                         pad=4, fontfamily=Theme.FONT_MONO)

    def _plot_series(self, ax, vals: list, color: str,
                     unit: str, labels: list) -> None:
        if len(vals) < 2:
            ax.text(0.5, 0.5, "Recopilando…",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color=Theme.TEXT_MUT, fontsize=8)
            return
        x = range(len(vals))
        ax.fill_between(x, vals, alpha=0.07, color=color)
        ax.plot(x, vals, color=color, linewidth=1.5)
        ax.scatter([len(vals)-1], [vals[-1]],
                   color=color, s=18, zorder=5)
        ax.annotate(f"{vals[-1]}{unit}",
                    xy=(len(vals)-1, vals[-1]),
                    fontsize=6, color=color,
                    fontfamily=Theme.FONT_MONO,
                    ha="right", va="bottom")
        step = max(1, len(labels) // 5)
        ax.set_xticks(range(0, len(labels), step))
        ax.set_xticklabels(labels[::step], rotation=30, ha="right",
                           fontsize=5, color=Theme.TEXT_MUT,
                           fontfamily=Theme.FONT_MONO)

    # ── Modos de gráfico ──────────────────────────────────────
    def _draw_multi(self) -> None:
        gs = gridspec.GridSpec(2, 2, figure=self._fig,
                               hspace=0.55, wspace=0.25,
                               left=0.06, right=0.97,
                               top=0.94, bottom=0.10)
        configs = [
            (0, 0, "temps",     "Temperatura °C",  Theme.SERIES[0], "°C"),
            (0, 1, "humids",    "Humedad %",        Theme.SERIES[1], "%"),
            (1, 0, "pressures", "Presión hPa",      Theme.SERIES[2], " hPa"),
            (1, 1, "winds",     "Viento km/h",      Theme.SERIES[3], " km/h"),
        ]
        lbl = self._history.xlabels()
        for r, c, key, title, color, unit in configs:
            ax   = self._fig.add_subplot(gs[r, c])
            vals = list(getattr(self._history, key))
            self._style_ax(ax, title)
            self._plot_series(ax, vals, color, unit, lbl)

    def _draw_correlation(self) -> None:
        ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(
            left=0.10, right=0.95, top=0.90, bottom=0.12)
        self._style_ax(ax, "Correlación: Temperatura vs Humedad")

        temps  = list(self._history.temps)
        humids = list(self._history.humids)

        if len(temps) >= 3:
            hours = [t.hour for t in self._history.times]
            sc = ax.scatter(temps, humids, c=hours,
                            cmap="Blues", s=30, alpha=0.85,
                            zorder=3, vmin=0, vmax=23)
            cbar = self._fig.colorbar(sc, ax=ax,
                                      fraction=0.025, pad=0.02)
            cbar.ax.tick_params(labelsize=6, colors=Theme.TEXT_MUT)
            cbar.set_label("Hora", fontsize=7,
                           color=Theme.TEXT_MUT,
                           fontfamily=Theme.FONT_MONO)
            ax.set_xlabel("Temperatura °C", fontsize=8,
                          color=Theme.TEXT_MUT,
                          fontfamily=Theme.FONT_MONO)
            ax.set_ylabel("Humedad %", fontsize=8,
                          color=Theme.TEXT_MUT,
                          fontfamily=Theme.FONT_MONO)
        else:
            ax.text(0.5, 0.5, "Se necesitan ≥3 lecturas",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color=Theme.TEXT_MUT, fontsize=10)

    def _draw_uv(self) -> None:
        ax = self._fig.add_subplot(111)
        self._fig.subplots_adjust(
            left=0.06, right=0.97, top=0.90, bottom=0.18)
        self._style_ax(ax, "Índice UV por lectura")

        vals = list(self._history.uv) or [0]
        x    = range(len(vals))
        colors = [Theme.uv_color(v) for v in vals]
        ax.bar(x, vals, color=colors, alpha=0.85, width=0.7)
        ax.set_ylim(0, 12)

        patches = [
            mpatches.Patch(color=Theme.SUCCESS, label="Bajo (<3)"),
            mpatches.Patch(color=Theme.WARNING, label="Moderado (3-5)"),
            mpatches.Patch(color="#EA580C",     label="Alto (6-7)"),
            mpatches.Patch(color=Theme.DANGER,  label="Muy alto (8-10)"),
            mpatches.Patch(color="#7C3AED",     label="Extremo (≥11)"),
        ]
        ax.legend(handles=patches, fontsize=7, loc="upper left",
                  framealpha=0.7, edgecolor=Theme.BORDER,
                  labelcolor=Theme.TEXT)

        lbl  = self._history.xlabels()
        if lbl:
            step = max(1, len(lbl) // 8)
            ax.set_xticks(range(0, len(lbl), step))
            ax.set_xticklabels(lbl[::step], rotation=30, ha="right",
                               fontsize=6, color=Theme.TEXT_MUT,
                               fontfamily=Theme.FONT_MONO)
