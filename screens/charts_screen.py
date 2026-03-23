"""
screens/charts_screen.py — Pantalla de gráficos históricos.
Usa matplotlib embebido en Kivy con 3 vistas seleccionables.
"""
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard

from config import Palette
from core.history import History
from core.weather_data import WeatherData

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from kivy.graphics.texture import Texture
    from kivy.uix.image import Image as KivyImage
    import numpy as np
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class ChartImage(KivyImage):
    """Widget Kivy que renderiza una figura matplotlib como textura."""

    def update_figure(self, fig: "Figure") -> None:
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        w, h = canvas.get_width_height()
        texture = Texture.create(size=(w, h), colorfmt="rgba")
        texture.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
        texture.flip_vertical()
        self.texture = texture


class ChartsScreen(MDScreen):
    """
    Pantalla de gráficos con 3 modos:
      - Multi-panel: 4 series simultáneas
      - Correlación: Temperatura vs Humedad (scatter)
      - UV: Barras por hora con colores de riesgo
    """

    def __init__(self, history: History, **kwargs):
        super().__init__(name="charts", **kwargs)
        self._history = history
        self._mode    = "multi"
        self._chart   = None
        self._build()

    def _build(self) -> None:
        root = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(12), dp(12), dp(12), dp(80)],
        )

        # Selector de modo — botones compatibles con KivyMD 2.x
        btn_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(44),
            padding=[0, dp(4), 0, dp(4)],
        )
        self._mode_btns: dict = {}
        for key, lbl in [("multi","Todos"),("correlation","Correlación"),
                          ("uv_bars","UV")]:
            btn = MDButton(
                MDButtonText(text=lbl),
                style="tonal",
                size_hint_x=1,
            )
            btn.bind(on_release=lambda x, k=key: self._switch(k))
            btn_row.add_widget(btn)
            self._mode_btns[key] = btn
        root.add_widget(btn_row)

        # Área del gráfico
        if MATPLOTLIB_OK:
            chart_card = MDCard(
                style="outlined", radius=[dp(16)],
                padding=dp(4),
            )
            self._chart = ChartImage(
                size_hint=(1, 1),
                allow_stretch=True,
                keep_ratio=True,
            )
            chart_card.add_widget(self._chart)
            root.add_widget(chart_card)
        else:
            root.add_widget(MDLabel(
                text="pip install matplotlib",
                halign="center",
                theme_text_color="Secondary",
            ))

        self.add_widget(root)
        if MATPLOTLIB_OK:
            self._draw()

    def _switch(self, key: str) -> None:
        self._mode = key
        self._draw()

    def refresh(self, data: WeatherData) -> None:
        self._draw()

    def _draw(self) -> None:
        if not MATPLOTLIB_OK or self._chart is None:
            return
        {
            "multi":       self._draw_multi,
            "correlation": self._draw_correlation,
            "uv_bars":     self._draw_uv,
        }[self._mode]()

    def _new_fig(self, rows=1, cols=1):
        fig = Figure(figsize=(6, 5), dpi=120,
                     facecolor=Palette.CHART_BG)
        fig.subplots_adjust(left=0.10, right=0.97,
                            top=0.93, bottom=0.12,
                            hspace=0.5, wspace=0.3)
        return fig

    def _style_ax(self, ax, title=""):
        ax.set_facecolor(Palette.CHART_BG)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.tick_params(colors="#8C96A5", labelsize=7,
                       bottom=False, left=False)
        ax.grid(axis="y", color=Palette.GRID,
                linewidth=0.4, alpha=0.8)
        ax.set_axisbelow(True)
        if title:
            ax.set_title(title, fontsize=8, color="#5A6578", pad=4)

    def _plot_line(self, ax, vals, color, unit, labels):
        if len(vals) < 2:
            ax.text(0.5, 0.5, "Recopilando…",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color="#8C96A5", fontsize=8)
            return
        x = range(len(vals))
        ax.fill_between(x, vals, alpha=0.08, color=color)
        ax.plot(x, vals, color=color, linewidth=1.8)
        ax.scatter([len(vals)-1], [vals[-1]], color=color, s=20, zorder=5)
        step = max(1, len(labels) // 5)
        ax.set_xticks(range(0, len(labels), step))
        ax.set_xticklabels(labels[::step], rotation=30,
                           ha="right", fontsize=6, color="#8C96A5")

    def _draw_multi(self) -> None:
        fig = self._new_fig()
        gs  = gridspec.GridSpec(2, 2, figure=fig,
                                hspace=0.55, wspace=0.3,
                                left=0.09, right=0.97,
                                top=0.94, bottom=0.10)
        lbl = self._history.xlabels()
        configs = [
            (0,0,"temps",    "Temperatura °C", Palette.SERIES[0],"°C"),
            (0,1,"humids",   "Humedad %",       Palette.SERIES[1],"%"),
            (1,0,"pressures","Presión hPa",     Palette.SERIES[2]," hPa"),
            (1,1,"winds",    "Viento km/h",     Palette.SERIES[3]," km/h"),
        ]
        for r, c, key, title, color, unit in configs:
            ax   = fig.add_subplot(gs[r, c])
            vals = list(getattr(self._history, key))
            self._style_ax(ax, title)
            self._plot_line(ax, vals, color, unit, lbl)
        self._chart.update_figure(fig)
        plt.close(fig)

    def _draw_correlation(self) -> None:
        fig = self._new_fig()
        ax  = fig.add_subplot(111)
        self._style_ax(ax, "Temperatura vs Humedad")
        temps  = list(self._history.temps)
        humids = list(self._history.humids)
        if len(temps) >= 3:
            hours = [t.hour for t in self._history.times]
            sc = ax.scatter(temps, humids, c=hours,
                            cmap="Blues", s=35, alpha=0.85,
                            zorder=3, vmin=0, vmax=23)
            cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
            cbar.ax.tick_params(labelsize=6, colors="#8C96A5")
            cbar.set_label("Hora", fontsize=7, color="#8C96A5")
            ax.set_xlabel("Temperatura °C", fontsize=8, color="#8C96A5")
            ax.set_ylabel("Humedad %",      fontsize=8, color="#8C96A5")
        else:
            ax.text(0.5, 0.5, "Se necesitan ≥3 lecturas",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color="#8C96A5", fontsize=10)
        self._chart.update_figure(fig)
        plt.close(fig)

    def _draw_uv(self) -> None:
        def uv_color(v):
            if v < 3:  return Palette.SUCCESS
            if v < 6:  return Palette.WARNING
            if v < 8:  return "#E64A19"
            if v < 11: return Palette.DANGER
            return "#6A1B9A"

        fig = self._new_fig()
        ax  = fig.add_subplot(111)
        self._style_ax(ax, "Índice UV por lectura")
        vals   = list(self._history.uv) or [0]
        colors = [uv_color(v) for v in vals]
        ax.bar(range(len(vals)), vals, color=colors,
               alpha=0.85, width=0.7)
        ax.set_ylim(0, 12)
        patches = [
            mpatches.Patch(color=Palette.SUCCESS, label="Bajo (<3)"),
            mpatches.Patch(color=Palette.WARNING, label="Moderado (3-5)"),
            mpatches.Patch(color="#E64A19",       label="Alto (6-7)"),
            mpatches.Patch(color=Palette.DANGER,  label="Muy alto (8+)"),
        ]
        ax.legend(handles=patches, fontsize=6, loc="upper left",
                  framealpha=0.7, edgecolor=Palette.OUTLINE)
        lbl  = self._history.xlabels()
        if lbl:
            step = max(1, len(lbl) // 8)
            ax.set_xticks(range(0, len(lbl), step))
            ax.set_xticklabels(lbl[::step], rotation=30,
                               ha="right", fontsize=6, color="#8C96A5")
        self._chart.update_figure(fig)
        plt.close(fig)