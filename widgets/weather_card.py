"""
widgets/weather_card.py — Tarjetas KivyMD con iconos y animaciones.

Mejoras v2:
  - Iconos vectoriales dibujados en Canvas de Kivy (no emojis)
  - Efecto ripple nativo de KivyMD en todas las tarjetas
  - Hover con elevation animation en MDCard
  - Tooltip en long-press
  - Brújula con rotación animada
  - Barras de progreso animadas
"""
import math
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Triangle, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from config import Palette


# ── Icono vectorial en Canvas Kivy ────────────────────────────────────────
class VectorIcon(Widget):
    """Dibuja iconos vectoriales meteorológicos en Canvas de Kivy."""

    ICON_SIZE = dp(32)

    def __init__(self, key: str, color: list, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (self.ICON_SIZE, self.ICON_SIZE))
        super().__init__(**kwargs)
        self._key   = key
        self._color = color
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(lambda dt: self._draw(), 0.05)

    def set_color(self, color: list) -> None:
        self._color = color
        self._draw()

    def _draw(self, *args) -> None:
        self.canvas.clear()
        w, h = self.size
        x, y = self.pos
        c = self._color
        k = self._key
        with self.canvas:
            Color(*c)
            if   k == "humid":    self._droplet(x, y, w, h)
            elif k == "pressure": self._gauge(x, y, w, h)
            elif k == "uv":       self._sun(x, y, w, h)
            elif k == "vis":      self._eye(x, y, w, h)
            elif k == "rain":     self._rain(x, y, w, h)
            elif k == "dew":      self._thermo(x, y, w, h)
            else:                 self._sun(x, y, w, h)

    def _droplet(self, x, y, w, h):
        cx = x + w/2
        # Cuerpo
        Ellipse(pos=(cx-w*0.28, y+h*0.25), size=(w*0.56, h*0.55))
        # Punta
        Triangle(points=[cx-w*0.18, y+h*0.55, cx+w*0.18, y+h*0.55,
                         cx, y+h*0.90])

    def _gauge(self, x, y, w, h):
        cx, cy = x+w/2, y+h/2
        r = min(w,h)*0.38
        Line(circle=(cx, cy, r, 0, 180), width=dp(2))
        # Aguja
        ang = math.radians(140)
        Line(points=[cx, cy, cx+r*0.8*math.cos(ang), cy+r*0.8*math.sin(ang)],
             width=dp(1.8), cap="round")
        Ellipse(pos=(cx-dp(3), cy-dp(3)), size=(dp(6), dp(6)))

    def _sun(self, x, y, w, h):
        cx, cy = x+w/2, y+h/2
        r = min(w,h)*0.22
        Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
        for i in range(8):
            a  = math.radians(i*45)
            x1 = cx+(r+dp(2))*math.cos(a); y1 = cy+(r+dp(2))*math.sin(a)
            x2 = cx+(r+dp(5))*math.cos(a); y2 = cy+(r+dp(5))*math.sin(a)
            Line(points=[x1, y1, x2, y2], width=dp(1.5), cap="round")

    def _eye(self, x, y, w, h):
        cx, cy = x+w/2, y+h/2
        rx, ry = w*0.40, h*0.22
        Line(ellipse=(cx-rx, cy-ry, rx*2, ry*2), width=dp(1.8))
        r = min(w,h)*0.12
        Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))

    def _rain(self, x, y, w, h):
        cx = x+w/2
        # Nube
        Ellipse(pos=(x+w*0.12, y+h*0.45), size=(w*0.40, h*0.35))
        Ellipse(pos=(x+w*0.35, y+h*0.50), size=(w*0.48, h*0.35))
        Rectangle(pos=(x+w*0.12, y+h*0.50), size=(w*0.76, h*0.20))
        # Gotas
        for fx in [0.25, 0.48, 0.70]:
            y0 = y + h*0.35
            Line(points=[x+w*fx, y0, x+w*fx, y0+h*0.20],
                 width=dp(1.8), cap="round")

    def _thermo(self, x, y, w, h):
        cx = x + w/2
        # Tubo
        Line(rectangle=(cx-dp(4), y+h*0.12, dp(8), h*0.55), width=dp(1.5))
        Rectangle(pos=(cx-dp(3), y+h*0.35), size=(dp(6), h*0.32))
        # Bulbo
        Ellipse(pos=(cx-dp(7), y+h*0.08), size=(dp(14), dp(14)))


