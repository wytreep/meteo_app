"""
main.py — Punto de entrada de la aplicación.

Uso:
    python main.py

Dependencias:
    pip install requests matplotlib
"""
import sys

def check_dependencies() -> None:
    missing = []
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    if missing:
        print("⚠  Faltan dependencias. Instálalas con:")
        print(f"   pip install {' '.join(missing)}")
        print("   (La app puede funcionar en modo limitado)\n")


if __name__ == "__main__":
    check_dependencies()
    from app import WeatherStation
    app = WeatherStation()
    app.mainloop()
