"""
widgets/sensor_card.py — Tarjeta individual de un sensor.
Muestra icono, etiqueta, valor y barra de progreso opcional.
"""
import tkinter as tk

from config import Theme
from core.weather_data import WeatherData
from widgets.base_widget import BaseWidget


class SensorCard(BaseWidget):
    """
    Tarjeta compacta para un sensor.
    Se actualiza llamando a set_value() directamente.
    """

    def __init__(self, parent, icon: str, label: str,
                 unit: str, color: str, show_bar: bool = True):
        super().__init__(parent, bg=Theme.CARD)
        self.configure(highlightthickness=1,
                       highlightbackground=Theme.BORDER)
        self._color    = color
        self._show_bar = show_bar
        self._build(icon, label, unit)

    def _build(self, icon: str, label: str, unit: str) -> None:
        pad = tk.Frame(self, bg=Theme.CARD, padx=12, pady=10)
        pad.pack(fill="both", expand=True)

        # Fila superior: icono + etiqueta
        top = tk.Frame(pad, bg=Theme.CARD)
        top.pack(fill="x")
        tk.Label(top, text=icon, font=("", 13),
                 bg=Theme.CARD).pack(side="left", padx=(0, 6))
        self.label(label, 8, color=Theme.TEXT_MUT,
                   parent=top).pack(side="left", anchor="w")

        # Valor principal
        self._val_lbl = self.label("—", 20, bold=True,
                                   color=self._color, mono=True)
        self._val_lbl.pack(anchor="w", pady=(2, 0))

        # Unidad
        if unit:
            self.label(unit, 9, color=Theme.TEXT_SEC).pack(anchor="w")

        # Barra de progreso
        if self._show_bar:
            bg_bar = tk.Frame(pad, bg=Theme.BORDER, height=3)
            bg_bar.pack(fill="x", pady=(6, 0))
            self._bar = tk.Frame(bg_bar, bg=self._color, height=3)
            self._bar.place(x=0, y=0, relheight=1, relwidth=0)
        else:
            self._bar = None

    def refresh(self, data: WeatherData) -> None:
        """No hace nada — se actualiza externamente con set_value()."""
        pass

    def set_value(self, val: str, pct: float = 0.0,
                  color: str = None) -> None:
        """
        Actualiza el valor mostrado.
        val   — texto a mostrar
        pct   — fracción 0.0–1.0 para la barra
        color — color opcional para el valor
        """
        self._val_lbl.config(text=val)
        if color:
            self._val_lbl.config(fg=color)
            if self._bar:
                self._bar.config(bg=color)
        if self._bar is not None:
            self._bar.place(relwidth=max(0.0, min(1.0, pct)))
