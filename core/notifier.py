"""
core/notifier.py — Notificaciones nativas del sistema operativo.
Compatible con Windows (Toast), macOS y Linux (notify-send).
"""
import platform
import subprocess

from config import Config
from core.weather_data import WeatherData


class Notifier:
    """
    Envía notificaciones nativas sin spam:
    cada alerta tiene una clave única y solo se dispara una vez
    hasta que la condición desaparezca (reset).
    """

    _fired: set = set()

    @classmethod
    def send(cls, title: str, body: str, key: str = "") -> None:
        """Muestra una notificación. Si key ya fue enviada, no repite."""
        if key and key in cls._fired:
            return
        if key:
            cls._fired.add(key)
        cls._dispatch(title, body)

    @classmethod
    def reset(cls, key: str) -> None:
        """Permite que esa alerta se dispare de nuevo la próxima vez."""
        cls._fired.discard(key)

    @staticmethod
    def _dispatch(title: str, body: str) -> None:
        """Selecciona el método según el OS y lanza en background."""
        try:
            os_ = platform.system()
            if os_ == "Windows":
                ps = (
                    f'[Windows.UI.Notifications.ToastNotificationManager,'
                    f'Windows.UI.Notifications,ContentType=WindowsRuntime]'
                    f'|Out-Null;'
                    f'$t=[Windows.UI.Notifications.ToastTemplateType]'
                    f'::ToastText02;'
                    f'$x=[Windows.UI.Notifications.ToastNotificationManager]'
                    f'::GetTemplateContent($t);'
                    f'$x.GetElementsByTagName("text")[0].AppendChild('
                    f'$x.CreateTextNode("{title}"))|Out-Null;'
                    f'$x.GetElementsByTagName("text")[1].AppendChild('
                    f'$x.CreateTextNode("{body}"))|Out-Null;'
                    f'$n=[Windows.UI.Notifications.ToastNotification]'
                    f'::new($x);'
                    f'[Windows.UI.Notifications.ToastNotificationManager]'
                    f'::CreateToastNotifier("MeteoStation").Show($n);'
                )
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden",
                     "-Command", ps],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os_ == "Darwin":
                subprocess.Popen(
                    ["osascript", "-e",
                     f'display notification "{body}" with title "{title}"'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os_ == "Linux":
                subprocess.Popen(
                    ["notify-send", title, body],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass  # las notificaciones nunca deben romper la app

    @classmethod
    def evaluate(cls, wd: WeatherData) -> None:
        """Evalúa todos los umbrales y dispara las alertas necesarias."""
        a = Config.ALERT

        # UV
        if wd.uv_index >= a["uv_extreme"]:
            cls.send("UV Extremo",
                     f"Índice {wd.uv_index} en {wd.city}", "uv_ext")
        elif wd.uv_index >= a["uv_high"]:
            cls.send("UV Alto",
                     f"Índice {wd.uv_index} — usa protector solar", "uv_hi")
        else:
            cls.reset("uv_ext")
            cls.reset("uv_hi")

        # Viento
        if wd.wind_speed >= a["wind_storm"]:
            cls.send("Viento de tormenta",
                     f"{wd.wind_speed} km/h en {wd.city}", "w_storm")
        elif wd.wind_speed >= a["wind_strong"]:
            cls.send("Vientos fuertes",
                     f"{wd.wind_speed} km/h", "w_strong")
        else:
            cls.reset("w_storm")
            cls.reset("w_strong")

        # Lluvia
        if wd.rain_1h >= a["rain_heavy"]:
            cls.send("Lluvia intensa",
                     f"{wd.rain_1h} mm/h en {wd.city}", "rain")
        else:
            cls.reset("rain")

        # Temperatura
        if wd.temp >= a["temp_hot"]:
            cls.send("Temperatura alta",
                     f"{wd.temp}°C — tomar precauciones", "hot")
        elif wd.temp <= a["temp_cold"]:
            cls.send("Temperatura baja",
                     f"{wd.temp}°C", "cold")
        else:
            cls.reset("hot")
            cls.reset("cold")
