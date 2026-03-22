# 🌦 Estación Meteorológica

> Aplicación de escritorio en Python para monitorear el clima en tiempo real con interfaz gráfica oscura, gráficos multi-panel, mapa interactivo y notificaciones del sistema.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=flat-square)
![Matplotlib](https://img.shields.io/badge/Charts-Matplotlib-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)
![API](https://img.shields.io/badge/API-OpenWeatherMap-red?style=flat-square)

---

## ✨ Características

| Feature | Descripción |
|---|---|
| 📊 **Dashboard** | Temperatura, humedad, presión, viento, UV y más |
| 📈 **4 tipos de gráficos** | Multi-panel, correlación, rosa de vientos, UV por hora |
| 🗺 **Mapa de Colombia** | Ubicación en tiempo real con marcador animado |
| 🔔 **Notificaciones** | Alertas nativas del OS (Windows, macOS, Linux) |
| ⬇ **Exportar CSV** | Historial completo exportable en un clic |
| 🔄 **Auto-refresh** | Actualización automática cada 30 segundos |
| 🎮 **Modo Demo** | Funciona sin API key con datos simulados |

---

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/weather-station.git
cd weather-station

# 2. Instalar dependencias
pip install requests matplotlib pillow

# En Linux puede necesitar tkinter:
sudo apt install python3-tk

# 3. Ejecutar
python weather_station.py
```

---

## 🔑 API Key (opcional)

La app funciona en **Modo Demo** sin API key. Para datos reales:

1. Crea cuenta gratis en [openweathermap.org/api](https://openweathermap.org/api)
2. Ve a **My API Keys** y copia tu clave
3. Pégala en la barra superior de la app

> ⚠️ Las keys nuevas tardan ~10 minutos en activarse.

---

## 🖥 Capturas

```
┌─────────────────────────────────────────────────────────┐
│  🌦 METEO-STATION v2.0          [API: ****]  [↺ Actualizar]│
├─────────┬───────────────────────────┬───────────────────┤
│         │  💨 Viento  🧭 Dirección   │  VIENTO           │
│   ⛅    │  18 km/h    NNO           │  [brújula]        │
│  24.3°C │  ────────────────────────│                   │
│         │  [gráfico temperatura]   │  ESTADÍSTICAS     │
│ 72%     │                          │  ────────────────│
│ 1013hPa │  [pronóstico 3h x8]      │  MAPA COLOMBIA    │
└─────────┴───────────────────────────┴───────────────────┘
```

---

## 📁 Estructura

```
weather-station/
├── weather_station.py     # App principal (~700 líneas)
├── weather_history.csv    # Generado al ejecutar (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🏗 Arquitectura

```
WeatherData      — Estructura de datos, parseo de API, modo demo
WeatherAPI       — Cliente HTTP OpenWeatherMap
History          — Historial con deque, estadísticas de sesión
Notifier         — Notificaciones nativas (Windows/macOS/Linux)
DataLogger       — Registro y exportación CSV
MapWidget        — Mapa de Colombia dibujado en Canvas de Tkinter
CompassWidget    — Brújula animada con Canvas
WeatherStation   — GUI principal: Dashboard + Gráficos + Mapa
```

---

## ⚙️ Configuración

Edita estas variables al inicio de `weather_station.py`:

```python
API_KEY      = ""          # Tu API key de OpenWeatherMap
CITY         = "Cali,CO"   # Ciudad por defecto
UNITS        = "metric"    # metric=°C | imperial=°F
INTERVAL     = 30          # Segundos entre actualizaciones
HISTORY_LEN  = 120         # Puntos máximos en gráficos
```

También puedes personalizar los umbrales de alerta:

```python
ALERT_THRESHOLDS = {
    "uv_high":    6,      # Índice UV alto
    "wind_strong": 45,    # Vientos fuertes (km/h)
    "rain_heavy":  10,    # Lluvia intensa (mm/h)
    "temp_hot":    35,    # Temperatura alta (°C)
    ...
}
```

---

## 📦 Dependencias

| Librería | Uso | Obligatoria |
|---|---|---|
| `requests` | Llamadas a la API | Sí |
| `matplotlib` | Gráficos | Sí |
| `pillow` | Procesamiento de imágenes | Recomendada |
| `tkinter` | GUI (incluida en Python) | Sí |
| `numpy` | Línea de tendencia en scatter | Opcional |

---

## 🐛 Solución de problemas

**`ModuleNotFoundError: No module named 'tkinter'`**
```bash
sudo apt install python3-tk    # Ubuntu/Debian
sudo dnf install python3-tkinter  # Fedora
```

**Error 401 (API Key inválida)**
- Verifica que la key esté copiada completa
- Las keys nuevas pueden tardar 10 min en activarse

**Notificaciones no aparecen en Windows**
- Verifica que las notificaciones de PowerShell estén habilitadas
- La app usa Toast Notifications nativas

---

## 📄 Licencia

MIT — libre para usar, modificar y distribuir.

---

*Hecho con Python 3.10+ · Tkinter · Matplotlib · OpenWeatherMap API*
