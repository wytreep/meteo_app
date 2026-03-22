"""
widgets/forecast_bar.py — Barra de pronóstico 3h.
"""
import tkinter as tk

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class ForecastBar(BaseWidget):
    """
    Muestra hasta 8 celdas de pronóstico en fila horizontal.
    Se actualiza con update_forecast(items).
    """

    def __init__(self, parent):
        super().__init__(parent, bg=Theme.CARD)
        self._row = tk.Frame(self, bg=Theme.CARD)
        self._row.pack(fill="x", padx=2, pady=4)

    def refresh(self, data: WeatherData) -> None:
        pass  # actualizado externamente con update_forecast()

    def update_forecast(self, items: list[dict]) -> None:
        """Reconstruye las celdas con los nuevos datos."""
        for w in self._row.winfo_children():
            w.destroy()

        for i, fc in enumerate(items[:8]):
            cell = tk.Frame(self._row, bg=Theme.CARD_ALT,
                            highlightthickness=1,
                            highlightbackground=Theme.BORDER)
            cell.pack(side="left", fill="x", expand=True,
                      padx=(0 if i == 0 else 4, 0))

            pad = tk.Frame(cell, bg=Theme.CARD_ALT, padx=6, pady=6)
            pad.pack(fill="both")

            tk.Label(pad, text=fc["hour"],
                     font=(Theme.FONT_MONO, 8),
                     fg=Theme.TEXT_MUT,
                     bg=Theme.CARD_ALT).pack()
            tk.Label(pad, text=WeatherData.WX_EMOJI.get(fc["icon"], "●"),
                     font=("", 16),
                     bg=Theme.CARD_ALT).pack()
            tk.Label(pad, text=f"{round(fc['temp']):.0f}°",
                     font=(Theme.FONT_MONO, 12, "bold"),
                     fg=Theme.TEXT,
                     bg=Theme.CARD_ALT).pack()
            tk.Label(pad, text=f"{fc['humid']}%",
                     font=(Theme.FONT_MONO, 8),
                     fg=Theme.INFO,
                     bg=Theme.CARD_ALT).pack()
