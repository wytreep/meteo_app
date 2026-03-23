# 🌦 MeteoApp — Kivy + KivyMD

App móvil de clima para Android e iOS construida en Python puro.
Reutiliza la capa `core/` de `meteo_app` (desktop).

---

## 📱 Pantallas

| Pantalla | Descripción |
|---|---|
| **Inicio** | Hero temperatura, sensores, pronóstico 3h, alertas |
| **Gráficos** | Multi-panel, correlación temp/humedad, barras UV |
| **Mapa** | Colombia con marcador animado de ubicación |

---

## 🚀 Ejecutar en escritorio (desarrollo)

```bash
pip install -r requirements.txt
python main.py
```

Se abre una ventana de 390×844px simulando un iPhone 14.

---

## 🤖 Compilar para Android

Requiere **Linux o WSL** (no funciona en Windows nativo):

```bash
pip install buildozer
buildozer android debug
```

El APK queda en `bin/`. Instálalo con:
```bash
adb install bin/meteoapp-1.0-arm64-v8a-debug.apk
```

---

## 🍎 Compilar para iOS

Requiere **macOS + Xcode**:

```bash
pip install kivy-ios
toolchain build kivy kivymd
toolchain create MeteoApp .
open MeteoApp-ios/MeteoApp.xcodeproj
```

---

## 🔑 API Key

Edita `config.py`:
```python
class Config:
    API_KEY = "tu_api_key_aqui"
    CITY    = "Cali,CO"
```

Gratis en: https://openweathermap.org/api

---

## 🏗 Arquitectura

```
meteo_mobile/
├── main.py                  ← MDApp + bottom nav
├── config.py                ← Config + Palette
├── buildozer.spec           ← configuración Android
│
├── core/                    ← reutilizado de meteo_app
│   ├── weather_data.py
│   ├── weather_api.py
│   ├── history.py
│   └── notifier.py
│
├── screens/                 ← pantallas completas
│   ├── dashboard_screen.py
│   ├── charts_screen.py
│   └── map_screen.py
│
└── widgets/                 ← componentes reutilizables
    └── weather_card.py      ← HeroCard, SensorCard, ForecastCard
```