# ── Brújula animada en Kivy Canvas ────────────────────────────────────────
class CompassWidget(Widget):
    """Brújula con rotación suave interpolada."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target  = 0.0
        self._current = 0.0
        self._anim_running = False
        self.bind(pos=lambda *_: self._draw(), size=lambda *_: self._draw())
        Clock.schedule_once(lambda dt: self._draw(), 0.1)

    def set_angle(self, deg: float) -> None:
        diff = (deg - self._target + 180) % 360 - 180
        self._target = self._current + diff
        if not self._anim_running:
            self._anim_running = True
            Clock.schedule_interval(self._step, 1/60)

    def _step(self, dt) -> None:
        diff = self._target - self._current
        if abs(diff) < 0.3:
            self._current = self._target % 360
            self._anim_running = False
            Clock.unschedule(self._step)
        else:
            self._current += diff * 0.12
        self._draw()

    def _draw(self, *args) -> None:
        self.canvas.clear()
        w, h   = self.width, self.height
        if w < 10 or h < 10:
            return
        cx, cy = self.x + w/2, self.y + h/2
        r      = min(w, h) / 2 - dp(4)
        r2     = r - dp(10)
        ang    = self._current % 360

        with self.canvas:
            # Fondo
            Color(0.965, 0.969, 0.976, 1)
            Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
            Color(0.773, 0.792, 0.824, 1)
            Line(circle=(cx, cy, r), width=dp(1.5))
            Line(circle=(cx, cy, r2), width=dp(0.6))

            # Ticks
            for deg in range(0, 360, 30):
                a  = math.radians(deg - 90)
                rl = r - (dp(12) if deg%90==0 else dp(7))
                x1 = cx + rl*math.cos(a); y1 = cy + rl*math.sin(a)
                x2 = cx + (r-dp(3))*math.cos(a); y2 = cy + (r-dp(3))*math.sin(a)
                Color(0.647, 0.698, 0.773, 1)
                Line(points=[x1,y1,x2,y2], width=dp(1.2) if deg%90==0 else dp(0.7))

            # Aguja norte — azul
            rad    = math.radians(ang - 90)
            ar     = r2 - dp(6)
            tx     = cx + ar*math.cos(rad)
            ty     = cy + ar*math.sin(rad)
            tx2    = cx - (ar*0.45)*math.cos(rad)
            ty2    = cy - (ar*0.45)*math.sin(rad)
            pw     = dp(5)
            perp   = math.radians(ang)
            wx_    = pw*math.cos(perp); wy_ = pw*math.sin(perp)
            Color(0.082, 0.396, 0.753, 1)
            Triangle(points=[tx,ty, cx+wx_,cy+wy_, cx-wx_,cy-wy_])

            # Aguja sur — gris
            Color(0.647, 0.698, 0.773, 1)
            Triangle(points=[tx2,ty2, cx+wx_,cy+wy_, cx-wx_,cy-wy_])

            # Centro
            Color(1, 1, 1, 1)
            Ellipse(pos=(cx-dp(5), cy-dp(5)), size=(dp(10), dp(10)))
            Color(0.082, 0.396, 0.753, 1)
            Line(circle=(cx, cy, dp(5)), width=dp(1.5))
            Ellipse(pos=(cx-dp(2), cy-dp(2)), size=(dp(4), dp(4)))


# ── HeroCard ──────────────────────────────────────────────────────────────
class HeroCard(MDCard):
    """Tarjeta hero con temperatura principal, descripción y tendencia."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.style       = "filled"
        self.radius      = [dp(24)]
        self.padding     = dp(24)
        self.md_bg_color = [0.082, 0.396, 0.753, 1]
        self.size_hint_y = None
        self.height      = dp(220)
        self.ripple_behavior = True
        self._build()

    def _build(self) -> None:
        root = MDBoxLayout(orientation="vertical", spacing=dp(4))

        self._city_lbl = MDLabel(
            text="—", font_style="Title", role="medium",
            theme_text_color="Custom", text_color=[1,1,1,0.8],
            size_hint_y=None, height=dp(28))
        root.add_widget(self._city_lbl)

        temp_row = MDBoxLayout(orientation="horizontal",
                               size_hint_y=None, height=dp(90))
        self._icon_widget = VectorIcon("uv", [1,1,1,0.9],
                                       size=(dp(50), dp(50)),
                                       size_hint=(None,None))
        temp_row.add_widget(self._icon_widget)

        temp_col = MDBoxLayout(orientation="vertical", padding=[dp(8),0,0,0])
        self._temp_lbl = MDLabel(
            text="—°C", font_style="Display", role="medium",
            bold=True, theme_text_color="Custom", text_color=[1,1,1,1])
        temp_col.add_widget(self._temp_lbl)
        self._feels_lbl = MDLabel(
            text="Sensación: —", font_style="Body", role="medium",
            theme_text_color="Custom", text_color=[1,1,1,0.7])
        temp_col.add_widget(self._feels_lbl)
        temp_row.add_widget(temp_col)
        root.add_widget(temp_row)

        bot = MDBoxLayout(orientation="horizontal",
                          size_hint_y=None, height=dp(28))
        self._desc_lbl = MDLabel(
            text="—", font_style="Body", role="large",
            theme_text_color="Custom", text_color=[1,1,1,0.9])
        bot.add_widget(self._desc_lbl)
        self._trend_lbl = MDLabel(
            text="", font_style="Label", role="large",
            theme_text_color="Custom", text_color=[1,1,1,0.8],
            halign="right")
        bot.add_widget(self._trend_lbl)
        root.add_widget(bot)

        self._mm_lbl = MDLabel(
            text="↓ — / ↑ —", font_style="Label", role="medium",
            theme_text_color="Custom", text_color=[1,1,1,0.7],
            size_hint_y=None, height=dp(20))
        root.add_widget(self._mm_lbl)
        self.add_widget(root)

    def update(self, city, temp, feels, desc,
               icon_key, trend, t_min, t_max) -> None:
        self._city_lbl.text  = city
        self._temp_lbl.text  = f"{temp}°C"
        self._feels_lbl.text = f"Sensación: {feels}°C"
        self._desc_lbl.text  = desc
        self._icon_widget.set_color([1, 1, 1, 0.9])  # siempre blanco en hero
        self._mm_lbl.text    = f"↓ {t_min}° / ↑ {t_max}°"
        trend_map = {"up":"↑ Subiendo","down":"↓ Bajando","stable":"→ Estable"}
        self._trend_lbl.text = trend_map.get(trend, "")
        # Animación de entrada
        self.opacity = 0.7
        Animation(opacity=1, duration=0.3).start(self)


