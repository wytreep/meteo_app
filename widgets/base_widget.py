"""
widgets/base_widget.py — Clase base abstracta para todos los widgets.
Provee helpers de construcción y el contrato refresh(data).
"""
import tkinter as tk
from abc import ABC, abstractmethod

from config import Theme
from core.weather_data import WeatherData


class BaseWidget(tk.Frame, ABC):
    """
    Todo widget custom hereda de esta clase.
    - Hereda tk.Frame para ser un widget Tkinter válido.
    - Implementa ABC para forzar el método refresh().
    - Provee helpers: label(), card_frame().
    """

    def __init__(self, parent, bg: str = Theme.CARD, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

    # ── Helpers de construcción ───────────────────────────────────
    def label(self, text: str = "", size: int = 10, bold: bool = False,
              color: str = None, mono: bool = False,
              parent: tk.Widget = None) -> tk.Label:
        """Crea un Label con el estilo del tema."""
        p   = parent or self
        col = color or Theme.TEXT
        fam = Theme.FONT_MONO if mono else Theme.FONT_SANS
        wt  = "bold" if bold else "normal"
        return tk.Label(p, text=text, font=(fam, size, wt),
                        fg=col, bg=p.cget("bg"))

    def card_frame(self, parent: tk.Widget = None,
                   pad_x: int = 14,
                   pad_y: int = 10) -> tuple[tk.Frame, tk.Frame]:
        """
        Devuelve (outer, inner):
          outer — frame con borde
          inner — frame interior con padding
        """
        p     = parent or self
        outer = tk.Frame(p, bg=Theme.CARD,
                         highlightthickness=1,
                         highlightbackground=Theme.BORDER)
        inner = tk.Frame(outer, bg=Theme.CARD,
                         padx=pad_x, pady=pad_y)
        inner.pack(fill="both", expand=True)
        return outer, inner

    # ── Contrato obligatorio ──────────────────────────────────────
    @abstractmethod
    def refresh(self, data: WeatherData) -> None:
        """Actualiza el widget con un nuevo snapshot de datos."""
