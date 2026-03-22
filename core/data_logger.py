"""
core/data_logger.py — Persistencia en CSV.
Registra cada lectura y permite exportar el historial.
"""
import csv
import shutil
from pathlib import Path
from tkinter import filedialog, messagebox
from datetime import datetime

from config import Config
from core.weather_data import WeatherData

# Bug fix: usar la carpeta del script como base, no el cwd
_BASE_DIR = Path(__file__).resolve().parent.parent


class DataLogger:
    """
    Escribe cada lectura en un CSV local junto al proyecto.
    Permite exportar ese CSV a una ruta elegida por el usuario.
    """

    def __init__(self, path: Path = None):
        # Si no se especifica path, guardar junto al proyecto
        self.path = path or (_BASE_DIR / Config.DATA_FILE)
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        """Crea el archivo con cabeceras si no existe."""
        if not self.path.exists():
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(WeatherData.CSV_HEADERS)

    def log(self, wd: WeatherData) -> None:
        """Agrega una fila con los datos de la lectura actual."""
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(wd.to_csv_row())

    def export(self, parent) -> None:
        """Abre un diálogo para guardar una copia del CSV."""
        default_name = f"clima_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        dest = filedialog.asksaveasfilename(
            parent=parent,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=default_name,
            title="Exportar historial meteorológico",
        )
        if dest and self.path.exists():
            shutil.copy2(self.path, dest)
            messagebox.showinfo(
                "Exportado",
                f"Historial guardado en:\n{dest}",
                parent=parent,
            )