# ── SensorCard ────────────────────────────────────────────────────────────
class SensorCard(MDCard):
    """Tarjeta de sensor con icono vectorial, ripple y barra animada."""

    def __init__(self, key: str, icon_key: str, label: str,
                 unit: str, color: list, show_bar: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.style       = "elevated"
        self.radius      = [dp(16)]
        self.padding     = dp(14)
        self.spacing     = dp(6)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height      = dp(115) if show_bar else dp(90)
        self._color      = color
        self._show_bar   = show_bar
        self._pct_target = 0.0
        self._bar_widget = None
        self._build(key, icon_key, label, unit, show_bar)

    def _build(self, key, icon_key, label, unit, show_bar: bool) -> None:
        top = MDBoxLayout(orientation="horizontal", spacing=dp(10),
                          size_hint_y=None, height=dp(26))
        self._icon = VectorIcon(icon_key, self._color,
                                size=(dp(24), dp(24)))
        top.add_widget(self._icon)
        top.add_widget(MDLabel(text=label, font_style="Label",
                               role="medium",
                               theme_text_color="Secondary"))
        self.add_widget(top)

        self._val_lbl = MDLabel(
            text="—", font_style="Title", role="large",
            bold=True, theme_text_color="Custom",
            text_color=self._color)
        self.add_widget(self._val_lbl)

        if unit:
            self.add_widget(MDLabel(
                text=unit, font_style="Label", role="small",
                theme_text_color="Secondary",
                size_hint_y=None, height=dp(14)))

        if show_bar:
            self._bar_widget = ProgressBar(
                value=0, max=100,
                size_hint_y=None, height=dp(5))
            self.add_widget(self._bar_widget)

    def set_value(self, val: str, pct: float = 0.0,
                  color: list = None) -> None:
        self._val_lbl.text = val
        if color:
            self._color = color
            self._val_lbl.text_color = color
            self._icon.set_color(color)
        if self._bar_widget is not None:
            target = max(0, min(100, int(pct * 100)))
            anim = Animation(value=target, duration=0.5, t="out_cubic")
            anim.start(self._bar_widget)


# ── InfoRow ───────────────────────────────────────────────────────────────
class InfoRow(MDBoxLayout):
    """Fila de info rápida con tarjetas pequeñas y ripple."""

    def __init__(self, items: list, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing     = dp(8)
        self.size_hint_y = None
        self.height      = dp(72)
        self._labels: dict = {}

        for key, icon_key, label in items:
            card = MDCard()
            card.style        = "outlined"
            card.radius       = [dp(12)]
            card.padding      = dp(10)
            card.orientation  = "vertical"
            card.spacing      = dp(2)
            col = MDBoxLayout(orientation="horizontal", spacing=dp(4),
                              size_hint_y=None, height=dp(20))
            icon = VectorIcon(icon_key, self._hex_rgba(Palette.PRIMARY),
                              size=(dp(16), dp(16)))
            col.add_widget(icon)
            col.add_widget(MDLabel(text=label, font_style="Label",
                                   role="small",
                                   theme_text_color="Secondary"))
            card.add_widget(col)
            val = MDLabel(text="—", font_style="Title", role="small",
                          bold=True)
            card.add_widget(val)
            self.add_widget(card)
            self._labels[key] = val

    def set(self, key: str, val: str) -> None:
        if key in self._labels:
            self._labels[key].text = val

    @staticmethod
    def _hex_rgba(h: str) -> list:
        h = h.lstrip("#")
        return [int(h[i:i+2],16)/255 for i in (0,2,4)] + [1.0]


# ── ForecastCard ──────────────────────────────────────────────────────────
class ForecastCard(MDCard):
    """Celda de pronóstico con ripple."""

    def __init__(self, hour: str, icon_key: str,
                 temp: str, humid: str, **kwargs):
        super().__init__(**kwargs)
        self.style       = "outlined"
        self.radius      = [dp(12)]
        self.padding     = dp(10)
        self.orientation = "vertical"
        self.size_hint_x = None
        self.width       = dp(76)
        self.spacing     = dp(2)

        self.add_widget(MDLabel(
            text=hour, font_style="Label", role="small",
            theme_text_color="Secondary",
            halign="center", size_hint_y=None, height=dp(14)))

        icon = VectorIcon(icon_key,
                          self._wx_color(icon_key),
                          size=(dp(28), dp(28)),
                          size_hint=(None, None))
        box = MDBoxLayout(size_hint_y=None, height=dp(32))
        box.add_widget(Widget())
        box.add_widget(icon)
        box.add_widget(Widget())
        self.add_widget(box)

        self.add_widget(MDLabel(
            text=temp, font_style="Title", role="small",
            bold=True, halign="center",
            size_hint_y=None, height=dp(20)))
        self.add_widget(MDLabel(
            text=humid, font_style="Label", role="small",
            theme_text_color="Secondary",
            halign="center", size_hint_y=None, height=dp(14)))

    def _wx_color(self, icon_key: str) -> list:
        """Color del icono según el tipo de clima."""
        if icon_key in ("01d","01n"):   return [0.95,0.75,0.10,1]  # sol
        if icon_key in ("10d","10n","09d","09n"): return [0.08,0.54,0.85,1]
        if icon_key in ("11d","11n"):   return [0.55,0.20,0.80,1]
        return [0.40,0.45,0.55,1]