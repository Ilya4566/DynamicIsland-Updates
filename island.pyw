# -*- coding: utf-8 -*-
"""Dynamic Island v0.2.5 — пружинная анимация под частоту монитора, капля, живой спектр, новая погода и поиск."""
import re, sys, os, math, time, json, ctypes, traceback, subprocess, datetime, calendar as _calendar, random, threading
import psutil
from PyQt6.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon,
    QTextEdit, QFileDialog, QFileIconProvider, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QLineEdit, QComboBox, QSlider, QPushButton,
    QStackedWidget, QScrollArea, QDialog, QColorDialog, QFrame, QGridLayout, QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView, QProgressBar)
from PyQt6.QtCore import (Qt, QRectF, QPointF, QPropertyAnimation, QEasingCurve,
    QTimer, QSettings, pyqtProperty, QObject, pyqtSignal, QFileInfo, QPoint, QSize, QMimeData, QUrl)
from PyQt6.QtGui import (QPainter, QColor, QPainterPath, QLinearGradient,
    QRadialGradient, QConicalGradient, QPen, QBrush, QFont, QFontMetrics,
    QIcon, QPixmap, QImage, QGuiApplication, QCursor, QDrag, QTransform, QPolygonF)

from update_client import UpdateManager, CURRENT_VERSION

from core import (LOG_PATH, log_error, HAS_PYCAW, HAS_WINRT, user32, dwmapi,
    HWND_TOPMOST, SWP_FLAGS, M, TOP, ACCENT, VIOLET, MUSIC_COLOR, TOOL_BG,
    WEATHER_COLOR, font, rgba, fmt_mmss, get_volume, set_volume,
    get_app_name, no_app_window_open, autostart_enabled, set_autostart,
    MediaBridge, WeatherWorker, ClipboardMonitor, NotesStore, RemindersStore,
    is_window_overlapping, AudioLevels, SysNotifyListener, GpuMonitor, DownloadWatcher, ShelfStore, SHELF_MAX,
    PrivacyWatcher, DeviceWatcher, MESSENGERS, MixerWatcher, InputStateWatcher, search_places)


# ═══════════════ Иконки (сетка 24x24) ═══════════════
def _pts(*a): return [QPointF(x, y) for x, y in a]
def _ln(p, *a):
    for i in range(0, len(a), 4): p.drawLine(QPointF(a[i], a[i+1]), QPointF(a[i+2], a[i+3]))
def _rr(p, x, y, w, h, r=2.5): p.drawRoundedRect(QRectF(x, y, w, h), r, r)
def _ci(p, x, y, r): p.drawEllipse(QPointF(x, y), r, r)
def _ic_home(p): p.drawPolyline(_pts((3,11),(12,3),(21,11))); p.drawPolyline(_pts((5,9.5),(5,20),(19,20),(19,9.5))); p.drawPolyline(_pts((10,20),(10,14),(14,14),(14,20)))
def _ic_clip(p): _rr(p,6,4,12,17); _rr(p,9,2,6,4,1.5); _ln(p,9,11,15,11,9,15,13,15)
def _ic_timer(p): _ci(p,12,13,8); _ln(p,12,13,12,8,9,2.5,15,2.5)
def _ic_sun(p):
    import math as m
    _ci(p,12,12,4)
    for i in range(8):
        a = i*m.pi/4; p.drawLine(QPointF(12+7*m.cos(a), 12+7*m.sin(a)), QPointF(12+9.5*m.cos(a), 12+9.5*m.sin(a)))
def _ic_cal(p): _rr(p,3,5,18,16,3); _ln(p,3,10,21,10,8,3,8,7,16,3,16,7)
def _ic_note(p): _rr(p,5,3,14,18); _ln(p,8,9,16,9,8,13,16,13,8,17,12,17)
def _ic_sys(p): _ln(p,4,7,20,7,4,17,20,17); p.setBrush(QColor(8,8,10)); _ci(p,9,7,2.4); _ci(p,15,17,2.4)
def _ic_gear(p):
    import math as m
    _ci(p,12,12,3.2)
    for i in range(8):
        a = i*m.pi/4; p.drawLine(QPointF(12+6.5*m.cos(a), 12+6.5*m.sin(a)), QPointF(12+9*m.cos(a), 12+9*m.sin(a)))
    _ci(p,12,12,6.5)
def _ic_area(p):
    for pts in (((3,8),(3,3),(8,3)),((16,3),(21,3),(21,8)),((21,16),(21,21),(16,21)),((8,21),(3,21),(3,16))): p.drawPolyline(_pts(*pts))
def _ic_screen(p): _rr(p,3,4,18,12); _ln(p,8,20,16,20,12,16,12,20)
def _ic_pip(p): _ln(p,5,19,14,10,13,5,19,11,15,3,21,9)
def _ic_erase(p): p.drawPolygon(_pts((4,16),(12,6),(20,12),(14,20),(7,20))); _ln(p,9,11,15,16)
def _ic_chart(p): _ln(p,6,20,6,12,12,20,12,5,18,20,18,15)
def _ic_lock(p): _rr(p,5,11,14,10); p.drawArc(QRectF(8,4,8,10), 0, 180*16)
def _ic_calc(p): _rr(p,5,3,14,18); _rr(p,8,6,8,3,1); _ln(p,9,13,9.1,13,15,13,15.1,13,9,17,9.1,17,15,17,15.1,17)
def _ic_cmd(p): p.drawPolyline(_pts((5,8),(10,12),(5,16))); _ln(p,12,17,19,17)
def _ic_wifi(p):
    for r in (4, 8, 12): p.drawArc(QRectF(12-r, 19-r, 2*r, 2*r), 45*16, 90*16)
    _ci(p,12,19,0.8)
def _ic_bt(p): p.drawPolyline(_pts((7,8),(17,16),(12,21),(12,3),(17,8),(7,16)))
def _ic_moon(p):
    a = QPainterPath(); a.addEllipse(QPointF(12,12), 8, 8); b = QPainterPath(); b.addEllipse(QPointF(16,9), 7, 7); p.drawPath(a.subtracted(b))
def _ic_power(p): p.drawArc(QRectF(5,5,14,14), 120*16, 300*16); _ln(p,12,3,12,12)
def _ic_restart(p): p.drawArc(QRectF(5,5,14,14), 100*16, 280*16); p.drawPolyline(_pts((12,2),(15.5,5),(12,8)))
def _ic_shield(p): p.drawPolygon(_pts((12,3),(20,6),(20,12),(12,21),(4,12),(4,6)))
def _ic_theme(p): _ci(p,12,12,8); p.setBrush(p.pen().color()); p.drawPie(QRectF(4,4,16,16), 90*16, 180*16)
def _ic_search(p): _ci(p,11,11,6); _ln(p,16,16,20,20)
def _ic_play(p): p.drawPolygon(_pts((8,5),(19,12),(8,19)))
def _ic_pause(p): _rr(p,7,5,3.5,14,1); _rr(p,13.5,5,3.5,14,1)
def _ic_prev(p): _rr(p,6,6,2,12,1); p.drawPolygon(_pts((18,6),(18,18),(9,12)))
def _ic_next(p): _rr(p,16,6,2,12,1); p.drawPolygon(_pts((6,6),(6,18),(15,12)))
def _ic_vol(p): p.drawPolygon(_pts((4,9),(8,9),(13,5),(13,19),(8,15),(4,15))); p.drawArc(QRectF(10,8,8,8), -50*16, 100*16); p.drawArc(QRectF(8,4,12,16), -50*16, 100*16)
def _ic_text(p): _ln(p,5,5,19,5,12,5,12,19,9,19,15,19)
def _ic_qr(p): _rr(p,3,3,7,7,1.5); _rr(p,14,3,7,7,1.5); _rr(p,3,14,7,7,1.5); _ln(p,14,14,14.1,14,18,14,21,14,14,18,14,21,18,18,21,21)
def _ic_rec(p): _rr(p,3,6,12,12,3); p.drawPolygon(_pts((15,10),(21,7),(21,17),(15,14)))
def _ic_shelf(p): _ln(p,3,18,21,18,6,21,6,18,18,21,18,18); _rr(p,5,9,5,9,1); _rr(p,12,5,7,13,1)
def _ic_ai(p):
    _rr(p,4,7,16,13,3); _ln(p,4,12,20,12)
    _ci(p,9,15,1.3); _ci(p,15,15,1.3); _ci(p,9,9.5,1.3); _ci(p,15,9.5,1.3)
    _ln(p,12,7,12,3); _ci(p,12,2.5,1.3)

def _ic_bell(p): p.drawArc(QRectF(6, 4, 12, 12), 0, 180 * 16); _ln(p,6,10,6,16, 18,10,18,16, 4,17,20,17); _ci(p,12,20,1.3)
def _ic_grid(p): _rr(p,4,4,7,7,2); _rr(p,13,4,7,7,2); _rr(p,4,13,7,7,2); _rr(p,13,13,7,7,2)
def _ic_down(p): _ln(p,12,4,12,15, 7,11,12,16, 12,16,17,11, 5,20,19,20)
def _ic_wave(p): _ln(p,6,9,6,15, 10,5,10,19, 14,8,14,16, 18,10,18,14)
def _ic_pulse(p): p.drawPolyline(_pts((3,12),(8,12),(10,7),(14,17),(16,12),(21,12)))
def _ic_mixer(p): _ln(p,6,4,6,20, 12,4,12,20, 18,4,18,20); _rr(p,4,14,4,4,1); _rr(p,10,7,4,4,1); _rr(p,16,11,4,4,1)
_ICONS = {n[4:]: f for n, f in list(globals().items()) if n.startswith("_ic_")}
_FILLED = {"play", "pause", "prev", "next"}

def draw_icon(p, name, r, col=None, w=1.7):
    f = _ICONS.get(name)
    if not f: return
    k = min(r.width(), r.height())/24.0; col = col or QColor(255, 255, 255, 235)
    p.save(); p.translate(r.center().x()-12*k, r.center().y()-12*k); p.scale(k, k)
    p.setPen(Qt.PenStyle.NoPen if name in _FILLED else QPen(col, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(col if name in _FILLED else Qt.BrushStyle.NoBrush); f(p); p.restore()


TAB_ICON = {"home": "home", "timer": "timer", "weather": "sun", "calendar": "cal",
            "clipboard": "clip", "notes": "note", "shelf": "shelf", "mixer": "mixer", "ai": "ai", "system": "sys"}

WMO_CODES = {0:("Ясно","☀"),1:("Преим. ясно","🌤"),2:("Переменная обл.","⛅"),3:("Пасмурно","☁"),
    45:("Туман","🌫"),48:("Изморозь","🌫"),51:("Морось","🌦"),53:("Морось","🌦"),
    55:("Морось","🌦"),61:("Дождь","🌧"),63:("Дождь","🌧"),65:("Сильный дождь","🌧"),
    71:("Снег","🌨"),73:("Снег","🌨"),75:("Сильный снег","🌨"),77:("Снежные зёрна","🌨"),
    80:("Ливень","🌧"),81:("Ливень","🌧"),82:("Сильный ливень","🌧"),85:("Снегопад","🌨"),
    86:("Снегопад","🌨"),95:("Гроза","⛈"),96:("Гроза с градом","⛈"),99:("Гроза с градом","⛈")}

WMO_CODES.update({56: ("Изморось", "🌧"), 57: ("Изморось", "🌧"), 66: ("Ледяной дождь", "🌧"), 67: ("Ледяной дождь", "🌧")})

MONTH_NAMES = ["Январь","Февраль","Март","Апрель","Май","Июнь",
               "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
WEEK_DAYS = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]

TABS = [("🏠","home","Home"),("⏱","timer","Таймер"),("☁","weather","Погода"),
        ("📅","calendar","Календарь"),("📋","clipboard","Буфер"),
        ("📝","notes","Заметки"),("🗄","shelf","Полка"),("🎚","mixer","Звук"),("🤖","ai","ИИ"),("⚙","system","Система")]


IOS_GREEN = QColor(48, 209, 88); IOS_ORANGE = QColor(255, 159, 10); IOS_RED = QColor(255, 69, 58); IOS_BLUE = QColor(10, 132, 255)
IOS_GRAY = QColor(58, 58, 60); IOS_GRAYT = QColor(142, 142, 147)

GARLAND_COLORS = (QColor(255, 70, 80), QColor(255, 200, 70), QColor(80, 220, 120), QColor(90, 170, 255), QColor(255, 130, 220))

THEME_PRESETS = [("Океан", (0, 205, 255), (150, 110, 255), (255, 100, 150)), ("Закат", (255, 140, 90), (190, 70, 120), (255, 190, 90)),
                 ("Мята", (60, 220, 170), (60, 150, 255), (120, 255, 200)), ("Роза", (255, 100, 170), (170, 100, 255), (255, 140, 200)),
                 ("Лайм", (170, 230, 60), (40, 200, 150), (210, 255, 100)), ("Моно", (235, 235, 235), (150, 150, 165), (255, 255, 255))]

THEME_KEYS = (("col_accent", ACCENT, (0, 205, 255)), ("col_violet", VIOLET, (150, 110, 255)), ("col_music", MUSIC_COLOR, (255, 100, 150)))
def apply_theme(st):
    """Цвета темы меняются «на месте» (setRgb), поэтому ACCENT/VIOLET/MUSIC_COLOR обновляются во всём коде сразу."""
    for key, col, d in THEME_KEYS:
        try:
            v = str(st.value(key, "") or ""); c = QColor(v) if v else QColor(*d)
            if not c.isValid(): c = QColor(*d)
            col.setRgb(c.red(), c.green(), c.blue())
        except Exception: pass


class CachedSettings:
    """Обёртка над QSettings: значения кэшируются, кэш сбрасывается при setValue.
    Раньше каждый кадр отрисовки десятки раз лез в реестр — это одна из причин рывков."""
    def __init__(self, qs):
        self._qs = qs; self._c = {}; self._lock = threading.Lock()
    def value(self, key, default=None, type=None):
        k = (key, repr(default), type)
        with self._lock:
            if k in self._c: return self._c[k]
        v = self._qs.value(key, default) if type is None else self._qs.value(key, default, type=type)
        with self._lock: self._c[k] = v
        return v
    def setValue(self, key, value):
        self._qs.setValue(key, value)
        with self._lock: self._c = {k: v for k, v in self._c.items() if k[0] != key}
    def remove(self, key):
        self._qs.remove(key)
        with self._lock: self._c = {k: v for k, v in self._c.items() if k[0] != key}
    def __getattr__(self, name): return getattr(self._qs, name)


def _bottom_wave(path, w, h, rb, wave):
    if not wave or w - 2 * rb < 8: path.lineTo(w - rb, h); return
    n = len(wave); span = w - 2 * rb
    pts = [QPointF(rb + span * i / (n - 1), h + wave[i]) for i in range(n)]
    path.lineTo(pts[0])
    for i in range(1, n): path.quadTo(pts[i - 1], QPointF((pts[i - 1].x() + pts[i].x()) / 2, (pts[i - 1].y() + pts[i].y()) / 2))
    path.lineTo(pts[-1])


def float_path(w, h, r, wave=None):
    """Свободно «плавающая» пилюля (у боковых краёв / при перетаскивании), низ может колыхаться от звука."""
    path = QPainterPath(); r = max(1.0, min(r, w / 2.0, h / 2.0))
    path.moveTo(r, 0); path.lineTo(w - r, 0); path.quadTo(w, 0, w, r); path.lineTo(w, h - r); path.quadTo(w, h, w - r, h)
    if wave and w - 2 * r > 8:
        n = len(wave); span = w - 2 * r
        pts = [QPointF(r + span * i / (n - 1), h + wave[i]) for i in range(n)][::-1]
        path.lineTo(pts[0])
        for i in range(1, n): path.quadTo(pts[i - 1], QPointF((pts[i - 1].x() + pts[i].x()) / 2, (pts[i - 1].y() + pts[i].y()) / 2))
        path.lineTo(pts[-1])
    else: path.lineTo(r, h)
    path.quadTo(0, h, 0, h - r); path.lineTo(0, r); path.quadTo(0, 0, r, 0); path.closeSubpath()
    return path


def island_path(w, h, rb=18.0, fl=10.0, drop=0.0, wave=None):
    """Форма острова, «вросшая» в верхний край экрана: плоский верх, вогнутые «ушки» (как у выреза), мягкий низ.
    drop 0..1 превращает форму в каплю: узкая шейка у края и округлое тело. Контур не замкнут — обводка не рисует верх."""
    path = QPainterPath()
    if w < 1.0 or h < 1.0: return path
    cx = w / 2.0
    drop = max(0.0, min(1.0, drop))
    nw = w - (w - min(w, 12.0 + w * 0.15)) * drop
    lx = cx - nw / 2.0; rx = cx + nw / 2.0
    rb = max(1.0, min(rb, w / 2.0, h / 2.0))
    fl = max(0.0, min(fl, h * 0.45))
    yb = h - rb; y0 = min(fl, yb); L = max(0.0, yb - y0)
    path.moveTo(lx - fl, 0.0)
    path.quadTo(lx, 0.0, lx, y0)
    path.cubicTo(lx, y0 + L * 0.7, 0.0, y0 + L * 0.5, 0.0, yb)
    path.quadTo(0.0, h, rb, h)
    _bottom_wave(path, w, h, rb, wave)
    path.quadTo(w, h, w, yb)
    path.cubicTo(w, y0 + L * 0.5, rx, y0 + L * 0.7, rx, y0)
    path.quadTo(rx, 0.0, rx + fl, 0.0)
    return path


def living_path(iw, ih, expand=0.0, wave_phase=0.0, amp=0.0, music=0.0):
    r_top = 6
    r_bot = min(ih/2, 20) if expand < 0.05 else 8
    path = QPainterPath(); path.moveTo(r_top, 0); path.lineTo(iw - r_top, 0)
    path.quadTo(iw, 0, iw, r_top)
    if amp < 0.5 and music > 0.05:
        by = ih - 4.0; span = max(1.0, iw - 2*r_bot); ph = time.monotonic() * 4.5
        path.lineTo(iw, ih - r_bot); path.quadTo(iw, by, iw - r_bot, by)
        x = iw - r_bot
        while x > r_bot:
            env = math.sin(math.pi * (x - r_bot) / span) ** 0.7
            y = by + music * env * (0.65*math.sin(ph + x*0.085) + 0.35*math.sin(ph*1.7 - x*0.17))
            path.lineTo(x, y); x -= 3
        path.lineTo(r_bot, by); path.quadTo(0, by, 0, ih - r_bot)
    elif amp < 0.5:
        path.lineTo(iw, ih - r_bot); path.quadTo(iw, ih, iw - r_bot, ih)
        path.lineTo(r_bot, ih); path.quadTo(0, ih, 0, ih - r_bot)
    else:
        path.lineTo(iw, ih - 14 - amp); n_waves = 6; seg_w = iw / n_waves; base_y = ih - 8
        for i in range(n_waves):
            ctrl_x = iw - (i + 0.5) * seg_w; end_x = iw - (i + 1) * seg_w
            ctrl_y = base_y + amp * math.sin(wave_phase + i * 1.7)
            end_y = base_y + amp * 0.5 * math.sin(wave_phase + (i + 0.5) * 1.7)
            path.quadTo(ctrl_x, ctrl_y, end_x, end_y)
        path.lineTo(0, r_top)
    path.quadTo(0, 0, r_top, 0); path.closeSubpath(); return path



# ═══════════════ Системные хелперы ═══════════════
CREATE_NO_WINDOW = 0x08000000
DOCK_MAX = 10   # сколько значков помещается в нижнюю панель
def _run(args, timeout=25):
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="oem", errors="replace", timeout=timeout, creationflags=CREATE_NO_WINDOW)
        return r.stdout or ""
    except Exception as e: log_error(f"run {args[:2]}: {e}"); return ""
def _netsh(*a): return _run(["netsh", *a])
def _ps(cmd, timeout=25):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, creationflags=CREATE_NO_WINDOW)
        return (r.stdout or "").strip()
    except Exception as e: log_error(f"ps: {e}"); return ""

_RADIO_PS = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]
$m=([System.WindowsRuntimeSystemExtensions].GetMethods()|?{$_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
function Aw($t,$r){$x=$m.MakeGenericMethod($r).Invoke($null,@($t));$x.Wait(-1)|Out-Null;$x.Result}
[void](Aw ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]))
$rs=Aw ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$r=$rs|?{$_.Kind -eq '@KIND@'}|select -First 1
if(-not $r){'none';exit}
@ACT@
"""
def radio_state(kind):
    o = _ps(_RADIO_PS.replace("@KIND@", kind).replace("@ACT@", "$r.State")).strip().lower()
    return "on" if o.endswith("on") else ("off" if o.endswith("off") else "unknown")
def radio_toggle(kind):
    act = "if($r.State -eq 'On'){$s='Off'}else{$s='On'};[void](Aw ($r.SetStateAsync($s)) ([Windows.Devices.Radios.RadioAccessStatus]));$s"
    _ps(_RADIO_PS.replace("@KIND@", kind).replace("@ACT@", act))

RU2EN = dict(zip("йцукенгшщзхъфывапролджэячсмитьбю", "qwertyuiop[]asdfghjkl;'zxcvbnm,."))
RU2EN.update({"х": "[", "ъ": "]", "ж": ";", "э": "'", "б": ",", "ю": "."})
BUILTIN_APPS = [("Калькулятор", "calc"), ("Блокнот", "notepad"), ("Диспетчер задач", "taskmgr"), ("Проводник", "explorer"),
    ("Командная строка", "cmd"), ("Paint", "mspaint"), ("Панель управления", "control"), ("Параметры Windows", "ms-settings:")]

class ExtBridge(QObject):
    """Глобальные хоткеи + пинг из фоновых потоков в GUI."""
    fired = pyqtSignal(str); ping = pyqtSignal()
    DEFAULTS = (("toggle", "Ctrl+Alt+I"), ("music", "Ctrl+Alt+M"), ("shot", "Ctrl+Alt+S"), ("settings", "Ctrl+Alt+T"))
    def __init__(self, settings):
        super().__init__(); self.settings = settings; self._reload = True; self._run = True
        threading.Thread(target=self._loop, daemon=True).start()
    def reload(self): self._reload = True
    @staticmethod
    def _parse(s):
        mods = 0; key = None
        for part in [x.strip().lower() for x in str(s).split("+")]:
            if part in ("ctrl", "control"): mods |= 2
            elif part == "alt": mods |= 1
            elif part == "shift": mods |= 4
            elif part in ("win", "meta"): mods |= 8
            elif len(part) == 1: key = ord(part.upper())
            elif part.startswith("f") and part[1:].isdigit(): key = 0x6F + int(part[1:])
        return (mods | 0x4000, key) if (key and mods) else None
    def _loop(self):
        import ctypes.wintypes as wt
        u = ctypes.windll.user32; reg = {}; msg = wt.MSG()
        while self._run:
            if self._reload:
                self._reload = False
                for i in list(reg): u.UnregisterHotKey(None, i)
                reg = {}
                for n, (k, d) in enumerate(self.DEFAULTS):
                    try: pk = self._parse(self.settings.value(f"hk_{k}", d) or d)
                    except Exception: pk = None
                    if pk and u.RegisterHotKey(None, 100 + n, pk[0], pk[1]): reg[100 + n] = k
                    elif pk: log_error(f"hotkey {k} занят")
            while u.PeekMessageW(ctypes.byref(msg), None, 0x312, 0x312, 1):
                k = reg.get(msg.wParam)
                if k: self.fired.emit(k)
            time.sleep(0.05)


# ═══════════════ Кнопки главного меню ═══════════════
# id: (имя иконки из draw_icon или None, emoji, подпись)
TOOL_CATALOG = {
    "area": ("area", "▭", "Область"), "screen": ("screen", "🖥", "Весь экран"), "text": ("text", "🔤", "Текст с экрана"),
    "qr": ("qr", "▦", "QR-код"), "pip": ("pip", "💧", "Пипетка"), "erase": ("erase", "🧹", "Чистый текст"),
    "rec": ("rec", "🔴", "Запись экрана"), "ai": ("search", "✨", "Открыть ИИ"),
    "calc": (None, "🧮", "Калькулятор"), "taskmgr": (None, "📈", "Диспетчер задач"), "explorer": (None, "📁", "Проводник"),
    "notepad": (None, "📝", "Блокнот"), "cmd": (None, "⌨", "Терминал"), "paint": (None, "🎨", "Paint"),
    "lock": ("lock", "🔒", "Блокировка"), "mute": ("vol", "🔇", "Без звука"), "settings": ("gear", "⚙", "Настройки"),
}
DEFAULT_TOOLS = ["area", "screen", "text", "qr", "pip", "erase", "rec", "ai"]
MAX_TOOLS = 8

def load_tools(settings):
    try: raw = str(settings.value("tools_layout", "") or "")
    except Exception: raw = ""
    ids = [x for x in raw.split(",") if x in TOOL_CATALOG]
    return list(dict.fromkeys(ids))[:MAX_TOOLS] if raw else list(DEFAULT_TOOLS)

class DropList(QListWidget):
    changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop); self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); self.setSpacing(3); self.setMinimumWidth(210)
        self.setStyleSheet("QListWidget{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);border-radius:14px;padding:6px;color:white;font-size:13px;outline:none}"
            "QListWidget::item{background:rgba(255,255,255,0.07);border-radius:10px;padding:10px 12px}"
            "QListWidget::item:hover{background:rgba(0,205,255,0.18)}QListWidget::item:selected{background:rgba(0,205,255,0.34);color:white}")
    def startDrag(self, actions):
        super().startDrag(actions); self.changed.emit()
    def ids(self): return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]

class GridPreview(QWidget):
    def __init__(self):
        super().__init__(); self.ids = []; self.setFixedSize(230, 330)
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        bw, bh, gap = 108, 74, 6
        for i in range(MAX_TOOLS):
            r = QRectF(2 + (i % 2) * (bw + gap), 2 + (i // 2) * (bh + gap), bw, bh)
            if i < len(self.ids):
                _, em, tt = TOOL_CATALOG[self.ids[i]]
                p.setPen(QPen(QColor(255, 255, 255, 40), 1)); p.setBrush(QColor(255, 255, 255, 22)); p.drawRoundedRect(r, 14, 14)
                p.setFont(QFont("Segoe UI Emoji", 15)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(QRectF(r.x(), r.y() + 8, r.width(), 28), Qt.AlignmentFlag.AlignCenter, em)
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 210))
                p.drawText(QRectF(r.x() + 4, r.y() + 38, r.width() - 8, 30), int(Qt.AlignmentFlag.AlignCenter.value | Qt.TextFlag.TextWordWrap.value), tt)
            else:
                pen = QPen(QColor(255, 255, 255, 50), 1, Qt.PenStyle.DashLine); p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(r, 14, 14)
                p.setFont(QFont("Segoe UI", 16)); p.setPen(QColor(255, 255, 255, 60)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, "+")

class ToolsEditor(QWidget):
    W, H = 760, 520
    def __init__(self, island):
        super().__init__()
        self.island = island; self.settings = island.settings; self._drag = None
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(self.W, self.H)
        lay = QVBoxLayout(self); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(10)
        top = QHBoxLayout()
        t = QLabel("Кнопки главного меню"); t.setStyleSheet("color:white;font-size:20px;font-weight:300;background:transparent;")
        x = QPushButton("✕"); x.setFixedSize(30, 30); x.clicked.connect(self.close); x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setStyleSheet("QPushButton{color:rgba(255,255,255,0.7);background:rgba(255,255,255,0.08);border:none;border-radius:15px;font-size:13px}QPushButton:hover{background:rgba(255,90,90,0.5);color:white}")
        top.addWidget(t); top.addStretch(); top.addWidget(x); lay.addLayout(top)
        s = QLabel(f"Перетащи кнопки между списками. Порядок справа = порядок в меню (по 2 в ряд, максимум {MAX_TOOLS}). Двойной клик — быстро добавить или убрать.")
        s.setWordWrap(True); s.setStyleSheet("color:rgba(255,255,255,0.55);font-size:12px;background:transparent;"); lay.addWidget(s)
        cols = QHBoxLayout(); cols.setSpacing(14)
        def col(title, w):
            v = QVBoxLayout(); l = QLabel(title); l.setStyleSheet("color:rgba(255,255,255,0.8);font-size:11px;font-weight:600;background:transparent;letter-spacing:1px;")
            v.addWidget(l); v.addWidget(w); return v
        self.avail = DropList(); self.used = DropList(); self.prev = GridPreview()
        cols.addLayout(col("ДОСТУПНЫЕ", self.avail)); cols.addLayout(col("В МЕНЮ", self.used))
        pv = QVBoxLayout(); pl = QLabel("ТАК БУДЕТ В ОСТРОВЕ"); pl.setStyleSheet("color:rgba(255,255,255,0.8);font-size:11px;font-weight:600;background:transparent;letter-spacing:1px;")
        pv.addWidget(pl); pv.addWidget(self.prev); pv.addStretch(); cols.addLayout(pv); lay.addLayout(cols, 1)
        for l_ in (self.avail, self.used):
            l_.changed.connect(self._sync)
            l_.itemDoubleClicked.connect(lambda it, src=l_: self._flip(src, it))
        bt = QHBoxLayout(); bt.addStretch()
        rb = QPushButton("По умолчанию"); db = QPushButton("Готово")
        for b, pr in ((rb, False), (db, True)):
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.setFixedHeight(36)
            b.setStyleSheet("QPushButton{color:%s;background:%s;border:none;border-radius:10px;padding:0 20px;font-size:13px;font-weight:600}QPushButton:hover{background:%s}" %
                            (("#0a0c14", "#00CDFF", "#5be0ff") if pr else ("white", "rgba(255,255,255,0.10)", "rgba(255,255,255,0.18)")))
            bt.addWidget(b)
        rb.clicked.connect(lambda: self._load(DEFAULT_TOOLS)); db.clicked.connect(self.close); lay.addLayout(bt)
        self._load(load_tools(self.settings))

    def _mk(self, tid):
        _, em, tt = TOOL_CATALOG[tid]; it = QListWidgetItem(f"{em}   {tt}"); it.setData(Qt.ItemDataRole.UserRole, tid); return it
    def _load(self, ids):
        self.avail.clear(); self.used.clear()
        for tid in ids: self.used.addItem(self._mk(tid))
        for tid in TOOL_CATALOG:
            if tid not in ids: self.avail.addItem(self._mk(tid))
        self._sync()
    def _flip(self, src, it):
        dst = self.avail if src is self.used else self.used
        tid = it.data(Qt.ItemDataRole.UserRole); src.takeItem(src.row(it)); dst.addItem(self._mk(tid)); self._sync()
    def _sync(self):
        while self.used.count() > MAX_TOOLS: self.avail.addItem(self._mk(self.used.takeItem(self.used.count() - 1).data(Qt.ItemDataRole.UserRole)))
        ids = self.used.ids(); self.settings.setValue("tools_layout", ",".join(ids) if ids else "none")
        self.prev.ids = ids; self.prev.update(); self.island.update()
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 36), 1)); p.setBrush(QColor(16, 18, 26, 250)); p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 22, 22)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() < 60: self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag is not None: self.move(e.globalPosition().toPoint() - self._drag)
    def mouseReleaseEvent(self, e): self._drag = None
    def showEvent(self, e):
        s = QApplication.primaryScreen().geometry(); self.move((s.width() - self.W) // 2, (s.height() - self.H) // 2); super().showEvent(e)

# ═══════════════ ConfirmDialog ═══════════════
class ConfirmDialog(QDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 200); self.title = title; self.message = message; self.result_ok = False
        self._btn_yes = QRectF(60, 140, 140, 40); self._btn_no = QRectF(220, 140, 140, 40)
        self.setMouseTracking(True)
    def showEvent(self, e):
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-420)//2, (s.height()-200)//2); super().showEvent(e)
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = 420, 200
        path = QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h), 16, 16)
        bg = QLinearGradient(0,0,0,h); bg.setColorAt(0, QColor(28,30,42,250)); bg.setColorAt(1, QColor(10,11,16,252))
        p.fillPath(path, bg)
        bp = QPainterPath(); bp.addRoundedRect(QRectF(0.5,0.5,w-1,h-1), 16, 16)
        p.setPen(QPen(QColor(255,255,255,40), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(bp)
        p.setPen(QColor(255,255,255,240)); p.setFont(font(16, QFont.Weight.DemiBold))
        p.drawText(QRectF(24,24,w-48,30), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, self.title)
        p.setFont(font(12)); p.setPen(QColor(255,255,255,180))
        p.drawText(QRectF(24,60,w-48,60), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap, self.message)
        mp = self.mapFromGlobal(QCursor.pos())
        for r, txt, ok in [(self._btn_yes,"Да",True),(self._btn_no,"Нет",False)]:
            hov = r.contains(QPointF(mp))
            if ok:
                g = QLinearGradient(r.topLeft(), r.bottomRight())
                g.setColorAt(0, QColor(0,205,255, 240 if hov else 200)); g.setColorAt(1, QColor(150,110,255, 240 if hov else 200))
                p.setBrush(g); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(r,10,10); p.setPen(QColor(10,12,20))
            else:
                p.setBrush(QColor(255,255,255, 30 if hov else 15)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(r,10,10); p.setPen(QColor(255,255,255,240))
            p.setFont(font(13, QFont.Weight.DemiBold)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, txt)
    def mousePressEvent(self, ev):
        pos = ev.position()
        if self._btn_yes.contains(pos): self.result_ok = True; self.accept()
        elif self._btn_no.contains(pos): self.result_ok = False; self.reject()
    def mouseMoveEvent(self, e): self.update()


# ═══════════════ AreaSelector ═══════════════
class AreaSelector(QWidget):
    finished = pyqtSignal(QPixmap)
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())
        self.start_pos = None; self.end_pos = None
    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(self.rect(), QColor(0,0,0,140))
        if self.start_pos and self.end_pos:
            r = QRectF(self.start_pos, self.end_pos).normalized()
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear); p.fillRect(r, Qt.GlobalColor.transparent)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.setPen(QPen(ACCENT, 2)); p.drawRect(r)
            p.setFont(font(11)); p.setPen(QColor(255,255,255,240))
            p.drawText(r.adjusted(6,6,-6,-6), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop, f"{int(r.width())} × {int(r.height())}")
    def mousePressEvent(self, e): self.start_pos = e.position(); self.end_pos = self.start_pos
    def mouseMoveEvent(self, e): self.end_pos = e.position(); self.update()
    def mouseReleaseEvent(self, e):
        self.end_pos = e.position(); r = QRectF(self.start_pos, self.end_pos).normalized(); self.close()
        if r.width() > 5 and r.height() > 5:
            px = QGuiApplication.primaryScreen().grabWindow(0, int(r.x()), int(r.y()), int(r.width()), int(r.height()))
            self.finished.emit(px)


# ═══════════════ LogWindow ═══════════════
class LogWindow(QWidget):
    W, H = 520, 420
    CLOSE_RECT = QRectF(474, 22, 24, 24)
    CLEAR_RECT = QRectF(24, 372, 100, 28)
    REFRESH_RECT = QRectF(132, 372, 100, 28)
    TITLE_RECT = QRectF(0, 0, 460, 60)
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.W, self.H); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._drag_pos = None; self._centered = False
        self.text = QTextEdit(self); self.text.setGeometry(24, 68, 472, 292); self.text.setReadOnly(True)
        self.text.setStyleSheet("QTextEdit{background:rgba(10,12,18,210);color:#d8e0ea;border:1px solid rgba(255,255,255,22);border-radius:10px;padding:8px;font-family:Consolas;font-size:11px}QScrollBar:vertical{background:transparent;width:8px}QScrollBar::handle:vertical{background:rgba(0,205,255,130);border-radius:4px;min-height:20px}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}")
        self._refresh()
        self._t = QTimer(self); self._t.timeout.connect(self._refresh); self._t.start(1000)
    def showEvent(self, e):
        if not self._centered:
            s = QApplication.primaryScreen().geometry()
            self.move((s.width()-self.W)//2, (s.height()-self.H)//2); self._centered = True
        self._refresh(); super().showEvent(e)
    def _refresh(self):
        try:
            c = ""
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f: c = f.read()
            if not c.strip(): c = "Журнал пуст."
            sb = self.text.verticalScrollBar(); ab = sb.value() >= sb.maximum()-8
            self.text.setPlainText(c)
            if ab: sb.setValue(sb.maximum())
        except: pass
    def _clear(self):
        try:
            with open(LOG_PATH, "w", encoding="utf-8") as f: f.write(f"[{datetime.datetime.now():%H:%M:%S}] очищено\n")
            self._refresh()
        except: pass
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.W, self.H
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(9):
            s = i*1.7; sp = QPainterPath(); sp.addRoundedRect(QRectF(10-s,14-s,w-20+2*s,h-24+2*s),18+s,18+s); p.fillPath(sp, QColor(0,0,0,10))
        path = QPainterPath(); path.addRoundedRect(QRectF(10,10,w-20,h-20),18,18)
        bg = QLinearGradient(0,10,0,h-10); bg.setColorAt(0,QColor(26,28,38,250)); bg.setColorAt(1,QColor(8,9,13,252))
        p.fillPath(path, bg)
        p.setPen(QColor(255,255,255,240)); p.setFont(font(15, QFont.Weight.DemiBold))
        p.drawText(QRectF(28,24,300,30), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, "Журнал событий")
        line = QLinearGradient(28,0,88,0); line.setColorAt(0, ACCENT); line.setColorAt(1, VIOLET)
        p.fillRect(QRectF(28,54,60,2), line)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,22)); p.drawEllipse(self.CLOSE_RECT)
        p.setPen(QPen(QColor(255,255,255,200),2))
        cx, cy = self.CLOSE_RECT.center().x(), self.CLOSE_RECT.center().y()
        p.drawLine(QPointF(cx-5,cy-5),QPointF(cx+5,cy+5)); p.drawLine(QPointF(cx+5,cy-5),QPointF(cx-5,cy+5))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,20))
        p.drawRoundedRect(self.CLEAR_RECT,10,10); p.drawRoundedRect(self.REFRESH_RECT,10,10)
        p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,220))
        p.drawText(self.CLEAR_RECT, Qt.AlignmentFlag.AlignCenter, "Очистить")
        p.drawText(self.REFRESH_RECT, Qt.AlignmentFlag.AlignCenter, "Обновить")
    def mousePressEvent(self, ev):
        pos = ev.position()
        if ev.button() == Qt.MouseButton.LeftButton:
            if self.CLOSE_RECT.contains(pos): self.close(); return
            if self.CLEAR_RECT.contains(pos): self._clear(); return
            if self.REFRESH_RECT.contains(pos): self._refresh(); return
            if self.TITLE_RECT.contains(pos): self._drag_pos = ev.globalPosition().toPoint()-self.frameGeometry().topLeft()
        super().mousePressEvent(ev)
    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            self.move(ev.globalPosition().toPoint()-self._drag_pos)
        super().mouseMoveEvent(ev)
    def mouseReleaseEvent(self, ev): self._drag_pos = None; super().mouseReleaseEvent(ev)
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape: self.close()
        super().keyPressEvent(ev)


# ═══════════════ PreviewWidget — ЖИВОЙ предпросмотр ═══════════════
class PreviewWidget(QWidget):
    """Предпросмотр: рисует настоящий остров (компакт + верх раскрытого) с живыми данными."""
    def __init__(self, island):
        super().__init__()
        self.island = island; self.settings = island.settings
        self.setFixedHeight(410); self.setStyleSheet("background: transparent;")
        self._timer = QTimer(self); self._timer.timeout.connect(self.update); self._timer.start(50)

    def paintEvent(self, _):
        isl = self.island; p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        w = self.width(); AL = Qt.AlignmentFlag
        saved = (isl._hits, isl._mouse, list(isl._dock_right_regions)); isl._hits = []; isl._mouse = None
        try:
            p.setFont(font(9, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 140))
            p.drawText(QRectF(0, 0, w, 14), AL.AlignLeft, "КОМПАКТНЫЙ ВИД")
            cw, ch = isl.CW, isl.CH
            p.save(); p.translate((w - cw) / 2, 20)
            path = living_path(cw, ch, 0.0, 0.0, 0.0, 3.4 if (isl.media.get('playing') and isl.mod_music) else 0.0); p.fillPath(path, QColor(8, 8, 10))
            p.setPen(QPen(QColor(255, 255, 255, 40), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)
            p.setClipPath(path); isl._draw_compact(p, cw, ch); p.restore()
            p.setFont(font(9, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 140))
            p.drawText(QRectF(0, 90, w, 14), AL.AlignLeft, "РАСКРЫТЫЙ ВИД")
            sc = min(1.0, w / float(isl.EW)); ph = 300
            p.save(); p.translate((w - isl.EW * sc) / 2, 110)
            p.setClipRect(QRectF(0, 0, isl.EW * sc, ph)); p.scale(sc, sc)
            ex = living_path(isl.EW, isl.EH, 1.0); p.fillPath(ex, QColor(8, 8, 10))
            p.setPen(QPen(QColor(255, 255, 255, 40), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(ex)
            isl._draw_top_nav(p, isl.EW); isl._draw_home(p); p.restore()
        except Exception as e: log_error(f"preview: {e}")
        finally: isl._hits, isl._mouse, isl._dock_right_regions = saved[0], saved[1], saved[2]


# ═══════════════ SettingsWindow ═══════════════
class SettingsWindow(QWidget):
    W, H = 920, 760
    SIDEBAR_W = 200; ITEM_H = 34; ITEM_PAD = 2
    CLOSE_RECT = QRectF(880, 16, 24, 24); TITLE_RECT = QRectF(0, 0, 800, 56)
    SECTIONS = [("gear", "Общие"), ("ai", "Персонаж"), ("cmd", "Клавиши"),
                ("sun", "Погода"), ("bell", "События"), ("clip", "Буфер"), ("grid", "Модули"), ("text", "Кнопки"), ("down", "Загрузки и полка"),
                ("theme", "Цвета и стиль"), ("pulse", "Активности и вид"), ("wave", "Анимация и звук"), ("screen", "Виджеты и положение"), ("down", "Обновления"), ("info", "О сборке") ]
    GROUP_AT = {0: "ОСНОВНОЕ", 3: "ФУНКЦИИ", 9: "ОФОРМЛЕНИЕ"}
    def _sb_layout(self):
        out = []; y = 66.0
        for i in range(len(self.SECTIONS)):
            if i in self.GROUP_AT: out.append(("g", self.GROUP_AT[i], QRectF(26, y + 8, self.SIDEBAR_W - 40, 14))); y += 28
            out.append(("i", i, QRectF(14, y, self.SIDEBAR_W - 24, self.ITEM_H))); y += self.ITEM_H + self.ITEM_PAD
        return out
    def __init__(self, island):
        super().__init__()
        self.island = island; self.settings = island.settings
        self._active = 0; self._drag_pos = None; self._centered = False
        self._preview = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.W, self.H); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.addSpacing(60)
        self.content_layout = QHBoxLayout(); self.content_layout.setContentsMargins(0,0,0,0)
        self.content_layout.addSpacing(self.SIDEBAR_W+10)
        self.stack = QStackedWidget(); self.stack.setStyleSheet("background: transparent;")
        self.content_layout.addWidget(self.stack); self.main_layout.addLayout(self.content_layout)
        self.pages = []
        factories = [self._p_general, self._p_character, self._p_hotkeys,
                     self._p_weather, self._p_events, self._p_clipboard, self._p_modules, self._p_tools, self._p_downloads,
                     self._p_colors, self._p_live, self._p_anim, self._p_widgets, self._p_updates, self._p_build_info]
        for f in factories:
            try: self.pages.append(f())
            except Exception as e:
                log_error(f"page {f.__name__}: {e}")
                fb = QWidget(); fl = QVBoxLayout(fb)
                l = QLabel("Ошибка"); l.setStyleSheet("color:#ff6464;"); fl.addWidget(l)
                self.pages.append(fb)
        for p in self.pages: self.stack.addWidget(p)
        self.stack.setCurrentIndex(0)
        self._st_timer = QTimer(self); self._st_timer.timeout.connect(self.update); self._st_timer.start(1000)

    def showEvent(self, e):
        if not self._centered:
            s = QApplication.primaryScreen().geometry()
            self.move((s.width()-self.W)//2, (s.height()-self.H)//2); self._centered = True
        super().showEvent(e)

    def _qss(self):
        a = "#%02x%02x%02x" % (ACCENT.red(), ACCENT.green(), ACCENT.blue()); chk = self._check_icon()
        t = """
            QLabel{color:#E4E7EE;background:transparent;border:none;font-size:12px}
            QCheckBox{color:#E4E7EE;spacing:12px;font-size:12px;background:transparent;border:none;padding:5px 0}
            QCheckBox::indicator{width:18px;height:18px;border-radius:5px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.28)}
            QCheckBox::indicator:hover{border:1px solid @A@}
            QCheckBox::indicator:checked{background:@A@;border:1px solid @A@;image:url(@CHK@)}
            QScrollBar:vertical{background:transparent;width:8px;margin:2px}
            QScrollBar::handle:vertical{background:rgba(255,255,255,0.18);border-radius:3px;min-height:30px}
            QScrollBar::handle:vertical:hover{background:rgba(255,255,255,0.32)}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
            QLineEdit,QComboBox{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);border-radius:8px;padding:6px 12px;color:#E4E7EE;min-height:22px;font-size:12px}
            QLineEdit:hover,QComboBox:hover{border:1px solid rgba(255,255,255,0.24)}
            QLineEdit:focus,QComboBox:focus{border:1px solid @A@}
            QComboBox::drop-down{border:none;width:26px}
            QComboBox QAbstractItemView{background:#14161d;color:#E4E7EE;border:1px solid rgba(255,255,255,0.14);selection-background-color:@A@;selection-color:#06121A;outline:none}
            QSlider{background:transparent;min-height:22px}
            QSlider::groove:horizontal{height:4px;background:rgba(255,255,255,0.14);border-radius:2px}
            QSlider::sub-page:horizontal{background:@A@;border-radius:2px}
            QSlider::handle:horizontal{background:#FFFFFF;width:14px;height:14px;margin:-5px 0;border-radius:7px;border:2px solid @A@}
            QSlider::handle:horizontal:hover{background:@A@}
            QToolTip{background:#14161d;color:#E4E7EE;border:1px solid rgba(255,255,255,0.18);padding:5px 9px;border-radius:6px}
        """
        return t.replace("@A@", a).replace("@CHK@", chk)

    def _card(self, title, subtitle, *widgets):
        """Строгий контейнер: тонкая рамка, заголовок с описанием, разделитель, затем элементы управления."""
        w = QWidget(); w.setObjectName("card")
        w.setStyleSheet("QWidget#card{background:rgba(255,255,255,0.035);border:1px solid rgba(255,255,255,0.09);border-radius:14px}")
        lay = QVBoxLayout(w); lay.setContentsMargins(22, 18, 22, 18); lay.setSpacing(12)
        if title:
            hd = QWidget(); hd.setStyleSheet("background:transparent;border:none;"); hl = QVBoxLayout(hd); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(3)
            t = QLabel(title); t.setStyleSheet("color:#FFFFFF;font-size:13px;font-weight:600;background:transparent;border:none;"); hl.addWidget(t)
            if subtitle:
                s = QLabel(subtitle); s.setWordWrap(True); s.setStyleSheet("color:rgba(255,255,255,0.52);font-size:11px;background:transparent;border:none;"); hl.addWidget(s)
            lay.addWidget(hd)
            ln = QWidget(); ln.setFixedHeight(1); ln.setStyleSheet("background:rgba(255,255,255,0.07);border:none;"); lay.addWidget(ln)
        elif subtitle:
            s = QLabel(subtitle); s.setWordWrap(True); s.setStyleSheet("color:rgba(255,255,255,0.52);font-size:11px;background:transparent;border:none;"); lay.addWidget(s)
        for wd in widgets: lay.addWidget(wd)
        return w

    def _header(self, title, subtitle=""):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w); lay.setContentsMargins(4, 14, 4, 10); lay.setSpacing(4)
        t = QLabel(title); t.setStyleSheet("color:#FFFFFF;font-size:22px;font-weight:600;background:transparent;"); lay.addWidget(t)
        if subtitle:
            s = QLabel(subtitle); s.setStyleSheet("color:rgba(255,255,255,0.50);font-size:12px;background:transparent;"); lay.addWidget(s)
        return w

    def _wrap(self, *widgets):
        page = QWidget(); page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(10)
        for w in widgets: lay.addWidget(w)
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(page)
        scroll.setStyleSheet(self._qss() + """
            QScrollArea{background:transparent;border:none}
            QScrollBar:vertical{background:transparent;width:6px}
            QScrollBar::handle:vertical{background:rgba(0,205,255,120);border-radius:3px;min-height:20px}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
        """)
        return scroll

    # ─── Страницы ───
    def _p_updates(self):
        """Центр обновлений: версия, проверка, загрузка и установка."""
        h = self._header("Обновления", "Следи за новыми версиями DynamicIsland и устанавливай их прямо отсюда")
        self.update_status = QLabel("Проверка обновлений ещё не выполнялась")
        self.update_status.setWordWrap(True)
        self.update_status.setStyleSheet("color:#DDE5F0;font-size:13px;background:transparent;padding:2px 0")
        self.update_version = QLabel(f"Установлена версия  {CURRENT_VERSION}")
        self.update_version.setStyleSheet("color:rgba(255,255,255,.55);font-size:11px;background:transparent")
        self.update_progress = QProgressBar()
        self.update_progress.setRange(0, 100); self.update_progress.setValue(0)
        self.update_progress.setTextVisible(True)
        self.update_progress.setFormat("Ожидание загрузки · %p%")
        self.update_progress.setFixedHeight(13)
        self.update_progress.setStyleSheet("QProgressBar{background:rgba(255,255,255,.08);border:0;border-radius:6px;text-align:center;color:#fff;font-size:9px}QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00A9D6,stop:1 #7B61FF);border-radius:6px}")
        self.update_detail = QLabel("Здесь будет отображаться ход проверки и загрузки.")
        self.update_detail.setStyleSheet("color:rgba(255,255,255,.48);font-size:11px;background:transparent")
        self.update_detail.setWordWrap(True)
        self.update_check_btn = QPushButton("Проверить обновления")
        self.update_check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_check_btn.setStyleSheet("QPushButton{background:#00A9D6;color:#07131A;border:0;border-radius:9px;padding:11px 16px;font-weight:600}QPushButton:hover{background:#32C8F0}QPushButton:disabled{background:rgba(255,255,255,.12);color:rgba(255,255,255,.35)}")
        self.update_install_btn = QPushButton("Скачать и установить")
        self.update_install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_install_btn.setEnabled(bool(getattr(self.island, "_update_info", None)))
        self.update_install_btn.setStyleSheet("QPushButton{background:rgba(123,97,255,.22);color:#D8D0FF;border:1px solid rgba(150,130,255,.35);border-radius:9px;padding:11px 16px;font-weight:600}QPushButton:hover{background:rgba(123,97,255,.35)}QPushButton:disabled{color:rgba(255,255,255,.3);background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.06)}")
        self.update_check_btn.clicked.connect(self.island._check_updates)
        self.update_install_btn.clicked.connect(self.island._install_update)
        actions = QHBoxLayout(); actions.setSpacing(8); actions.addWidget(self.update_check_btn); actions.addWidget(self.update_install_btn)
        action_box = QWidget(); action_box.setStyleSheet("background:transparent"); action_box.setLayout(actions)
        status_card = self._card("Состояние приложения", "Обновления проверяются через официальный канал DynamicIsland", self.update_version, self.update_status, self.update_detail, self.update_progress, action_box)
        info = QLabel("Пока идёт загрузка, не закрывай приложение. После успешной загрузки установщик заменит файлы и перезапустит DynamicIsland. Твои пользовательские настройки и заметки сохраняются отдельно от файлов программы.")
        info.setWordWrap(True); info.setStyleSheet("color:rgba(255,255,255,.48);font-size:11px;background:transparent;padding:2px")
        return self._wrap(h, status_card, self._card("Как это работает", "Проверка версии → загрузка архива → проверка пакета → установка и перезапуск", info))

    def _p_build_info(self):
        """Информация о сборке — контрольная страница для проверки фактической замены файлов."""
        h = self._header("О сборке", "Проверка установленной версии и состава DynamicIsland")
        build_id = "DI-026-NOTES-XMAS-01"
        version = QLabel(f"DynamicIsland  {CURRENT_VERSION}")
        version.setStyleSheet("color:#FFFFFF;font-size:20px;font-weight:700;background:transparent")
        marker = QLabel(f"Контрольная метка: {build_id}")
        marker.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        marker.setStyleSheet("color:#00C8F0;font-size:12px;font-weight:600;background:transparent")
        desc = QLabel("Если эта страница отображается в настройках, значит установленная копия содержит новую сборку интерфейса. Метка уникальна для этой версии и не зависит от текста в GitHub Release.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color:rgba(255,255,255,.58);font-size:11px;background:transparent")
        copy_btn = QPushButton("Копировать сведения о сборке")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("QPushButton{background:#00A9D6;color:#07131A;border:0;border-radius:9px;padding:10px 14px;font-weight:600}QPushButton:hover{background:#32C8F0}")
        details = f"DynamicIsland {CURRENT_VERSION}\n{build_id}\nФайл интерфейса: island.pyw\nМодуль ядра: core.py\nМодуль обновления: update_client.py"
        copy_btn.clicked.connect(lambda: (QApplication.clipboard().setText(details), copy_btn.setText("Сведения скопированы ✓")))
        return self._wrap(h, self._card("Установленная сборка", "Проверочная информация, встроенная непосредственно в приложение", version, marker, desc, copy_btn), self._card("Что проверить", "После установки этой версии", QLabel("1. Открой настройки.\n2. Внизу списка выбери «О сборке».\n3. Убедись, что видишь метку DI-026-NOTES-XMAS-01.\n4. Если пункта нет — приложение запущено из старой папки или обновление не заменило island.pyw.")))

    def _p_general(self):
        h = self._header("Общие", "Поведение и параметры")
        cb_auto = QCheckBox("Запускать при входе в Windows")
        cb_auto.setChecked(autostart_enabled()); cb_auto.toggled.connect(set_autostart)
        cb_desk = QCheckBox("Скрывать при открытых окнах")
        try: cb_desk.setChecked(bool(self.settings.value("desktop_only", True, type=bool)))
        except: cb_desk.setChecked(True)
        def _d(v):
            self.settings.setValue("desktop_only", bool(v)); self.island.desktop_only = bool(v)
            try: self.island._check_visibility()
            except: pass
        cb_desk.toggled.connect(_d)
        cb_autohide = QCheckBox("Авто-скрытие после неактивности")
        try: cb_autohide.setChecked(bool(self.settings.value("autohide_enabled", True, type=bool)))
        except: cb_autohide.setChecked(True)
        cb_autohide.toggled.connect(lambda v: self.settings.setValue("autohide_enabled", bool(v)))
        slider_ad = QSlider(Qt.Orientation.Horizontal); slider_ad.setRange(1, 30)
        try: slider_ad.setValue(int(self.settings.value("autohide_delay", 3)))
        except: slider_ad.setValue(3)
        lbl_ad = QLabel(f"{slider_ad.value()} сек"); lbl_ad.setStyleSheet("color:rgba(255,255,255,0.7);font-size:11px;background:transparent")
        slider_ad.valueChanged.connect(lambda v: (self.settings.setValue("autohide_delay", int(v)), lbl_ad.setText(f"{v} сек")))
        cb_reveal = QCheckBox("Показывать по наведению к верху экрана")
        try: cb_reveal.setChecked(bool(self.settings.value("reveal_enabled", True, type=bool)))
        except: cb_reveal.setChecked(True)
        cb_reveal.toggled.connect(lambda v: self.settings.setValue("reveal_enabled", bool(v)))
        slider_rz = QSlider(Qt.Orientation.Horizontal); slider_rz.setRange(5, 40)
        try: slider_rz.setValue(int(self.settings.value("reveal_height", 15)))
        except: slider_rz.setValue(15)
        lbl_rz = QLabel(f"{slider_rz.value()} px"); lbl_rz.setStyleSheet("color:rgba(255,255,255,0.7);font-size:11px;background:transparent")
        slider_rz.valueChanged.connect(lambda v: (self.settings.setValue("reveal_height", int(v)), lbl_rz.setText(f"{v} px")))
        return self._wrap(h,
            self._card("Автозапуск", "Запускать островок вместе с Windows", cb_auto),
            self._card("Видимость", "Поведение при открытых окнах", cb_desk, cb_autohide),
            self._card("Авто-скрытие", "Через сколько скрывать", slider_ad, lbl_ad),
            self._card("Наведение", "Показ при курсоре у верха экрана", cb_reveal),
            self._card("Зона наведения", "Высота активной зоны", slider_rz, lbl_rz))

    def _p_character(self):
        h = self._header("Персонаж", "Живой предпросмотр — реальные данные")
        self._preview = PreviewWidget(self.island)

        colors_w = QWidget(); colors_w.setStyleSheet("background: transparent; border: none;")
        cl = QHBoxLayout(colors_w); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(8)
        presets = [("#00CDFF","Cyan"),("#966EFF","Violet"),("#FF64AA","Pink"),("#64FF96","Green"),("#FFBE64","Orange")]
        try: cur = self.settings.value("accent", "#00CDFF")
        except: cur = "#00CDFF"
        self._color_btns = []
        for c, name in presets:
            btn = QPushButton(name); btn.setFixedHeight(34); btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("accent", c); self._apply_color_btn(btn, c == cur, c)
            btn.clicked.connect(lambda checked, cc=c: self._set_accent(cc))
            cl.addWidget(btn); self._color_btns.append(btn)
        cl.addStretch()

        sizes_w = QWidget(); sizes_w.setStyleSheet("background: transparent; border: none;")
        sl = QVBoxLayout(sizes_w); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(8)
        def make_size_row(label, key, min_v, max_v, default):
            try: cur_v = int(self.settings.value(key, default))
            except: cur_v = default
            row = QWidget(); row.setStyleSheet("background: transparent; border: none;")
            rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label); lbl.setStyleSheet("color:rgba(255,255,255,0.85);font-size:11px;background:transparent;min-width:150px")
            rl.addWidget(lbl)
            slider = QSlider(Qt.Orientation.Horizontal); slider.setRange(min_v, max_v); slider.setValue(cur_v)
            val_lbl = QLabel(f"{cur_v}"); val_lbl.setStyleSheet("color:rgba(255,255,255,0.85);font-size:11px;background:transparent;min-width:36px")
            rl.addWidget(slider, 1); rl.addWidget(val_lbl)
            def _ch(v):
                self.settings.setValue(key, int(v)); val_lbl.setText(str(int(v)))
                try: self.island.reload_dimensions()
                except: pass
            slider.valueChanged.connect(_ch)
            return row
        sl.addWidget(make_size_row("Ширина компакта", "island_cw", 180, 400, 260))
        sl.addWidget(make_size_row("Высота компакта", "island_ch", 32, 60, 40))
        sl.addWidget(make_size_row("Ширина раскрытого", "island_ew", 600, 1200, 800))
        sl.addWidget(make_size_row("Высота раскрытого", "island_eh", 400, 800, 540))

        chars_w = QWidget(); chars_w.setStyleSheet("background: transparent; border: none;")
        chl = QGridLayout(chars_w); chl.setContentsMargins(0, 0, 0, 0); chl.setSpacing(6); self._char_btns = {}
        def _pick_char(key):
            self.settings.setValue("character", key); self.island._ch_t = 0
            for k_, b_ in self._char_btns.items(): self._apply_color_btn(b_, k_ == key, "#00CDFF")
            self.island.update()
        def _pick_custom():
            fn, _ = QFileDialog.getOpenFileName(self, "Картинка персонажа", "", "Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp)")
            if fn: self.settings.setValue("char_image", fn); self.island._cimg_path = None; _pick_char("custom")
        try: cur_ch = str(self.settings.value("character", "eyes"))
        except Exception: cur_ch = "eyes"
        for k_, name_ in list(DynamicIsland.CHARACTERS) + [("custom", "🖼 Свой…")]:
            b_ = QPushButton(name_); b_.setFixedHeight(34); b_.setCursor(Qt.CursorShape.PointingHandCursor)
            self._apply_color_btn(b_, k_ == cur_ch, "#00CDFF")
            b_.clicked.connect((lambda checked=False: _pick_custom()) if k_ == "custom" else (lambda checked=False, kk=k_: _pick_char(kk)))
            chl.addWidget(b_, len(self._char_btns) // 4, len(self._char_btns) % 4); self._char_btns[k_] = b_

        apply_btn = QPushButton("✓ Применить"); apply_btn.setFixedHeight(42); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00CDFF, stop:1 #966EFF);
                color: #0a0c14; border: none; border-radius: 10px;
                font-weight: 700; font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22D8FF, stop:1 #A87EFF); }
        """)
        apply_btn.clicked.connect(self._apply_all)

        return self._wrap(h,
            self._card("Живой предпросмотр", "Обновляется автоматически с реальными данными", self._preview),
            self._card("Персонаж", "Следит за курсором, моргает, радуется, засыпает", chars_w),
            self._card("Размеры", "Изменения применяются сразу", sizes_w),
            self._card("Цвет акцента", "Используется во всём интерфейсе", colors_w),
            self._card("", "", apply_btn))

    def _apply_color_btn(self, btn, active, c):
        if active: btn.setStyleSheet(f"background:{c};color:#0a0c14;border:none;border-radius:8px;font-weight:600;font-size:11px;padding:0 12px")
        else: btn.setStyleSheet(f"background:rgba(255,255,255,8);color:{c};border:1px solid {c};border-radius:8px;font-size:11px;padding:0 12px")

    def _set_accent(self, c):
        try:
            self.settings.setValue("accent", c)
            for btn in self._color_btns: self._apply_color_btn(btn, btn.property("accent") == c, btn.property("accent"))
        except: pass

    def _apply_all(self):
        try: self.island.apply_current_settings()
        except: pass

    def _p_hotkeys(self):
        h = self._header("Клавиши", "Горячие клавиши")
        items = [("Ctrl+Alt+I","Показать/скрыть","toggle"),("Ctrl+Alt+M","Плеер","music"),
                 ("Ctrl+Alt+S","Скриншот","shot"),("Ctrl+Alt+T","Настройки","settings")]
        cards = [h]
        for hk, desc, key in items:
            w = QWidget(); w.setStyleSheet("background: transparent; border: none;")
            hl = QHBoxLayout(w); hl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(desc); lbl.setStyleSheet("color:rgba(255,255,255,0.85);font-size:12px;background:transparent")
            hl.addWidget(lbl); hl.addStretch()
            inp = QLineEdit(hk); inp.setFixedWidth(160)
            try:
                s = self.settings.value(f"hk_{key}", hk)
                if s: inp.setText(str(s))
            except: pass
            inp.editingFinished.connect(lambda i=inp, k=key: (self.settings.setValue(f"hk_{k}", i.text()), self.island._ext.reload()))
            hl.addWidget(inp); cards.append(self._card("", "", w))
        return self._wrap(*cards)

    def _p_ai(self):
        h = self._header("ИИ", "Языковые модели")
        cb = QCheckBox("Включить ИИ")
        try: cb.setChecked(bool(self.settings.value("ai_enabled", False, type=bool)))
        except: cb.setChecked(False)
        cb.toggled.connect(lambda v: self.settings.setValue("ai_enabled", bool(v)))
        key = QLineEdit(); key.setEchoMode(QLineEdit.EchoMode.Password); key.setPlaceholderText("sk-...")
        try: key.setText(str(self.settings.value("ai_key", "") or ""))
        except: pass
        key.editingFinished.connect(lambda: self.settings.setValue("ai_key", key.text()))
        combo = QComboBox(); combo.addItems(["OpenAI GPT-4","OpenAI GPT-3.5","Anthropic Claude","Локальная"])
        try: combo.setCurrentText(str(self.settings.value("ai_model","OpenAI GPT-4")))
        except: pass
        combo.currentTextChanged.connect(lambda v: self.settings.setValue("ai_model", v))
        return self._wrap(h, self._card("Активация","",cb), self._card("API Ключ","",key), self._card("Модель","",combo))

    def _p_voice(self):
        h = self._header("Голос", "Распознавание")
        cb = QCheckBox("Включить")
        try: cb.setChecked(bool(self.settings.value("voice_enabled", False, type=bool)))
        except: cb.setChecked(False)
        cb.toggled.connect(lambda v: self.settings.setValue("voice_enabled", bool(v)))
        combo = QComboBox(); combo.addItems(["Whisper Tiny","Whisper Base","Whisper Small","Whisper Medium"])
        try: combo.setCurrentText(str(self.settings.value("voice_model","Whisper Base")))
        except: pass
        combo.currentTextChanged.connect(lambda v: self.settings.setValue("voice_model", v))
        return self._wrap(h, self._card("Активация","",cb), self._card("Модель","",combo))

    @property
    def SEG_QSS(self):
        a = "#%02x%02x%02x" % (ACCENT.red(), ACCENT.green(), ACCENT.blue())
        return ("QPushButton{color:#D7DBE4;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);border-radius:8px;padding:7px 16px;font-size:12px;min-height:18px}"
                "QPushButton:hover{background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.22)}QPushButton:pressed{background:rgba(255,255,255,0.15)}"
                "QPushButton:checked{color:#06121A;background:%s;border:1px solid %s;font-weight:600}" % (a, a))

    @staticmethod
    def _check_icon():
        try:
            pth = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "di_check.png")
            pm = QPixmap(18, 18); pm.fill(Qt.GlobalColor.transparent); pp = QPainter(pm); pp.setRenderHint(QPainter.RenderHint.Antialiasing)
            pp.setPen(QPen(QColor(6, 18, 26), 2.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            pp.drawPolyline(QPolygonF([QPointF(4.6, 9.4), QPointF(7.8, 12.6), QPointF(13.6, 5.8)])); pp.end(); pm.save(pth)
            return pth.replace("\\", "/")
        except Exception: return ""

    def _seg(self, key, labels, default=0):
        w = QWidget(); w.setStyleSheet("background:transparent;border:none;"); l = QHBoxLayout(w); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)
        try: cur = int(self.settings.value(key, default))
        except Exception: cur = default
        grp = QButtonGroup(w); grp.setExclusive(True)
        for i, t in enumerate(labels):
            b = QPushButton(t); b.setCheckable(True); b.setChecked(i == cur); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setStyleSheet(self.SEG_QSS); grp.addButton(b, i); l.addWidget(b)
            b.clicked.connect(lambda _, i=i, k=key: (self.settings.setValue(k, i), self.island.update()))
        l.addStretch(); return w
    def _chk(self, label, key, default=True):
        cb = QCheckBox(label)
        try: cb.setChecked(bool(self.settings.value(key, default, type=bool)))
        except Exception: cb.setChecked(default)
        cb.toggled.connect(lambda v, k=key: (self.settings.setValue(k, bool(v)), self.island.update())); return cb

    def _weather_search_card(self):
        isl = self.island; wk = isl._weather_worker; res = []; done = [False]
        inp = QLineEdit(); inp.setPlaceholderText("Название города…")
        btn = QPushButton("Найти"); btn.setStyleSheet(self.SEG_QSS); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row = QWidget(); row.setStyleSheet("background:transparent;border:none;"); rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.addWidget(inp, 1); rl.addWidget(btn)
        combo = QComboBox(); use = QPushButton("Использовать выбранный"); use.setStyleSheet(self.SEG_QSS); use.setCursor(Qt.CursorShape.PointingHandCursor)
        st = self._lab("")
        tm = QTimer(self)
        def check():
            if not done[0]: return
            tm.stop(); combo.clear()
            for nm, cn, ad, la, lo in res: combo.addItem(", ".join([x for x in (nm, ad, cn) if x]))
            st.setText("Выбери нужный вариант и нажми «Использовать»" if res else "Ничего не найдено — проверь написание или соединение (кнопка ниже)")
        tm.timeout.connect(check)
        def find():
            q = inp.text().strip()
            if not q: return
            st.setText("Ищу…"); done[0] = False
            def work(): res[:] = search_places(q, 6); done[0] = True
            threading.Thread(target=work, daemon=True).start(); tm.start(150)
        def choose():
            i = combo.currentIndex()
            if 0 <= i < len(res):
                nm, cn, ad, la, lo = res[i]; wk.use_place(nm, la, lo); st.setText(f"✓ Выбрано: {nm}"); isl._weather_loading = True
        btn.clicked.connect(find); inp.returnPressed.connect(find); use.clicked.connect(choose)
        return self._card("Поиск города", "Если автоопределение по IP не сработало — найди и выбери свой город", row, combo, use, st)

    def _weather_diag_card(self):
        wk = self.island._weather_worker
        b = QPushButton("Проверить соединение"); b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor)
        out = QLabel(wk.diag or "Покажет, какой из сервисов недоступен (погода, резерв, поиск городов, определение места)")
        out.setWordWrap(True); out.setStyleSheet("color:rgba(255,255,255,0.75);font-size:11px;background:transparent;border:none;")
        tm = QTimer(self)
        def tick():
            out.setText(wk.diag or out.text())
            if not wk.diag_busy: tm.stop()
        tm.timeout.connect(tick)
        b.clicked.connect(lambda: (wk.diagnose(), tm.start(400)))
        return self._card("Диагностика", "Полезно на новом компьютере, если погода не загружается", b, out)

    def _p_weather(self):
        isl = self.island; ST = self.settings
        h = self._header("Погода", "Город, единицы, внешний вид и что показывать")
        live = QLabel(); live.setWordWrap(True)
        live.setStyleSheet("color:white;font-size:14px;background:rgba(0,205,255,0.10);border:1px solid rgba(0,205,255,0.25);border-radius:12px;padding:12px;")
        def upd():
            w = isl.weather
            if not w.get("ok"): live.setText(("⚠ " + str(w["error"])) if w.get("error") else "⏳ Погода загружается…"); return
            v, u = isl._wwind(w.get("wind") or 0); pv, pu = isl._wpres(w.get("pres") or 0); ic = WMO_CODES.get(w.get("code", 0), ("—", "?"))[1]
            live.setText(f"{ic}  {w.get('city', '—')} · {isl._wtemp(w.get('temp'))} · ощущается {isl._wtemp(w.get('feels'))}\nВетер {v} {u} · влажность {(w.get('hum') or 0):.0f}% · давление {pv} {pu}")
        tm = QTimer(live); tm.timeout.connect(upd); tm.start(800); upd()
        row = QWidget(); row.setStyleSheet("background:transparent;border:none;"); rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(8)
        inp = QLineEdit(); inp.setPlaceholderText("Город, например: Берлин (пусто = по IP)"); inp.setText(str(ST.value("weather_city", "") or ""))
        ab = QPushButton("Применить"); ib = QPushButton("По IP")
        for b in (ab, ib): b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor)
        def apply(): ST.setValue("weather_city", inp.text().strip()); isl._weather_refresh()
        def byip(): inp.setText(""); apply()
        inp.returnPressed.connect(apply); ab.clicked.connect(apply); ib.clicked.connect(byip)
        rl.addWidget(inp, 1); rl.addWidget(ab); rl.addWidget(ib)
        return self._wrap(h, live, self._weather_search_card(), self._weather_diag_card(), self._card("Город", "Название ищется через геокодер, после «Применить» погода обновится сразу", row),
            self._card("Температура", "", self._seg("w_temp_unit", ["°C", "°F"])),
            self._card("Скорость ветра", "", self._seg("w_wind_unit", ["км/ч", "м/с", "миль/ч"])),
            self._card("Давление", "", self._seg("w_pres_unit", ["мм рт. ст.", "гПа", "inHg"])),
            self._card("Цвет карточки", "Авто подбирает цвет под погоду и время суток", self._seg("w_theme", ["Авто", "Синий", "Закат", "Графит", "Фиолет"])),
            self._card("Частота обновления", "", self._seg("weather_interval", ["5 минут", "10 минут", "30 минут", "1 час"], 1)),
            self._card("Почасовой прогноз", "", self._chk("Показывать почасовой прогноз", "w_show_hours"), self._seg("w_hours", ["4 часа", "6 часов", "8 часов"], 2)),
            self._card("Левая карточка", "", self._chk("Ощущается как, минимум и максимум", "w_show_feels"), self._chk("Вероятность осадков", "w_show_rain")),
            self._card("Плитки", "Отключённые плитки скрываются, остальные перестраиваются",
                self._chk("💨 Ветер", "w_tile_wind"), self._chk("💧 Влажность", "w_tile_hum"), self._chk("🧭 Давление", "w_tile_pres"),
                self._chk("🌅 Солнце", "w_tile_sun"), self._chk("🌧 Осадки", "w_tile_rain"), self._chk("☀ УФ-индекс", "w_tile_uv")),
            self._card("Компактный остров", "", self._chk("Показывать погоду рядом со временем", "mod_weather"), self._chk("Добавлять название города", "w_compact_city", False)))

    def _p_anim(self):
        isl = self.island; ST = self.settings
        h = self._header("Анимация и звук", "Плавность, эффект капли и визуализация музыки")
        hz_vals = [0, 60, 75, 120, 144, 165, 200, 240]
        hz = QComboBox(); hz.addItems(["Авто — по частоте монитора"] + [f"{v} Гц" for v in hz_vals[1:]])
        try: cur = int(ST.value("anim_hz", 0))
        except Exception: cur = 0
        hz.setCurrentIndex(hz_vals.index(cur) if cur in hz_vals else 0)
        hz.currentIndexChanged.connect(lambda i: (ST.setValue("anim_hz", hz_vals[i]), isl._wake()))
        def slider(key, lo, hi, default, suffix):
            s = QSlider(Qt.Orientation.Horizontal); s.setRange(lo, hi)
            try: s.setValue(int(ST.value(key, default)))
            except Exception: s.setValue(default)
            lb = QLabel(f"{s.value()}{suffix}"); lb.setStyleSheet("color:rgba(255,255,255,0.7);font-size:11px;background:transparent")
            s.valueChanged.connect(lambda v, k=key, l=lb, sf=suffix: (ST.setValue(k, int(v)), l.setText(f"{v}{sf}"), isl._wake()))
            return s, lb
        spd, spd_l = slider("anim_speed", 50, 200, 100, " %")
        sns, sns_l = slider("eq_sens", 50, 250, 100, " %")
        note = QLabel("Настоящий спектр звука нужен пакеты numpy и soundcard (pip install numpy soundcard). Без них остров рисует спектр по реальной громкости из pycaw.")
        note.setWordWrap(True); note.setStyleSheet("color:rgba(255,255,255,0.55);font-size:11px;background:transparent;border:none;")
        return self._wrap(h,
            self._card("Частота кадров", "Во время анимации остров рисуется с этой частотой; в покое — реже, чтобы не грузить процессор", hz),
            self._card("Производительность", "Авто подбирает ровный ритм кадров; «Экономный» — меньше нагрузка на процессор и батарею; «Максимум» — всегда на полной частоте", self._seg_cb("perf_mode", ["Авто", "Экономный", "Максимум"], 0, lambda i: isl._wake())),
            self._card("Характер анимации", "Мягкая — без отскоков; упругая — «желе»; резкая — быстрые отклики", self._seg_cb("anim_style", ["Мягкая", "Упругая", "Резкая"], 0, lambda i: isl._wake()), self._chk("Синхронизировать кадры с развёрткой монитора (плавнее, меньше дрожания)", "anim_vsync")),
            self._card("Скорость анимации", "Жёсткость пружин: больше — резче, меньше — плавнее и «желейнее»", spd, spd_l),
            self._card("Эффекты", "", self._chk("Эффект капли: остров вытягивается и стягивается как жидкость", "anim_drop"),
                       self._chk("Миниатюра: при открытых окнах остров сжимается в каплю у края, а не исчезает", "anim_mini")),
            self._card("Визуализация музыки", "Стиль большого спектра в плеере", self._seg("eq_style", ["Столбики", "Зеркало", "Волна", "Точки"], 1)),
            self._card("Чувствительность спектра", "", sns, sns_l),
            self._card("Источник спектра", "", self._chk("Реальный спектр через WASAPI (применится после перезапуска)", "eq_real"), note))

    COLOR_PRESETS = THEME_PRESETS

    def _p_colors(self):
        isl = self.island; ST = self.settings
        h = self._header("Цвета и эффекты", "Цвета островка, свечение и частицы — видно сразу")
        sw = {}
        def paint_sw():
            for key, col, d in THEME_KEYS:
                sw[key].setStyleSheet(f"QPushButton{{background:rgb({col.red()},{col.green()},{col.blue()});border:2px solid rgba(255,255,255,0.35);border-radius:10px;min-width:64px;min-height:26px}}QPushButton:hover{{border:2px solid white}}")
        def set_rgb(key, rgb):
            ST.setValue(key, "#%02x%02x%02x" % tuple(rgb)); apply_theme(ST); paint_sw(); isl.update()
        grid = QWidget(); grid.setStyleSheet("background:transparent;border:none;"); gl = QGridLayout(grid); gl.setContentsMargins(0, 0, 0, 0); gl.setSpacing(8)
        for i, (nm, a, v, m) in enumerate(self.COLOR_PRESETS):
            b = QPushButton(nm); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{color:#fff;font-weight:600;font-size:12px;padding:10px 14px;border:2px solid transparent;border-radius:10px;background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgb{a},stop:1 rgb{v})}}QPushButton:hover{{border:2px solid white}}")
            b.clicked.connect(lambda _, a=a, v=v, m=m: (set_rgb("col_accent", a), set_rgb("col_violet", v), set_rgb("col_music", m)))
            gl.addWidget(b, i // 3, i % 3)
        rows = QWidget(); rows.setStyleSheet("background:transparent;border:none;"); rl = QVBoxLayout(rows); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(8)
        for (key, col, d), label in zip(THEME_KEYS, ("Основной акцент", "Дополнительный цвет", "Цвет музыки")):
            row = QWidget(); row.setStyleSheet("background:transparent;border:none;"); hl = QHBoxLayout(row); hl.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(label); b = QPushButton(); b.setCursor(Qt.CursorShape.PointingHandCursor); sw[key] = b
            def pick(_, k=key, c=col):
                got = QColorDialog.getColor(QColor(c.red(), c.green(), c.blue()), self, "Выбери цвет")
                if got.isValid(): set_rgb(k, (got.red(), got.green(), got.blue()))
            b.clicked.connect(pick); hl.addWidget(lb, 1); hl.addWidget(b); rl.addWidget(row)
        paint_sw()
        glow = QSlider(Qt.Orientation.Horizontal); glow.setRange(0, 200)
        try: glow.setValue(int(ST.value("fx_glow", 100)))
        except Exception: glow.setValue(100)
        gl_l = QLabel(f"{glow.value()} %"); gl_l.setStyleSheet("color:rgba(255,255,255,0.7);font-size:11px;background:transparent")
        glow.valueChanged.connect(lambda v: (ST.setValue("fx_glow", int(v)), gl_l.setText(f"{v} %"), isl.update()))
        rb = QPushButton("Сбросить цвета"); rb.setStyleSheet(self.SEG_QSS); rb.setCursor(Qt.CursorShape.PointingHandCursor)
        def reset():
            for key, col, d in THEME_KEYS: ST.setValue(key, "")
            apply_theme(ST); paint_sw(); isl.update()
        rb.clicked.connect(reset)
        xmas = QCheckBox("Включить новогоднее оформление")
        xmas.setChecked(bool(ST.value("xmas_theme", False, type=bool)))
        xmas.setStyleSheet("color:#E4E7EE;spacing:12px;font-size:12px;background:transparent;padding:5px 0")
        xmas.toggled.connect(isl.set_christmas_theme)
        xmas_hint = QLabel("Меняет палитру приложения, включает падающий снег, гирлянду по контуру островка и шапку на персонаже. Отключение возвращает твои прежние цвета.")
        xmas_hint.setWordWrap(True); xmas_hint.setStyleSheet("color:rgba(255,255,255,0.55);font-size:11px;background:transparent;border:none")
        return self._wrap(h, self._card("Новогодняя тема", "Полное сезонное оформление приложения", xmas, xmas_hint),
                          self._card("Стиль поверхностей", "Вид всех панелей и контейнеров острова", self._seg_cb("ui_style", ["Стекло", "Графит", "Корпоративный", "Неон", "Полночь"], 0, lambda i: isl.update())),
                          self._card("Готовые схемы", "Один клик меняет все цвета", grid), self._card("Свои цвета", "", rows, rb),
                          self._card("Свечение", "Подсветка острова под музыку и по краям", glow, gl_l),
                          self._card("Эффекты раскрытого острова", "", self._chk("Плавающие частицы на фоне", "fx_particles")))

    def _p_downloads(self):
        isl = self.island; ST = self.settings
        h = self._header("Загрузки и полка", "Остров следит за загрузками в любом браузере и хранит файлы на полке")
        cur = QLabel(); cur.setWordWrap(True); cur.setStyleSheet("color:rgba(255,255,255,0.6);font-size:11px;background:transparent;border:none;")
        def show_folder():
            c = str(ST.value("dl_folder", "") or "")
            cur.setText("Папка загрузок: " + (c if c else "определяется автоматически (системная «Загрузки»)"))
        show_folder()
        pick = QPushButton("Выбрать другую папку загрузок…"); pick.setStyleSheet(self.SEG_QSS); pick.setCursor(Qt.CursorShape.PointingHandCursor)
        def choose():
            d = QFileDialog.getExistingDirectory(self, "Папка, куда браузер сохраняет файлы", str(ST.value("dl_folder", "") or os.path.expanduser("~")))
            if d: ST.setValue("dl_folder", d); show_folder()
        pick.clicked.connect(choose)
        rst = QPushButton("Сбросить на системную"); rst.setStyleSheet(self.SEG_QSS); rst.setCursor(Qt.CursorShape.PointingHandCursor)
        rst.clicked.connect(lambda: (ST.setValue("dl_folder", ""), show_folder()))
        clr = QPushButton("Очистить полку"); clr.setStyleSheet(self.SEG_QSS); clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.clicked.connect(lambda: (isl._shelf.clear(), isl.update()))
        note = QLabel("Работает с Chrome, Edge, Brave, Opera, Yandex, Firefox и другими: остров видит временный файл загрузки. Пока файл качается, остров показывает только его.")
        note.setWordWrap(True); note.setStyleSheet("color:rgba(255,255,255,0.55);font-size:11px;background:transparent;border:none;")
        return self._wrap(h,
            self._card("Загрузки", "", self._chk("Показывать загрузки в островке (имя, размер, процент)", "dl_track"), self._chk("Показывать скорость и оставшееся время", "dl_speed"),
                       self._chk("Уведомлять, когда файл скачан", "dl_notify"), note),
            self._card("Папка загрузок", "Нужна, только если браузер сохраняет не в «Загрузки»", cur, pick, rst),
            self._card("Полка", f"Лимит — {SHELF_MAX} файлов. Перетащи файл на остров — он ляжет на полку", self._chk("Открывать полку сама, когда файл тащат к острову", "shelf_auto"), clr))

    def _lab(self, t):
        l = QLabel(t); l.setStyleSheet("color:rgba(255,255,255,0.75);font-size:12px;background:transparent;border:none;"); return l

    def _seg_cb(self, key, labels, default, cb):
        w = QWidget(); w.setStyleSheet("background:transparent;border:none;"); l = QHBoxLayout(w); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)
        try: cur = int(self.settings.value(key, default))
        except Exception: cur = default
        grp = QButtonGroup(w); grp.setExclusive(True)
        for i, t in enumerate(labels):
            b = QPushButton(t); b.setCheckable(True); b.setChecked(i == cur); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setStyleSheet(self.SEG_QSS); grp.addButton(b, i); l.addWidget(b)
            b.clicked.connect(lambda _, i=i, k=key: (self.settings.setValue(k, i), cb(i)))
        l.addStretch(); return w

    def _slider_row(self, key, lo, hi, default, suffix, cb=None):
        ST = self.settings; s = QSlider(Qt.Orientation.Horizontal); s.setRange(lo, hi)
        try: s.setValue(int(ST.value(key, default)))
        except Exception: s.setValue(default)
        lb = QLabel(f"{s.value()}{suffix}"); lb.setStyleSheet("color:rgba(255,255,255,0.7);font-size:11px;background:transparent")
        s.valueChanged.connect(lambda v, k=key, l=lb, sf=suffix: (ST.setValue(k, int(v)), l.setText(f"{v}{sf}"), cb() if cb else None, self.island.update()))
        return s, lb

    def _p_live(self):
        isl = self.island; ST = self.settings
        h = self._header("Активности и вид", "Живые активности, форма острова, тема и пульс по краям экрана")
        shape = self._seg_cb("island_shape", ["Пилюля", "Капля", "Чёрная дыра"], 0, lambda i: (isl._wake(), isl.update()))
        theme = self._seg_cb("theme_mode", ["Свои цвета", "День и ночь", "По обложке трека"], 0, lambda i: (apply_theme(ST), isl.update()))
        d_s, d_l = self._slider_row("theme_day_h", 0, 23, 7, " ч"); n_s, n_l = self._slider_row("theme_night_h", 0, 23, 20, " ч")
        def combo(key, default):
            c = QComboBox(); c.addItems([p_[0] for p_ in THEME_PRESETS])
            try: c.setCurrentIndex(max(0, min(len(THEME_PRESETS) - 1, int(ST.value(key, default)))))
            except Exception: c.setCurrentIndex(default)
            c.currentIndexChanged.connect(lambda i, k=key: ST.setValue(k, i)); return c
        return self._wrap(h,
            self._card("Форма острова", "Пилюля — вросшая в край; капля — с округлым телом; чёрная дыра — со световым кольцом", shape),
            self._card("Персонаж", "", self._chk("Эмоции: реагирует на музыку, нагрузку, уведомления, заряд и твой курсор", "ch_emotions")),
            self._card("Звук", "", self._chk("Нижний край острова колышется волной от музыки, контур — в цвет трека", "eq_edge")),
            self._card("Живые активности", "Что остров показывает, пока оно идёт или происходит",
                       self._chk("📞 Звонок с таймером (микрофон занят)", "la_call"), self._chk("⏺ Запись экрана", "la_rec"), self._chk("📷 Камера включена", "la_cam"),
                       self._chk("⚡ Зарядка и низкий заряд", "la_charge"), self._chk("🎧 Подключение наушников / смена вывода звука", "la_audio"), self._chk("📶 Wi‑Fi: подключение и отключение", "la_wifi")),
            self._card("Тема", "«День и ночь» меняет схему по времени; «По обложке» берёт цвета из играющего трека. Свои цвета — в разделе «Цвета и эффекты»", theme,
                       self._lab("Начало дня"), d_s, d_l, self._lab("Начало ночи"), n_s, n_l, self._lab("Схема днём"), combo("theme_day_p", 0), self._lab("Схема ночью"), combo("theme_night_p", 1)),
            self._card("Пульс по краям экрана", "", self._chk("Мягкая вспышка света по краям экрана при уведомлении", "fx_edge_pulse")))

    def _p_widgets(self):
        isl = self.island; ST = self.settings
        h = self._header("Виджеты и положение", "Виджеты на рабочем столе и расположение острова")
        box = QWidget(); box.setStyleSheet("background:transparent;border:none;"); lay = QVBoxLayout(box); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        info = QLabel(""); info.setStyleSheet("color:rgba(255,255,255,0.6);font-size:11px;background:transparent;border:none;")
        def rebuild():
            while lay.count():
                it = lay.takeAt(0); w_ = it.widget()
                if w_ is not None: w_.setParent(None); w_.deleteLater()
            if not isl._widgets:
                e = QLabel("Пока нет виджетов"); e.setStyleSheet("color:rgba(255,255,255,0.5);font-size:12px;background:transparent;border:none;"); lay.addWidget(e)
            for w in list(isl._widgets):
                row = QWidget(); row.setObjectName("wrow"); row.setStyleSheet("QWidget#wrow{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px}")
                hl = QHBoxLayout(row); hl.setContentsMargins(12, 8, 12, 8); hl.setSpacing(8)
                lb = QLabel(WIDGET_KINDS[w.kind][0]); lb.setStyleSheet("color:white;font-size:12px;font-weight:600;background:transparent;border:none;"); hl.addWidget(lb, 1)
                cb = QComboBox(); cb.addItems(WIDGET_THEMES); cb.setCurrentIndex(max(0, min(len(WIDGET_THEMES) - 1, w.theme))); cb.currentIndexChanged.connect(lambda i, ww=w: ww.set_theme(i)); hl.addWidget(cb)
                cbn = QPushButton("Цвет"); cbn.setStyleSheet(self.SEG_QSS); cbn.setCursor(Qt.CursorShape.PointingHandCursor); cbn.clicked.connect(lambda _, ww=w: ww._pick_color()); hl.addWidget(cbn)
                b = QPushButton("Удалить"); b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(lambda _, wid=w.wid: isl.remove_widget(wid)); hl.addWidget(b)
                lay.addWidget(row)
            info.setText(f"Виджетов: {len(isl._widgets)} из {WIDGET_MAX}")
        self._wd_rebuild = rebuild
        adds = QWidget(); adds.setStyleSheet("background:transparent;border:none;"); al = QGridLayout(adds); al.setContentsMargins(0, 0, 0, 0); al.setSpacing(6)
        for n_, (kind, (nm, _w, _h)) in enumerate(WIDGET_KINDS.items()):
            b = QPushButton("＋ " + nm); b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, k=kind: (isl.add_widget(k), rebuild())); al.addWidget(b, n_ // 4, n_ % 4)
        rebuild()
        op, op_l = self._slider_row("wd_opacity", 30, 100, 85, " %")
        edges = QWidget(); edges.setStyleSheet("background:transparent;border:none;"); el = QHBoxLayout(edges); el.setContentsMargins(0, 0, 0, 0); el.setSpacing(6)
        for nm, e_ in (("Верх", "top"), ("Низ", "bottom"), ("Слева", "left"), ("Справа", "right")):
            b = QPushButton(nm); b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(lambda _, e_=e_: isl.set_edge(e_, 0.5)); el.addWidget(b)
        el.addStretch()
        mons = QWidget(); mons.setStyleSheet("background:transparent;border:none;"); ml = QHBoxLayout(mons); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(6)
        prim = QGuiApplication.primaryScreen()
        for i_, s_ in enumerate(QGuiApplication.screens()):
            g_ = s_.geometry(); b = QPushButton(f"{i_ + 1}: {g_.width()}×{g_.height()}" + (" · основной" if s_ == prim else "")); b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, i=i_: isl.move_to_screen(i)); ml.addWidget(b)
        ml.addStretch()
        note = QLabel("Остров можно перетащить мышью: потяни его сразу после нажатия — он прилипнет к ближайшему краю экрана; если мониторов несколько — его можно перетащить и на другой. Виджеты тянутся так же, правый клик по виджету — размер и удаление.")
        note.setWordWrap(True); note.setStyleSheet("color:rgba(255,255,255,0.55);font-size:11px;background:transparent;border:none;")
        return self._wrap(h,
            self._card("Виджеты на рабочем столе", "7 видов в стиле iOS. У каждого своя тема и цвет. Лимит — 8 виджетов", adds, box, info),
            self._card("Вид виджетов", "", self._lab("Прозрачность"), op, op_l, self._chk("Магнитить к краям и друг к другу", "wd_snap")),
            self._card("Монитор", "На каком экране живёт остров", mons),
            self._card("Положение острова", "Перенести к краю экрана", edges, note))

    def _p_tools(self):
        h = self._header("Кнопки", "Правая часть главного меню")
        info = QLabel("Выбери, какие кнопки видны на главной и в каком порядке. Редактор открывается и отдельной кнопкой ▦ рядом с шестерёнкой в острове.")
        info.setWordWrap(True); info.setStyleSheet("color:rgba(255,255,255,0.7);font-size:12px;background:transparent;border:none;")
        ob = QPushButton("Открыть редактор кнопок"); rb = QPushButton("Сбросить по умолчанию")
        for b in (ob, rb): b.setStyleSheet(self.SEG_QSS); b.setCursor(Qt.CursorShape.PointingHandCursor)
        ob.clicked.connect(self.island._open_tools_editor)
        def reset():
            self.settings.setValue("tools_layout", ""); self.island.update()
            ed = getattr(self.island, "_tools_editor", None)
            if ed is not None: ed._load(DEFAULT_TOOLS)
        rb.clicked.connect(reset)
        return self._wrap(h, self._card("Редактор", "", info, ob, rb))

    def _p_events(self):
        h = self._header("События", "Уведомления")
        events = [("🎵 Новые треки","notif_music",True),("🔊 Смена громкости","notif_vol",True),
                  ("🔋 Низкий заряд","notif_battery",True),("⏱ Конец таймера","notif_timer",True),
                  ("📋 Буфер обмена","notif_clipboard",False),("💬 Системные","notif_system",False),("⌨️ Caps Lock и смена языка ввода","notif_input_state",True),
                  ("💬 Сообщения мессенджеров (Telegram, WhatsApp, Discord, VK, Teams…)","notif_msgr",True),
                  ("🔔 Уведомления всех приложений Windows","notif_msgr_all",False),("📳 Вибрация при уведомлении","notif_vibe",True),
                  ("🎨 Цвет уведомления по приложению","fx_notify_color",True),
                  ("🔔 Напоминания календаря: сигнал, вибрация и подтверждение","rem_alert",True)]
        cards = [h]; cbs = []
        for label, key, default in events:
            cb = QCheckBox(label)
            try: cb.setChecked(bool(self.settings.value(key, default, type=bool)))
            except: cb.setChecked(default)
            cb.toggled.connect(lambda v, k=key: self.settings.setValue(k, bool(v)))
            cbs.append(cb)
        cards.append(self._card("Что показывать", "Уведомления острова, мессенджеры и системные события", *cbs))
        tb = QPushButton("Показать тестовое уведомление"); tb.setStyleSheet(self.SEG_QSS); tb.setCursor(Qt.CursorShape.PointingHandCursor)
        tb.clicked.connect(lambda: self.island._show_toast("Алексей", "", "✈", app="Telegram", body="Так будут выглядеть сообщения", color=QColor(42, 171, 238)))
        cards.append(self._card("Проверка", "Мессенджеры читаются из центра уведомлений Windows — включи их показ в Параметрах Windows", tb))
        return self._wrap(*cards)

    def _p_clipboard(self):
        h = self._header("Буфер обмена", "История")
        cb = QCheckBox("Сохранять историю")
        try: cb.setChecked(bool(self.settings.value("clip_enabled", True, type=bool)))
        except: cb.setChecked(True)
        cb.toggled.connect(lambda v: self.settings.setValue("clip_enabled", bool(v)))
        slider = QSlider(Qt.Orientation.Horizontal); slider.setRange(10, 100)
        try: slider.setValue(int(self.settings.value("clip_limit", 30)))
        except: slider.setValue(30)
        slider.valueChanged.connect(lambda v: self.settings.setValue("clip_limit", int(v)))
        return self._wrap(h, self._card("История","",cb), self._card("Лимит", f"{slider.value()}", slider))

    def _p_modules(self):
        h = self._header("Модули", "Функции")
        mods = [("🎵 Музыка","mod_music",True),("☁️ Погода","mod_weather",True),
                ("⏱ Таймер","mod_timer",True),("📋 Буфер","mod_clipboard",True),
                ("📸 Скриншоты","mod_screenshot",True)]
        mods_extra = [("📊 Монитор на вкладке «Система»","sys_stats"),("   Процессор","sys_cpu"),("   Память","sys_ram"),("   Диск","sys_disk"),("   Видеокарта","sys_gpu"),("   Батарея","sys_batt"),("   Сеть, время работы и график","sys_net")]
        cards = [h]; mod_cbs = []
        for name, key, default in mods:
            cb = QCheckBox(name)
            try: cb.setChecked(bool(self.settings.value(key, default, type=bool)))
            except: cb.setChecked(default)
            def _tog(v, k=key):
                self.settings.setValue(k, bool(v))
                try: self.island.apply_modules()
                except: pass
            cb.toggled.connect(_tog); mod_cbs.append(cb)
        cards.append(self._card("Модули", "Какие функции острова включены", *mod_cbs))
        cards.append(self._card("Системный монитор", "Правый клик по нему на вкладке «Система» открывает то же меню", *[self._chk(l, k) for l, k in mods_extra]))
        cards.append(self._card("Показатели в островке", "Полоски с цифрами в свёрнутом острове. Быстро включить: правый клик по островку. FPS — частота кадров самого острова.", self._chk("Показывать вместо часов", "compact_stats", False), self._chk("   Процессор", "cs_cpu"), self._chk("   Память", "cs_ram"), self._chk("   Видеокарта", "cs_gpu"), self._chk("   FPS", "cs_fps")))
        return self._wrap(*cards)

    # ─── Отрисовка окна ───
    def paintEvent(self, _):
        try:
            p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            w, h = self.W, self.H
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(10):
                s = i*1.7; sp = QPainterPath(); sp.addRoundedRect(QRectF(10-s,14-s,w-20+2*s,h-24+2*s),20+s,20+s); p.fillPath(sp, QColor(0,0,0,10))
            path = QPainterPath(); path.addRoundedRect(QRectF(10,10,w-20,h-20),20,20)
            bg = QLinearGradient(0,10,0,h-10); bg.setColorAt(0,QColor(16,16,18,252)); bg.setColorAt(1,QColor(5,5,6,254))
            p.fillPath(path, bg)
            p.save(); p.setClipPath(path)
            g1 = QRadialGradient(QPointF(w*0.1,10), w*0.6); g1.setColorAt(0, QColor(0,205,255,10)); g1.setColorAt(1, QColor(0,205,255,0))
            p.fillRect(QRectF(10,10,w,h), g1)
            g2 = QRadialGradient(QPointF(w*0.95,h*0.95), w*0.55); g2.setColorAt(0, QColor(150,110,255,8)); g2.setColorAt(1, QColor(150,110,255,0))
            p.fillRect(QRectF(10,10,w,h), g2)
            p.restore()
            bp = QPainterPath(); bp.addRoundedRect(QRectF(10.5,10.5,w-21,h-21),20,20)
            bg2 = QLinearGradient(0,0,0,h); bg2.setColorAt(0,QColor(255,255,255,90)); bg2.setColorAt(0.5,QColor(255,255,255,20)); bg2.setColorAt(1,QColor(255,255,255,40))
            p.setPen(QPen(QBrush(bg2),1.0)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(bp)
            p.setPen(QColor(255,255,255,240)); p.setFont(font(15, QFont.Weight.DemiBold))
            p.drawText(QRectF(28,16,300,30), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, "Настройки")
            lp = self.mapFromGlobal(QCursor.pos())
            hov = self.CLOSE_RECT.contains(QPointF(lp))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,90,100,210) if hov else QColor(255,255,255,22)); p.drawEllipse(self.CLOSE_RECT)
            p.setPen(QPen(QColor(255,255,255,200),2))
            cx, cy = self.CLOSE_RECT.center().x(), self.CLOSE_RECT.center().y()
            p.drawLine(QPointF(cx-5,cy-5),QPointF(cx+5,cy+5)); p.drawLine(QPointF(cx+5,cy-5),QPointF(cx-5,cy+5))
            sep = QLinearGradient(10,0,w-10,0); sep.setColorAt(0,QColor(255,255,255,0)); sep.setColorAt(0.5,QColor(255,255,255,30)); sep.setColorAt(1,QColor(255,255,255,0))
            p.fillRect(QRectF(10,56,w-20,1), sep)
            mp = QPointF(lp); AL_ = Qt.AlignmentFlag
            for kind, v, r in self._sb_layout():
                if kind == "g":
                    p.setFont(font(8, QFont.Weight.DemiBold, spacing=1.3)); p.setPen(QColor(255, 255, 255, 95)); p.drawText(r, AL_.AlignLeft | AL_.AlignVCenter, v); continue
                icon, name = self.SECTIONS[v]; active = v == self._active; hov = r.contains(mp)
                p.setPen(Qt.PenStyle.NoPen)
                if active:
                    p.setBrush(rgba(ACCENT, 34)); p.drawRoundedRect(r, 8, 8); p.setBrush(ACCENT); p.drawRoundedRect(QRectF(r.x(), r.y() + 8, 3, r.height() - 16), 1.5, 1.5)
                elif hov: p.setBrush(QColor(255, 255, 255, 14)); p.drawRoundedRect(r, 8, 8)
                draw_icon(p, icon, QRectF(r.x() + 13, r.y() + (r.height() - 18) / 2, 18, 18), ACCENT.lighter(125) if active else QColor(255, 255, 255, 170), w=1.5)
                p.setFont(font(12, QFont.Weight.DemiBold if active else QFont.Weight.Normal)); p.setPen(QColor(255, 255, 255, 250 if active else 205))
                p.drawText(QRectF(r.x() + 44, r.y(), r.width() - 44, r.height()), AL_.AlignLeft | AL_.AlignVCenter, name)
            p.fillRect(QRectF(self.SIDEBAR_W+5,60,1,h-70), QColor(255,255,255,20))
            isl = self.island; au = getattr(isl, "_audio", None)
            mode = "реальный спектр" if (au is not None and au.is_real()) else ("по уровню звука" if au is not None else "нет данных")
            p.setFont(font(9)); p.setPen(QColor(255,255,255,120)); AL_ = Qt.AlignmentFlag.AlignLeft
            p.drawText(QRectF(20, h-86, self.SIDEBAR_W-30, 14), AL_, f"Кадры: {isl._anim_hz()} Гц")
            p.drawText(QRectF(20, h-70, self.SIDEBAR_W-30, 14), AL_, f"Звук: {mode}")
            p.setPen(QColor(255,255,255,70)); p.drawText(QRectF(20, h-52, self.SIDEBAR_W-30, 14), AL_, "Dynamic Island v43")
        except: pass

    def mousePressEvent(self, ev):
        pos = ev.position()
        if ev.button() == Qt.MouseButton.LeftButton:
            if self.CLOSE_RECT.contains(pos): self.close(); return
            for kind, v, r in self._sb_layout():
                if kind == "i" and r.contains(pos): self._switch_page(v); return
            if self.TITLE_RECT.contains(pos): self._drag_pos = ev.globalPosition().toPoint()-self.frameGeometry().topLeft()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            self.move(ev.globalPosition().toPoint()-self._drag_pos)
        else: self.update()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev): self._drag_pos = None; super().mouseReleaseEvent(ev)
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape: self.close()
        super().keyPressEvent(ev)
    def _switch_page(self, i):
        if i == self._active: return
        self._active = i; self.stack.setCurrentIndex(i); self.update()


# ═══════════════ AIWindow ═══════════════
class AIWindow(QWidget):
    """Отдельное окно с WebEngine для ИИ-чата."""
    def __init__(self, url, title="ИИ"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 700)
        self.resize(1100, 760)
        self._drag_pos = None

        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        top = QWidget()
        top.setFixedHeight(44)
        top.setStyleSheet("background: #12141c; border-bottom: 1px solid rgba(255,255,255,22);")
        tl = QHBoxLayout(top); tl.setContentsMargins(16, 0, 10, 0); tl.setSpacing(10)
        dot = QLabel("●"); dot.setStyleSheet("color: #00CDFF; font-size: 10px;")
        tl.addWidget(dot)
        lbl = QLabel(title)
        lbl.setStyleSheet("color: white; font-weight: 600; font-size: 12px; background: transparent;")
        tl.addWidget(lbl); tl.addStretch()

        def _mk_btn(text, hover_color="#ff5a64"):
            b = QPushButton(text); b.setFixedSize(30, 26); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{ background: rgba(255,255,255,18); color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: bold; }}
                QPushButton:hover {{ background: {hover_color}; }}
            """)
            return b

        btn_min = _mk_btn("—", "#4a5060"); btn_min.clicked.connect(self.showMinimized); tl.addWidget(btn_min)
        btn_close = _mk_btn("✕"); btn_close.clicked.connect(self.close); tl.addWidget(btn_close)
        layout.addWidget(top)

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEngineProfile
            from PyQt6.QtCore import QUrl
            self._profile = QWebEngineProfile(f"ai_{id(self)}", self)
            self._profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
            self._profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
            self._view = QWebEngineView(self)
            self._view.setStyleSheet("background: #0a0c14;")
            self._view.setUrl(QUrl(url))
            layout.addWidget(self._view, 1)
        except ImportError:
            err = QLabel("PyQt6-WebEngine не установлен.\n\nУстановите:\npip install PyQt6-WebEngine\n\nЗатем перезапустите приложение.")
            err.setStyleSheet("color: #ff8080; background: #0a0c14; padding: 40px; font-size: 14px; font-family: 'Segoe UI';")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(err, 1)

        self._center()

    def _center(self):
        try:
            s = QGuiApplication.primaryScreen().availableGeometry()
            self.move((s.width() - self.width()) // 2 + s.x(), (s.height() - self.height()) // 2 + s.y())
        except Exception: pass

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and ev.position().y() < 48:
            self._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(ev)
    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            self.move(ev.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(ev)
    def mouseReleaseEvent(self, ev): self._drag_pos = None; super().mouseReleaseEvent(ev)
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape: self.close(); return
        super().keyPressEvent(ev)


# ═══════════════ DynamicIsland ═══════════════
class ScreenGlow(QWidget):
    """Прозрачное окно на весь экран: короткий мягкий пульс света по краям при уведомлении (клики проходят сквозь него)."""
    DUR = 1.15
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._t0 = 0.0; self._col = QColor(0, 205, 255)
        self._timer = QTimer(self); self._timer.setTimerType(Qt.TimerType.PreciseTimer); self._timer.timeout.connect(self._tick)

    def pulse(self, color, geom=None):
        self.setGeometry(geom if geom is not None else QGuiApplication.primaryScreen().geometry())
        self._col = QColor(color.red(), color.green(), color.blue()); self._t0 = time.perf_counter()
        self.show(); self._timer.start(8)

    def _tick(self):
        if time.perf_counter() - self._t0 > self.DUR: self._timer.stop(); self.hide(); return
        self.update()

    def paintEvent(self, _):
        age = (time.perf_counter() - self._t0) / self.DUR
        if age >= 1.0: return
        a = math.sin(math.pi * age) ** 1.3; c = self._col; p = QPainter(self); w, h = self.width(), self.height(); t = 120
        for (x0, y0, x1, y1, r) in ((0, 0, 0, t, QRectF(0, 0, w, t)), (0, h, 0, h - t, QRectF(0, h - t, w, t)),
                                    (0, 0, t, 0, QRectF(0, 0, t, h)), (w, 0, w - t, 0, QRectF(w - t, 0, t, h))):
            g = QLinearGradient(x0, y0, x1, y1); g.setColorAt(0, QColor(c.red(), c.green(), c.blue(), int(125 * a))); g.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
            p.fillRect(r, g)


WIDGET_KINDS = {"clock": ("Часы", 330, 150), "weather": ("Погода", 330, 150), "music": ("Музыка", 330, 150), "notes": ("Заметки", 330, 170),
                "system": ("Система", 170, 170), "battery": ("Батарея", 170, 170), "calendar": ("Календарь", 300, 270)}
WIDGET_MAX = 8
WIDGET_THEMES = ["Стекло", "Светлый", "Градиент", "Графит", "Неон"]
WD_DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
WD_MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]

class DesktopWidget(QWidget):
    """Виджет на рабочем столе в стиле iOS: 7 видов, 5 тем оформления, свой цвет акцента.
    Лежит под окнами, тянется мышью, магнитится к краям экрана и к другим виджетам."""
    def __init__(self, island, wid, kind, x, y, scale=1.0, theme=0, color=""):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.island = island; self.wid = wid; self.kind = kind; self.scale = float(scale); self.theme = int(theme); self.color = str(color or ""); self._drag = None
        _, self.BW, self.BH = WIDGET_KINDS[kind]
        self.setGeometry(int(x), int(y), int(self.BW * self.scale) + 20, int(self.BH * self.scale) + 20)
        self._fg = QColor(255, 255, 255, 245); self._fg2 = QColor(255, 255, 255, 150); self._acc = QColor(ACCENT)
        self._timer = QTimer(self); self._timer.timeout.connect(self.update); self._timer.start(1000 if kind != "music" else 120)

    def accent(self):
        if self.color:
            c = QColor(self.color)
            if c.isValid(): return c
        return QColor(ACCENT)

    def resize_to(self, sc):
        self.scale = float(sc); self.resize(int(self.BW * self.scale) + 20, int(self.BH * self.scale) + 20); self.update()

    def set_theme(self, i): self.theme = int(i); self.update(); self.island._save_widgets()
    def set_color(self, hexs): self.color = hexs; self.update(); self.island._save_widgets()
    def _pick_color(self):
        c = QColorDialog.getColor(self.accent(), None, "Цвет виджета")
        if c.isValid(): self.set_color("#%02x%02x%02x" % (c.red(), c.green(), c.blue()))

    def _T(self, p, rect, text, px, weight=QFont.Weight.Normal, color=None, align=Qt.AlignmentFlag.AlignLeft, elide=True):
        f = font(px, weight); p.setFont(f); p.setPen(color if color is not None else self._fg)
        if elide: text = QFontMetrics(f).elidedText(str(text), Qt.TextElideMode.ElideRight, int(rect.width()))
        p.drawText(rect, align | Qt.AlignmentFlag.AlignVCenter, text)

    def _ring(self, p, c, R, w, frac, col):
        arc = QRectF(c.x() - R, c.y() - R, 2 * R, 2 * R); p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(128, 128, 128, 46) if self.theme == 1 else QColor(255, 255, 255, 30), w)); p.drawEllipse(arc)
        f = max(0.0, min(1.0, frac))
        if f > 0.004: p.setPen(QPen(col, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 90 * 16, -int(360 * 16 * min(f, 0.9999)))

    def paintEvent(self, _):
        isl = self.island; p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        k = self.scale; p.translate(10, 10); p.scale(k, k)
        try: op = int(isl.settings.value("wd_opacity", 85)) / 100.0
        except Exception: op = 0.85
        th = self.theme; acc = self.accent(); r = QRectF(0, 0, self.BW, self.BH); rad = 28.0
        self._acc = acc; self._fg = QColor(255, 255, 255, 245); self._fg2 = QColor(255, 255, 255, 150)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for w_, a_ in ((18, 4), (11, 6), (6, 9)):
            p.setPen(QPen(QColor(0, 0, 0, a_ if th != 1 else a_ - 2), w_)); p.drawRoundedRect(r.translated(0, 4), rad, rad)
        p.setPen(Qt.PenStyle.NoPen)
        if th == 1:
            self._fg = QColor(28, 28, 30, 250); self._fg2 = QColor(95, 95, 105, 220)
            bg = QLinearGradient(0, 0, 0, self.BH); bg.setColorAt(0, QColor(252, 252, 254, int(246 * max(op, 0.5)))); bg.setColorAt(1, QColor(236, 236, 242, int(246 * max(op, 0.5)))); p.setBrush(bg)
        elif th == 2:
            self._fg2 = QColor(255, 255, 255, 205)
            bg = QLinearGradient(0, 0, self.BW, self.BH); bg.setColorAt(0, acc.lighter(118)); bg.setColorAt(1, acc.darker(175)); p.setBrush(bg)
        elif th == 3: p.setBrush(QColor(32, 32, 35, 252))
        elif th == 4: p.setBrush(QColor(3, 5, 10, 248))
        else:
            bg = QLinearGradient(0, 0, 0, self.BH); bg.setColorAt(0, QColor(20, 22, 32, int(238 * op))); bg.setColorAt(1, QColor(8, 9, 14, int(246 * op))); p.setBrush(bg)
        p.drawRoundedRect(r, rad, rad)
        if th in (0, 4):
            cp = QPainterPath(); cp.addRoundedRect(r, rad, rad); p.save(); p.setClipPath(cp)
            gg = QRadialGradient(QPointF(self.BW * 0.12, 0), self.BW * 0.85); gg.setColorAt(0, rgba(acc, int(46 * op) if th == 0 else 36)); gg.setColorAt(1, rgba(acc, 0)); p.fillRect(r, gg); p.restore()
        if th == 4:
            p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(rgba(acc, 50), 5)); p.drawRoundedRect(r, rad, rad); p.setPen(QPen(rgba(acc, 235), 1.5)); p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        else: p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(0, 0, 0, 24) if th == 1 else QColor(255, 255, 255, 30), 1)); p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        try: getattr(self, "_k_" + self.kind)(p, isl)
        except Exception as e: log_error(f"widget {self.kind}: {e}")

    def _k_clock(self, p, isl):
        AL = Qt.AlignmentFlag; now = isl.now; acc = self._acc
        self._T(p, QRectF(22, 6, 210, 74), now.strftime("%H:%M"), 56, QFont.Weight.Light, elide=False)
        self._T(p, QRectF(24, 84, 200, 22), WD_DAYS[now.weekday()].capitalize(), 14, QFont.Weight.DemiBold, acc)
        self._T(p, QRectF(24, 106, 200, 20), f"{now.day} {WD_MONTHS[now.month - 1]} {now.year}", 12, QFont.Weight.Normal, self._fg2)
        c = QPointF(272, 75); R = 48.0; p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(128, 128, 128, 60) if self.theme == 1 else QColor(255, 255, 255, 36), 1.6)); p.drawEllipse(c, R, R)
        for i in range(12):
            a = math.radians(i * 30); l = 5 if i % 3 == 0 else 2.6
            p.setPen(QPen(self._fg2, 1.6 if i % 3 == 0 else 1.0)); p.drawLine(QPointF(c.x() + math.sin(a) * (R - 3), c.y() - math.cos(a) * (R - 3)), QPointF(c.x() + math.sin(a) * (R - 3 - l), c.y() - math.cos(a) * (R - 3 - l)))
        for ang, ln, wd, col in (((now.hour % 12 + now.minute / 60.0) * 30, 25, 4.0, self._fg), ((now.minute + now.second / 60.0) * 6, 37, 3.0, self._fg), (now.second * 6, 41, 1.5, acc)):
            p.save(); p.translate(c); p.rotate(ang); p.setPen(QPen(col, wd, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawLine(QPointF(0, 4), QPointF(0, -ln)); p.restore()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(acc); p.drawEllipse(c, 3.2, 3.2)

    def _k_weather(self, p, isl):
        AL = Qt.AlignmentFlag; w = isl.weather
        if not w.get("ok"): self._T(p, QRectF(0, 0, self.BW, self.BH), "Погода загружается…", 13, QFont.Weight.Normal, self._fg2, AL.AlignHCenter); return
        desc, icon = WMO_CODES.get(w.get("code", 0), ("—", "?"))
        self._T(p, QRectF(22, 14, 190, 22), "📍 " + str(w.get("city", "")), 13, QFont.Weight.DemiBold, self._fg2)
        self._T(p, QRectF(18, 36, 190, 76), isl._wtemp(w.get("temp")), 62, QFont.Weight.Light, elide=False)
        self._T(p, QRectF(22, 112, 200, 22), desc, 13, QFont.Weight.DemiBold, self._acc)
        p.setFont(font(54, family="Segoe UI Emoji")); p.setPen(self._fg); p.drawText(QRectF(216, 14, 100, 72), AL.AlignCenter, icon)
        self._T(p, QRectF(206, 98, 118, 20), f"↑ {isl._wtemp(w.get('tmax'))}   ↓ {isl._wtemp(w.get('tmin'))}", 12, QFont.Weight.DemiBold, self._fg, AL.AlignHCenter)

    def _k_system(self, p, isl):
        AL = Qt.AlignmentFlag; c = QPointF(85, 78); g = isl._gpu
        vals = (("CPU", isl.d["cpu"], self._acc), ("RAM", isl.d["mem"], IOS_BLUE if self.theme == 1 else QColor(190, 130, 255)), ("GPU", g.load if g.ok else isl.d["disk"], IOS_GREEN))
        for (nm, v, col), R in zip(vals, (62, 47, 32)): self._ring(p, c, R, 9, v / 100.0, col)
        self._T(p, QRectF(0, 138, self.BW, 14), f"CPU {vals[0][1]:.0f}  ·  RAM {vals[1][1]:.0f}  ·  {'GPU' if g.ok else 'ДИСК'} {vals[2][1]:.0f}", 9, QFont.Weight.DemiBold, self._fg2, AL.AlignHCenter)
        self._T(p, QRectF(0, 152, self.BW, 14), "нагрузка, %", 8, QFont.Weight.Normal, self._fg2, AL.AlignHCenter)

    def _k_battery(self, p, isl):
        AL = Qt.AlignmentFlag; b = isl.battery; c = QPointF(85, 78)
        if not b:
            self._T(p, QRectF(0, 52, self.BW, 50), "—", 40, QFont.Weight.Light, self._fg2, AL.AlignHCenter); self._T(p, QRectF(0, 110, self.BW, 20), "Нет батареи", 12, QFont.Weight.Normal, self._fg2, AL.AlignHCenter); return
        pct, plug = b; col = IOS_GREEN if pct > 30 else (IOS_ORANGE if pct > 15 else IOS_RED)
        self._ring(p, c, 54, 12, pct / 100.0, col)
        self._T(p, QRectF(30, 52, 110, 50), f"{pct:.0f}", 36, QFont.Weight.Light, align=AL.AlignHCenter, elide=False)
        self._T(p, QRectF(0, 140, self.BW, 18), "⚡ Заряжается" if plug else "От батареи", 11, QFont.Weight.DemiBold, col, AL.AlignHCenter)

    def _k_music(self, p, isl):
        AL = Qt.AlignmentFlag; m = isl.media; cov = QRectF(22, 22, 106, 106); cp = QPainterPath(); cp.addRoundedRect(cov, 22, 22)
        th = m.get("thumb") if m.get("active") else None
        if th is not None and not th.isNull(): p.save(); p.setClipPath(cp); p.drawPixmap(cov.toRect(), th); p.restore()
        else:
            g = QLinearGradient(cov.topLeft(), cov.bottomRight()); g.setColorAt(0, self._acc.lighter(120)); g.setColorAt(1, self._acc.darker(160)); p.setPen(Qt.PenStyle.NoPen); p.setBrush(g); p.drawPath(cp)
            self._T(p, cov, "♪", 44, QFont.Weight.Bold, QColor(255, 255, 255, 230), AL.AlignHCenter)
        if not m.get("active"):
            self._T(p, QRectF(142, 38, 172, 26), "Нет трека", 17, QFont.Weight.Bold); self._T(p, QRectF(142, 66, 172, 20), "Включи музыку — она появится здесь", 11, QFont.Weight.Normal, self._fg2); return
        self._T(p, QRectF(142, 20, 172, 24), m.get("title", ""), 16, QFont.Weight.Bold); self._T(p, QRectF(142, 44, 172, 20), m.get("artist", ""), 12, QFont.Weight.Normal, self._fg2)
        dur = max(1.0, float(m.get("duration", 1) or 1)); f = max(0.0, min(1.0, float(m.get("position", 0)) / dur))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(128, 128, 128, 60) if self.theme == 1 else QColor(255, 255, 255, 38)); p.drawRoundedRect(QRectF(142, 80, 172, 5), 2.5, 2.5)
        p.setBrush(self._acc); p.drawRoundedRect(QRectF(142, 80, max(5.0, 172 * f), 5), 2.5, 2.5)
        pos = int(m.get("position", 0)); self._T(p, QRectF(142, 88, 80, 14), f"{pos // 60}:{pos % 60:02d}", 9, QFont.Weight.Normal, self._fg2)
        d_ = isl._eq_disp
        for i in range(12):
            v = d_[min(31, i * 2)] if m.get("playing") else 0.0; h = 4 + 20 * min(1.0, v * 1.2); p.setBrush(self._acc if m.get("playing") else self._fg2)
            p.drawRoundedRect(QRectF(142 + i * 14.4, 128 - h, 8, h), 4, 4)

    def _k_calendar(self, p, isl):
        AL = Qt.AlignmentFlag; now = isl.now; today = datetime.date.today(); y0, m0 = today.year, today.month
        self._T(p, QRectF(20, 12, 200, 28), MONTH_NAMES[m0 - 1], 20, QFont.Weight.Bold, self._acc); self._T(p, QRectF(190, 12, 90, 28), str(y0), 16, QFont.Weight.Normal, self._fg2, AL.AlignRight)
        cw = (self.BW - 28) / 7.0
        for i, dn in enumerate(WEEK_DAYS): self._T(p, QRectF(14 + i * cw, 46, cw, 18), dn, 9, QFont.Weight.DemiBold, self._fg2 if i < 5 else IOS_ORANGE, AL.AlignHCenter)
        y = 68.0
        try: weeks = _calendar.Calendar(firstweekday=0).monthdayscalendar(y0, m0)
        except Exception: weeks = []
        for week in weeks:
            for i, d in enumerate(week):
                if not d: continue
                rc = QRectF(14 + i * cw, y, cw, 32); c = rc.center(); istd = d == today.day
                if istd: p.setPen(Qt.PenStyle.NoPen); p.setBrush(self._acc); p.drawEllipse(c, 13, 13)
                self._T(p, rc, str(d), 12, QFont.Weight.Bold if istd else QFont.Weight.Normal, (QColor(255, 255, 255) if self.theme != 1 else QColor(255, 255, 255)) if istd else (self._fg if i < 5 else IOS_ORANGE), AL.AlignHCenter)
                if isl._reminders.get(datetime.date(y0, m0, d).strftime("%Y-%m-%d")): p.setPen(Qt.PenStyle.NoPen); p.setBrush(IOS_ORANGE); p.drawEllipse(QPointF(c.x(), rc.bottom() - 1), 1.8, 1.8)
            y += 32.0

    def _k_notes(self, p, isl):
        AL = Qt.AlignmentFlag; notes = isl._notes.items[:3]
        self._T(p, QRectF(22, 12, 200, 24), "Заметки", 15, QFont.Weight.Bold, self._acc)
        if not notes: self._T(p, QRectF(0, 60, self.BW, 60), "Нет заметок", 13, QFont.Weight.Normal, self._fg2, AL.AlignHCenter); return
        y = 44.0
        for i, n in enumerate(notes):
            lines_ = n.get("text", "").split("\n")
            self._T(p, QRectF(22, y, self.BW - 110, 22), lines_[0], 13, QFont.Weight.DemiBold)
            self._T(p, QRectF(self.BW - 82, y, 62, 22), n.get("time", ""), 10, QFont.Weight.Normal, self._fg2, AL.AlignRight)
            if i < len(notes) - 1: p.setPen(QPen(QColor(128, 128, 128, 50), 1)); p.drawLine(QPointF(22, y + 34), QPointF(self.BW - 22, y + 34))
            y += 40.0

    def _snap(self, x, y):
        isl = self.island
        if not isl.settings.value("wd_snap", True, type=bool): return x, y
        s = isl._virt_geom(); gap = 14; R = 22
        cw = self.BW * self.scale; ch = self.BH * self.scale; cx = x + 10.0; cy = y + 10.0
        for t in (s.x() + gap, s.x() + s.width() - gap - cw, s.x() + (s.width() - cw) / 2):
            if abs(cx - t) < R: cx = t; break
        for t in (s.y() + gap, s.y() + s.height() - gap - ch, s.y() + (s.height() - ch) / 2):
            if abs(cy - t) < R: cy = t; break
        for o in isl._widgets:
            if o is self: continue
            ox, oy = o.x() + 10.0, o.y() + 10.0; ow, oh = o.width() - 20.0, o.height() - 20.0
            if abs(cx - (ox + ow + 10)) < R: cx = ox + ow + 10
            elif abs(cx + cw + 10 - ox) < R: cx = ox - 10 - cw
            elif abs(cx - ox) < R: cx = ox
            if abs(cy - oy) < R: cy = oy
            elif abs(cy - (oy + oh + 10)) < R: cy = oy + oh + 10
            elif abs(cy + ch + 10 - oy) < R: cy = oy - 10 - ch
        return int(cx - 10), int(cy - 10)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton: self._menu(ev.globalPosition().toPoint()); return
        if ev.button() == Qt.MouseButton.LeftButton: self._drag = (ev.globalPosition(), self.pos())

    def mouseMoveEvent(self, ev):
        if self._drag is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            p0, w0 = self._drag; d = ev.globalPosition() - p0
            nx, ny = self._snap(int(w0.x() + d.x()), int(w0.y() + d.y())); self.move(nx, ny)

    def mouseReleaseEvent(self, ev):
        if self._drag is not None: self._drag = None; self.island._save_widgets()

    def _menu(self, gpos):
        m = QMenu(self)
        m.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(0,205,255,80)}QMenu::separator{height:1px;background:rgba(255,255,255,25);margin:4px 8px}")
        tm = m.addMenu("Тема оформления")
        for i, nm in enumerate(WIDGET_THEMES): tm.addAction(("✓  " if i == self.theme else "     ") + nm, lambda i=i: self.set_theme(i))
        m.addAction("Цвет акцента…", self._pick_color); m.addAction("Цвет как у острова", lambda: self.set_color(""))
        sm = m.addMenu("Размер")
        for nm, sc in (("Маленький", 0.8), ("Средний", 1.0), ("Большой", 1.25)): sm.addAction(nm, lambda s=sc: (self.resize_to(s), self.island._save_widgets()))
        m.addSeparator(); m.addAction("🗑 Удалить виджет", lambda: self.island.remove_widget(self.wid)); m.exec(gpos)


class InlineNoteEditor(QWidget):
    """Встроенный редактор заметок поверх страницы островка (не отдельное окно)."""
    def __init__(self, island):
        super().__init__(island)
        self.island = island
        self.index = -1
        self._dirty = False
        self.setObjectName("inlineNoteEditor")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 14, 18, 14)
        self.root.setSpacing(9)

        head = QHBoxLayout(); head.setSpacing(8)
        self.caption = QLabel("ЗАМЕТКИ  /  РЕДАКТОР")
        self.caption.setObjectName("noteCaption")
        head.addWidget(self.caption)
        head.addStretch(1)
        self.status = QLabel("Сохранено")
        self.status.setObjectName("noteStatus")
        head.addWidget(self.status)
        close = QPushButton("×"); close.setObjectName("noteClose"); close.setFixedSize(32, 30)
        close.setToolTip("Закрыть редактор (изменения сохранятся)")
        close.clicked.connect(self.close_editor); head.addWidget(close)
        self.root.addLayout(head)

        self.title = QLineEdit(); self.title.setObjectName("noteTitle")
        self.title.setPlaceholderText("Название заметки")
        self.root.addWidget(self.title)

        self.body = QTextEdit(); self.body.setObjectName("noteBody")
        self.body.setAcceptRichText(False)
        self.body.setPlaceholderText("Начните писать…\n\nИдеи, планы, списки покупок и важные мысли.")
        self.root.addWidget(self.body, 1)

        # Две отдельные строки инструментов — кнопки не сжимаются и не налезают друг на друга.
        findrow = QHBoxLayout(); findrow.setSpacing(7)
        self.find = QLineEdit(); self.find.setObjectName("noteSearch")
        self.find.setPlaceholderText("Поиск в этой заметке")
        findrow.addWidget(self.find, 1)
        bfind = self._button("Найти", "noteTool"); bfind.clicked.connect(self.find_next); findrow.addWidget(bfind)
        self.counter = QLabel("0 символов"); self.counter.setObjectName("noteCounter")
        findrow.addWidget(self.counter)
        self.root.addLayout(findrow)

        tools = QGridLayout(); tools.setHorizontalSpacing(7); tools.setVerticalSpacing(6)
        actions = [
            ("•  Список", self.insert_bullet), ("☐  Задача", self.insert_check),
            ("Дата", self.insert_date), ("↶  Отменить", self.body.undo),
            ("↷  Повторить", self.body.redo), ("Очистить формат", self.clear_format),
        ]
        for i, (label, callback) in enumerate(actions):
            btn = self._button(label, "noteTool")
            btn.clicked.connect(callback)
            tools.addWidget(btn, i // 3, i % 3)
        for c in range(3): tools.setColumnStretch(c, 1)
        self.root.addLayout(tools)

        foot = QHBoxLayout(); foot.setSpacing(8)
        self.delete_btn = self._button("Удалить", "noteDanger")
        self.delete_btn.clicked.connect(self.delete_note); foot.addWidget(self.delete_btn)
        foot.addStretch(1)
        cancel = self._button("Закрыть", "noteTool"); cancel.clicked.connect(self.close_editor); foot.addWidget(cancel)
        save = self._button("Сохранить  ✓", "notePrimary"); save.clicked.connect(self.save_now); foot.addWidget(save)
        self.root.addLayout(foot)

        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(550)
        self.timer.timeout.connect(self.save_now)
        self.title.textChanged.connect(self.changed); self.body.textChanged.connect(self.changed)
        self.find.returnPressed.connect(self.find_next)
        self._apply_app_style()

    def _button(self, label, obj):
        b = QPushButton(label); b.setObjectName(obj); b.setMinimumHeight(31)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

    def _apply_app_style(self):
        # Палитра берётся из текущей темы самого Dynamic Island.
        try:
            accent = ACCENT.name()
            style = self.island._ui_style()
        except Exception:
            accent, style = "#168cff", 0
        bg = {0:"#17191f", 1:"#20232b", 2:"#171c27", 3:"#080d18", 4:"#090a0d"}.get(style, "#17191f")
        field = {0:"#22252d", 1:"#292d37", 2:"#222938", 3:"#101827", 4:"#15171c"}.get(style, "#22252d")
        self.setStyleSheet(f"""
            QWidget#inlineNoteEditor {{ background:{bg}; color:#f4f6fb; border:1px solid rgba(255,255,255,34); border-radius:22px; }}
            QLabel {{ background:transparent; border:0; color:#a7afbd; }}
            QLabel#noteCaption {{ color:{accent}; font-size:10px; font-weight:800; letter-spacing:1px; }}
            QLabel#noteStatus, QLabel#noteCounter {{ color:#8c95a4; font-size:10px; }}
            QLineEdit {{ background:{field}; color:#f5f7fb; border:1px solid rgba(255,255,255,22); border-radius:10px; padding:8px 11px; font-size:12px; selection-background-color:{accent}; }}
            QLineEdit:focus {{ border:1px solid {accent}; }}
            QLineEdit#noteTitle {{ font-size:19px; font-weight:700; padding:9px 12px; }}
            QTextEdit {{ background:{field}; color:#f0f2f7; border:1px solid rgba(255,255,255,22); border-radius:13px; padding:12px; font-size:13px; selection-background-color:{accent}; }}
            QTextEdit:focus {{ border:1px solid {accent}; }}
            QPushButton {{ color:#e9edf5; background:#2a303b; border:1px solid rgba(255,255,255,22); border-radius:9px; padding:6px 10px; font-size:10px; }}
            QPushButton:hover {{ background:#394354; border-color:rgba(255,255,255,55); }}
            QPushButton#notePrimary {{ background:{accent}; color:white; border:0; font-weight:700; padding-left:14px; padding-right:14px; }}
            QPushButton#notePrimary:hover {{ background:{accent}; }}
            QPushButton#noteDanger {{ color:#ff8585; }}
            QPushButton#noteClose {{ font-size:18px; padding:0; background:rgba(255,255,255,10); }}
        """)

    def open_note(self, index=-1):
        self.index = index; self._dirty = False
        note = self.island._notes.items[index] if 0 <= index < len(self.island._notes.items) else {}
        title = note.get("title", ""); body = note.get("text", "")
        if not title and body:
            lines = body.splitlines(); title = lines[0][:70] if lines else ""
            body = "\n".join(lines[1:]).lstrip()
        self.title.blockSignals(True); self.body.blockSignals(True)
        self.title.setText(title); self.body.setPlainText(body)
        self.title.blockSignals(False); self.body.blockSignals(False)
        self.delete_btn.setVisible(index >= 0)
        self.status.setText("Новая заметка" if index < 0 else "Сохранено")
        self.find.clear(); self._count()
        # Редактор является дочерним виджетом островка. Не активируем его как отдельное
        # окно: перевод фокуса на QLineEdit/QTextEdit не должен запускать автосворачивание.
        self._place(); self.show(); self.raise_()
        self.title.setFocus(Qt.FocusReason.OtherFocusReason)
        self.island._wake(); self.island.update()

    def _place(self):
        # Координаты совпадают с областью отрисовки страницы: origin + смещение контента.
        ox = self.island._org_x() + getattr(self.island, "_ox", 0.0)
        oy = self.island._org_y()
        margin = 18
        w = max(300, int(self.island.EW - margin * 2))
        h = max(260, int(self.island.EH - 76))
        x = int(round(ox + margin)); y = int(round(oy + 62))
        # Защита от выхода панели за границы canvas на нестандартных размерах.
        w = min(w, max(300, self.island.width() - x - margin))
        h = min(h, max(260, self.island.height() - y - margin))
        self.setGeometry(x, y, w, h)
        self.raise_()

    def changed(self, *_):
        self._dirty = True; self.status.setText("Изменения не сохранены…")
        self._count(); self.timer.start()

    def _count(self):
        n = len(self.body.toPlainText())
        self.counter.setText(f"{n:,} символов".replace(",", " "))

    def save_now(self, *_):
        self.timer.stop()
        title = self.title.text().strip(); body = self.body.toPlainText()
        if not self._dirty: return
        if not title and not body.strip():
            self._dirty = False; self.status.setText("Пустая заметка"); return
        try:
            if self.index >= 0 and self.index < len(self.island._notes.items):
                self.island._notes.update(self.index, body, title)
            else:
                self.island._notes.add(body, title); self.index = 0
            self._dirty = False; self.status.setText("Сохранено · только что")
            self.island.update()
        except Exception as e:
            self.status.setText("Ошибка сохранения"); log_error(f"inline note save: {e}")

    def close_editor(self):
        self.save_now(); self.hide(); self.island.update()

    def delete_note(self):
        if self.index >= 0:
            self.island._notes.remove(self.index)
        self.index = -1; self._dirty = False; self.timer.stop(); self.hide(); self.island.update()

    def insert_bullet(self): self.body.insertPlainText("• ")
    def insert_check(self): self.body.insertPlainText("☐ ")
    def insert_date(self): self.body.insertPlainText(datetime.datetime.now().strftime("%d.%m.%Y · "))
    def clear_format(self):
        # Plain-text editor: normalize pasted rich text and preserve readable paragraphs.
        self.body.setPlainText(self.body.toPlainText())
    def find_next(self):
        q = self.find.text().strip()
        if q and not self.body.find(q):
            cur = self.body.textCursor(); cur.movePosition(cur.MoveOperation.Start)
            self.body.setTextCursor(cur); self.body.find(q)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Qt layouts handle all internal geometry; no manual text placement.



class ChristmasSnow(QWidget):
    """Лёгкий прозрачный снегопад поверх рабочего стола; мышь проходит сквозь окно."""
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.geometry() if screen else QRectF(0,0,1920,1080).toRect())
        random.seed(7341)
        self.flakes = []
        w, h = max(1,self.width()), max(1,self.height())
        for _ in range(105):
            self.flakes.append([random.uniform(0,w), random.uniform(0,h), random.uniform(0.65,2.8),
                                random.uniform(0.55,1.75), random.uniform(0,math.tau), random.uniform(65,190)])
        self.phase = 0.0
        self.timer = QTimer(self); self.timer.timeout.connect(self._step); self.timer.start(33)
        self.show()

    def _step(self):
        screen = QGuiApplication.primaryScreen()
        if screen and self.geometry() != screen.geometry():
            self.setGeometry(screen.geometry())
        self.phase += 0.035
        h = max(1,self.height()); w = max(1,self.width())
        for f in self.flakes:
            f[1] += f[3]; f[0] += math.sin(self.phase+f[4])*0.52 + 0.22
            if f[1] > h+8: f[1] = -8; f[0] = random.uniform(0,w)
            if f[0] > w+5: f[0] = -5
        self.update()

    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for x,y,r,spd,ph,a in self.flakes:
            alpha=int(a*(0.82+0.18*math.sin(self.phase*2+ph)))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(235,245,255,alpha))
            p.drawEllipse(QPointF(x,y),r,r)
            if r>2.25:
                p.setPen(QPen(QColor(220,240,255,int(alpha*0.35)),0.7))
                p.drawLine(QPointF(x-r*1.7,y),QPointF(x+r*1.7,y))

    def closeEvent(self, ev):
        self.timer.stop(); super().closeEvent(ev)


class DynamicIsland(QWidget):
    TIMER_PRESETS = [1, 5, 10, 15, 25, 45, 60]
    _ocr_result = pyqtSignal(str)
    _qr_result = pyqtSignal(str)
    CHARACTERS = [("eyes", "Глаза"), ("claude", "Claude"), ("clawd", "Clawd"), ("cat", "Кот"), ("ghost", "Призрак"), ("robot", "Робот"), ("alien", "Пришелец"), ("panda", "Панда"), ("fox", "Лиса"), ("frog", "Лягушка")]

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus); self.setMouseTracking(True)
        self.settings = CachedSettings(QSettings("DynamicIsland", "island"))
        apply_theme(self.settings)
        self.CW = int(self.settings.value("island_cw", 260))
        self.CH = int(self.settings.value("island_ch", 40))
        self.EW = int(self.settings.value("island_ew", 800))
        self.EH = int(self.settings.value("island_eh", 480))
        if self.EH == 540:
            self.EH = 480
            self.settings.setValue("island_eh", 480)
        try: self.desktop_only = bool(self.settings.value("desktop_only", True, type=bool))
        except: self.desktop_only = True
        try:
            self.mod_music = bool(self.settings.value("mod_music", True, type=bool))
            self.mod_weather = bool(self.settings.value("mod_weather", True, type=bool))
            self.mod_timer = bool(self.settings.value("mod_timer", True, type=bool))
            self.mod_screenshot = bool(self.settings.value("mod_screenshot", True, type=bool))
            self.mod_ai = bool(self.settings.value("mod_ai", False, type=bool))
            self.mod_voice = bool(self.settings.value("mod_voice", False, type=bool))
            self.mod_clipboard = bool(self.settings.value("mod_clipboard", True, type=bool))
        except:
            self.mod_music = self.mod_weather = self.mod_timer = self.mod_screenshot = True
            self.mod_ai = self.mod_voice = False; self.mod_clipboard = True
        try:
            raw = self.settings.value("dock_items", "")
            self.dock = json.loads(raw) if raw else None
            if not self.dock:
                self.dock = [{"path":"C:\\Windows\\explorer.exe","type":"app"},
                             {"path":"C:\\Windows\\System32\\notepad.exe","type":"app"},
                             {"path":"C:\\Windows\\System32\\calc.exe","type":"app"}]
        except:
            self.dock = [{"path":"C:\\Windows\\explorer.exe","type":"app"}]
        self._settings_window = None; self._log_window = None
        self._notify = None; self._notify_wake = False
        self._notify_timer = QTimer(self); self._notify_timer.setSingleShot(True)
        self._notify_timer.timeout.connect(self._clear_notification)
        self._last_hover = time.monotonic()
        self._reveal_timer = QTimer(self); self._reveal_timer.timeout.connect(self._check_reveal); self._reveal_timer.start(80)
        self.expanded = False; self._expand = 0.0; self._glow = 0.0; self._wave_phase = 0.0
        # пружины: раскрытие (ширина и высота — разные, отсюда «жидкая» форма) и появление капли
        self._ex_w = 0.0; self._ex_h = 0.0; self._exw_v = 0.0; self._exh_v = 0.0; self._ex_target = 0.0
        self._show = 0.0; self._show_v = 0.0; self._show_target = 1.0
        self._iw = 0.0; self._ih = 0.0; self._rb = 20.0; self._fl = 9.0; self._drop = 1.0
        self._full_mode = False; self._animating = True; self._frame_interval = 0
        self._last_frame = time.perf_counter(); self._reveal_started = 0.0
        self._eq_disp = [0.0] * 32; self._eq_peak = [0.0] * 32; self._bass = 0.0
        self._ai_service = ""; self._weather_loading = False; self._ds_add_mode = False
        self._ds_flash_msg = ("", 0.0, True); self._app_index_ts = 0.0
        self._nw = float(self.CW); self._nw_v = 0.0; self._edit_note_idx = -1
        self._alarm_queue = []; self._reminder_time = ""; self._reminder_field = "text"; self._err_ts = {}; self._paint_ms = 4.0; self._dock_bounce = {}; self._scr_name = str(self.settings.value("isl_screen", "") or ""); self._nav_ind = None; self._mood = "calm"
        self._alarm = None; self._alarm_rects = {}; self._mixer = MixerWatcher(); self._mx_drag = None; self._mx_local = {}
        self._free = None; self._gliding = False; self._moving = False; self._move_press = None; self._cx = 0.0; self._cy = 0.0
        self._live_cur = []; self._batt_prev = None; self._low_warned = False; self._widgets = []
        try:
            self._edge = str(self.settings.value("isl_edge", "top"))
            if self._edge not in ("top", "bottom", "left", "right"): self._edge = "top"
            self._epos = max(0.0, min(1.0, float(self.settings.value("isl_pos", 0.5))))
        except Exception: self._edge = "top"; self._epos = 0.5
        self._cpu_hist = []; self._gv = {}; self._clip_thumbs = {}; self._clip_flash = None; self._sys_stats_rect = QRectF(20, 322, 760, 202)
        self._anim = None; self._hits = []; self._mouse = None; self._ox = 0.0
        self._user_hidden = False; self._tick_n = 0; self._grace_until = 0.0
        self._hide_streak = 0; self._seek_lock_until = 0.0
        self._seek_drag = False; self._vol_drag = False
        self._smtc_last_pos = -1.0
        self._blink_until = 0.0; self._blink_start = 0.0
        self._next_blink = time.monotonic() + 3.0
        self._click_timer = None
        self._bounce_start = 0.0
        self._shake_start = 0.0
        self._shake_amp = 0.0
        self._pip_active = False
        self._pip_overlay = None
        
        # AI / WebEngine
        self._ai_view = None
        self._ai_profile = None
        self._ai_webengine_ok = False
        self._ai_url = ""
        self._ai_windows = []
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            self._ai_webengine_ok = True
        except ImportError:
            log_error("PyQt6-WebEngine не установлен — вкладка ИИ использует отдельные окна")

        self._ocr_result.connect(self._ocr_done)
        self._qr_result.connect(self._qr_done)
        self.current_page = "home"
        self.system_view = "menu"
        self.wifi_networks = []
        self.bt_state = "unknown"
        self._new_note_text = ""; self._new_note_active = False
        self._reminder_text = ""; self._reminder_active = False
        self._cal_selected = datetime.date.today()
        self._cal_year = self._cal_selected.year
        self._cal_month = self._cal_selected.month
        self._weather_started = time.monotonic()
        self._reminders_shown_today = set()
        self._volume = 0.5
        if HAS_PYCAW:
            v = get_volume()
            if v is not None: self._volume = v
        self._evt_last_title = ""
        self._evt_last_vol = self._volume
        self._evt_vol_cooldown = 0.0
        self._evt_battery_shown = False
        self.media = {"active": False,"title": "","artist": "","duration": 1.0,"position": 0.0,"playing": False,"thumb": None}
        self.weather = {"ok": False}
        self._media_bridge = MediaBridge()
        self._media_bridge.changed.connect(self._on_media_changed)
        self._priv = PrivacyWatcher(); self._devw = DeviceWatcher(self.settings)
        self._devw.audio.connect(self._on_audio_dev); self._devw.wifi.connect(self._on_wifi)
        self._glow_overlay = ScreenGlow()
        self._dl = DownloadWatcher(self.settings); self._dl.finished.connect(self._on_dl_finished)
        self._shelf = ShelfStore(self.settings); self.setAcceptDrops(True)
        self._dl_cur = []; self._frame_data_t = 0.0; self._drag_over = False; self._shelf_press = None; self._shelf_rects = []; self._shelf_x = []
        self._shelf_flash = ("", 0.0, True); self._dragging_out = False; self._pending_toasts = []; self._shelf_info = {}; self._shelf_thumbs = {}
        self._gpu = GpuMonitor(); self._fr_n = 0; self._fr_t0 = time.perf_counter(); self._fps = 0.0
        self._sysnotif = SysNotifyListener(self.settings); self._sysnotif.got.connect(self._on_sys_notif)
        self._input_watcher = InputStateWatcher(); self._input_watcher.changed.connect(self._on_input_state_changed)
        self._update_manager = UpdateManager(self)
        self._update_manager.checked.connect(self._on_update_checked)
        self._update_manager.installed.connect(self._on_update_installed)
        self._update_manager.progress.connect(self._on_update_progress)
        self._update_info = None
        self._update_action = None
        self._weather_worker = WeatherWorker(self.settings)
        self._weather_worker.changed.connect(self._on_weather_changed)
        self._clipboard = ClipboardMonitor(max_items=30)
        self._clipboard.changed.connect(self._on_clipboard_changed)
        self._notes = NotesStore(self.settings)
        self._note_editor = InlineNoteEditor(self)
        self._notes.changed.connect(self._on_notes_changed)
        self._reminders = RemindersStore(self.settings)
        self._reminders.changed.connect(self._on_reminders_changed)
        self.now = datetime.datetime.now()
        self.v = {"cpu": 0.0,"mem": 0.0,"disk": 0.0}; self.d = dict(self.v)
        self.mem_used = self.mem_total = 0.0; self.battery = None
        self.net_down = self.net_up = 0.0
        self._net_last = psutil.net_io_counters(); self._net_time = time.monotonic()
        psutil.cpu_percent()
        self.preset = 4; self.t_total = 25*60; self.t_left = float(self.t_total)
        self.t_running = False; self.t_end = 0.0
        # Кастомный таймер
        self._timer_custom_mode = False
        self._timer_h_input = ""
        self._timer_m_input = ""
        self._timer_s_input = ""
        self._timer_active_field = None
        self._timer_field_fresh = False
        self._init_ext()
        try: self._audio = AudioLevels(use_loopback=bool(self.settings.value("eq_real", True, type=bool)))
        except Exception as _e: log_error(f"audio init: {_e}"); self._audio = None
        self._init_center(); self._apply_geometry(); self._load_widgets(); self._build_tray(); self._sample()
        self.tick_timer = QTimer(self); self.tick_timer.timeout.connect(self._tick); self.tick_timer.start(150)
        self.vis_timer = QTimer(self); self.vis_timer.timeout.connect(self._check_visibility); self.vis_timer.start(150)
        self._frame_timer = QTimer(self); self._frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._frame_timer.timeout.connect(self._frame)
        self.show(); self._keep_on_top(); self._wake()
        QTimer.singleShot(0, self._check_visibility)
        QTimer.singleShot(9000, lambda: self._update_manager.check(manual=False))

    def _init_ext(self):
        self._ds_active = False; self._ds_text = ""; self._ds_res = []; self._ds_sel = 0; self._app_index = None; self._ds_icons = {}
        self._wifi_cur = ""; self._wifi_profiles = set(); self._wifi_on = None; self._wifi_pw_for = None; self._wifi_pw = ""; self._wifi_msg = ""
        self._bt_devs = []; self._dock_right_regions = []
        self._ext = ExtBridge(self.settings); self._ext.ping.connect(self.update); self._ext.fired.connect(self._on_hotkey)
        threading.Thread(target=self._build_app_index, daemon=True).start()

    def _on_hotkey(self, k):
        if k == "toggle": self.toggle_visible()
        elif k == "music":
            self.current_page = "home"
            if not self.expanded: self.toggle_expand()
            self.update()
        elif k == "shot": self._shot_full()
        elif k == "settings": self._open_settings()

    def _bg(self, fn):
        def run():
            try: fn()
            except Exception as e: log_error(f"bg: {e}")
            self._ext.ping.emit()
        threading.Thread(target=run, daemon=True).start()

    # ═════════ анимационный движок ═════════
    MINI = 0.5                      # «миниатюра» — маленькая капля у края
    MINI_W, MINI_H = 30.0, 15.0

    def _zk(self):
        try: return {0: 1.15, 1: 1.0, 2: 0.85}.get(int(self.settings.value("anim_style", 0)), 1.15)
        except Exception: return 1.15

    def _anim_hz(self):
        try: hz = int(self.settings.value("anim_hz", 0))
        except Exception: hz = 0
        if hz <= 0:
            try: hz = int(round(self._scr().refreshRate()))
            except Exception: hz = 60
        return max(30, min(240, hz))

    def _speed(self):
        try: return max(0.5, min(2.0, int(self.settings.value("anim_speed", 100)) / 100.0))
        except Exception: return 1.0

    def _wake(self):
        self._last_frame = time.perf_counter()
        if not self._frame_timer.isActive(): self._frame_timer.start(1)

    def showEvent(self, e):
        super().showEvent(e); self._wake()

    @staticmethod
    def _spring(x, v, target, w0, zeta, dt):
        """Пружина с подшагами: одинаково стабильна и на 60, и на 240 Гц (анимация привязана ко времени, а не к кадрам)."""
        n = max(1, int(dt / 0.004) + 1); h = dt / n; k = w0 * w0; c = 2.0 * zeta * w0
        for _ in range(n):
            v += (k * (target - x) - c * v) * h
            x += v * h
        return x, v

    def _theme_target(self):
        try: mode = int(self.settings.value("theme_mode", 0))
        except Exception: mode = 0
        if mode == 1:
            try:
                ds = int(self.settings.value("theme_day_h", 7)); ns = int(self.settings.value("theme_night_h", 20))
                dp = int(self.settings.value("theme_day_p", 0)); np_ = int(self.settings.value("theme_night_p", 1))
            except Exception: ds, ns, dp, np_ = 7, 20, 0, 1
            h = self.now.hour; day = (ds <= h < ns) if ds < ns else not (ns <= h < ds)
            pr = THEME_PRESETS[max(0, min(len(THEME_PRESETS) - 1, dp if day else np_))]
            return pr[1], pr[2], pr[3]
        if mode == 2 and self.media.get("active"):
            h_, s_, v_, _a = self._dyn().getHsv(); h_ = max(0, h_)
            a = QColor.fromHsv(h_, max(s_, 150), max(v_, 215)); v = QColor.fromHsv((h_ + 50) % 360, max(s_, 140), 235); m = QColor.fromHsv((h_ - 35) % 360, max(s_, 130), 255)
            return (a.red(), a.green(), a.blue()), (v.red(), v.green(), v.blue()), (m.red(), m.green(), m.blue())
        return None

    def _theme_step(self):
        tg = self._theme_target()
        if tg is None: return
        def st(c, t):
            d = t - c
            if abs(d) <= 1: return t
            s = d * 0.25
            return c + int(s if abs(s) >= 1 else (1 if d > 0 else -1))
        for col, t in zip((ACCENT, VIOLET, MUSIC_COLOR), tg): col.setRgb(st(col.red(), t[0]), st(col.green(), t[1]), st(col.blue(), t[2]))

    def _load_widgets(self):
        self._widgets = []
        try: data = json.loads(self.settings.value("widgets", "[]") or "[]")
        except Exception: data = []
        for d in data[:WIDGET_MAX]:
            try: self._make_widget(d)
            except Exception as e: log_error(f"widget load: {e}")

    def _make_widget(self, d):
        w = DesktopWidget(self, str(d["id"]), d["kind"], int(d["x"]), int(d["y"]), float(d.get("scale", 1.0)), int(d.get("theme", 0)), d.get("color", "")); w.show(); self._widgets.append(w)

    def _save_widgets(self):
        try: self.settings.setValue("widgets", json.dumps([{"id": w.wid, "kind": w.kind, "x": w.x(), "y": w.y(), "scale": w.scale, "theme": w.theme, "color": w.color} for w in self._widgets]))
        except Exception as e: log_error(f"widget save: {e}")

    def add_widget(self, kind):
        if len(self._widgets) >= WIDGET_MAX or kind not in WIDGET_KINDS: return False
        s = self._scr_geom(); st = len(self._widgets) * 34
        self._make_widget({"id": str(int(time.time() * 1000)), "kind": kind, "x": s.x() + 80 + st, "y": s.y() + 220 + st, "scale": 1.0}); self._save_widgets(); return True

    def remove_widget(self, wid):
        for w in list(self._widgets):
            if w.wid == wid: w.close(); w.deleteLater(); self._widgets.remove(w)
        self._save_widgets()
        sw = getattr(self, "_settings_window", None)
        if sw is not None and hasattr(sw, "_wd_rebuild"):
            try: sw._wd_rebuild()
            except Exception: pass

    def _wave_offsets(self, ih):
        d = self._eq_disp; n = 24; t = time.monotonic(); amp = min(16.0, 4.0 + 0.2 * ih); out = []
        playing = bool(self.media.get("active") and self.media.get("playing") and self.mod_music)
        idle = 2.0 + 0.5 * math.sin(t * 1.1)
        for i in range(n):
            taper = math.sin(math.pi * i / (n - 1)) ** 0.6
            base = idle * (0.55 + 0.45 * math.sin(i * 0.62 - t * 2.4))
            mus = 0.0
            if playing:
                k = min(31, int(i * 32 / n)); v = min(1.0, (d[k] + d[min(31, k + 1)]) * 0.5 * 1.4) ** 0.8
                mus = amp * max(0.0, v + 0.22 * math.sin(i * 0.95 + t * 7.0) * (0.3 + v))
            out.append(taper * (base + mus))
        return out

    def _draw_bottom_waves(self, p, iw, ih, e):
        """В развёрнутом виде: у дна острова две «волны воды», которые поднимаются от музыки."""
        t = time.monotonic(); d = self._eq_disp; c = self._dyn(); n = 48
        for amp_k, ph, alpha in ((1.0, 0.0, 78), (0.65, 1.7, 46)):
            pp = QPainterPath(); pp.moveTo(0, ih)
            for i in range(n + 1):
                v = min(1.0, d[min(31, int(i * 32 / (n + 1)))] * 1.3)
                pp.lineTo(iw * i / n, ih - 5 - e * 16.0 * amp_k * (0.3 + v * 1.1) - 4.0 * amp_k * math.sin(i * 0.36 + t * 3.2 + ph) * (0.4 + v))
            pp.lineTo(iw, ih); pp.closeSubpath()
            g = QLinearGradient(0, ih - 44, 0, ih); g.setColorAt(0, rgba(c, alpha)); g.setColorAt(1, rgba(c, alpha // 3)); p.fillPath(pp, g)

    def _shape(self):
        try: return int(self.settings.value("island_shape", 0))
        except Exception: return 0

    def _compute_dims(self):
        s = max(0.0, min(self._show, 1.12))
        CW, CH = float(self._nw), float(self.CH)
        if s <= self.MINI:
            t = s / self.MINI
            cw_, ch_ = self.MINI_W * t, self.MINI_H * t; drop = 1.0
        else:
            q = (s - self.MINI) / (1.0 - self.MINI)
            cw_ = self.MINI_W + (CW - self.MINI_W) * q
            ch_ = self.MINI_H + (CH - self.MINI_H) * q
            drop = max(0.0, 1.0 - q) ** 1.4
        e_w = max(-0.05, self._ex_w); e_h = max(-0.05, self._ex_h)
        self._iw = cw_ + (self.EW - cw_) * e_w
        self._ih = ch_ + (self.EH - ch_) * e_h
        if bool(self.settings.value("anim_drop", True, type=bool)):
            drop = max(drop, max(0.0, min(0.5, (e_h - e_w) * 1.4)))
        e = max(0.0, min(1.0, (e_w + e_h) * 0.5))
        self._drop = drop
        self._rb = 20.0 + 10.0 * e
        self._fl = (9.0 + 5.0 * e) * (1.0 - 0.6 * min(1.0, drop))
        shape = self._shape()
        if shape == 1: self._drop = max(self._drop, 0.3 * (1.0 - e)); self._fl *= 0.5
        elif shape == 2: self._rb = (self._ih / 2.0) * (1.0 - e) + 30.0 * e; self._fl = 0.0
        self._expand = e
        self._ox = (self._iw - self.EW) / 2.0

    def _frame(self):
        try:
            if not self.isVisible():
                self._frame_timer.stop(); return
            now = time.perf_counter(); dt = max(0.0005, min(now - self._last_frame, 0.05)); self._last_frame = now
            self._fr_n += 1
            if now - self._fr_t0 >= 0.5: self._fps = self._fr_n / (now - self._fr_t0); self._fr_n = 0; self._fr_t0 = now
            # Дорогие опросы процессов/загрузок не должны выполняться на каждом кадре.
            # Данные обновляются отдельно от отрисовки и переиспользуются между кадрами.
            if now - self._frame_data_t >= 0.18:
                self._frame_data_t = now
                self._dl_cur = self._dl.snapshot() if self._wb("dl_track", True) else []
                self._live_cur = self._live_activities()
            if self._alarm: self._alarm_step()
            sp = self._speed(); busy = False; zk = self._zk()
            tgt = self._ex_target
            if tgt > 0.5:
                self._ex_h, self._exh_v = self._spring(self._ex_h, self._exh_v, tgt, 17.0 * sp, 0.68 * zk, dt)
                self._ex_w, self._exw_v = self._spring(self._ex_w, self._exw_v, tgt, 13.5 * sp, 0.72 * zk, dt)
            else:
                self._ex_w, self._exw_v = self._spring(self._ex_w, self._exw_v, tgt, 19.0 * sp, 0.80 * zk, dt)
                self._ex_h, self._exh_v = self._spring(self._ex_h, self._exh_v, tgt, 12.5 * sp, 0.86 * zk, dt)
            def rest(x, v, t, ex=0.0006, ev=0.01): return abs(x - t) < ex and abs(v) < ev
            if rest(self._ex_w, self._exw_v, tgt) and rest(self._ex_h, self._exh_v, tgt):
                self._ex_w = self._ex_h = tgt; self._exw_v = self._exh_v = 0.0
            else: busy = True
            st = self._show_target
            self._show, self._show_v = self._spring(self._show, self._show_v, st, 15.0 * sp, (0.55 if st > self._show else 0.85) * zk, dt)
            if rest(self._show, self._show_v, st, 0.0008, 0.02): self._show = st; self._show_v = 0.0
            else: busy = True
            n_ = self._notify
            forced = bool(n_ and n_.get("force"))
            if self._dl_cur and not forced: ntw = float(max(self.CW, 400))
            else:
                ntw = float(max(self.CW, 380 if n_.get("app") else 320)) if (n_ and n_.get("out_start", 0) == 0) else float(self.CW)
                if self._live_cur and ntw <= self.CW: ntw = float(max(self.CW, 340))
            if self._alarm: ntw = float(max(self.CW, 420))
            self._nw, self._nw_v = self._spring(self._nw, self._nw_v, ntw, 15.0 * sp, 0.62 * zk, dt)
            if rest(self._nw, self._nw_v, ntw, 0.05, 0.5): self._nw = ntw; self._nw_v = 0.0
            else: busy = True
            need_full = self.expanded or self._ex_w > 0.004 or self._ex_h > 0.004 or abs(self._exw_v) > 0.01 or abs(self._exh_v) > 0.01
            if need_full != self._full_mode:
                self._full_mode = need_full; self._apply_geometry()
            busy = self._step_position(dt, busy)
            self._compute_dims()
            t = time.monotonic()
            self._glow = (t * 0.66) % 1.0; self._wave_phase = t * 2.0
            playing = bool(self.media.get("active") and self.media.get("playing") and self.mod_music)
            if playing or self._bass > 0.003 or any(v > 0.004 for v in self._eq_disp): self._eq_step(dt, playing)
            if self._show <= 0.002 and self._show_target <= 0.0 and not self._notify:
                self._frame_timer.stop(); self.hide(); return
            was = self._animating; self._animating = busy
            if was and not busy: self._update_ai_visibility()
            perf = self._perf()
            if busy:
                hz = float(self._anim_hz() if perf != 1 else min(60, self._anim_hz()))
                if perf != 2:       # если кадр рисуется дольше интервала — берём ровный делитель частоты (стабильный ритм вместо рваного)
                    ivm = 1000.0 / hz
                    if self._paint_ms > ivm * 0.85: hz = hz / max(1, math.ceil(self._paint_ms * 1.12 / ivm))
            elif self.expanded: hz = 45.0 if self._page_animated() else 18.0
            elif playing or self._notify or self._dl_cur or self._live_cur or self._alarm or self._wb("compact_stats", False): hz = 60.0
            else: hz = 30.0
            if perf == 1 and not busy: hz = min(hz, 30.0 if self.expanded else 24.0)
            iv = max(1, int(round(1000.0 / hz)))
            if iv != self._frame_interval: self._frame_timer.setInterval(iv); self._frame_interval = iv
            if busy and self._wb("anim_vsync", True):       # кадр рисуется сразу и привязывается к развёртке монитора — без «рваного» ритма
                self.repaint()
                try: dwmapi.DwmFlush()
                except Exception: pass
            else: self.update()
        except Exception as ex: log_error(f"frame: {ex}\n{traceback.format_exc()}")

    def _set_show_target(self, v):
        if abs(self._show_target - v) > 1e-6:
            self._show_target = v; self._wake()
        if v > 0 and not self.isVisible(): self.show(); self._keep_on_top()

    def _org_x(self): return self._origin()[0]
    def _org_y(self): return self._origin()[1]

    EDGE_GAP = 10

    def _scr(self):
        try:
            for s in QGuiApplication.screens():
                if s.name() == self._scr_name: return s
        except Exception: pass
        return QGuiApplication.primaryScreen()

    def _scr_geom(self): return self._scr().geometry()

    def _virt_geom(self):
        g = None
        for s in QGuiApplication.screens(): g = s.geometry() if g is None else g.united(s.geometry())
        return g if g is not None else QGuiApplication.primaryScreen().geometry()

    def move_to_screen(self, i):
        try:
            scr = QGuiApplication.screens(); i = max(0, min(len(scr) - 1, int(i)))
            self._scr_name = scr[i].name(); self.settings.setValue("isl_screen", self._scr_name)
            self._free = None; self._gliding = False; self._init_center(); self._place_window(); self._set_show_target(1.0); self._wake()
        except Exception as e: log_error(f"move_to_screen: {e}")

    def next_screen(self):
        scr = QGuiApplication.screens(); cur = self._scr()
        try: idx = [s.name() for s in scr].index(cur.name())
        except ValueError: idx = 0
        self.move_to_screen((idx + 1) % max(1, len(scr)))

    def _canvas_size(self):
        if self._full_mode: return int(self.EW * 1.12) + 2 * M, int(self.EH * 1.12) + 2 * M
        return int(max(self.CW, 400) * 1.2) + 2 * M, int(self.CH * 1.5) + 2 * M

    def _floating(self): return self._free is not None or self._edge in ("left", "right")

    def _origin(self):
        W, H = self.width(), self.height(); iw, ih = self._iw, self._ih
        if self._free is not None: return (W - iw) / 2.0, (H - ih) / 2.0
        e = self._edge
        if e == "bottom": return (W - iw) / 2.0, H - M - ih
        if e == "left": return float(M), (H - ih) / 2.0
        if e == "right": return W - M - iw, (H - ih) / 2.0
        return (W - iw) / 2.0, float(M)

    def _target_center(self):
        s = self._scr_geom(); gap = self.EDGE_GAP
        hw, hh = ((self.EW / 2.0, self.EH / 2.0) if self._full_mode else (max(self.CW, 400) / 2.0, self.CH / 2.0))
        if self._edge in ("top", "bottom"):
            lo, hi = s.x() + hw + gap, s.x() + s.width() - hw - gap
            return max(lo, min(max(lo, hi), s.x() + self._epos * s.width())), 0.0
        lo, hi = s.y() + hh + gap, s.y() + s.height() - hh - gap
        return 0.0, max(lo, min(max(lo, hi), s.y() + self._epos * s.height()))

    def _init_center(self): self._cx, self._cy = self._target_center()

    def _edge_island_center(self):
        s = self._scr_geom(); gap = self.EDGE_GAP; cx, cy = self._target_center(); e = self._edge
        if e == "top": return cx, s.y() + TOP + self._ih / 2.0
        if e == "bottom": return cx, s.y() + s.height() - self._ih / 2.0
        if e == "left": return s.x() + gap + self._iw / 2.0, cy
        return s.x() + s.width() - gap - self._iw / 2.0, cy

    def _place_window(self):
        W, H = self._canvas_size(); s = self._scr_geom(); gap = self.EDGE_GAP; e = self._edge
        if self._free is not None: x = self._free[0] - W / 2.0; y = self._free[1] - H / 2.0
        elif e == "top": x = self._cx - W / 2.0; y = s.y() + TOP - M
        elif e == "bottom": x = self._cx - W / 2.0; y = s.y() + s.height() - H + M
        elif e == "left": x = s.x() + gap - M; y = self._cy - H / 2.0
        else: x = s.x() + s.width() - gap - W + M; y = self._cy - H / 2.0
        self.setGeometry(int(round(x)), int(round(y)), W, H)

    def _apply_geometry(self): self._place_window()

    def _step_position(self, dt, busy):
        """Плавное скольжение острова к краю после перетаскивания и при смене размера."""
        if self._moving: return True
        if self._free is not None and self._gliding:
            tx, ty = self._edge_island_center(); fx, fy = self._free; k = 1.0 - math.exp(-dt * 16.0)
            fx += (tx - fx) * k; fy += (ty - fy) * k
            if abs(tx - fx) < 0.6 and abs(ty - fy) < 0.6: self._free = None; self._gliding = False; self._init_center()
            else: self._free = (fx, fy)
            self._place_window(); return True
        if self._free is None:
            tx, ty = self._target_center(); dx, dy = tx - self._cx, ty - self._cy
            if abs(dx) > 0.4 or abs(dy) > 0.4:
                k = 1.0 - math.exp(-dt * 12.0); self._cx += dx * k; self._cy += dy * k; self._place_window(); return True
            if dx or dy: self._cx, self._cy = tx, ty; self._place_window()
        return busy

    def set_edge(self, edge, pos=0.5):
        try:
            c = self._island_screen_rect().center(); self._edge = edge; self._epos = pos
            self.settings.setValue("isl_edge", edge); self.settings.setValue("isl_pos", float(pos))
            self._free = (c.x(), c.y()); self._gliding = True; self._set_show_target(1.0); self._wake()
        except Exception as e: log_error(f"set_edge: {e}")

    def _finish_move(self):
        self._moving = False
        if self._free is None: return
        fx, fy = self._free; scr = QGuiApplication.screenAt(QPoint(int(fx), int(fy))) or self._scr(); self._scr_name = scr.name()
        self.settings.setValue("isl_screen", scr.name()); s = scr.geometry(); iw, ih = self._iw, self._ih
        d = {"top": fy - ih / 2 - s.y(), "bottom": s.y() + s.height() - (fy + ih / 2), "left": fx - iw / 2 - s.x(), "right": s.x() + s.width() - (fx + iw / 2)}
        edge = min(d, key=d.get); self._edge = edge
        self._epos = max(0.0, min(1.0, ((fx - s.x()) / s.width()) if edge in ("top", "bottom") else ((fy - s.y()) / s.height())))
        self.settings.setValue("isl_edge", edge); self.settings.setValue("isl_pos", float(self._epos))
        self._gliding = True; self._wake()

    def reload_dimensions(self):
        self.CW = int(self.settings.value("island_cw", 260))
        self.CH = int(self.settings.value("island_ch", 40))
        self.EW = int(self.settings.value("island_ew", 800))
        self.EH = int(self.settings.value("island_eh", 480))
        if self.EH == 540:
            self.EH = 480
            self.settings.setValue("island_eh", 480)
        self._apply_geometry(); self._wake()

    # ── эквалайзер ──
    def _eq_targets(self):
        NB = 32
        a = getattr(self, "_audio", None)
        if a is not None and a.is_real(): return list(a.bands)
        t = time.monotonic(); lvl = a.level if a is not None else 0.0
        if a is not None and HAS_PYCAW and (t - a.audible_ts < 1.5 or lvl > 0.003): base = min(1.0, (lvl ** 0.55) * 1.25)
        else: base = 0.6
        out = []
        for i in range(NB):
            n1 = 0.5 + 0.5 * math.sin(t * 5.3 + i * 0.83); n2 = 0.5 + 0.5 * math.sin(t * 8.1 - i * 1.37 + 1.7)
            tilt = 1.0 - 0.42 * i / (NB - 1)
            out.append(max(0.0, min(1.0, base * (0.22 + 0.78 * (0.55 * n1 + 0.45 * n2)) * tilt)))
        return out

    def _eq_step(self, dt, playing):
        tg = self._eq_targets() if playing else [0.0] * 32
        try: sens = max(0.5, min(2.5, int(self.settings.value("eq_sens", 100)) / 100.0))
        except Exception: sens = 1.0
        att = 1.0 - math.exp(-dt * 38.0); dec = 1.0 - math.exp(-dt * 9.0)
        for i in range(32):
            v = min(1.0, tg[i] * sens); d = self._eq_disp[i]
            d += (v - d) * (att if v > d else dec); self._eq_disp[i] = d
            self._eq_peak[i] = max(d, self._eq_peak[i] - dt * 0.55)
        bass = sum(self._eq_disp[0:5]) / 5.0
        self._bass += (bass - self._bass) * (1.0 - math.exp(-dt * 20.0))

    def apply_modules(self): self.update()
    def apply_current_settings(self): self.update()

    def _show_toast(self, title, message, icon="🔔", app=None, body="", color=None, force=False):
        try:
            if self._dl_cur and not force:      # идёт загрузка — она в приоритете, остальное ждёт
                self._pending_toasts.append((title, message, icon, app, body, color)); del self._pending_toasts[:-3]; return
            if app:
                text = (title or app).replace("\n", " ").strip(); sub = str(body or "").replace("\n", " ").strip()
            else:
                text = (f"{title} {message}".strip() if title != icon else message).replace("\n", " ").strip(); sub = ""
            dur = 4300 if app else 3500
            self._notify = {"icon": icon, "text": text, "sub": sub, "app": app or "", "color": color,
                            "end": time.monotonic() + dur / 1000.0, "start": time.monotonic(), "out_start": 0.0, "force": force}
            self._notify_timer.start(dur)
            self._shake_start = time.monotonic()
            self._shake_amp = 6.5 if self.settings.value("notif_vibe", True, type=bool) else 0.0
            if not self._user_hidden:
                if not self.isVisible() or self._show_target < 1.0: self._notify_wake = True
                self._set_show_target(1.0); self._keep_on_top(); self._last_hover = time.monotonic()
            self._wake(); self.update()
            if self._wb("fx_edge_pulse", True): self._glow_overlay.pulse(color if color is not None else ACCENT, self._scr_geom())
        except Exception as e: log_error(f"toast: {e}")

    @staticmethod
    def _fmt_size(b):
        b = float(b)
        if b < 1024: return f"{b:.0f} Б"
        if b < 1048576: return f"{b / 1024:.0f} КБ"
        if b < 1073741824: return f"{b / 1048576:.1f} МБ"
        return f"{b / 1073741824:.2f} ГБ"

    @staticmethod
    def _fmt_eta(s):
        if s < 60: return f"{max(1, s):.0f} с"
        if s < 3600: return f"{s / 60:.0f} мин"
        return f"{int(s // 3600)} ч {int(s % 3600 // 60)} м"

    @staticmethod
    def _file_emoji(name):
        e = os.path.splitext(name.lower())[1]
        if e in (".zip", ".rar", ".7z", ".tar", ".gz"): return "📦"
        if e in (".mp4", ".mkv", ".avi", ".mov", ".webm"): return "🎬"
        if e in (".mp3", ".wav", ".flac", ".ogg", ".m4a"): return "🎵"
        if e in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"): return "🖼"
        if e in (".exe", ".msi"): return "⚙"
        if e in (".iso", ".img"): return "💿"
        if e in (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"): return "📄"
        return "⬇"

    def _on_dl_finished(self, name, size, path):
        try:
            if self._wb("dl_notify", True):
                self._show_toast(name, "", self._file_emoji(name), app="Файл скачан", body=self._fmt_size(size), color=QColor(80, 220, 150), force=True)
                QTimer.singleShot(4800, self._flush_pending)
            else: QTimer.singleShot(400, self._flush_pending)
        except Exception as e: log_error(f"dl finished: {e}")

    def _flush_pending(self):
        if self._dl_cur or not self._pending_toasts: return
        t = self._pending_toasts[-1]; self._pending_toasts = []
        self._show_toast(*t)

    @staticmethod
    def _friendly_app(name):
        low = name.lower()
        for key, nm, _ic, _c in MESSENGERS:
            if key in low: return nm
        for key, nm in (("chrome", "Chrome"), ("msedge", "Edge"), ("firefox", "Firefox"), ("opera", "Opera"), ("brave", "Brave"), ("yandex", "Яндекс"), ("obs", "OBS"), ("zoom", "Zoom")):
            if key in low: return nm
        return name.split("_")[0].split(".")[-1] or name

    def _live_activities(self):
        a = self._priv.active; out = []
        if not a: return out
        comm = ("telegram", "whatsapp", "discord", "viber", "slack", "teams", "skype", "zoom", "chrome", "msedge", "firefox", "opera", "brave", "yandex", "vk", "max", "signal", "meet", "webex", "element")
        if "rec" in a and self._wb("la_rec", True):
            app, st = a["rec"]; out.append({"kind": "rec", "title": "Запись экрана", "app": self._friendly_app(app), "start": st, "icon": "⏺", "color": QColor(255, 70, 80)})
        if "mic" in a and self._wb("la_call", True):
            app, st = a["mic"]; cam = "cam" in a; is_call = any(k in app.lower() for k in comm)
            out.append({"kind": "call", "title": ("Видеозвонок" if cam else "Идёт звонок") if is_call else "Микрофон используется", "app": self._friendly_app(app), "start": st,
                        "icon": "📹" if cam else "📞", "color": QColor(70, 220, 130)})
        elif "cam" in a and self._wb("la_cam", True):
            app, st = a["cam"]; out.append({"kind": "cam", "title": "Камера включена", "app": self._friendly_app(app), "start": st, "icon": "📷", "color": QColor(70, 220, 130)})
        return out

    def _draw_compact_live(self, p, iw, ih):
        lst = self._live_cur
        if not lst: return False
        AL = Qt.AlignmentFlag; a = lst[0]; t = time.monotonic(); col = a["color"]; n = len(lst)
        cx, cy = 26.0, ih / 2; pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        g = QRadialGradient(QPointF(cx, cy), 20); g.setColorAt(0, rgba(col, int(80 + 100 * pulse))); g.setColorAt(1, rgba(col, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(g); p.drawEllipse(QPointF(cx, cy), 20, 20)
        if a["kind"] == "rec":
            p.setBrush(rgba(col, int(60 + 80 * pulse))); p.drawEllipse(QPointF(cx, cy), 10 + 2 * pulse, 10 + 2 * pulse)
            p.setBrush(col); p.drawEllipse(QPointF(cx, cy), 6.5, 6.5)
        else:
            bg_ = QLinearGradient(cx, cy - 12, cx, cy + 12); bg_.setColorAt(0, col.lighter(125)); bg_.setColorAt(1, col.darker(115))
            p.setBrush(bg_); p.drawEllipse(QPointF(cx, cy), 12, 12)
            p.setFont(font(11, family="Segoe UI Emoji")); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(cx - 12, cy - 12, 24, 24), AL.AlignCenter, a["icon"])
        secs = max(0, int(time.time() - a["start"])); tm = f"{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}" if secs >= 3600 else f"{secs // 60:02d}:{secs % 60:02d}"
        rw = 66.0 if n == 1 else 92.0; tx = cx + 24; tw = iw - tx - rw - 6
        if tw > 30:
            f1 = font(11, QFont.Weight.Bold); p.setFont(f1); p.setPen(QColor(255, 255, 255, 245))
            p.drawText(QRectF(tx, 3, tw, 17), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(f1).elidedText(a["title"], Qt.TextElideMode.ElideRight, int(tw)))
            f2 = font(9); p.setFont(f2); p.setPen(QColor(255, 255, 255, 150))
            p.drawText(QRectF(tx, 20, tw, 16), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(f2).elidedText(f"{a['app']}  ·  {tm}", Qt.TextElideMode.ElideRight, int(tw)))
        rx = iw - rw - 10
        if a["kind"] == "rec":
            r_ = QRectF(rx + rw - 40, cy - 9, 40, 18); p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(col, 235)); p.drawRoundedRect(r_, 9, 9)
            p.setFont(font(8, QFont.Weight.Bold, spacing=0.8)); p.setPen(QColor(255, 255, 255)); p.drawText(r_, AL.AlignCenter, "REC")
        else:
            lvl = min(1.0, (getattr(self._audio, "level", 0.0) if self._audio else 0.0) * 3.0); p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(col, 235))
            for i in range(5):
                bh = 4.0 + 13.0 * (0.25 + 0.75 * lvl) * abs(math.sin(t * 7.0 + i * 1.3)); p.drawRoundedRect(QRectF(rx + rw - 36 + i * 7.5, cy - bh / 2, 3.6, bh), 1.8, 1.8)
        if n > 1:
            p.setFont(font(9, QFont.Weight.Bold)); p.setPen(rgba(col.lighter(130), 240)); p.drawText(QRectF(rx, 0, 26, ih), AL.AlignLeft | AL.AlignVCenter, f"+{n - 1}")
        return True

    def _on_audio_dev(self, name):
        try:
            if not self._wb("la_audio", True): return
            nm = name or "Другое устройство"; low = nm.lower()
            hp = any(k in low for k in ("науш", "headphone", "headset", "airpods", "buds", "гарнитур", "bluetooth"))
            self._show_toast("Наушники подключены" if hp else "Вывод звука изменён", "", "🎧" if hp else "🔊", app="Звук", body=nm, color=QColor(120, 170, 255))
        except Exception as e: log_error(f"audio dev: {e}")

    def _on_wifi(self, ssid, ok):
        try:
            if not self._wb("la_wifi", True): return
            if ok: self._show_toast(ssid, "", "📶", app="Wi‑Fi подключён", body="", color=QColor(90, 200, 255))
            else: self._show_toast("Отключено", "", "📶", app="Wi‑Fi", body="", color=QColor(160, 170, 190))
        except Exception as e: log_error(f"wifi: {e}")

    def _check_battery_events(self):
        b = self.battery
        if not b: return
        pct, plug = b
        if self._wb("la_charge", True):
            if self._batt_prev is not None and bool(plug) != bool(self._batt_prev):
                if plug: self._show_toast(f"Подключено · {pct:.0f}%", "", "⚡", app="Зарядка", body="Идёт зарядка", color=QColor(90, 225, 130))
                else: self._show_toast(f"Отключено · {pct:.0f}%", "", "🔋", app="Зарядка", body="Работа от батареи", color=QColor(255, 190, 90))
            if not plug and pct <= 15 and not self._low_warned:
                self._low_warned = True; self._show_toast(f"Низкий заряд · {pct:.0f}%", "", "🪫", app="Батарея", body="Подключи зарядку", color=QColor(255, 90, 90))
            if plug or pct > 20: self._low_warned = False
        self._batt_prev = plug

    def _on_sys_notif(self, app, title, body, icon, color):
        try:
            c = QColor(*color) if (color and self.settings.value("fx_notify_color", True, type=bool)) else None
            self._show_toast(title, "", icon, app=app, body=body, color=c)
        except Exception as e: log_error(f"sys notif: {e}")

    def _clear_notification(self):
        if not self._notify: return
        self._notify["out_start"] = time.monotonic()
        QTimer.singleShot(280, self._finish_clear_notification)

    def _finish_clear_notification(self):
        self._notify = None
        if self._notify_wake:
            self._notify_wake = False
            QTimer.singleShot(300, self._maybe_autohide_now)
        self.update()

    def _maybe_autohide_now(self):
        try:
            if self._notify or self.expanded: return
            if not self.desktop_only: return
            if self._mouse_over_island(): return
            self._check_visibility()
        except: pass

    def _make_icon(self):
        pm = QPixmap(64,64); pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath(); path.addRoundedRect(QRectF(3,3,58,58),18,18)
        g = QLinearGradient(0,0,0,64); g.setColorAt(0,QColor(40,42,54)); g.setColorAt(1,QColor(12,12,18))
        p.fillPath(path, g)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,240))
        p.drawEllipse(QPointF(24,32), 6, 7); p.drawEllipse(QPointF(40,32), 6, 7)
        p.setBrush(QColor(15,20,30)); p.drawEllipse(QPointF(24,32), 2.5, 3); p.drawEllipse(QPointF(40,32), 2.5, 3)
        p.end()
        return QIcon(pm)

    def _build_tray(self):
        self.menu = QMenu()
        self.menu.addAction("Показать / скрыть островок", self.toggle_visible)
        self.menu.addSeparator()
        self.menu.addAction("Настройки", self._open_settings)
        self.menu.addAction("Проверить обновления", self._check_updates)
        self._update_action = self.menu.addAction("Установить обновление", self._install_update)
        self._update_action.setEnabled(False)
        self.menu.addAction("Вернуть остров наверх", lambda: self.set_edge("top", 0.5))
        self.menu.addAction("Следующий монитор", self.next_screen)
        self.menu.addSeparator()
        self.act_fs = self.menu.addAction("Скрывать при открытых окнах")
        self.act_fs.setCheckable(True); self.act_fs.setChecked(self.desktop_only)
        self.act_fs.toggled.connect(self._set_desktop_only)
        self.menu.addSeparator()
        self.menu.addAction("Открыть журнал", self._open_log)
        self.menu.addAction("Открыть папку", self._open_folder)
        self.menu.addSeparator()
        self.menu.addAction("Выход", QApplication.instance().quit)
        self.tray = QSystemTrayIcon(self._make_icon(), self)
        self.tray.setContextMenu(self.menu); self.tray.activated.connect(self._tray_activated)
        self.tray.setToolTip("Dynamic Island"); self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.toggle_visible()

    def _check_updates(self):
        if self._settings_window is not None and hasattr(self._settings_window, "update_status"):
            self._settings_window.update_status.setText("Ищу новую версию на сервере обновлений…")
            self._settings_window.update_detail.setText("Подключение к GitHub Releases")
            self._settings_window.update_progress.setValue(0)
            self._settings_window.update_progress.setFormat("Проверка…")
            self._settings_window.update_check_btn.setEnabled(False)
        self._show_toast("Обновления", "Проверяю новую версию…", "⬇", force=True)
        self._update_manager.check(manual=True)

    def _on_update_progress(self, percent, received, total, stage):
        try:
            w = self._settings_window
            if w is not None and hasattr(w, "update_progress"):
                w.update_progress.setValue(int(percent))
                w.update_progress.setFormat(f"{int(percent)}%")
                if total > 0:
                    w.update_detail.setText(f"{stage} · {received/1048576:.1f} / {total/1048576:.1f} МБ")
                else:
                    w.update_detail.setText(stage)
        except Exception as e:
            log_error(f"update progress UI: {e}")

    def _on_update_checked(self, result):
        try:
            w = self._settings_window
            if w is not None and hasattr(w, "update_status"):
                w.update_check_btn.setEnabled(True)
                w.update_progress.setValue(0)
                w.update_progress.setFormat("Ожидание загрузки · %p%")
            if not result.get("ok"):
                if w is not None and hasattr(w, "update_status"):
                    w.update_status.setText("Не удалось проверить обновления")
                    w.update_detail.setText(str(result.get("error", "Проверь подключение к интернету")))
                if result.get("manual"):
                    self._show_toast("Проверка обновлений", str(result.get("error", "Не удалось проверить")), "⚠", force=True)
                return
            if result.get("available"):
                self._update_info = result
                if w is not None and hasattr(w, "update_status"):
                    w.update_status.setText(f"Доступна новая версия: {result['version']}")
                    w.update_detail.setText("Новая версия готова к загрузке. Нажми «Скачать и установить».")
                    w.update_install_btn.setEnabled(True)
                    w.update_progress.setValue(0)
                if self._update_action:
                    self._update_action.setText(f"Скачать и установить v{result['version']}")
                    self._update_action.setEnabled(True)
                self._show_toast("Доступно обновление", f"Версия {result['version']} · открой меню в трее", "⬇", force=True)
            elif result.get("manual"):
                if w is not None and hasattr(w, "update_status"):
                    w.update_status.setText("У тебя установлена последняя версия")
                    w.update_detail.setText(f"DynamicIsland {CURRENT_VERSION} · обновлений пока нет")
                    w.update_install_btn.setEnabled(False)
                self._show_toast("Обновления", f"У тебя последняя версия ({CURRENT_VERSION})", "✓", force=True)
        except Exception as e:
            log_error(f"update checked: {e}")

    def _install_update(self):
        info = self._update_info
        if not info or not info.get("url"):
            self._check_updates()
            return
        if self._settings_window is not None and hasattr(self._settings_window, "update_status"):
            self._settings_window.update_status.setText(f"Загружаю обновление {info.get('version', '')}…")
            self._settings_window.update_detail.setText("Не закрывай приложение во время загрузки.")
            self._settings_window.update_install_btn.setEnabled(False)
            self._settings_window.update_check_btn.setEnabled(False)
        self._show_toast("Обновление", "Скачиваю пакет. Остров перезапустится автоматически.", "⬇", force=True)
        self._update_manager.install(info["url"], os.path.abspath(__file__))

    def _on_update_installed(self, message):
        try:
            if self._settings_window is not None and hasattr(self._settings_window, "update_status"):
                self._settings_window.update_status.setText(message)
                self._settings_window.update_detail.setText("DynamicIsland будет перезапущен установщиком." if "Ошибка" not in message else "Попробуй повторить проверку позже.")
            self._show_toast("Обновление", message, "⬇" if "Ошибка" not in message else "⚠", force=True)
            if "Ошибка" not in message:
                QTimer.singleShot(650, QApplication.instance().quit)
        except Exception as e:
            log_error(f"update install signal: {e}")

    def _open_log(self):
        if self._log_window is None: self._log_window = LogWindow()
        self._log_window.show(); self._log_window.raise_(); self._log_window.setFocus()

    def _open_settings(self):
        try:
            if self._settings_window is None: self._settings_window = SettingsWindow(self)
            self._settings_window.show(); self._settings_window.raise_(); self._settings_window.setFocus()
        except Exception as e: log_error(f"_open_settings: {e}\n{traceback.format_exc()}")

    def _open_folder(self):
        try: os.startfile(os.path.dirname(os.path.abspath(__file__)))
        except: pass

    def _set_desktop_only(self, on):
        self.desktop_only = bool(on); self.settings.setValue("desktop_only", bool(on))
        if on and not self._user_hidden: self._check_visibility()

    def toggle_visible(self):
        if self._user_hidden or self._show_target <= 0.0:
            self._user_hidden = False; self._set_show_target(1.0); self._keep_on_top()
        else:
            self._user_hidden = True; self._set_show_target(0.0)

    def _keep_on_top(self):
        try: user32.SetWindowPos(int(self.winId()), HWND_TOPMOST, 0,0,0,0, SWP_FLAGS)
        except: pass

    def _mouse_in_reveal_zone(self):
        try:
            if self._free is not None: return False
            gp = QCursor.pos(); zh = int(self.settings.value("reveal_height", 15)); s = self._scr_geom(); e = self._edge
            if e == "top": return abs(gp.x() - self._cx) <= 250 and s.y() <= gp.y() <= s.y() + zh
            if e == "bottom": return abs(gp.x() - self._cx) <= 250 and s.y() + s.height() - zh <= gp.y() <= s.y() + s.height()
            if e == "left": return abs(gp.y() - self._cy) <= 250 and s.x() <= gp.x() <= s.x() + zh
            return abs(gp.y() - self._cy) <= 250 and s.x() + s.width() - zh <= gp.x() <= s.x() + s.width()
        except Exception: return False

    def _island_screen_rect(self):
        g = self.geometry(); ox, oy = self._origin()
        return QRectF(g.x() + ox - 4, g.y() + oy - 2, self._iw + 8, self._ih + 4)

    def _compact_screen_rect(self):
        s = self._scr_geom(); e = self._edge; gap = self.EDGE_GAP; cw, ch = self.CW, self.CH
        if e == "top": l = self._cx - cw / 2; t = s.y() + TOP
        elif e == "bottom": l = self._cx - cw / 2; t = s.y() + s.height() - ch
        elif e == "left": l = s.x() + gap; t = self._cy - ch / 2
        else: l = s.x() + s.width() - gap - cw; t = self._cy - ch / 2
        return (int(l) + 3, int(t) + 3, int(l) + cw - 3, int(t) + ch - 3)

    def _mouse_over_island(self):
        try:
            if not self.isVisible() or self._iw < 4: return False
            gp = QCursor.pos(); return self._island_screen_rect().contains(QPointF(gp.x(), gp.y()))
        except: return False

    def _check_reveal(self):
        """Курсор у верхнего края → у границы «накапливается капля», потом она падает и растёт в остров."""
        try:
            if self._user_hidden: return
            now = time.monotonic()
            if self._mouse_over_island():
                self._last_hover = now
                if self._show_target < 1.0: self._set_show_target(1.0)
                return
            reveal_enabled = bool(self.settings.value("reveal_enabled", True, type=bool))
            if reveal_enabled and self._mouse_in_reveal_zone():
                self._last_hover = now
                if self._show_target < 1.0:
                    if self._reveal_started == 0.0 and self._show < 0.3:
                        self._reveal_started = now; self._set_show_target(self.MINI)
                    elif self._reveal_started == 0.0 or now - self._reveal_started >= 0.28:
                        self._set_show_target(1.0)
            else:
                self._reveal_started = 0.0
        except Exception: pass

    def _check_visibility(self):
        if self._user_hidden:
            self._set_show_target(0.0); return
        now = time.monotonic()
        if now < self._grace_until: return
        if self._notify or self._notify_wake or self.expanded or self._dl_cur or self._live_cur or self._alarm:
            self._set_show_target(1.0); self._keep_on_top(); self._last_hover = now; return
        autohide_enabled = bool(self.settings.value("autohide_enabled", True, type=bool))
        autohide_delay = int(self.settings.value("autohide_delay", 3))
        mini = bool(self.settings.value("anim_mini", True, type=bool))
        if not self.desktop_only:
            self._set_show_target(1.0); self._keep_on_top(); self._last_hover = now; return
        is_covered = is_window_overlapping(int(self.winId()), self._compact_screen_rect())
        if not is_covered:
            self._hide_streak = 0; self._set_show_target(1.0); self._keep_on_top(); self._last_hover = now; return
        if not autohide_enabled:
            self._hide_streak = 0; self._set_show_target(1.0); self._keep_on_top(); return
        if now - self._last_hover < autohide_delay:
            self._hide_streak = 0; self._set_show_target(1.0); self._keep_on_top()
        else:
            self._hide_streak += 1
            if self._hide_streak >= 2 and not self.expanded:
                self._set_show_target(self.MINI if mini else 0.0)   # остров втягивается в миниатюру-каплю

    def focusOutEvent(self, ev):
        # Дочерние поля заметки получают фокус отдельно от родительского QWidget.
        # Qt вызывает focusOutEvent у островка при переходе в QLineEdit/QTextEdit;
        # это внутренний переход, а не клик вне приложения. Не сворачиваем островок,
        # пока встроенный редактор открыт, и проверяем остальные дочерние виджеты.
        note_editor = getattr(self, "_note_editor", None)
        if note_editor is not None and note_editor.isVisible():
            super().focusOutEvent(ev); return
        fw = QApplication.focusWidget()
        if fw is not None and (fw is self or self.isAncestorOf(fw)):
            super().focusOutEvent(ev); return

        # Если мы вводим текст в заметки или таймер — не закрываем
        if self._new_note_active or self._reminder_active or self._timer_active_field:
            super().focusOutEvent(ev); return
            
        # ⬇️ НОВЫЙ БЛОК: Если открыт ИИ и мышь внутри островка, не сворачиваем ⬇️
        if self._ai_view is not None and self._ai_view.isVisible():
            if self._mouse_over_island():
                super().focusOutEvent(ev); return
        # ⬆️ КОНЕЦ НОВОГО БЛОКА ⬆️

        if self.expanded: self.toggle_expand()
        super().focusOutEvent(ev)

    def _sample(self):
        self.v["cpu"] = psutil.cpu_percent()
        vm = psutil.virtual_memory(); self.v["mem"] = vm.percent
        self.mem_used = vm.used/1024**3; self.mem_total = vm.total/1024**3
        try: self.v["disk"] = psutil.disk_usage("C:\\").percent
        except: self.v["disk"] = 0.0
        try:
            b = psutil.sensors_battery(); self.battery = (b.percent, b.power_plugged) if b else None
        except: self.battery = None
        try:
            cur = psutil.net_io_counters(); t = time.monotonic(); dt = max(t-self._net_time, 0.001)
            self.net_down = (cur.bytes_recv-self._net_last.bytes_recv)/dt
            self.net_up = (cur.bytes_sent-self._net_last.bytes_sent)/dt
            self._net_last, self._net_time = cur, t
        except: pass

    def _tick(self):
        self.now = datetime.datetime.now(); self._tick_n += 1
        try: self._theme_step()
        except Exception as e: log_error(f"theme: {e}")
        if self._tick_n % 5 == 0:
            self._sample()
            self._cpu_hist.append(self.v["cpu"]); del self._cpu_hist[:-48]
            self._mixer.want = bool(self.expanded and self.current_page == "mixer")
            self._check_battery_events()
            self._gpu.want = bool((self._wb("compact_stats", False) and self._wb("cs_gpu", True)) or (self.expanded and self.current_page == "system" and self._wb("sys_gpu", True)) or any(w.kind == "system" for w in self._widgets))
            if HAS_PYCAW:
                v = get_volume()
                if v is not None and not self._vol_drag: self._volume = v
            for k in self.d: self.d[k] += (self.v[k]-self.d[k])*0.35
        if self.t_running:
            left = self.t_end - time.monotonic()
            if left <= 0: self._timer_done()
            else: self.t_left = left
        _nt = time.monotonic(); _dtp = max(0.0, min(1.0, _nt - getattr(self, "_pos_t", _nt))); self._pos_t = _nt
        if self.media["active"] and self.media["playing"] and not self._seek_drag:      # раньше тут стояло +0.2 за тик в 0.15 с — отсюда текст «убегал вперёд»
            self.media["position"] = min(self.media["position"] + _dtp, self.media["duration"])
        now_t = time.monotonic()
        if now_t > self._next_blink and now_t > self._blink_until:
            self._blink_start = now_t; self._blink_until = now_t + 0.18
            self._next_blink = now_t + 2.5 + random.random() * 4.0
        today_key = self.now.strftime("%Y-%m-%d")
        self._check_reminders()
        try:
            if self.media.get("active") and self.media.get("playing"):
                title = self.media.get("title", "")
                if title and title != self._evt_last_title:
                    self._evt_last_title = title
                    if self.settings.value("notif_music", True, type=bool):
                        self._show_toast("", title[:30], "🎵")
        except: pass
        try:
            if abs(self._volume - self._evt_last_vol) > 0.05:
                self._evt_last_vol = self._volume
                if self.settings.value("notif_vol", True, type=bool) and not self._vol_drag:
                    if time.monotonic() - self._evt_vol_cooldown > 2.0:
                        self._evt_vol_cooldown = time.monotonic()
                        self._show_toast("", f"{int(self._volume*100)}%", "🔊")
        except: pass
        try:
            if self.battery:
                pct, plugged = self.battery
                if pct < 20 and not plugged and not self._evt_battery_shown:
                    self._evt_battery_shown = True
                    if self.settings.value("notif_battery", True, type=bool):
                        self._show_toast("", f"{pct:.0f}%", "🔋")
                elif plugged or pct > 25:
                    self._evt_battery_shown = False
        except: pass
        if self.isVisible(): self.update()

    def _on_media_changed(self, data):
        data = dict(data)
        img = data.pop("thumb_image", None)
        if img is not None:
            try: data["thumb"] = QPixmap.fromImage(img).scaled(240,240, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            except: data["thumb"] = None
            try:
                c = img.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).pixelColor(0, 0)
                h, sa, v, _ = c.getHsvF(); self._mcol = QColor.fromHsvF(max(h, 0), min(1.0, max(sa, 0.55) * 1.1), max(v, 0.85))
            except: pass
        new_pos = data.get("position")
        old_title = self.media.get("title", "")
        new_title = data.get("title", "")
        track_changed = new_title and new_title != old_title
        if new_pos is not None and not self._seek_drag and time.monotonic() >= self._seek_lock_until:
            if not track_changed and abs(new_pos - self._smtc_last_pos) < 0.1:
                data.pop("position", None)
            self._smtc_last_pos = new_pos
        self.media = {**self.media, **data}
        if self.isVisible(): self.update()

    def _on_weather_changed(self, data):
        self.weather = data; self._weather_loading = False
        if self.isVisible(): self.update()

    def _on_clipboard_changed(self):
        try:
            if self._clipboard.items and self.settings.value("notif_clipboard", False, type=bool):
                first = self._clipboard.items[0]
                if first.get("type") == "text":
                    preview = first["preview"][:24] + ("…" if len(first["preview"]) > 24 else "")
                    if preview: self._show_toast("", f"{preview}", "📋")
                else:
                    self._show_toast("", "Сохранено в буфер", "📋")
        except: pass
        if self.isVisible(): self.update()

    def _on_input_state_changed(self, kind, label):
        if not self.settings.value("notif_input_state", True, type=bool): return
        if kind == "caps": self._show_toast("Caps Lock", f"Заглавные буквы: {label}", "⇧", force=True)
        elif kind == "language": self._show_toast("Язык ввода", label, "🌐", force=True)

    def _on_notes_changed(self):
        if self.isVisible(): self.update()

    def _on_reminders_changed(self):
        if self.isVisible(): self.update()

    def _media_control(self, action, value=None):
        self._media_bridge.control(action, value)
        if action == "toggle": self.media["playing"] = not self.media["playing"]

    def _clipboard_copy(self, item):
        try:
            self._clipboard.to_clipboard(item)
            self._show_toast("", "Сохранено в буфер", "📋")
        except Exception as e:
            log_error(f"clipboard copy: {e}")

    # ─── Wi-Fi / Bluetooth без перехода в настройки Windows ───
    def _sys_info(self): self._wifi_info(); self._bt_state_only()
    def _bt_state_only(self): self.bt_state = radio_state("Bluetooth")

    def _wifi_info(self):
        self._wifi_on = radio_state("WiFi"); self._wifi_cur = ""
        for l in _netsh("wlan", "show", "interfaces").splitlines():
            s = l.strip()
            if re.match(r"^SSID\s*:", s): self._wifi_cur = s.split(":", 1)[1].strip(); break
        prof = set()
        for l in _netsh("wlan", "show", "profiles").splitlines():
            if ":" in l:
                k, v = l.split(":", 1)
                if v.strip() and ("rofile" in k or "рофил" in k): prof.add(v.strip())
        self._wifi_profiles = prof

    def _wifi_scan(self):
        nets = {}; cur = None
        for line in _netsh("wlan", "show", "networks", "mode=bssid").splitlines():
            s = line.strip(); m = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", s)
            if m:
                cur = {"ssid": m.group(1).strip(), "auth": "", "signal": "0%"}
                if cur["ssid"]: nets[cur["ssid"]] = cur
                else: cur = None
            elif cur and ":" in s:
                k, v = s.split(":", 1); k = k.lower(); v = v.strip()
                if "authentication" in k or "проверка подлинности" in k: cur["auth"] = v
                elif "signal" in k or "сигнал" in k:
                    try:
                        if int(v.rstrip("%")) > int(cur["signal"].rstrip("%")): cur["signal"] = v
                    except Exception: pass
        self.wifi_networks = sorted(nets.values(), key=lambda n: -int(n["signal"].rstrip("%") or 0))

    def _load_wifi_networks(self): self._bg(lambda: (self._wifi_info(), self._wifi_scan()))
    def _wifi_toggle(self): self._bg(lambda: (radio_toggle("WiFi"), time.sleep(1.5), self._wifi_info(), self._wifi_scan()))

    @staticmethod
    def _wifi_is_open(net): return net.get("auth", "").lower().startswith(("open", "откр"))

    def _wifi_click(self, net):
        if net["ssid"] == self._wifi_cur: return
        if net["ssid"] in self._wifi_profiles: self._wifi_connect(net)
        elif self._wifi_is_open(net): self._wifi_connect(net, "")
        else: self._wifi_pw_for = net; self._wifi_pw = ""; self._wifi_msg = ""; self.update()

    def _wifi_connect(self, net, pw=None):
        ssid = net["ssid"]
        def f():
            self._wifi_msg = f"Подключение к {ssid}…"; self._ext.ping.emit()
            if pw is not None:
                from xml.sax.saxutils import escape
                if pw == "": sec = "<authEncryption><authentication>open</authentication><encryption>none</encryption><useOneX>false</useOneX></authEncryption>"
                else:
                    a = "WPA3SAE" if "WPA3" in net.get("auth", "") else "WPA2PSK"
                    sec = (f"<authEncryption><authentication>{a}</authentication><encryption>AES</encryption><useOneX>false</useOneX></authEncryption>"
                           f"<sharedKey><keyType>passPhrase</keyType><protected>false</protected><keyMaterial>{escape(pw)}</keyMaterial></sharedKey>")
                s = escape(ssid)
                xml = (f'<?xml version="1.0"?><WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1"><name>{s}</name>'
                       f'<SSIDConfig><SSID><name>{s}</name></SSID></SSIDConfig><connectionType>ESS</connectionType><connectionMode>auto</connectionMode><MSM><security>{sec}</security></MSM></WLANProfile>')
                fn = os.path.join(os.environ.get("TEMP", "."), "island_wifi.xml")
                try:
                    with open(fn, "w", encoding="utf-8") as fh: fh.write(xml)
                    _netsh("wlan", "add", "profile", f"filename={fn}", "user=current")
                finally:
                    try: os.remove(fn)
                    except Exception: pass
            _netsh("wlan", "connect", f"name={ssid}", f"ssid={ssid}"); time.sleep(3.5); self._wifi_info()
            self._wifi_msg = "✓ Подключено" if self._wifi_cur == ssid else "Не удалось подключиться (проверьте пароль)"
        self._bg(f)

    def _wifi_key(self, ev):
        K = Qt.Key; k = ev.key(); t = ev.text()
        if k in (K.Key_Return, K.Key_Enter):
            net = self._wifi_pw_for; pw = self._wifi_pw; self._wifi_pw_for = None; self._wifi_pw = ""
            if net and pw: self._wifi_connect(net, pw)
            self.update(); return True
        if k == K.Key_Escape: self._wifi_pw_for = None; self._wifi_pw = ""; self.update(); return True
        if k == K.Key_Backspace: self._wifi_pw = self._wifi_pw[:-1]; self.update(); return True
        if t and t.isprintable(): self._wifi_pw += t; self.update(); return True
        return False

    def _bt_refresh(self):
        self.bt_state = radio_state("Bluetooth")
        out = _ps("Get-PnpDevice -Class Bluetooth -PresentOnly -ErrorAction SilentlyContinue | ?{$_.FriendlyName -notmatch 'Radio|Adapter|Enumerator|Generic|Microsoft|Transport|LE$|Protocol|Service'} | select -Expand FriendlyName -Unique")
        self._bt_devs = [l.strip() for l in out.splitlines() if l.strip()][:7]
    def _bt_toggle(self): self._bg(self._bt_refresh)
    def _bt_actual_toggle(self): self._bg(lambda: (radio_toggle("Bluetooth"), time.sleep(1.2), self._bt_refresh()))
    def _mute_toggle(self):
        user32.keybd_event(0xAD, 0, 0, 0); user32.keybd_event(0xAD, 0, 2, 0)

    def _restart_pc(self):
        try: subprocess.run(['shutdown','/r','/t','5'], shell=True)
        except: pass

    def _shutdown_pc(self):
        try: subprocess.run(['shutdown','/s','/t','5'], shell=True)
        except: pass

    def _sleep_pc(self):
        try: subprocess.run(['rundll32.exe','powrprof.dll,SetSuspendState','0,1,0'], shell=True)
        except: pass

    def _confirm(self, title, msg, action):
        try:
            self.hide()
            d = ConfirmDialog(None, title, msg); d.exec(); self.show()
            if d.result_ok: action()
        except: pass

    def _shot_area(self):
        self.hide(); QTimer.singleShot(200, self._show_selector)

    def _show_selector(self):
        self.sel = AreaSelector(); self.sel.finished.connect(self._on_area_shot); self.sel.show()

    def _on_area_shot(self, pixmap):
        try:
            path = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"); os.makedirs(path, exist_ok=True)
            pixmap.save(os.path.join(path, f"area_{datetime.datetime.now():%H%M%S}.png"))
            QGuiApplication.clipboard().setPixmap(pixmap)
            self.show(); self._show_toast("", "Сохранено в буфер", "📸")
        except Exception as e: log_error(f"area shot: {e}")

    def _shot_full(self):
        try:
            pix = QGuiApplication.primaryScreen().grabWindow(0)
            path = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"); os.makedirs(path, exist_ok=True)
            pix.save(os.path.join(path, f"full_{datetime.datetime.now():%H%M%S}.png"))
            QGuiApplication.clipboard().setPixmap(pix)
            self._show_toast("", "Сохранено в буфер", "📸")
        except Exception as e: log_error(f"full shot: {e}")

    def _scan_text(self):
        self.hide(); QTimer.singleShot(200, self._show_ocr_selector)

    def _show_ocr_selector(self):
        self._ocr_sel = AreaSelector()
        self._ocr_sel.finished.connect(self._on_ocr_area)
        self._ocr_sel.show()

    def _on_ocr_area(self, pixmap):
        self.show()
        tmp_path = os.path.join(os.environ.get("TEMP", "."), f"_ocr_{int(time.time() * 1000)}.png")
        try: pixmap.save(tmp_path)
        except Exception as e: log_error(f"ocr save: {e}"); return
        def work():
            text = ""
            if HAS_WINRT:
                try:
                    import asyncio
                    from winrt.windows.media.ocr import OcrEngine
                    from winrt.windows.graphics.imaging import BitmapDecoder
                    from winrt.windows.storage import StorageFile, FileAccessMode
                    from winrt.windows.globalization import Language
                    async def _run():
                        sf = await StorageFile.get_file_from_path_async(tmp_path)
                        stream = await sf.open_async(FileAccessMode.READ)
                        dec = await BitmapDecoder.create_async(stream)
                        sb = await dec.get_software_bitmap_async()
                        engine = (OcrEngine.try_create_from_language(Language("ru-RU")) or
                                  OcrEngine.try_create_from_language(Language("en-US")) or
                                  OcrEngine.try_create_from_user_profile_languages())
                        if engine is None: return ""
                        res = await engine.recognize_async(sb)
                        return "\n".join(line.text for line in res.lines)
                    loop = asyncio.new_event_loop()
                    try: text = loop.run_until_complete(_run())
                    finally: loop.close()
                except Exception as e: log_error(f"winrt ocr: {e}")
            if not text.strip():
                try:
                    import pytesseract
                    from PIL import Image
                    text = pytesseract.image_to_string(Image.open(tmp_path), lang="rus+eng")
                except Exception as e: log_error(f"tesseract: {e}")
            try: os.remove(tmp_path)
            except: pass
            self._ocr_result.emit(text)
        threading.Thread(target=work, daemon=True).start()

    def _ocr_done(self, text):
        if text and text.strip():
            QGuiApplication.clipboard().setText(text)
            self._show_toast("OCR", "Сохранено в буфер", "📝")
        else:
            self._show_toast("OCR", "Текст не найден (нужен winrt/pytesseract)", "📝")

    def _scan_qr(self):
        self.hide()
        QTimer.singleShot(260, self._do_qr_scan)

    def _do_qr_scan(self):
        try:
            pix = QGuiApplication.primaryScreen().grabWindow(0)
            img = pix.toImage()
        except Exception as e:
            log_error(f"qr grab: {e}"); self.show(); return
        self.show()
        def work():
            result = None
            try:
                import numpy as np
                from pyzbar.pyzbar import decode
                w, h = img.width(), img.height()
                fmt_img = img.convertToFormat(QImage.Format.Format_RGB888)
                bpl = fmt_img.bytesPerLine()
                ptr = fmt_img.constBits(); ptr.setsize(fmt_img.sizeInBytes())
                arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, bpl))[:, :w*3].reshape((h, w, 3))
                codes = decode(arr)
                if codes: result = codes[0].data.decode("utf-8", errors="replace")
            except ImportError:
                result = "__missing__"
            except Exception as ex:
                log_error(f"qr scan: {ex}")
            self._qr_result.emit(result if result is not None else "")
        threading.Thread(target=work, daemon=True).start()

    def _qr_done(self, data):
        if data == "__missing__":
            self._show_toast("QR", "pip install pyzbar pillow numpy", "🔳")
        elif data:
            QGuiApplication.clipboard().setText(data)
            preview = data if len(data) <= 30 else data[:29] + "…"
            self._show_toast("QR", preview, "🔳")
        else:
            self._show_toast("QR", "Код не найден", "🔳")

    def _pick_color(self):
        self.hide()
        self._pip_active = True
        self._pip_col = QColor(255, 255, 255)
        self._pip_overlay = QWidget()
        self._pip_overlay.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self._pip_overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._pip_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._pip_overlay.setFixedSize(140, 90)
        self._pip_overlay.show()
        def _update():
            if not self._pip_active: return
            pos = QCursor.pos()
            scr = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
            g = scr.geometry()
            try:
                c = scr.grabWindow(0, pos.x()-g.x(), pos.y()-g.y(), 1, 1).toImage().pixelColor(0, 0)
                self._pip_col = c
            except: pass
            self._pip_overlay.move(pos.x() + 22, pos.y() + 22)
            self._pip_overlay.update()
        def _paint_pip(_widget):
            p = QPainter(self._pip_overlay)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = self._pip_overlay.rect().adjusted(2, 2, -2, -2)
            path = QPainterPath(); path.addRoundedRect(QRectF(r), 14, 14)
            p.fillPath(path, QColor(20, 22, 32, 240))
            p.setPen(QPen(QColor(255, 255, 255, 60), 1)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            sw = QRectF(r.x()+10, r.y()+10, 60, r.height()-20)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(self._pip_col)
            p.drawRoundedRect(sw, 8, 8)
            p.setPen(QColor(255, 255, 255, 240)); p.setFont(font(12, QFont.Weight.DemiBold))
            p.drawText(QRectF(sw.right()+8, r.y(), 60, r.height()//2), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._pip_col.name().upper())
            p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 140))
            p.drawText(QRectF(sw.right()+8, r.center().y(), 60, r.height()//2), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "3 сек…")
        self._pip_overlay.paintEvent = _paint_pip
        self._pip_timer = QTimer(self)
        self._pip_timer.timeout.connect(_update)
        self._pip_timer.start(33)
        def _grab():
            if not self._pip_active: return
            self._pip_active = False
            self._pip_timer.stop()
            self._pip_overlay.close()
            QGuiApplication.clipboard().setText(self._pip_col.name().upper())
            self.show()
            self._show_toast(self._pip_col.name().upper(), "Сохранено в буфер", "🎨")
        QTimer.singleShot(3000, _grab)

    def _clean_text(self):
        cb = QGuiApplication.clipboard(); t = cb.text()
        if not t.strip(): self._show_toast("", "В буфере нет текста", "🧹"); return
        cb.setText(" ".join(t.split()) if "\n" not in t else "\n".join(l.strip() for l in t.splitlines() if l.strip()))
        self._show_toast("Чистый текст", "Форматирование убрано", "🧹")

    def _run_cmd(self): subprocess.Popen("cmd.exe", creationflags=subprocess.CREATE_NEW_CONSOLE)

    @staticmethod
    def _path_ok(path):
        pl = str(path).lower()
        return pl.startswith(("shell:", "ms-settings:")) or os.path.exists(path)

    @staticmethod
    def _dock_key(path):
        pl = str(path).lower()
        return pl if pl.startswith(("shell:", "ms-settings:")) else os.path.normcase(os.path.normpath(str(path)))

    def _dock_add(self, path, kind="app", name=None):
        """Единая точка добавления в док → (успех, сообщение). Не даёт переполнить панель и не плодит дубликаты."""
        import shutil
        path = str(path or "")
        if not path: return False, "Нечего добавлять"
        if not self._path_ok(path):
            found = shutil.which(path)
            if not found: return False, "Не удалось найти программу"
            path = found
        if len(self.dock) >= DOCK_MAX: return False, f"Док заполнен ({DOCK_MAX}) — удали значок правой кнопкой"
        k = self._dock_key(path)
        if any(self._dock_key(it.get("path", "")) == k for it in self.dock): return False, "Уже в доке"
        item = {"path": path, "type": kind}
        if name: item["name"] = str(name)
        self.dock.append(item); self._save_dock()
        return True, "Добавлено в док"

    def _ds_flash(self, msg, ok=True): self._ds_flash_msg = (msg, time.monotonic() + 2.4, ok); self.update()

    def _ds_add(self, name, path):
        ok, msg = self._dock_add(path, "app", name); self._ds_flash(("✓ " if ok else "⚠ ") + msg, ok)
        if ok and self._ds_add_mode: self._ds_reset()
        self.update()

    def _ds_add_selected(self):
        if not self._ds_res: self._ds_flash("⚠ Сначала введи название", False); return
        n, pth = self._ds_res[min(self._ds_sel, len(self._ds_res) - 1)]; self._ds_add(n, pth)

    def _ds_start_add_mode(self):
        self._ds_add_mode = True; self._ds_text = ""; self._ds_res = []; self._ds_focus()

    def _add_dock_item(self):
        if len(self.dock) >= DOCK_MAX: self._ds_flash(f"⚠ Док заполнен ({DOCK_MAX})", False); return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(0,205,255,80)}")
        menu.addAction("🔎 Найти приложение и добавить", self._ds_start_add_mode)
        menu.addSeparator()
        menu.addAction("📁 Папка", lambda: self._add_dock_path("folder"))
        menu.addAction("📄 Файл", lambda: self._add_dock_path("file"))
        menu.addAction("🚀 Программа", lambda: self._add_dock_path("app"))
        menu.exec(QCursor.pos())

    def _add_dock_path(self, kind):
        if kind == "folder": p = QFileDialog.getExistingDirectory(self, "Папка", "C:\\")
        elif kind == "file": p, _ = QFileDialog.getOpenFileName(self, "Файл", "C:\\", "Все файлы (*.*)")
        else: p, _ = QFileDialog.getOpenFileName(self, "Программа", "C:\\", "*.exe")
        if p:
            ok, msg = self._dock_add(p, kind); self._ds_flash(("✓ " if ok else "⚠ ") + msg, ok)

    def _remove_dock_item(self, idx):
        if 0 <= idx < len(self.dock): self.dock.pop(idx); self._save_dock()

    def _save_dock(self):
        try: self.settings.setValue("dock_items", json.dumps(self.dock, ensure_ascii=False))
        except: pass
        self.update()

    def _launch(self, path):
        try: os.startfile(path)
        except:
            try: subprocess.Popen([path])
            except Exception as e: log_error(f"launch: {e}")

    def _activate_note_input(self):
        self.raise_(); self.activateWindow()
        self._open_note_editor(-1)

    def _add_note(self, text):
        if text.strip():
            if self._edit_note_idx >= 0: self._notes.update(self._edit_note_idx, text)
            else: self._notes.add(text)
            self._new_note_text = ""; self._new_note_active = False; self._edit_note_idx = -1
            self.update()

    def _reminder_focus(self, field):
        self._reminder_active = True; self._reminder_field = field
        self.raise_(); self.activateWindow(); self.setFocus(Qt.FocusReason.MouseFocusReason); self.update()

    def _remove_reminder_id(self, rid): self._reminders.remove_id(rid); self.update()

    def _activate_reminder_input(self):
        self._reminder_active = True; self._reminder_field = "text"
        self._reminder_text = ""; self._reminder_time = ""
        self.raise_(); self.activateWindow(); self.setFocus(Qt.FocusReason.MouseFocusReason)
        self.update()

    def _save_reminder(self):
        date_key = self._cal_selected.strftime("%Y-%m-%d")
        it = self._reminders.add(date_key, self._reminder_time, self._reminder_text)
        if it is None and self._reminder_text.strip():        # неверное время — подсказываем, текст не теряем
            self._reminder_field = "time"; self._reminder_time = ""; self.update(); return
        self._reminder_active = False; self._reminder_text = ""; self._reminder_time = ""; self.update()

    def _timer_toggle(self):
        if self.t_running: self.t_left = max(0.0, self.t_end-time.monotonic()); self.t_running = False
        else:
            if self.t_left <= 0: self.t_left = float(self.t_total)
            self.t_end = time.monotonic()+self.t_left; self.t_running = True

    def _timer_reset(self): self.t_running = False; self.t_left = float(self.t_total)

    def _set_preset(self, i):
        self.preset = i
        self.t_total = self.TIMER_PRESETS[i] * 60
        self.t_running = False
        self.t_left = float(self.t_total)
        self._timer_custom_mode = False
        self._timer_h_input = ""
        self._timer_m_input = ""
        self._timer_s_input = ""
        self._timer_active_field = None

    def _timer_done(self):
        self.t_running = False; self.t_left = 0.0
        if self.settings.value("notif_timer", True, type=bool):
            self._alarm = {"start": time.monotonic(), "next": 0.0}
            self._user_hidden = False
            if self.expanded: self.toggle_expand()
            self._set_show_target(1.0); self._keep_on_top(); self._wake()

    def _check_reminders(self):
        """Срабатывание напоминаний в назначенную дату и время: остров трясётся и ждёт подтверждения («Готово» или «+10 мин»)."""
        nt = time.monotonic()
        if nt - getattr(self, "_rem_chk", 0.0) < 1.0: return
        self._rem_chk = nt
        try: due = self._reminders.due(datetime.datetime.now())
        except Exception as e: log_error(f"reminders due: {e}"); return
        for it in due:
            self._reminders.mark_fired(it["id"])
            if not self._wb("rem_alert", True): continue
            al = {"kind": "reminder", "rid": it["id"], "title": "Напоминание" + (f" · {it['time']}" if it.get("time") else ""), "sub": it["text"],
                  "stop": "Готово", "snooze_label": "+10 мин", "icon": "🔔", "start": time.monotonic(), "next": 0.0}
            if self._alarm is None:
                self._alarm = al; self._user_hidden = False
                if self.expanded: self.toggle_expand()
                self._set_show_target(1.0); self._keep_on_top(); self._wake()
            else: self._alarm_queue.append(al)

    def _alarm_step(self):
        a = self._alarm; now = time.monotonic()
        if a is not None and now >= a["next"]:
            a["next"] = now + 1.4; self._shake_start = now; self._shake_amp = 7.5
            if self._wb("fx_edge_pulse", True): self._glow_overlay.pulse(QColor(255, 150, 70), self._scr_geom())
            try: ctypes.windll.user32.MessageBeep(0x30)
            except Exception: pass

    def _alarm_stop(self):
        self._alarm = None; self._shake_start = 0.0; self._alarm_rects = {}
        if self._alarm_queue: self._alarm = self._alarm_queue.pop(0); self._alarm["next"] = 0.0
        self.update()

    def _alarm_snooze(self):
        a = self._alarm
        if a and a.get("kind") == "reminder": self._reminders.snooze(a["rid"], 10)
        else: self.t_total = 300; self.t_end = time.monotonic() + 300; self.t_left = 300.0; self.t_running = True
        self._alarm_stop()

    def _draw_compact_alarm(self, p, iw, ih):
        if not self._alarm: return False
        AL = Qt.AlignmentFlag; t = time.monotonic(); pulse = 0.5 + 0.5 * math.sin(t * 8.0); col = QColor(255, 150, 70)
        g = QLinearGradient(0, 0, iw, 0); g.setColorAt(0, rgba(col, int(50 + 60 * pulse))); g.setColorAt(1, rgba(col, int(10 + 24 * pulse)))
        p.setPen(Qt.PenStyle.NoPen); p.fillRect(QRectF(0, 0, iw, ih), g)
        cx, cy = 26.0, ih / 2
        for i in range(2):
            ph = (t * 1.4 + i * 0.5) % 1.0; p.setPen(QPen(rgba(col, int((1 - ph) * 150)), 2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(QPointF(cx, cy), 12 + ph * 22, 12 + ph * 22)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(col); p.drawEllipse(QPointF(cx, cy), 12, 12)
        p.setFont(font(12, family="Segoe UI Emoji")); p.setPen(QColor(20, 12, 4)); p.drawText(QRectF(cx - 12, cy - 12, 24, 24), AL.AlignCenter, self._alarm.get("icon", "⏱"))
        tx = cx + 24; tw = iw - tx - 186
        if tw > 40:
            p.setFont(font(12, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(tx, 3, tw, 18), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(self._alarm.get("title", "Таймер завершён"), Qt.TextElideMode.ElideRight, int(tw)))
            p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 170)); p.drawText(QRectF(tx, 21, tw, 15), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(self._alarm.get("sub", "Подтверди, чтобы выключить"), Qt.TextElideMode.ElideRight, int(tw)))
        stop = QRectF(iw - 170, (ih - 26) / 2, 98, 26); sn = QRectF(iw - 66, (ih - 26) / 2, 54, 26)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(col); p.drawRoundedRect(stop, 13, 13)
        p.setFont(font(10, QFont.Weight.Bold)); p.setPen(QColor(28, 14, 2)); p.drawText(stop, AL.AlignCenter, self._alarm.get("stop", "Выключить"))
        p.setPen(QPen(QColor(255, 255, 255, 90), 1)); p.setBrush(QColor(255, 255, 255, 18)); p.drawRoundedRect(sn, 13, 13)
        p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(sn, AL.AlignCenter, self._alarm.get("snooze_label", "+5 мин"))
        self._alarm_rects = {"stop": stop, "snooze": sn}
        return True

    def _activate_timer_field(self, field):
        self._timer_active_field = field
        self._timer_custom_mode = True
        total = int(self.t_total)
        h, m, s = total // 3600, (total % 3600) // 60, total % 60
        if not (self._timer_h_input or self._timer_m_input or self._timer_s_input):
            self._timer_h_input = f"{h:02d}"
            self._timer_m_input = f"{m:02d}"
            self._timer_s_input = f"{s:02d}"
        self._timer_field_fresh = True
        self.raise_(); self.activateWindow(); self.setFocus()
        self.update()

    def _apply_custom_timer(self):
        try:
            h = int(self._timer_h_input or 0)
            m = int(self._timer_m_input or 0)
            s = int(self._timer_s_input or 0)
            total = h * 3600 + m * 60 + s
            if total > 0:
                self.t_total = total
                self.t_running = False
                self.t_left = float(total)
                self.preset = -1
                self._show_toast("", f"⏱ {fmt_mmss(total)}", "⏱")
        except Exception as e:
            log_error(f"custom timer: {e}")
        self._timer_active_field = None
        self.update()

    def _switch_page(self, page):
        if getattr(self, "_note_editor", None) and page != "notes": self._note_editor.close_editor()
        if self._new_note_active: self._new_note_active = False; self._new_note_text = ""; self._edit_note_idx = -1
        if self._reminder_active: self._reminder_active = False; self._reminder_text = ""
        if self._timer_active_field: self._timer_active_field = None
        self.current_page = page
        self.system_view = "menu"; self._ds_active = False; self._ds_text = ""; self._ds_res = []; self._wifi_pw_for = None
        if page == "system": self._bg(self._sys_info)
        if page != "ai":
            self._ai_url = ""; self._ai_service = ""
        self._update_ai_visibility()
        self.update()

    def toggle_expand(self):
        self.expanded = not self.expanded
        if not self.expanded and getattr(self, "_note_editor", None): self._note_editor.close_editor()
        if not self.expanded:
            self._ds_active = False; self._ds_text = ""; self._ds_res = []; self._wifi_pw_for = None; self._ds_add_mode = False
        self._ex_target = 1.0 if self.expanded else 0.0
        if self.expanded: self._set_show_target(1.0)
        self._animating = True
        self._update_ai_visibility(); self._wake()

    def _draw_garland(self, p, path, e):
        """Гирлянда вдоль контура острова: лампочки мигают, провод тёмно-зелёный."""
        L = path.length()
        if L < 60: return
        t = time.monotonic(); step = 20.0 if e < 0.5 else 26.0; n = int(L / step); rr = 2.6 + 0.9 * e
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(22, 96, 52, 210), 1.4)); p.drawPath(path); p.setPen(Qt.PenStyle.NoPen)
        for i in range(n + 1):
            pct = min(1.0, i * step / L); pt = path.pointAtPercent(pct); ang = math.radians(path.angleAtPercent(pct)); dx, dy = math.cos(ang), -math.sin(ang)
            bx = pt.x() - dy * 3.6; by = pt.y() + dx * 3.6 + 1.2; c = GARLAND_COLORS[i % len(GARLAND_COLORS)]; a = 0.55 + 0.45 * math.sin(t * 3.2 + i * 1.7)
            p.setBrush(QColor(c.red(), c.green(), c.blue(), int(50 * a))); p.drawEllipse(QPointF(bx, by), rr * 2.6, rr * 2.6)
            p.setBrush(QColor(c.red(), c.green(), c.blue(), int(130 + 125 * a))); p.drawEllipse(QPointF(bx, by), rr, rr * 1.25)


    def _draw_snow(self, p, iw, ih, e):
        t = time.monotonic(); n = int(16 + 44 * e); p.setPen(Qt.PenStyle.NoPen)
        for i in range(n):
            sp = 12.0 + (i % 5) * 6.5 + 14.0 * e; r = 0.8 + (i % 3) * 0.45 + 0.5 * e
            x = (i * 97.3 + math.sin(t * 0.8 + i) * 7.0) % max(1.0, iw); y = (t * sp + i * 53.7) % (ih + 8.0) - 4.0
            p.setBrush(QColor(255, 255, 255, 150 + (i % 4) * 25)); p.drawEllipse(QPointF(x, y), r, r)

    def _draw_snow_rect(self, p, r, n):
        t = time.monotonic(); p.setPen(Qt.PenStyle.NoPen)
        for i in range(n):
            sp = 16.0 + (i % 5) * 7.0; rad = 1.0 + (i % 3) * 0.6
            x = r.x() + (i * 83.1 + math.sin(t * 0.8 + i) * 9.0) % r.width(); y = r.y() + (t * sp + i * 47.3) % (r.height() + 8.0) - 4.0
            p.setBrush(QColor(255, 255, 255, 140 + (i % 4) * 28)); p.drawEllipse(QPointF(x, y), rad, rad)


    def paintEvent(self, ev):
        t0 = time.perf_counter()
        self._paint_impl(ev)
        self._paint_ms = self._paint_ms * 0.85 + (time.perf_counter() - t0) * 1000.0 * 0.15

    def set_christmas_theme(self, enabled):
        """Переключает сезонную палитру, снег и гирлянду; пользовательские цвета сохраняются."""
        enabled = bool(enabled)
        if enabled:
            if not bool(self.settings.value("xmas_theme", False, type=bool)):
                for key in ("col_accent", "col_violet", "col_music", "ui_style"):
                    self.settings.setValue("xmas_prev_" + key, str(self.settings.value(key, "") or ""))
            self.settings.setValue("col_accent", "#e5484d")
            self.settings.setValue("col_violet", "#27b879")
            self.settings.setValue("col_music", "#f4c95d")
            self.settings.setValue("ui_style", 1)
            self.settings.setValue("xmas_theme", True)
        else:
            for key in ("col_accent", "col_violet", "col_music", "ui_style"):
                prev = self.settings.value("xmas_prev_" + key, None)
                if prev is not None:
                    if prev == "": self.settings.remove(key)
                    else:
                        try: self.settings.setValue(key, int(prev) if key == "ui_style" else str(prev))
                        except Exception: self.settings.setValue(key, prev)
                    self.settings.remove("xmas_prev_" + key)
            self.settings.setValue("xmas_theme", False)
        apply_theme(self.settings)
        self.update()
        if getattr(self, "_settings_window", None) and self._settings_window:
            self._settings_window.update()

    def _perf(self):
        try: return int(self.settings.value("perf_mode", 0))
        except Exception: return 0

    def _page_animated(self):
        # Не держим 60 FPS на статичных страницах: это заметно ускоряет
        # переключение вкладок и снижает нагрузку на слабых ноутбуках.
        pg = self.current_page
        if pg in ("home", "mixer", "system", "shelf"): return True
        if pg == "weather": return bool(self._weather_loading or self._drag_over)
        if pg == "timer": return bool(self.t_running or self._timer_active_field)
        if pg == "notes": return bool(self._new_note_active)
        if pg == "calendar": return bool(self._reminder_active)
        return bool(self._drag_over or self._ds_active)

    def _paint_impl(self, _):
        try:
            iw = self._iw; ih = self._ih
            if iw < 1.0 or ih < 1.0: return
            if getattr(self, "_note_editor", None) and self._note_editor.isVisible(): self._note_editor._place()
            p = QPainter(self)
            p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            self._hits = []; self._dock_right_regions = []
            e = max(0.0, min(1.0, self._expand)); s = max(0.0, min(1.0, self._show))
            shake_dx = 0.0
            if self._shake_start > 0:
                t_s = time.monotonic() - self._shake_start
                if t_s < 0.5:
                    decay = max(0.0, 1.0 - t_s / 0.5) ** 1.4
                    shake_dx = math.sin(t_s * 55.0) * self._shake_amp * decay
                else:
                    self._shake_start = 0.0
            p.setPen(Qt.PenStyle.NoPen)
            ox_, oy_ = self._origin(); p.translate(ox_ + shake_dx, oy_)
            shape = self._shape(); flip = (self._edge == "bottom" and self._free is None)
            playing = bool(self.media.get("playing") and self.media.get("active") and self.mod_music)
            dyn = self._dyn()
            try: glow_k = int(self.settings.value("fx_glow", 100)) / 100.0
            except Exception: glow_k = 1.0
            part_on = bool(self.settings.value("fx_particles", True, type=bool)) and self._perf() != 1
            wave = self._wave_offsets(ih) if self._wb("eq_edge", True) else None
            if self._floating(): path = float_path(iw, ih, 22.0 + 8.0 * e, wave)
            else: path = island_path(iw, ih, self._rb, self._fl, self._drop, wave)
            if flip: p.save(); p.translate(0, ih); p.scale(1, -1)
            # мягкая тень: несколько широких обводок контура (дешевле 14 заливок на кадр)
            p.setBrush(Qt.BrushStyle.NoBrush)
            sh = path.translated(0, 5.0); sa = 0.35 + 0.65 * s
            for w_, a_ in (((22, 5), (12, 8), (5, 12)) if (e < 0.5 and self._perf() != 1) else ((14, 7), (5, 12))):
                p.setPen(QPen(QColor(0, 0, 0, int(a_ * sa)), w_, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                p.drawPath(sh)
            p.setPen(Qt.PenStyle.NoPen)
            bg = QLinearGradient(0, 0, 0, ih)
            bg.setColorAt(0.0, QColor(0, 0, 0, 255))      # верх чисто-чёрный — сливается с рамкой монитора
            ust = self._ui_style()
            c1_, c2_ = ((6, 6, 8), (3, 3, 4)) if ust == 0 else ((24, 26, 33), (14, 15, 19)) if ust == 1 else ((15, 18, 25), (15, 18, 25)) if ust == 2 else ((3, 4, 10), (3, 4, 10)) if ust == 3 else ((0, 0, 0), (0, 0, 0))
            bg.setColorAt(0.45, QColor(c1_[0], c1_[1], c1_[2], 253)); bg.setColorAt(1.0, QColor(c2_[0], c2_[1], c2_[2], 254))
            p.fillPath(path, bg)
            p.save(); p.setClipPath(path)
            if playing:
                ga = (46 * e + (28 + 80 * (1.0 - e)) * min(1.0, self._bass * 1.6)) * glow_k
                gg = QRadialGradient(QPointF(iw * 0.2, ih), iw * 0.6); gg.setColorAt(0, rgba(dyn, int(min(255, ga)))); gg.setColorAt(1, rgba(dyn, 0))
                p.fillRect(QRectF(0, 0, iw, ih), gg)
            gl = QLinearGradient(0, 0, 0, ih * 0.5)
            gl.setColorAt(0, QColor(255, 255, 255, 12)); gl.setColorAt(0.5, QColor(255, 255, 255, 8)); gl.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillPath(path, gl)
            if part_on and e > 0.05 and int(iw) > 0 and int(ih) > 0:
                n_p = int(6 * e)
                for idx in range(n_p):
                    px_ = (idx * 137 + int(self._glow * 40)) % int(iw)
                    py_ = (idx * 89) % int(ih)
                    a = 30 + int(40 * math.sin(self._glow * 3 + idx))
                    p.setBrush(QColor(255, 255, 255, max(10, a)))
                    p.drawEllipse(QPointF(px_, py_), 1.5, 1.5)
            p.restore()
            if self._notify:
                out_start = self._notify.get("out_start", 0)
                if out_start > 0:
                    out_age = time.monotonic() - out_start
                    fade = 1.0 if out_age > 0.28 else max(0.0, out_age / 0.28)
                else:
                    fade = 1.0
                pulse = 0.5 + 0.5 * math.sin(time.monotonic() * 7.0)
                for w, a in [(14, 22), (8, 45), (4.5, 78)]:
                    alpha = int(a * pulse * fade)
                    if alpha <= 0: continue
                    gp = QLinearGradient(0, 0, 0, ih)
                    nc = self._notify.get("color"); c1_ = nc if nc is not None else ACCENT; c2_ = nc.lighter(150) if nc is not None else VIOLET
                    gp.setColorAt(0, rgba(c1_, alpha)); gp.setColorAt(0.5, rgba(c2_, alpha)); gp.setColorAt(1, rgba(c1_, alpha))
                    p.setPen(QPen(QBrush(gp), w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)
            pen_g = QLinearGradient(0, 0, 0, ih); p.setBrush(Qt.BrushStyle.NoBrush)
            if playing:      # цветной контур в цвет трека + мягкое свечение, пульсирует от баса
                pen_g.setColorAt(0.0, QColor(255, 255, 255, 60)); pen_g.setColorAt(0.4, rgba(dyn, 150)); pen_g.setColorAt(1.0, rgba(dyn, 255))
                p.setPen(QPen(rgba(dyn, int(26 + 70 * min(1.0, self._bass * 1.5))), 5.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); p.drawPath(path)
                p.setPen(QPen(QBrush(pen_g), 1.6))
            elif ust == 3:
                pen_g.setColorAt(0.0, rgba(ACCENT, 200)); pen_g.setColorAt(1.0, rgba(VIOLET, 200)); p.setPen(QPen(QBrush(pen_g), 1.4))
            else:
                pen_g.setColorAt(0.0, QColor(255, 255, 255, 70)); pen_g.setColorAt(0.5, QColor(255, 255, 255, 22)); pen_g.setColorAt(1.0, QColor(255, 255, 255, 30))
                p.setPen(QPen(QBrush(pen_g), 1.2))
            p.drawPath(path)
            # Оригинальная гирлянда из пользовательского island.pyw.
            if bool(self.settings.value("xmas_theme", False, type=bool)):
                self._draw_garland(p, path, e)
            if shape == 2:      # «чёрная дыра»: вращающееся световое кольцо по контуру
                cg = QConicalGradient(QPointF(iw / 2, ih / 2), (time.monotonic() * 70) % 360)
                cg.setColorAt(0.0, rgba(ACCENT, 235)); cg.setColorAt(0.3, rgba(VIOLET, 170)); cg.setColorAt(0.55, rgba(VIOLET, 0)); cg.setColorAt(0.8, rgba(ACCENT, 0)); cg.setColorAt(1.0, rgba(ACCENT, 235))
                for w_, a_ in ((9, 0.16), (4.5, 0.38), (1.8, 1.0)):
                    p.setOpacity(a_); p.setPen(QPen(QBrush(cg), w_)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)
                p.setOpacity(1.0)
            if e > 0.6 and playing:
                p.save(); p.setClipPath(path)
                wave_grad = QLinearGradient(0, ih - 20, 0, ih)
                wave_grad.setColorAt(0, QColor(0, 205, 255, 0)); wave_grad.setColorAt(1, rgba(dyn, int(150 * e)))
                p.fillRect(QRectF(0, ih - 20, iw, 20), wave_grad)
                p.restore()
            if flip:
                p.restore(); tr_ = QTransform(); tr_.translate(0, ih); tr_.scale(1, -1); clip_path = tr_.map(path)
            else: clip_path = path
            p.setClipPath(clip_path)
            # Снегопад перенесён из оригинального island.pyw пользователя.
            if bool(self.settings.value("xmas_theme", False, type=bool)):
                self._draw_snow(p, iw, ih, e)
            if playing and e > 0.2 and self._wb("eq_edge", True):
                if flip: p.save(); p.translate(0, ih); p.scale(1, -1)
                self._draw_bottom_waves(p, iw, ih, e)
                if flip: p.restore()
            ca = 1.0 - min(1.0, e / 0.4)
            vis = max(0.0, min(1.0, (s - 0.66) / 0.3))
            if s < 0.97 and e < 0.05:      # блик на капле + пульс звука, пока остров свёрнут в миниатюру
                ma = 1.0 - vis
                gl2 = QRadialGradient(QPointF(iw * 0.34, ih * 0.32), max(2.0, min(iw, ih) * 0.55))
                gl2.setColorAt(0, QColor(255, 255, 255, int(110 * ma))); gl2.setColorAt(1, QColor(255, 255, 255, 0))
                p.fillRect(QRectF(0, 0, iw, ih), gl2)
                if playing and ma > 0.3 and iw > 14:
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(dyn, int(230 * ma)))
                    for k in range(3):
                        bh = max(1.5, (ih * 0.55) * (0.25 + 0.75 * self._eq_disp[2 + k * 6]))
                        p.drawRoundedRect(QRectF(iw / 2 - 7 + k * 5.5, ih * 0.62 - bh / 2, 3, bh), 1.5, 1.5)
            if ca * vis > 0.01:
                p.setOpacity(ca * vis); self._safe(p, "compact", self._draw_compact, p, iw, ih); p.setOpacity(1.0)
            xa = max(0.0, min(1.0, (e - 0.45) / 0.55))
            if xa > 0.01:
                self._ox = (iw - self.EW) / 2; p.translate(self._ox, 0); p.setOpacity(xa)
                if getattr(self, "_note_editor", None) and self._note_editor.isVisible(): self._note_editor._place()
                self._safe(p, "nav", self._draw_top_nav, p, iw)
                pg = {"home": self._draw_home, "timer": self._draw_timer, "weather": self._draw_weather, "calendar": self._draw_calendar, "clipboard": self._draw_clipboard,
                      "notes": self._draw_notes, "shelf": self._draw_shelf, "mixer": self._draw_mixer, "ai": self._draw_ai, "system": self._draw_system}.get(self.current_page)
                if pg is not None: self._safe(p, self.current_page, pg, p)
        except Exception as ex: log_error(f"paint: {ex}")

    def _gaze(self, cx, cy, mx=3.2, my=4.0):
        gp = QCursor.pos(); wg = self.mapToGlobal(QPoint(0, 0)); now = time.monotonic()
        dx = gp.x()-(wg.x()+self._org_x()+cx); dy = gp.y()-(wg.y()+self._org_y()+cy); d = math.hypot(dx, dy)
        px, py = ((dx/d)*mx, (dy/d)*my) if d > 1 else (0.0, 0.0)
        if (gp.x(), gp.y()) != getattr(self, "_last_gp", None): self._last_gp = (gp.x(), gp.y()); self._last_move = now
        sleepy = now - getattr(self, "_last_move", now) > 45
        bl = 0.0
        if now < self._blink_until and self._blink_until > self._blink_start:
            bl = 1.0 - abs((now-self._blink_start)/(self._blink_until-self._blink_start) - 0.5)*2
        if sleepy: bl = 0.92
        self._mood_update(now, d, sleepy)
        return px, py, bl, now < getattr(self, "_happy_until", 0), sleepy

    def _mood_update(self, now, d, sleepy):
        playing = bool(self.media.get("active") and self.media.get("playing") and self.mod_music); m = "calm"
        if self._alarm: m = "alarm"
        elif self._notify and now - self._notify.get("start", 0) < 1.8: m = "surprised"
        elif now < getattr(self, "_happy_until", 0): m = "happy"
        elif now < getattr(self, "_playful_until", 0): m = "playful"
        elif self.battery and not self.battery[1] and self.battery[0] <= 20: m = "tired"
        elif self.d["cpu"] > 88: m = "stress"
        elif playing: m = "groove"
        elif sleepy: m = "sleepy"
        elif d < 90: m = "curious"
        elif now >= getattr(self, "_next_idle_emote", 0.0):
            # Небольшие спонтанные реакции: персонаж не повторяет одну улыбку.
            if random.random() < 0.34:
                self._playful_until = now + 1.8
                m = "playful"
            else:
                self._happy_until = now + 1.45
                m = "happy"
            self._next_idle_emote = now + 7.0 + random.random() * 9.0
        if not self._wb("ch_emotions", True): m = "sleepy" if sleepy else "calm"
        self._mood = m

    def _draw_face_eyes(self, p, cx, cy, g, W, D):
        """Глаза с настроением: брови, веки, подмигивание, микро-движения зрачков."""
        t = time.monotonic(); m = self._mood; px, py, bl, happy, sleepy = g[:5]; bass = min(1.0, self._bass * 2.0)
        sw = sh = 1.0; brow = 0.0; lid = 0.0; arcs = bool(happy); slant = 0.0
        if m in ("surprised", "alarm"): sw, sh, brow = 1.1, 1.28, -3.2
        elif m == "stress": sh, brow, slant = 1.18, -2.0, 1.5
        elif m == "tired": lid, brow, slant = 0.5, 1.5, -1.7
        elif m == "curious": sw, sh, brow = 1.05, 1.12, -2.0
        elif m == "playful": sw, sh, brow = 1.12, 0.92, -2.6; arcs = True
        elif m == "groove": arcs = arcs or (bass > 0.3 and math.sin(t * 6.0) > -0.35)
        if m in ("calm", "curious") and t > getattr(self, "_next_wink", 0.0):
            self._wink_until = t + 0.25; self._next_wink = t + 9.0 + random.random() * 14.0
        wink = t < getattr(self, "_wink_until", 0.0); sac = math.sin(t * 1.7) * 0.35 + math.sin(t * 3.1) * 0.2
        for sgn in (-1, 1):
            ex = cx + sgn * 10.5; ey = cy; rw, rh = 11 * sw, 14 * sh
            if arcs or (wink and sgn > 0):
                p.setPen(QPen(W, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawArc(QRectF(ex - rw / 2, ey - rh / 4, rw, rh / 2 + 2), 0, 180 * 16)
            else:
                eh = rh * (1.0 - 0.92 * bl)
                if eh < 2: p.setPen(QPen(W, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawLine(QPointF(ex - rw / 2, ey), QPointF(ex + rw / 2, ey))
                else:
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(W); p.drawEllipse(QPointF(ex, ey), rw / 2, eh / 2)
                    pr = min(2.9, eh / 2.4); pxx = ex + (px + sac) * rw / 11.0; pyy = ey + py * rh / 14.0
                    p.setBrush(D); p.drawEllipse(QPointF(pxx, pyy), pr, pr * 1.15); p.setBrush(QColor(255, 255, 255, 210)); p.drawEllipse(QPointF(pxx - 0.9, pyy - 1.1), 1.1, 1.1)
                    if lid > 0:
                        p.save(); cp = QPainterPath(); cp.addEllipse(QPointF(ex, ey), rw / 2, eh / 2); p.setClipPath(cp)
                        p.setBrush(QColor(5, 5, 7)); p.drawRect(QRectF(ex - rw, ey - eh / 2 - 1, 2 * rw, eh * lid + 1)); p.restore()
            if brow or slant:
                by = ey - rh / 2 - 3.5 + brow; p.setPen(QPen(QColor(255, 255, 255, 205), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(ex + sgn * 4.6, by - slant), QPointF(ex - sgn * 4.6, by + slant))

    def _draw_mood_overlay(self, p, cx, cy, g):
        m = self._mood; t = time.monotonic()
        if m == "calm" or m == "sleepy" or m == "curious": return
        p.save(); p.setPen(Qt.PenStyle.NoPen)
        if m in ("groove", "happy", "playful"):
            p.setBrush(QColor(255, 120, 150, 80))
            for sgn in (-1, 1): p.drawEllipse(QPointF(cx + sgn * 14.5, cy + 7), 3.4, 2.0)
        if m == "playful":
            age = max(0.0, 1.8 - (getattr(self, "_playful_until", t) - t))
            pulse = 0.65 + 0.35 * math.sin(t * 9.0)
            p.setPen(QPen(QColor(255, 218, 110, int(210 * pulse)), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for k in range(3):
                a = t * 2.8 + k * math.tau / 3
                sx = cx + math.cos(a) * (17 + age * 1.5)
                sy = cy - 10 + math.sin(a) * 7
                p.drawLine(QPointF(sx - 2, sy), QPointF(sx + 2, sy))
                p.drawLine(QPointF(sx, sy - 2), QPointF(sx, sy + 2))
        if m == "groove":
            ph = (t * 1.3) % 1.0; p.setFont(font(10, QFont.Weight.Bold, family="Segoe UI Symbol")); p.setPen(rgba(self._dyn(), int(230 * (1 - ph))))
            p.drawText(QPointF(cx + 15, cy - 4 - ph * 10), "♪")
        elif m == "stress":
            ph = (t * 1.1) % 1.0; p.setBrush(QColor(120, 190, 255, int(230 * (1 - ph * 0.5)))); p.drawEllipse(QPointF(cx + 17, cy - 8 + ph * 12), 1.7, 2.4)
        elif m == "tired":
            ph = (t * 0.8) % 1.0; p.setBrush(QColor(120, 190, 255, int(220 * (1 - ph * 0.6)))); p.drawEllipse(QPointF(cx - 11, cy + 5 + ph * 8), 1.4, 2.0)
        elif m == "happy":
            age = max(0.0, t - (getattr(self, "_happy_until", 0) - 1.4)); p.setFont(font(9, QFont.Weight.Bold, family="Segoe UI Symbol"))
            for k in range(2):
                a = max(0.0, 1.0 - age / 1.4); p.setPen(QColor(255, 90, 120, int(240 * a))); p.drawText(QPointF(cx + (k * 2 - 1) * 10 + math.sin(age * 6 + k) * 2, cy - 7 - age * 12 - k * 4), "♥")
        elif m in ("surprised", "alarm"):
            pulse = 1.0 + 0.16 * math.sin(t * 13.0)
            p.setPen(QPen(QColor(255,190,70,190), 1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx+17,cy-9),3.8*pulse,3.8*pulse)
            p.setFont(font(12, QFont.Weight.Bold)); p.setPen(QColor(255, 190, 70, 245)); p.drawText(QPointF(cx + 14, cy - 5), "!")
        elif m == "curious":
            bob = math.sin(t*3.2)*2.0
            p.setFont(font(10,QFont.Weight.Bold)); p.setPen(QColor(120,210,255,210)); p.drawText(QPointF(cx+16,cy-10+bob),"?")
        elif m in ("sleepy", "tired"):
            p.setFont(font(8,QFont.Weight.Bold)); p.setPen(QColor(150,190,255,190)); p.drawText(QPointF(cx+14,cy-10-(t%1.4)*5),"z")
        p.restore()

    def _eye(self, p, ex, ey, rw, rh, g, white, pupil, lc, pr=2.6):
        px, py, bl, happy, _ = g[:5]; k = rw/11.0
        if happy:
            p.setPen(QPen(lc, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(ex-rw/2, ey-rh/4, rw, rh/2+2), 0, 180*16); return
        eh = rh*(1.0-0.92*bl)
        if eh < 2:
            p.setPen(QPen(lc, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawLine(QPointF(ex-rw/2, ey), QPointF(ex+rw/2, ey)); return
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(white); p.drawEllipse(QPointF(ex, ey), rw/2, eh/2)
        if pr > 0:
            r_ = min(pr, eh/2.5); p.setBrush(pupil); p.drawEllipse(QPointF(ex+px*k, ey+py*k), r_, r_*1.15)
            p.setBrush(QColor(255,255,255,200)); p.drawEllipse(QPointF(ex+px*k-0.9, ey+py*k-1.1), 1.1, 1.1)

    def _draw_eyes(self, p, cx, cy):
        now = time.monotonic()
        if getattr(self, "_bounce_start", 0):
            bt = now - self._bounce_start
            if bt < 0.45:
                cy += -math.sin(bt / 0.45 * math.pi) * 4.0
        if now - getattr(self, "_ch_t", 0) > 0.5:
            self._ch_t = now
        try: self._ch = str(self.settings.value("character", "eyes")); self._ch_img = str(self.settings.value("char_image", "") or "")
        except Exception: self._ch = "eyes"; self._ch_img = ""
        ch = getattr(self, "_ch", "eyes"); g = self._gaze(cx, cy); t = now; playing = bool(self.media.get("playing"))
        if self._mood == "groove": cy -= min(1.0, self._bass * 2.0) * 2.2
        elif self._mood in ("surprised", "alarm"): cy += math.sin(now * 40.0) * 0.6
        W = QColor(255,255,255,245); D = QColor(15,20,30); p.save(); p.setPen(Qt.PenStyle.NoPen)
        # Живое idle-состояние: дыхание, лёгкий наклон и мягкая контактная тень.
        idle = math.sin(t * (5.0 if playing else 1.65))
        breath = 1.0 + (0.025 if playing else 0.012) * idle
        sway = math.sin(t * (3.2 if playing else 0.72)) * (2.0 if playing else 0.65)
        p.setBrush(QColor(0,0,0,45)); p.drawEllipse(QRectF(cx-10,cy+12,20,3.2))
        p.translate(cx, cy); p.rotate(sway); p.scale(breath, 1.0 + (breath-1.0)*0.65); p.translate(-cx, -cy)
        if ch == "custom" and getattr(self, "_ch_img", ""):
            if self._ch_img != getattr(self, "_cimg_path", None):
                self._cimg_path = self._ch_img; pm = QPixmap(self._ch_img)
                self._cimg = None if pm.isNull() else pm.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            if self._cimg is not None:
                sc = 1.0 + (0.06*math.sin(t*9) if playing else 0.0); bob = math.sin(t*(3.0 if playing else 1.2))*(1.6 if playing else 0.8)
                sz = 30*sc; rr = QRectF(cx-sz/2, cy-sz/2+bob, sz, sz); pa = QPainterPath(); pa.addRoundedRect(rr, 9, 9)
                p.setClipPath(pa); p.drawPixmap(rr.toRect(), self._cimg); p.restore(); return
        DK = QColor(40, 24, 20)
        if ch == "claude":
            C = QColor(217, 119, 87); p.save(); p.translate(cx, cy); p.rotate(math.sin(t*(2.5 if playing else 0.8))*(12 if playing else 4)); p.setBrush(C)
            pa = QPainterPath()
            for i in range(24):
                a = i*math.pi/12; r_ = 13.5 if i % 2 == 0 else 6.5
                (pa.moveTo if i == 0 else pa.lineTo)(math.cos(a)*r_, math.sin(a)*r_)
            pa.closeSubpath(); p.drawPath(pa); p.restore()
            for sgn in (-1, 1): self._eye(p, cx+sgn*3.6, cy-0.5, 4, 6, g, DK, DK, DK, 0)
        elif ch == "clawd":
            C = QColor(217, 119, 87); p.translate(0, math.sin(t*(6 if playing else 2))*(1.5 if playing else 0.6)); p.setBrush(C)
            p.drawRoundedRect(QRectF(cx-12, cy-7, 24, 15), 3, 3)
            for sgn in (-1, 1):
                p.drawRect(QRectF(cx+sgn*12-(0 if sgn > 0 else 3), cy-2, 3, 5)); p.drawRect(QRectF(cx+sgn*6-1.5, cy+8, 3, 4))
            for sgn in (-1, 1): self._eye(p, cx+sgn*5, cy-1.5, 4, 6, g, DK, DK, DK, 0)
        elif ch == "panda":
            p.setBrush(QColor(25, 25, 30))
            for sgn in (-1, 1): p.drawEllipse(QPointF(cx+sgn*9.5, cy-9), 4.2, 4.2)
            p.setBrush(QColor(248, 248, 250)); p.drawEllipse(QPointF(cx, cy), 13, 11.5)
            p.setBrush(QColor(25, 25, 30))
            for sgn in (-1, 1): p.drawEllipse(QPointF(cx+sgn*5.5, cy-1), 3.6, 4.6)
            p.drawEllipse(QPointF(cx, cy+4), 1.8, 1.3)
            for sgn in (-1, 1): self._eye(p, cx+sgn*5.5, cy-1, 3, 4, g, QColor(255, 255, 255), QColor(255, 255, 255), QColor(255, 255, 255), 0)
        elif ch == "fox":
            O = QColor(240, 134, 50); p.setBrush(O)
            for sgn in (-1, 1): p.drawPolygon(_pts((cx+sgn*12, cy-3), (cx+sgn*9, cy-15), (cx+sgn*2.5, cy-8)))
            p.drawEllipse(QPointF(cx, cy+1), 13, 11)
            p.setBrush(QColor(255, 244, 232)); p.drawPolygon(_pts((cx-12, cy+3), (cx, cy+12), (cx+12, cy+3), (cx, cy+4)))
            p.setBrush(QColor(30, 22, 20)); p.drawEllipse(QPointF(cx, cy+5), 1.8, 1.4)
            for sgn in (-1, 1): self._eye(p, cx+sgn*5.2, cy-1.5, 4, 6, g, QColor(30, 22, 20), QColor(30, 22, 20), QColor(30, 22, 20), 0)
        elif ch == "frog":
            G = QColor(110, 205, 110); p.setBrush(G); p.drawEllipse(QPointF(cx, cy+2), 13, 10)
            for sgn in (-1, 1): p.setBrush(G); p.drawEllipse(QPointF(cx+sgn*7, cy-6), 5, 5)
            for sgn in (-1, 1): self._eye(p, cx+sgn*7, cy-6, 7, 8, g, QColor(255, 255, 255), QColor(20, 30, 20), QColor(20, 30, 20), 2.0)
            p.setPen(QPen(QColor(30, 80, 40), 1.3)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawArc(QRectF(cx-6, cy+1, 12, 8), 200*16, 140*16)
        elif ch == "cat":
            fur = QColor(255,196,128); p.setBrush(fur)
            for sgn in (-1, 1): p.drawPolygon(_pts((cx+sgn*12, cy-4), (cx+sgn*9, cy-14), (cx+sgn*3, cy-8)))
            p.drawEllipse(QPointF(cx, cy+1), 13, 11)
            p.setBrush(QColor(255,150,170)); p.drawPolygon(_pts((cx-1.6, cy+4), (cx+1.6, cy+4), (cx, cy+6.2)))
            for sgn in (-1, 1): self._eye(p, cx+sgn*5.2, cy-1, 6, 8, g, QColor(40,30,28), QColor(255,255,255), QColor(80,50,40), 1.6)
            p.setPen(QPen(QColor(90,60,50,170), 1)); p.setBrush(Qt.BrushStyle.NoBrush)
            for sgn in (-1, 1):
                p.drawLine(QPointF(cx+sgn*14, cy+3), QPointF(cx+sgn*8, cy+4.5)); p.drawLine(QPointF(cx+sgn*14, cy+6.5), QPointF(cx+sgn*8, cy+6))
        elif ch == "ghost":
            by = math.sin(t*2.2)*1.5; p.translate(0, by); p.setBrush(QColor(245,247,255))
            pa = QPainterPath(); pa.moveTo(cx-11, cy+12); pa.lineTo(cx-11, cy-2); pa.arcTo(QRectF(cx-11, cy-14, 22, 22), 180, -180)
            for pt in ((cx+11, cy+12), (cx+7, cy+8), (cx+3.5, cy+12), (cx, cy+8), (cx-3.5, cy+12), (cx-7, cy+8)): pa.lineTo(*pt)
            pa.closeSubpath(); p.drawPath(pa)
            for sgn in (-1, 1): self._eye(p, cx+sgn*4.5, cy-3, 5, 7, g, QColor(30,32,50), QColor(255,255,255), QColor(30,32,50), 1.3)
            if playing: p.setBrush(QColor(30,32,50)); p.drawEllipse(QPointF(cx, cy+4.5), 2, 2.8)
        elif ch == "robot":
            p.setBrush(QColor(196,206,222)); p.drawRoundedRect(QRectF(cx-12, cy-8, 24, 19), 5, 5)
            p.setPen(QPen(QColor(150,160,180), 1.6)); p.drawLine(QPointF(cx, cy-8), QPointF(cx, cy-13)); p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(rgba(ACCENT, int(140+110*math.sin(t*4)))); p.drawEllipse(QPointF(cx, cy-14), 2.2, 2.2)
            p.setBrush(QColor(18,22,32)); p.drawRoundedRect(QRectF(cx-9, cy-5, 18, 12), 3, 3)
            for sgn in (-1, 1): self._eye(p, cx+sgn*4.6, cy+1, 5, 6, g, QColor(ACCENT), QColor(ACCENT), QColor(ACCENT), 0)
        elif ch == "alien":
            p.setBrush(QColor(130,235,160)); p.drawEllipse(QPointF(cx, cy), 12, 12)
            p.setPen(QPen(QColor(130,235,160), 1.5))
            for sgn in (-1, 1): p.drawLine(QPointF(cx+sgn*6, cy-10), QPointF(cx+sgn*9, cy-15))
            p.setBrush(QColor(130,235,160))
            for sgn in (-1, 1): p.drawEllipse(QPointF(cx+sgn*9, cy-15.5), 1.6, 1.6)
            for sgn in (-1, 1): self._eye(p, cx+sgn*5.3, cy-1, 7, 9, g, QColor(12,18,16), QColor(255,255,255), QColor(12,18,16), 1.5)
            p.setPen(QPen(QColor(20,60,40), 1.2)); p.drawLine(QPointF(cx-2.5, cy+7), QPointF(cx+2.5, cy+7))
        else:
            self._draw_face_eyes(p, cx, cy, g, W, D)

        # Новогодняя шапка рисуется поверх любого выбранного персонажа,
        # включая пользовательскую картинку и увеличенный персонаж на главной.
        if bool(self.settings.value("xmas_theme", False, type=bool)):
            p.save()
            p.translate(0, math.sin(t * 2.1) * 0.55)
            cap = QPainterPath()
            cap.moveTo(cx - 13.5, cy - 7.0)
            cap.quadTo(cx - 8.0, cy - 20.0, cx + 8.5, cy - 18.0)
            cap.quadTo(cx + 11.0, cy - 15.0, cx + 10.5, cy - 8.0)
            cap.closeSubpath()
            p.setPen(QPen(QColor(120, 28, 42, 190), 0.8))
            p.setBrush(QColor(205, 48, 62))
            p.drawPath(cap)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(250, 248, 242))
            p.drawRoundedRect(QRectF(cx - 14.0, cy - 9.0, 26.0, 4.5), 2.2, 2.2)
            p.drawEllipse(QPointF(cx + 9.0, cy - 19.0), 3.4, 3.4)
            p.restore()

        # Щёки и блики добавляют объём, не перегружая минималистичный стиль.
        if ch in ("cat", "fox", "panda", "frog", "eyes"):
            cheek_a = int(28 + 18 * (0.5 + 0.5 * math.sin(t * 1.4)))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,125,145,cheek_a))
            p.drawEllipse(QPointF(cx-8.5,cy+5),2.3,1.3); p.drawEllipse(QPointF(cx+8.5,cy+5),2.3,1.3)
        # Две редкие искры рядом с персонажем — небольшая анимация ожидания.
        if not playing and int(t*2.0)%5 == 0:
            pulse = 0.55 + 0.45*math.sin(t*5.0)
            p.setPen(QPen(QColor(255,255,255,int(90*pulse)),1.1)); p.setBrush(Qt.BrushStyle.NoBrush)
            for sx,sy in ((cx-18,cy-11),(cx+17,cy-13)):
                p.drawLine(QPointF(sx-1.5,sy),QPointF(sx+1.5,sy)); p.drawLine(QPointF(sx,sy-1.5),QPointF(sx,sy+1.5))
        self._draw_mood_overlay(p, cx, cy, g)
        if g[4]:
            p.setFont(font(8, QFont.Weight.Bold)); p.setPen(QColor(255,255,255, int(120+100*math.sin(t*2)))); p.drawText(QPointF(cx+10, cy-8-2*math.sin(t*2)), "z")
        p.restore()

    def _draw_compact_download(self, p, iw, ih):
        lst = self._dl_cur
        if not lst: return False
        AL = Qt.AlignmentFlag; d = lst[0]; now_ = time.monotonic(); n = len(lst)
        total = d.get("total", 0) or 0; size = d.get("size", 0); spd = d.get("speed", 0.0)
        det = total > 0
        cur = self._gv.get("dlp", 0.0)
        if det: cur += (min(1.0, size / total) - cur) * 0.2; self._gv["dlp"] = cur
        else: self._gv["dlp"] = 0.0
        name = d.get("name", "")
        if name.lower().startswith("unconfirmed") or not name: name = "Загрузка файла…"
        cx, cy, R = 26.0, ih / 2, 13.0; arc = QRectF(cx - R, cy - R, 2 * R, 2 * R)
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(255, 255, 255, 34), 3)); p.drawEllipse(QPointF(cx, cy), R, R)
        if det:
            p.setPen(QPen(rgba(ACCENT, 60), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 90 * 16, int(-360 * 16 * cur))
            p.setPen(QPen(ACCENT, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 90 * 16, int(-360 * 16 * cur))
        else:
            p.setPen(QPen(ACCENT, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, int((-now_ * 300 % 360) * 16), 100 * 16)
        p.setFont(font(10, family="Segoe UI Emoji")); p.setPen(QColor(255, 255, 255, 240)); p.drawText(QRectF(cx - 10, cy - 10, 20, 20), AL.AlignCenter, self._file_emoji(d.get("name", "")))
        rw = 62.0; tx = cx + R + 12; tw = iw - tx - rw - 8
        if det:
            p.setFont(font(15, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(iw - rw - 10, 0, rw, ih), AL.AlignRight | AL.AlignVCenter, f"{cur * 100:.0f}%")
        elif spd > 0:
            p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 220)); p.drawText(QRectF(iw - rw - 10, 0, rw, ih), AL.AlignRight | AL.AlignVCenter, self._fmt_speed(spd))
        if n > 1:
            p.setFont(font(9, QFont.Weight.Bold)); p.setPen(rgba(ACCENT.lighter(130), 240)); p.drawText(QRectF(iw - rw - 40, 0, 32, ih), AL.AlignRight | AL.AlignVCenter, f"+{n - 1}")
            tw -= 24
        if tw > 30:
            f1 = font(11, QFont.Weight.Bold); fm1 = QFontMetrics(f1)
            p.setFont(f1); p.setPen(QColor(255, 255, 255, 245)); p.drawText(QRectF(tx, 3, tw, 17), AL.AlignLeft | AL.AlignVCenter, fm1.elidedText(name, Qt.TextElideMode.ElideMiddle, int(tw)))
            parts = [f"{self._fmt_size(size)} / {self._fmt_size(total)}" if det else self._fmt_size(size)]
            if self._wb("dl_speed", True) and spd > 1024:
                if det: parts.append(self._fmt_speed(spd))
                if det and total > size: parts.append("ещё " + self._fmt_eta((total - size) / spd))
            f2 = font(9); fm2 = QFontMetrics(f2); p.setFont(f2); p.setPen(QColor(255, 255, 255, 150))
            p.drawText(QRectF(tx, 20, tw, 16), AL.AlignLeft | AL.AlignVCenter, fm2.elidedText("  ·  ".join(parts), Qt.TextElideMode.ElideRight, int(tw)))
        return True

    def _mx_apply(self):
        if self._mx_drag is None or self._mouse is None: return
        pid, r = self._mx_drag; v = max(0.0, min(1.0, (self._mouse.x() - r.x()) / max(1.0, r.width())))
        if pid == -1: self._volume = v; set_volume(v)
        else: self._mx_local[pid] = (v, time.monotonic() + 0.9); self._mixer.set_volume(pid, v)
        self.update()

    def _mx_start(self, pid, r): self._mx_drag = (pid, r); self._mx_apply()

    def _mx_mute(self, a):
        self._mx_local.pop(a["pid"], None); self._mixer.set_mute(a["pid"], not a["mute"]); a["mute"] = not a["mute"]; self.update()

    def _draw_mixer(self, p):
        AL = Qt.AlignmentFlag; now_ = time.monotonic(); mx = self._mixer; apps = list(mx.apps)
        p.setFont(font(16, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 240)); p.drawText(QRectF(24, 56, 300, 28), AL.AlignLeft | AL.AlignVCenter, "Микшер звука")
        p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 120))
        p.drawText(QRectF(24, 84, 560, 16), AL.AlignLeft | AL.AlignVCenter, "Громкость каждого приложения · потяни ползунок или нажми на значок динамика" if HAS_PYCAW else "Нужен пакет pycaw: pip install pycaw")
        rows = [{"pid": -1, "name": "Общая громкость", "exe": "", "vol": self._volume if self._volume is not None else 0.0, "mute": False, "peak": 0.0}] + apps[:7]
        y = 108.0; rh = 46.0; gap = 6.0
        for a in rows:
            r = QRectF(20, y, 760, rh); hov = self._hover(r); master = a["pid"] == -1
            self._glass(p, r, 14, hov)
            if master: p.setPen(QPen(rgba(ACCENT, 90), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(r, 14, 14)
            vol = a["vol"]; loc = self._mx_local.get(a["pid"])
            if loc and now_ < loc[1]: vol = loc[0]
            icr = QRectF(r.x() + 14, r.center().y() - 14, 28, 28)
            if master: draw_icon(p, "vol", icr.adjusted(2, 2, -2, -2), rgba(ACCENT.lighter(130), 255))
            else: p.drawPixmap(icr.toRect(), self._ds_icon(a["exe"], 28, a["name"]) if a["exe"] else self._letter_tile(a["name"] or "?", 28))
            nm = a["name"][:-4] if a["name"].lower().endswith(".exe") else a["name"]
            p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 240 if not a["mute"] else 130))
            p.drawText(QRectF(r.x() + 54, r.y() + 6, 200, 18), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(nm.capitalize() if nm.islower() else nm, Qt.TextElideMode.ElideRight, 196))
            if not master:      # индикатор уровня звука приложения
                pk = min(1.0, a["peak"] * 2.2); self._gv["mp%d" % a["pid"]] = self._gv.get("mp%d" % a["pid"], 0.0) * 0.7 + pk * 0.3; pk = self._gv["mp%d" % a["pid"]]
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 22)); p.drawRoundedRect(QRectF(r.x() + 54, r.y() + 30, 190, 4), 2, 2)
                p.setBrush(rgba(ACCENT, 230)); p.drawRoundedRect(QRectF(r.x() + 54, r.y() + 30, max(3.0, 190 * pk), 4), 2, 2)
            else:
                p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 110)); p.drawText(QRectF(r.x() + 54, r.y() + 26, 200, 14), AL.AlignLeft | AL.AlignVCenter, "Динамики по умолчанию")
            tr = QRectF(r.x() + 272, r.center().y() - 3, 372, 6); hit = QRectF(tr.x() - 8, r.y() + 6, tr.width() + 16, rh - 12)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 30)); p.drawRoundedRect(tr, 3, 3)
            f = max(0.0, min(1.0, vol)); col = QColor(150, 155, 170) if a["mute"] else ACCENT
            p.setBrush(col); p.drawRoundedRect(QRectF(tr.x(), tr.y(), max(6.0, tr.width() * f), 6), 3, 3)
            kx = tr.x() + tr.width() * f; p.setBrush(QColor(255, 255, 255)); p.drawEllipse(QPointF(kx, tr.center().y()), 7.5 if self._hover(hit) else 6.5, 7.5 if self._hover(hit) else 6.5)
            p.setFont(font(11, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(QRectF(r.x() + 656, r.y(), 44, rh), AL.AlignRight | AL.AlignVCenter, f"{vol * 100:.0f}%")
            self._add_hit(hit, lambda pid=a["pid"], rr_=tr: self._mx_start(pid, rr_))
            if not master:
                mb = QRectF(r.right() - 44, r.center().y() - 14, 28, 28); hm = self._hover(mb)
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 90, 100, 90) if a["mute"] else QColor(255, 255, 255, 30 if hm else 14)); p.drawRoundedRect(mb, 9, 9)
                draw_icon(p, "vol", mb.adjusted(6, 6, -6, -6), QColor(255, 120, 130) if a["mute"] else QColor(255, 255, 255, 200))
                if a["mute"]: p.setPen(QPen(QColor(255, 120, 130), 1.8)); p.drawLine(QPointF(mb.x() + 7, mb.y() + 7), QPointF(mb.right() - 7, mb.bottom() - 7))
                self._add_hit(mb, lambda aa=a: self._mx_mute(aa))
            y += rh + gap
        if not apps:
            p.setFont(font(12)); p.setPen(QColor(255, 255, 255, 120)); p.drawText(QRectF(20, y + 8, 760, 24), AL.AlignCenter, "Сейчас ни одно приложение не воспроизводит звук")
        elif len(apps) > 7:
            p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 120)); p.drawText(QRectF(20, y + 2, 760, 18), AL.AlignCenter, f"и ещё {len(apps) - 7}")

    def _shelf_item_info(self, path):
        c = self._shelf_info.get(path); now_ = time.monotonic()
        if c and now_ - c[0] < 2.0: return c[1]
        try: ex = os.path.exists(path); isdir = os.path.isdir(path); sz = os.path.getsize(path) if ex and not isdir else 0
        except Exception: ex = isdir = False; sz = 0
        info = (ex, isdir, sz, path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")))
        self._shelf_info[path] = (now_, info); return info

    def _shelf_thumb(self, path):
        if path in self._shelf_thumbs: return self._shelf_thumbs[path] or None
        pm = QPixmap(path)
        if pm.isNull(): self._shelf_thumbs[path] = False; return None
        pm = pm.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self._shelf_thumbs[path] = pm; return pm

    def _draw_shelf(self, p):
        AL = Qt.AlignmentFlag; items = self._shelf.items; now_ = time.monotonic(); t = now_
        self._shelf_rects = []; self._shelf_x = []
        p.setFont(font(26, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(28, 48, 300, 36), AL.AlignLeft | AL.AlignVCenter, "Полка")
        fm_, fu_, fok_ = self._shelf_flash
        p.setFont(font(10))
        if self._drag_over: p.setPen(rgba(ACCENT.lighter(130), 245)); txt = "Отпусти файл — он ляжет на полку"
        elif fm_ and now_ < fu_: p.setPen(QColor(120, 255, 170, 245) if fok_ else QColor(255, 190, 110, 245)); txt = fm_
        else: p.setPen(QColor(255, 255, 255, 120)); txt = f"{len(items)} из {SHELF_MAX} · перетащи файл на остров, чтобы положить сюда · клик — открыть, потянуть — вынуть"
        p.drawText(QRectF(29, 84, self.EW - 170, 16), AL.AlignLeft | AL.AlignVCenter, txt)
        if items:
            rc = QRectF(self.EW - 124, 62, 104, 28); hv = self._hover(rc)
            p.setPen(QPen(QColor(255, 255, 255, 46 if hv else 24), 1)); p.setBrush(QColor(255, 90, 100, 60 if hv else 0)); p.drawRoundedRect(rc, 14, 14)
            p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 215 if hv else 150)); p.drawText(rc, AL.AlignCenter, "Очистить")
            self._add_hit(rc, lambda: (self._shelf.clear(), self.update()))
        if self._drag_over:
            pulse = 0.5 + 0.5 * math.sin(t * 6)
            p.setPen(QPen(rgba(ACCENT, int(140 + 90 * pulse)), 2, Qt.PenStyle.DashLine)); p.setBrush(rgba(ACCENT, 16)); p.drawRoundedRect(QRectF(12, 104, self.EW - 24, 420), 22, 22)
        for r in range(2):
            top = 108 + r * 206; by = top + 116
            panel = QRectF(20, top + 2, self.EW - 40, 128); self._ios_card(p, panel, 24)
            sg = QLinearGradient(0, by + 14, 0, by + 38); sg.setColorAt(0, QColor(0, 0, 0, 90)); sg.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(sg); p.drawRect(QRectF(34, by + 14, self.EW - 68, 24))
            bd = QRectF(20, by, self.EW - 40, 14); bg_ = QLinearGradient(0, by, 0, by + 14)
            bg_.setColorAt(0, QColor(255, 255, 255, 96)); bg_.setColorAt(0.5, QColor(255, 255, 255, 40)); bg_.setColorAt(1, rgba(ACCENT, 54))
            p.setBrush(bg_); p.drawRoundedRect(bd, 7, 7)
            p.setPen(QPen(QColor(255, 255, 255, 150), 1)); p.drawLine(QPointF(32, by + 1.5), QPointF(self.EW - 32, by + 1.5))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 150))
            for px_ in (50, self.EW - 50): p.drawEllipse(QPointF(px_, by + 8), 2.4, 2.4)
            for c in range(6):
                idx = r * 6 + c; cx = 100 + c * 120
                if idx >= len(items):
                    pu = (0.5 + 0.5 * math.sin(t * 6)) if (self._drag_over and idx == len(items)) else 0.0
                    p.setPen(QPen(rgba(ACCENT, int(70 + 140 * pu)) if pu else QColor(255, 255, 255, 18), 1.2, Qt.PenStyle.DashLine)); p.setBrush(rgba(ACCENT, int(40 * pu)))
                    p.drawRoundedRect(QRectF(cx - 34, by - 76, 68, 68), 16, 16); continue
                item = items[idx]; ex, isdir, sz, isimg = self._shelf_item_info(item["path"])
                hit = QRectF(cx - 56, by - 92, 112, 152); hov = self._hover(hit) and not self._drag_over
                key = f"sh{idx}"; h = self._gv.get(key, 0.0); h += ((1.0 if hov else 0.0) - h) * 0.25; self._gv[key] = h
                tile = QRectF(cx - 36, by - 84 - 8 * h, 72, 72)
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, int(80 - 30 * h))); p.drawEllipse(QPointF(cx, by + 4), 32 - 5 * h, 4.2)
                if h > 0.02:
                    gg = QRadialGradient(tile.center(), 60); gg.setColorAt(0, rgba(ACCENT, int(70 * h))); gg.setColorAt(1, rgba(ACCENT, 0)); p.setBrush(gg); p.drawEllipse(tile.center(), 60, 60)
                p.save(); p.setOpacity(1.0 if ex else 0.4)
                tp = QPainterPath(); tp.addRoundedRect(tile, 18, 18); thumb = self._shelf_thumb(item["path"]) if (isimg and ex) else None
                if thumb is not None:
                    p.save(); p.setClipPath(tp); p.drawPixmap(tile.toRect(), thumb); p.restore()
                else:
                    tg = QLinearGradient(tile.topLeft(), tile.bottomRight()); tg.setColorAt(0, QColor(255, 255, 255, int(34 + 22 * h))); tg.setColorAt(1, QColor(255, 255, 255, int(12 + 12 * h)))
                    p.setBrush(tg); p.drawPath(tp)
                    p.drawPixmap(QRectF(tile.center().x() - 24, tile.center().y() - 24, 48, 48).toRect(), self._ds_icon(item["path"], 48, item.get("name")))
                p.setPen(QPen(QColor(255, 255, 255, int(46 + 60 * h)), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(tile, 18, 18); p.restore()
                if not ex:
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 90, 90, 230)); p.drawEllipse(QPointF(tile.x() + 10, tile.y() + 10), 8, 8)
                    p.setFont(font(10, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255)); p.drawText(QRectF(tile.x() + 2, tile.y() + 2, 16, 16), AL.AlignCenter, "!")
                p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 235))
                p.save(); p.setClipRect(QRectF(cx - 56, by + 20, 112, 32))
                p.drawText(QRectF(cx - 54, by + 21, 108, 32), int(AL.AlignHCenter.value | AL.AlignTop.value | Qt.TextFlag.TextWrapAnywhere.value), item.get("name", ""))
                p.restore()
                p.setFont(font(8)); p.setPen(QColor(255, 140, 140, 200) if not ex else QColor(255, 255, 255, 110))
                p.drawText(QRectF(cx - 54, by + 54, 108, 12), AL.AlignCenter, "файл не найден" if not ex else ("папка" if isdir else self._fmt_size(sz)))
                self._shelf_rects.append((hit, idx))
                if hov:
                    xb = QRectF(tile.right() - 12, tile.y() - 8, 20, 20); hx = self._hover(xb)
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 90, 100, 230 if hx else 150)); p.drawEllipse(xb)
                    p.setFont(font(12, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255)); p.drawText(xb, AL.AlignCenter, "×")
                    self._shelf_x.append((xb, idx))
        if not items and not self._drag_over:
            p.setFont(font(12)); p.setPen(QColor(255, 255, 255, 110)); p.drawText(QRectF(0, 150, self.EW, 20), AL.AlignCenter, "Полка пуста")

    def _draw_compact_stats(self, p, iw, ih):
        """Компактные «полосочки» с цифрами: CPU, RAM, GPU, FPS. Возвращает False, если ничего не включено."""
        AL = Qt.AlignmentFlag; ms = []
        if self._wb("cs_cpu", True): ms.append(("CPU", self.d["cpu"] / 100.0, f"{self.d['cpu']:.0f}%", False))
        if self._wb("cs_ram", True): ms.append(("RAM", self.d["mem"] / 100.0, f"{self.d['mem']:.0f}%", False))
        if self._wb("cs_gpu", True):
            g = self._gpu; ms.append(("GPU", g.load / 100.0 if g.ok else 0.0, f"{g.load:.0f}%" if g.ok else "…", False))
        if self._wb("cs_fps", True):
            try: hz = float(self._anim_hz())
            except Exception: hz = 60.0
            ms.append(("FPS", min(1.0, self._fps / max(1.0, hz)), f"{self._fps:.0f}", True))
        if not ms: return False
        n = len(ms); gap = 14.0; x0 = 18.0; cw = (iw - 2 * x0 - gap * (n - 1)) / n
        if cw < 24: return True
        for i, (lb, fr, txt, good) in enumerate(ms):
            key = "cs" + lb; cur = self._gv.get(key, 0.0); cur += (fr - cur) * 0.18; self._gv[key] = cur
            f = max(0.0, min(1.0, cur)); x = x0 + i * (cw + gap)
            col = QColor(110, 235, 160) if good else (QColor(255, 90, 90) if f > 0.85 else (QColor(255, 170, 70) if f > 0.65 else ACCENT))
            p.setFont(font(8, QFont.Weight.DemiBold, spacing=0.8)); p.setPen(QColor(255, 255, 255, 140))
            p.drawText(QRectF(x, 4, cw, 14), AL.AlignLeft | AL.AlignVCenter, lb)
            p.setFont(font(11, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 245))
            p.drawText(QRectF(x, 4, cw, 14), AL.AlignRight | AL.AlignVCenter, txt)
            by = ih - 13; bh = 5.0
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 28)); p.drawRoundedRect(QRectF(x, by, cw, bh), bh / 2, bh / 2)
            fw = max(bh, cw * f)
            gg = QLinearGradient(x, 0, x + cw, 0); gg.setColorAt(0, col.darker(130)); gg.setColorAt(1, col.lighter(125))
            p.setBrush(rgba(col, 60)); p.drawRoundedRect(QRectF(x - 1, by - 2, fw + 2, bh + 4), bh, bh)
            p.setBrush(gg); p.drawRoundedRect(QRectF(x, by, fw, bh), bh / 2, bh / 2)
        return True

    def _compact_menu(self, gpos):
        m = QMenu(self)
        m.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(0,205,255,80)}QMenu::separator{height:1px;background:rgba(255,255,255,25);margin:4px 8px}")
        def add(label, key, default):
            a = m.addAction(label); a.setCheckable(True); a.setChecked(self._wb(key, default))
            a.toggled.connect(lambda v, k=key: (self.settings.setValue(k, bool(v)), self._wake(), self.update()))
        add("📊 Показатели в островке", "compact_stats", False); m.addSeparator()
        add("Процессор", "cs_cpu", True); add("Память", "cs_ram", True); add("Видеокарта", "cs_gpu", True); add("FPS", "cs_fps", True)
        m.addSeparator(); m.addAction("☰ Меню острова", lambda: self.menu.exec(gpos)); m.exec(gpos)

    def _draw_edge_wave(self, p, iw, ih):
        """Звук как волна вдоль свободного края острова."""
        d = self._eq_disp; n = 32; rb = min(self._rb, iw / 2.0, ih / 2.0); x0 = rb * 0.8 + 6.0; x1 = iw - x0
        if x1 - x0 < 24: return
        amp = min(8.0, 3.0 + ih * 0.05); base = ih - 2.6
        pts = [QPointF(x0 + (x1 - x0) * i / (n - 1), base - amp * (min(1.0, d[i]) ** 0.9)) for i in range(n)]
        pp = QPainterPath(); pp.moveTo(pts[0])
        for i in range(1, n): pp.quadTo(pts[i - 1], QPointF((pts[i - 1].x() + pts[i].x()) / 2, (pts[i - 1].y() + pts[i].y()) / 2))
        pp.lineTo(pts[-1]); c = self._dyn(); p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(rgba(c, 60), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); p.drawPath(pp)
        p.setPen(QPen(rgba(c, 235), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); p.drawPath(pp)

    def _draw_mini_eq(self, p, rect, bars=5):
        """Маленький эквалайзер: пять групп частот из реального (или рассчитанного по уровню) спектра."""
        groups = [(0, 3), (3, 8), (8, 14), (14, 22), (22, 32)][:bars]
        bw = 3.6; gap = (rect.width() - bars * bw) / max(1, bars - 1); c = self._dyn()
        p.setPen(Qt.PenStyle.NoPen)
        for i, (a, b) in enumerate(groups):
            v = max(self._eq_disp[a:b]); bh = max(3.0, rect.height() * (0.18 + 0.82 * v))
            x = rect.x() + i * (bw + gap); y = rect.bottom() - bh
            g = QLinearGradient(x, y, x, y + bh); g.setColorAt(0, QColor(min(255, c.red() + 60), min(255, c.green() + 60), min(255, c.blue() + 60))); g.setColorAt(1, rgba(c, 150))
            p.setBrush(g); p.drawRoundedRect(QRectF(x, y, bw, bh), bw / 2, bw / 2)

    def _draw_spectrum(self, p, rect, color, style=None, alpha=1.0):
        """Большая визуализация. Стили: 0 столбики, 1 зеркало, 2 волна, 3 точки."""
        if style is None:
            try: style = int(self.settings.value("eq_style", 1))
            except Exception: style = 1
        n = 32; d = self._eq_disp; pk = self._eq_peak
        pitch = rect.width() / n; bw = max(2.0, pitch * 0.62)
        p.setPen(Qt.PenStyle.NoPen)
        if style == 2:
            pts = [QPointF(rect.x() + (i + 0.5) * pitch, rect.bottom() - rect.height() * (0.04 + 0.96 * d[i])) for i in range(n)]
            wp = QPainterPath(); wp.moveTo(rect.x(), rect.bottom()); wp.lineTo(pts[0])
            for i in range(1, n):
                mx = (pts[i - 1].x() + pts[i].x()) / 2
                wp.cubicTo(QPointF(mx, pts[i - 1].y()), QPointF(mx, pts[i].y()), pts[i])
            wp.lineTo(rect.right(), rect.bottom()); wp.closeSubpath()
            g = QLinearGradient(0, rect.top(), 0, rect.bottom()); g.setColorAt(0, rgba(color, int(200 * alpha))); g.setColorAt(1, rgba(color, 0))
            p.setBrush(g); p.drawPath(wp)
            return
        for i in range(n):
            x = rect.x() + i * pitch + (pitch - bw) / 2; v = d[i]
            if style == 3:
                rows = int(1 + v * 9); dot = bw * 0.9
                for r_ in range(rows):
                    a = 0.35 + 0.65 * r_ / 9.0
                    p.setBrush(rgba(color, int(235 * a * alpha))); p.drawEllipse(QPointF(x + bw / 2, rect.bottom() - dot / 2 - r_ * (dot + 2.2)), dot / 2, dot / 2)
                continue
            if style == 1:
                mid = rect.center().y(); h2 = max(1.5, rect.height() * 0.5 * (0.06 + 0.94 * v))
                g = QLinearGradient(0, mid - h2, 0, mid + h2); g.setColorAt(0, rgba(color, int(220 * alpha))); g.setColorAt(0.5, rgba(color, int(120 * alpha))); g.setColorAt(1, rgba(color, int(220 * alpha)))
                p.setBrush(g); p.drawRoundedRect(QRectF(x, mid - h2, bw, h2 * 2), bw / 2, bw / 2)
            else:
                h = max(2.0, rect.height() * (0.04 + 0.96 * v)); y = rect.bottom() - h
                g = QLinearGradient(0, y, 0, rect.bottom()); g.setColorAt(0, rgba(color, int(230 * alpha))); g.setColorAt(1, rgba(color, int(40 * alpha)))
                p.setBrush(g); p.drawRoundedRect(QRectF(x, y, bw, h), bw / 2, bw / 2)
                if pk[i] > v + 0.04:
                    p.setBrush(QColor(255, 255, 255, int(150 * alpha))); p.drawRoundedRect(QRectF(x, rect.bottom() - rect.height() * pk[i] - 3, bw, 2), 1, 1)

    def _draw_equalizer(self, p, rect, bars=14, color=ACCENT):
        p.setPen(Qt.PenStyle.NoPen)
        t = self._glow * 8.0 + time.monotonic() * 2.0
        bar_w = rect.width() / bars
        for i in range(bars):
            a = math.sin(t + i * 0.55) * 0.5 + 0.5
            b = math.sin(t * 1.7 + i * 0.9) * 0.5 + 0.5
            amp = (a * 0.55 + b * 0.45)
            bh = rect.height() * (0.15 + 0.85 * amp)
            g = QLinearGradient(rect.x()+i*bar_w, rect.y()+rect.height()-bh, rect.x()+i*bar_w, rect.y()+rect.height())
            g.setColorAt(0, rgba(color, 230)); g.setColorAt(1, rgba(color, 80))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(rect.x() + i*bar_w + 1, rect.y() + rect.height() - bh, bar_w - 2, bh), 1.5, 1.5)

    def _draw_compact(self, p, iw, ih):
        if self._alarm and self._draw_compact_alarm(p, iw, ih): return
        if self._dl_cur and not (self._notify and self._notify.get("force")) and self._draw_compact_download(p, iw, ih): return
        if self._notify:
            n = self._notify; now_ = time.monotonic()
            elapsed = now_ - n.get("start", 0)
            slide_in = 1.0 - math.exp(-elapsed * 12.0)
            if n.get("out_start", 0) > 0: slide = slide_in * (1.0 - min((now_ - n["out_start"]) / 0.28, 1.0))
            else: slide = slide_in
            col = n.get("color") if n.get("color") is not None else ACCENT
            cx, cy = 24, ih / 2
            if n.get("out_start", 0) == 0:       # круги от значка, как рябь
                for i in range(3):
                    ring_age = elapsed - i * 0.12
                    if 0 <= ring_age < 0.8:
                        ring_alpha = int((1.0 - ring_age / 0.8) * 130 * slide)
                        if ring_alpha > 0:
                            p.setPen(QPen(rgba(col, ring_alpha), 2)); p.setBrush(Qt.BrushStyle.NoBrush)
                            p.drawEllipse(QPointF(cx, cy), 12 + ring_age * 60, 12 + ring_age * 60)
            p.setPen(Qt.PenStyle.NoPen)
            g = QRadialGradient(QPointF(cx, cy), 18); g.setColorAt(0, rgba(col, int(120 * slide))); g.setColorAt(1, rgba(col, 0))
            p.setBrush(g); p.drawEllipse(QPointF(cx, cy), 18, 18)
            pop = max(0.1, 1.0 + 0.32 * math.exp(-elapsed * 8.0) * math.sin(elapsed * 20.0 + 1.2)) * (0.55 + 0.45 * slide_in)
            bg_ = QLinearGradient(cx, cy - 12, cx, cy + 12); bg_.setColorAt(0, col.lighter(125)); bg_.setColorAt(1, col.darker(115))
            p.save(); p.translate(cx, cy); p.scale(pop, pop); p.setOpacity(p.opacity() * min(1.0, slide * 1.4))
            p.setBrush(bg_); p.drawEllipse(QPointF(0, 0), 12, 12)
            p.setFont(font(12, QFont.Weight.Bold, family="Segoe UI Emoji")); p.setPen(QColor(255, 255, 255, 250))
            p.drawText(QRectF(-12, -12, 24, 24), Qt.AlignmentFlag.AlignCenter, n["icon"]); p.restore()
            tx = cx + 24 + 16 * (1 - slide); tw = iw - tx - 18
            AL = Qt.AlignmentFlag
            if tw > 20:
                if n.get("app"):
                    p.setFont(font(8, QFont.Weight.DemiBold, spacing=0.8)); p.setPen(rgba(col.lighter(135), int(225 * slide)))
                    p.drawText(QRectF(tx, 3, tw, 13), AL.AlignLeft | AL.AlignVCenter, n["app"].upper())
                    f1 = font(12, QFont.Weight.Bold); f2 = font(12); fm1 = QFontMetrics(f1); fm2 = QFontMetrics(f2)
                    head = fm1.elidedText(n["text"], Qt.TextElideMode.ElideRight, int(tw * (0.55 if n.get("sub") else 1.0)))
                    hw = fm1.horizontalAdvance(head)
                    base = 16 + (ih - 20 - 6) / 2 + (fm1.ascent() - fm1.descent()) / 2
                    p.setFont(f1); p.setPen(QColor(255, 255, 255, int(250 * slide))); p.drawText(QPointF(tx, base), head)
                    if n.get("sub") and tw - hw - 8 > 12:
                        p.setFont(f2); p.setPen(QColor(255, 255, 255, int(165 * slide)))
                        p.drawText(QPointF(tx + hw + 8, base), fm2.elidedText(n["sub"], Qt.TextElideMode.ElideRight, int(tw - hw - 8)))
                else:
                    p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, int(245 * slide)))
                    p.drawText(QRectF(tx, 0, tw, ih), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(n["text"], Qt.TextElideMode.ElideRight, int(tw)))
            return
        if self._live_cur and self._draw_compact_live(p, iw, ih): return
        if self._wb("compact_stats", False) and self._draw_compact_stats(p, iw, ih): return
        is_playing = self.media.get("active") and self.media.get("playing") and self.mod_music
        cover_r = None
        if is_playing:
            self._draw_mini_eq(p, QRectF(16, (ih - 18) / 2, 30, 18))
            th = self.media.get("thumb")
            if th is not None and not th.isNull():
                cover_r = QRectF(iw - 38, (ih - 24) / 2, 24, 24)
                glow = min(1.0, self._bass * 1.5); c_ = self._dyn()
                gg = QRadialGradient(cover_r.center(), 20); gg.setColorAt(0, rgba(c_, int(40 + 120 * glow))); gg.setColorAt(1, rgba(c_, 0))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(gg); p.drawEllipse(cover_r.center(), 20, 20)
                cp = QPainterPath(); cp.addRoundedRect(cover_r, 7, 7)
                p.save(); p.setClipPath(cp); p.drawPixmap(cover_r.toRect(), th); p.restore()
                p.setPen(QPen(QColor(255, 255, 255, 46), 1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(cover_r, 7, 7)
        else:
            self._draw_eyes(p, 26, ih/2)
        items = [(self.now.strftime("%H:%M"), font(14, QFont.Weight.DemiBold, spacing=0.6), QColor(255, 255, 255, 245), 0)]
        if self.mod_weather and self.weather.get("ok"):
            temp = self.weather.get("temp"); code = self.weather.get("code", 0); desc, icon = WMO_CODES.get(code, ("—", "?"))
            items.append((f"{icon} {self._wtemp(temp)}" + (f" {str(self.weather.get('city') or '')[:10]}" if self._wb("w_compact_city", False) else ""), font(12, QFont.Weight.DemiBold), rgba(WEATHER_COLOR, 245), 3))
        if self.mod_timer and self.t_running: items.append((fmt_mmss(self.t_left), font(12, QFont.Weight.DemiBold), QColor(255, 140, 100), 1))
        if self.battery and self.battery[0] <= 20 and not self.battery[1]: items.append((f"🪫 {self.battery[0]:.0f}%", font(11, QFont.Weight.DemiBold), QColor(255, 110, 110), 4))
        nr = self._reminders.next_today(datetime.datetime.now())
        if nr: items.append(((f"🔔 {nr.get('time') or ''} {nr.get('text', '')[:9]}").replace("  ", " "), font(10), QColor(255, 180, 80, 240), 5))
        right_lim = iw - (46 if cover_r is not None else 20)
        if self.mod_timer and self.t_running and self.t_total:
            fr = max(0.0, min(1.0, self.t_left / self.t_total)); bw = max(10.0, right_lim - 20)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 18)); p.drawRoundedRect(QRectF(20, ih - 3.5, bw, 2), 1, 1)
            gb = QLinearGradient(20, 0, 20 + bw, 0); gb.setColorAt(0, QColor(255, 140, 100)); gb.setColorAt(1, VIOLET)
            p.setBrush(gb); p.drawRoundedRect(QRectF(20, ih - 3.5, bw * fr, 2), 1, 1)
        f_sep = font(11); area_x = 56; area_w = iw - area_x - (46 if cover_r is not None else 14)
        def measure(its, sp): return sum(QFontMetrics(f).horizontalAdvance(tx) for tx, f, _c, _p in its) + QFontMetrics(f_sep).horizontalAdvance(sp) * max(0, len(its) - 1)
        sep = "  ·  "
        while len(items) > 1 and measure(items, sep) > area_w:       # не помещается (музыка + таймер + погода…) — убираем наименее важное
            worst = max(range(len(items)), key=lambda k: items[k][3])
            if items[worst][3] == 0: break
            items.pop(worst)
        if measure(items, sep) > area_w: sep = " · "
        sep_w = QFontMetrics(f_sep).horizontalAdvance(sep); widths = [QFontMetrics(f).horizontalAdvance(tx) for tx, f, _c, _p in items]
        total_w = sum(widths) + sep_w * max(0, len(items) - 1); x = area_x + (area_w - total_w) / 2
        if x < area_x: x = area_x
        for i, (text, f, col, _pr) in enumerate(items):
            fm = QFontMetrics(f); base = ih / 2 + (fm.ascent() - fm.descent()) / 2
            p.setFont(f); p.setPen(col); p.drawText(QPointF(x, base), text); x += widths[i]
            if i < len(items) - 1:
                p.setFont(f_sep); p.setPen(QColor(255, 255, 255, 100)); sfm = QFontMetrics(f_sep); sbase = ih / 2 + (sfm.ascent() - sfm.descent()) / 2
                p.drawText(QPointF(x, sbase), sep); x += sep_w

    def _nav_btn(self, p, r, icon, cb):
        hov = self._hover(r); self._glass(p, r, 11, hov)
        draw_icon(p, icon, r.adjusted(9, 8, -9, -8), ACCENT.lighter(140) if hov else QColor(255, 255, 255, 205)); self._add_hit(r, cb)

    def _draw_top_nav(self, p, iw):
        AL = Qt.AlignmentFlag
        is_ai = (self.current_page == "ai" and self._ai_view is not None and self._ai_view.isVisible())
        self._glass(p, QRectF(20, 8, (self.EW - 340) if is_ai else (self.EW - 130), 40), 20)
        max_x = self.EW - 335 if is_ai else self.EW - 125
        fm = QFontMetrics(font(11, QFont.Weight.DemiBold)); rects = []; x = 28.0
        for icon, key, label in TABS:
            active = self.current_page == key; w = 38 + (fm.horizontalAdvance(label) + 8 if active else 0)
            if x + w > max_x: break
            rects.append((key, label, QRectF(x, 13, w, 30), active)); x += w + 4
        act = next((r for (_k, _l, r, a) in rects if a), None)
        if act is not None:       # скользящий индикатор активной вкладки
            ind = self._nav_ind if self._nav_ind is not None else [act.x(), act.width()]
            ind[0] += (act.x() - ind[0]) * 0.3; ind[1] += (act.width() - ind[1]) * 0.3; self._nav_ind = ind
            ir = QRectF(ind[0], act.y(), ind[1], act.height())
            p.setPen(QPen(rgba(ACCENT, 135), 1)); p.setBrush(rgba(ACCENT, 38)); p.drawRoundedRect(ir, 15, 15)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(ACCENT); p.drawRoundedRect(QRectF(ir.center().x() - 9, ir.bottom() - 3.5, 18, 2.5), 1.2, 1.2)
        for key, label, r, active in rects:
            hov = self._hover(r)
            if hov and not active: p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 18)); p.drawRoundedRect(r, 15, 15)
            draw_icon(p, TAB_ICON[key], QRectF(r.x() + 11, r.y() + 7, 16, 16), ACCENT.lighter(135) if active else QColor(255, 255, 255, 218 if hov else 155))
            if active:
                p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 252))
                p.drawText(QRectF(r.x() + 32, r.y(), r.width() - 32, r.height()), AL.AlignLeft | AL.AlignVCenter, label)
            self._add_hit(r, lambda k=key: self._switch_page(k))

        if is_ai:
            # быстрое переключение между ИИ-сервисами
            for k, (nm, url_, col_) in enumerate((("DeepSeek", "https://chat.deepseek.com", QColor(77, 107, 254)),
                                                  ("Gemini", "https://gemini.google.com/app", QColor(66, 133, 244)))):
                pr = QRectF(self.EW - 312 + k * 80, 16, 76, 24); act_ = self._ai_service == nm.lower(); hv_ = self._hover(pr)
                p.setPen(QPen(rgba(col_, 200), 1) if act_ else Qt.PenStyle.NoPen)
                p.setBrush(rgba(col_, 110) if act_ else QColor(255, 255, 255, 30 if hv_ else 14)); p.drawRoundedRect(pr, 12, 12)
                p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 245 if act_ else 190))
                p.drawText(pr, Qt.AlignmentFlag.AlignCenter, nm)
                self._add_hit(pr, lambda u=url_: self._ai_open_inline(u))
            # Кнопка "Назад" (к карточкам сервисов)
            r_back = QRectF(self.EW - 150, 16, 30, 24)
            hov_b = self._hover(r_back)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 50 if hov_b else 25))
            p.drawRoundedRect(r_back, 10, 10)
            p.setFont(font(14, QFont.Weight.Bold))
            p.setPen(QColor(255, 255, 255, 240))
            p.drawText(r_back, Qt.AlignmentFlag.AlignCenter, "←")
            self._add_hit(r_back, self._ai_close_inline)

            # Кнопка "Обновить"
            r_reload = QRectF(self.EW - 112, 16, 30, 24)
            hov_r = self._hover(r_reload)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 50 if hov_r else 25))
            p.drawRoundedRect(r_reload, 10, 10)
            p.setFont(font(14, QFont.Weight.Bold))
            p.setPen(QColor(255, 255, 255, 240))
            p.drawText(r_reload, Qt.AlignmentFlag.AlignCenter, "↻")
            self._add_hit(r_reload, lambda: self._ai_view.reload() if self._ai_view else None)

            # Кнопка "В окно"
            r_pop = QRectF(self.EW - 74, 16, 30, 24)
            hov_p = self._hover(r_pop)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 205, 255, 60 if hov_p else 30))
            p.drawRoundedRect(r_pop, 10, 10)
            draw_icon(p, "screen", r_pop.adjusted(6, 5, -6, -5), QColor(255, 255, 255, 240))
            self._add_hit(r_pop, self._ai_pop_out)
        else:
            self._nav_btn(p, QRectF(self.EW - 72, 12, 34, 32), "gear", self._open_settings)
            if self.current_page == "home": self._nav_btn(p, QRectF(self.EW - 110, 12, 34, 32), "grid", self._open_tools_editor)

    def _dyn(self): return getattr(self, "_mcol", None) or QColor(255, 140, 70)

    def _ios_card(self, p, r, rad=22, hov=False):
        """Карточка в стиле iOS: плотный тёмный фон, крупное скругление, тонкая кромка."""
        st = self._ui_style(); base = {0: (30, 30, 34), 1: (38, 40, 48), 2: (28, 31, 40), 3: (8, 12, 22), 4: (0, 0, 0)}.get(st, (30, 30, 34))
        p.setBrush(QColor(base[0], base[1], base[2], 255 if hov else 248))
        p.setPen(QPen(rgba(ACCENT, 150 if hov else 90), 1.2) if st == 3 else QPen(QColor(255, 255, 255, 26 if hov else 14), 1)); p.drawRoundedRect(r, rad, rad)

    def _ios_title(self, p, title, sub=""):
        AL = Qt.AlignmentFlag
        p.setFont(font(26, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(28, 48, 460, 36), AL.AlignLeft | AL.AlignVCenter, title)
        if sub: p.setFont(font(11)); p.setPen(IOS_GRAYT); p.drawText(QRectF(29, 84, 560, 16), AL.AlignLeft | AL.AlignVCenter, sub)

    def _ios_pill(self, p, r, text, fill, fg, cb=None, fpx=12, bold=True):
        hov = self._hover(r); c = QColor(fill); c = c.lighter(112) if hov else c
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(c); p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setFont(font(fpx, QFont.Weight.DemiBold if bold else QFont.Weight.Normal)); p.setPen(fg); p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        if cb is not None: self._add_hit(r, cb)

    def _ios_round_btn(self, p, c, d, text, col, cb):
        """Круглая кнопка как в «Таймере» iPhone: цветной круг с кольцом."""
        r = QRectF(c.x() - d / 2, c.y() - d / 2, d, d); hov = self._hover(r)
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(rgba(col, 90 if hov else 55), 1.6)); p.drawEllipse(c, d / 2 + 4, d / 2 + 4)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(col, 78 if hov else 58)); p.drawEllipse(c, d / 2, d / 2)
        p.setFont(font(14, QFont.Weight.DemiBold)); p.setPen(col.lighter(125)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, text); self._add_hit(r, cb)

    def _ui_style(self):
        try: return int(self.settings.value("ui_style", 0))
        except Exception: return 0

    def _glass(self, p, r, rad=14, hov=False):
        """Единый контейнер всех панелей. Вид зависит от выбранного стиля: стекло, графит, корпоративный, неон, полночь."""
        st = self._ui_style(); p.setBrush(Qt.BrushStyle.NoBrush)
        if st == 1: fill = QColor(38, 40, 48, 240 if hov else 230); pen = QPen(QColor(255, 255, 255, 34 if hov else 18), 1)
        elif st == 2: fill = QColor(28, 31, 40, 252 if hov else 246); pen = QPen(QColor(255, 255, 255, 78 if hov else 40), 1)
        elif st == 3:
            fill = QColor(6, 10, 20, 226)
            if hov: p.setPen(QPen(rgba(ACCENT, 60), 5)); p.drawRoundedRect(r, rad, rad)
            pen = QPen(rgba(ACCENT, 235 if hov else 150), 1.2)
        elif st == 4: fill = QColor(0, 0, 0, 255); pen = QPen(QColor(255, 255, 255, 84 if hov else 38), 1)
        else: fill = QColor(255, 255, 255, 22 if hov else 11); pen = QPen(QColor(255, 255, 255, 26 if hov else 12), 1)
        p.setBrush(fill); p.setPen(pen); p.drawRoundedRect(r, rad, rad)

    def _safe(self, p, name, fn, *a):
        """Рисует раздел изолированно: при ошибке возвращает состояние кисти (трансформация, прозрачность, обрезка) и продолжает."""
        tr = p.transform(); op = p.opacity(); had = p.hasClipping(); cp = p.clipPath() if had else None
        try: fn(*a)
        except Exception as e:
            now = time.monotonic()
            if now - self._err_ts.get(name, 0.0) > 5.0: self._err_ts[name] = now; log_error(f"draw {name}: {e}\n{traceback.format_exc()}")
            try:
                p.setTransform(tr); p.setOpacity(op)
                if had: p.setClipPath(cp)
                else: p.setClipping(False)
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(Qt.BrushStyle.NoBrush)
            except Exception: pass

    def _draw_home(self, p):
        for nm, fn in (("player", self._draw_big_media), ("tools", self._draw_tools_grid), ("dock", self._draw_dock), ("search", self._draw_dsearch_results)):
            self._safe(p, nm, fn, p)

    def _ensure_lyrics(self):
        key = (self.media.get("title", ""), self.media.get("artist", ""))
        if key == getattr(self, "_lyr_key", None): return
        self._lyr_key = key; self._lyr = None
        if not key[0]: return
        def work(k=key, dur=int(self.media.get("duration", 0) or 0)):
            try:
                import re as _re
                from urllib.parse import quote
                from urllib.request import urlopen
                d = json.load(urlopen(f"https://lrclib.net/api/get?artist_name={quote(k[1])}&track_name={quote(k[0])}&duration={dur}", timeout=8))
                out = []
                for ln in (d.get("syncedLyrics") or "").splitlines():
                    m = _re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", ln)
                    if m and m.group(3).strip(): out.append((int(m.group(1))*60 + float(m.group(2)), m.group(3).strip()))
                if key == self._lyr_key: self._lyr = out or []
            except Exception as ex:
                log_error(f"lyrics: {ex}")
                if key == self._lyr_key: self._lyr = []
        threading.Thread(target=work, daemon=True).start()

    def _lyr_off(self):
        try: return float(self.settings.value("lyr_offset", 0.0))
        except Exception: return 0.0

    def _lyr_adj(self, d):
        self.settings.setValue("lyr_offset", round(max(-5.0, min(5.0, self._lyr_off() + d)), 2)); self.update()

    def _play_media_key(self):
        try: ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0); ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        except Exception: pass

    def _draw_idle_card(self, p, r):
        """Вместо «Нет трека»: живая аврора, приветствие, время и большой персонаж."""
        AL = Qt.AlignmentFlag; t = time.monotonic()
        cl = QPainterPath(); cl.addRoundedRect(r, 22, 22); p.save(); p.setClipPath(cl); p.setPen(Qt.PenStyle.NoPen)
        for k, (col, spd, ox, oy, rad) in enumerate(((ACCENT, 0.31, 0.25, 0.35, 170), (VIOLET, 0.23, 0.72, 0.4, 190), (MUSIC_COLOR, 0.19, 0.5, 0.85, 150))):
            x = r.x() + r.width() * (ox + 0.18 * math.sin(t * spd + k * 2.0)); y = r.y() + r.height() * (oy + 0.2 * math.cos(t * spd * 1.3 + k))
            g = QRadialGradient(QPointF(x, y), rad); g.setColorAt(0, rgba(col, 78)); g.setColorAt(1, rgba(col, 0)); p.setBrush(g); p.drawEllipse(QPointF(x, y), rad, rad)
        if bool(self.settings.value("xmas_theme", False, type=bool)):
            self._draw_snow_rect(p, r, 46)
        p.restore()
        hh = self.now.hour; greet = "Доброй ночи" if hh < 5 else "Доброе утро" if hh < 12 else "Добрый день" if hh < 18 else "Добрый вечер"
        p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(rgba(ACCENT.lighter(150), 240)); p.drawText(QRectF(r.x() + 28, r.y() + 24, 300, 20), AL.AlignLeft | AL.AlignVCenter, greet)
        p.setFont(font(60, QFont.Weight.Light)); p.setPen(QColor(255, 255, 255, 252)); p.drawText(QRectF(r.x() + 24, r.y() + 44, 300, 78), AL.AlignLeft | AL.AlignVCenter, self.now.strftime("%H:%M"))
        p.setFont(font(13)); p.setPen(QColor(255, 255, 255, 165)); p.drawText(QRectF(r.x() + 28, r.y() + 124, 300, 20), AL.AlignLeft | AL.AlignVCenter, f"{WD_DAYS[self.now.weekday()].capitalize()}, {self.now.day} {WD_MONTHS[self.now.month - 1]}")
        phrases = ("Тишина — тоже музыка", "Что сегодня послушаем?", "Перетащи файл на остров — он ляжет на полку", "Правый клик по островку — быстрые показатели",
                   "Потяни остров к краю — он прилипнет", "Загляни в микшер: у каждого приложения своя громкость", "Задай таймер — и за дело")
        k = int(t / 6.0) % len(phrases); ph = (t % 6.0) / 6.0; a = min(1.0, ph * 6.0, (1.0 - ph) * 6.0)
        p.setFont(font(12)); p.setPen(QColor(255, 255, 255, int(190 * a))); p.drawText(QRectF(r.x() + 28, r.y() + 164, 280, 44), int(AL.AlignLeft.value | AL.AlignTop.value | Qt.TextFlag.TextWordWrap.value), phrases[k])
        self._ios_pill(p, QRectF(r.x() + 28, r.y() + 218, 190, 38), "▶  Включить музыку", rgba(ACCENT, 235), QColor(8, 14, 20), self._play_media_key, 12)
        cx, cy = r.x() + r.width() * 0.78, r.y() + r.height() * 0.46 + math.sin(t * 1.4) * 3.0
        gg = QRadialGradient(QPointF(cx, cy), 92); gg.setColorAt(0, rgba(ACCENT, 70)); gg.setColorAt(1, rgba(ACCENT, 0)); p.setPen(Qt.PenStyle.NoPen); p.setBrush(gg); p.drawEllipse(QPointF(cx, cy), 92, 92)
        p.save(); p.translate(cx, cy); p.scale(3.3, 3.3); p.translate(-cx, -cy); self._draw_eyes(p, cx, cy); p.restore()

    def _draw_big_media(self, p):
        AL = Qt.AlignmentFlag; WR = Qt.TextFlag.TextWordWrap.value
        r = QRectF(20, 60, 500, 276); self._glass(p, r, 22)
        if not self.mod_music:
            p.setPen(QColor(255,255,255,120)); p.setFont(font(13, QFont.Weight.DemiBold)); p.drawText(r, AL.AlignCenter, "Модуль музыки отключён"); return
        if not self.media["active"]:
            self._draw_idle_card(p, r); return
        self._ensure_lyrics(); dyn = self._dyn(); cx = 182
        bass = self._bass if self.media["playing"] else 0.0
        p.save(); cl = QPainterPath(); cl.addRoundedRect(r, 22, 22); p.setClipPath(cl)
        gg = QRadialGradient(QPointF(cx, 132), 200 + 40 * bass); gg.setColorAt(0, rgba(dyn, int((95 if self.media["playing"] else 55) + 70 * bass))); gg.setColorAt(1, rgba(dyn, 0))
        p.fillRect(r, gg)
        self._draw_spectrum(p, QRectF(26, 262, 488, 70), dyn, alpha=0.55)
        p.restore()
        p.setPen(QPen(QColor(255,255,255,18), 1)); p.drawLine(QPointF(344, 74), QPointF(344, 322))
        asz = 116 * (1.0 + 0.045 * bass); art = QRectF(cx - asz / 2, 130 - asz / 2, asz, asz)
        ha = QRadialGradient(art.center(), 110); ha.setColorAt(0, rgba(dyn, int(min(255, 150 + 90 * bass)))); ha.setColorAt(1, rgba(dyn, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(ha); p.drawEllipse(art.center(), 110, 110)
        p.setBrush(QColor(255,255,255,20)); p.drawRoundedRect(art, 14, 14)
        if self.media.get("thumb"):
            pa = QPainterPath(); pa.addRoundedRect(art, 14, 14); p.save(); p.setClipPath(pa); p.drawPixmap(art.toRect(), self.media["thumb"]); p.restore()
        p.setFont(font(16, QFont.Weight.Bold)); p.setPen(QColor(255,255,255))
        p.drawText(QRectF(40, 196, 284, 24), AL.AlignCenter, QFontMetrics(p.font()).elidedText(self.media["title"], Qt.TextElideMode.ElideRight, 280))
        p.setFont(font(12)); p.setPen(QColor(255,255,255,170))
        p.drawText(QRectF(40, 220, 284, 20), AL.AlignCenter, QFontMetrics(p.font()).elidedText(self.media["artist"], Qt.TextElideMode.ElideRight, 280))
        sx, sy, sw = 44, 256, 282
        dur = max(self.media["duration"], 1); pos = min(self.media["position"], dur); frac = pos/dur
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,34)); p.drawRoundedRect(QRectF(sx, sy, sw, 3), 1.5, 1.5)
        p.setBrush(dyn); p.drawRoundedRect(QRectF(sx, sy, max(2, sw*frac), 3), 1.5, 1.5)
        if self._hover(QRectF(sx, sy-8, sw, 20)) or self._seek_drag:
            p.setBrush(QColor(255,255,255)); p.drawEllipse(QPointF(sx+sw*frac, sy+1.5), 5, 5)
        p.setFont(font(9)); p.setPen(QColor(255,255,255,140))
        p.drawText(QRectF(sx, sy+8, 50, 14), AL.AlignLeft, fmt_mmss(pos)); p.drawText(QRectF(sx+sw-50, sy+8, 50, 14), AL.AlignRight, fmt_mmss(dur))
        self._icon_btn(p, QRectF(cx-72, 286, 32, 32), "⏮", lambda: self._media_control("prev"))
        self._icon_btn(p, QRectF(cx-23, 280, 46, 46), "⏸" if self.media["playing"] else "▶", lambda: self._media_control("toggle"), big=True)
        self._icon_btn(p, QRectF(cx+40, 286, 32, 32), "⏭", lambda: self._media_control("next"))
        lines = getattr(self, "_lyr", None) or []; lx, lw = 358, 150; off = self._lyr_off(); lp = pos + off
        if lines:
            idx = max([i for i, (t_, _) in enumerate(lines) if t_ <= lp] or [-1])
            fi = getattr(self, "_lyr_fi", float(idx))
            if abs(fi - idx) > 5: fi = float(idx)
            fi += (idx - fi) * 0.2; self._lyr_fi = fi
            p.save(); p.setClipRect(QRectF(lx - 4, 66, lw + 8, 232))
            for i in range(idx - 3, idx + 5):
                if not (0 <= i < len(lines)): continue
                d = i - fi; y = 184.0 + d * 44.0; near = max(0.0, 1.0 - abs(d) * 0.7)
                if y < 60 or y > 310: continue
                cur = near > 0.6; p.setFont(font(10.5 + 3.0 * near, QFont.Weight.Bold if cur else QFont.Weight.Normal))
                c = QColor(255, 255, 255, int(55 + 200 * near))
                if cur: c = QColor(min(255, 235 + dyn.red() // 20), min(255, 235 + dyn.green() // 20), min(255, 235 + dyn.blue() // 20), 252)
                p.setPen(c); p.drawText(QRectF(lx, y - 20, lw, 40), int(AL.AlignLeft.value | AL.AlignVCenter.value | WR), lines[i][1] or "♪")
            p.restore()
        else:
            p.setFont(font(10)); p.setPen(QColor(255,255,255,90)); p.drawText(QRectF(lx, 72, lw, 220), AL.AlignCenter, "Загрузка текста…" if getattr(self, "_lyr", None) is None else "Текст не найден")
        mb = QRectF(lx, 304, 18, 18); pb = QRectF(lx + 96, 304, 18, 18)
        for rr_, tx_, dl in ((mb, "−", -0.25), (pb, "+", 0.25)):
            hv = self._hover(rr_); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 46 if hv else 22)); p.drawEllipse(rr_)
            p.setFont(font(11, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(rr_, AL.AlignCenter, tx_); self._add_hit(rr_, lambda d=dl: self._lyr_adj(d))
        p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 150)); p.drawText(QRectF(lx + 20, 304, 74, 18), AL.AlignCenter, f"синх {off:+.2f} с".replace(".00", ".0"))
        p.setFont(font(7)); p.setPen(QColor(255,255,255,70)); p.drawText(QRectF(lx + 118, 306, lw - 118, 14), AL.AlignRight, "LRCLIB")
        vr = QRectF(20, 348, 500, 36); self._glass(p, vr, 18)
        draw_icon(p, "vol", QRectF(34, 356, 20, 20), QColor(255,255,255,200))
        vsx, vsy, vsw = 66, 364, 300; v = max(0.0, min(1.0, self._volume))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,34)); p.drawRoundedRect(QRectF(vsx, vsy, vsw, 4), 2, 2)
        p.setBrush(QColor(255,255,255,240)); p.drawRoundedRect(QRectF(vsx, vsy, max(2, vsw*v), 4), 2, 2); p.drawEllipse(QPointF(vsx+vsw*v, vsy+2), 5, 5)
        p.setFont(font(9)); p.setPen(QColor(255,255,255,150)); p.drawText(QRectF(vsx+vsw+10, 356, 30, 20), AL.AlignLeft|AL.AlignVCenter, f"{int(v*100)}")
        pill = QRectF(416, 354, 94, 24); p.setBrush(QColor(255,255,255,16)); p.drawRoundedRect(pill, 12, 12)
        p.setFont(font(9, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,210))
        p.drawText(pill.adjusted(8,0,-8,0), AL.AlignCenter, QFontMetrics(p.font()).elidedText(get_app_name() or "Динамики", Qt.TextElideMode.ElideRight, 76))

    def _tool_cb(self, tid):
        sf = lambda c: (lambda: os.startfile(c))
        return {"area": self._shot_area, "screen": self._shot_full, "text": self._scan_text, "qr": self._scan_qr, "pip": self._pick_color,
                "erase": self._clean_text, "rec": self._record_screen, "ai": self._open_ai_window_quick, "calc": sf("calc"),
                "taskmgr": sf("taskmgr"), "explorer": sf("explorer"), "notepad": sf("notepad"), "cmd": sf("cmd"), "paint": sf("mspaint"),
                "lock": lambda: user32.LockWorkStation(), "mute": self._mute_toggle, "settings": self._open_settings}.get(tid, lambda: None)

    def _open_tools_editor(self):
        try:
            ed = getattr(self, "_tools_editor", None)
            if ed is not None:
                try: ed.close()
                except Exception: pass
            ed = ToolsEditor(self); self._tools_editor = ed
            ed.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            ed.destroyed.connect(lambda *_: setattr(self, "_tools_editor", None))
            ed.show(); ed.raise_(); ed.activateWindow()
        except Exception as e: log_error(f"tools editor: {e}\n{traceback.format_exc()}")

    def _draw_tools_grid(self, p):
        x0, y0, bw, bh, gap = 534, 60, 118, 74, 8
        ids = load_tools(self.settings)
        fl = int(Qt.AlignmentFlag.AlignLeft.value | Qt.AlignmentFlag.AlignVCenter.value | Qt.TextFlag.TextWordWrap.value)
        for i in range(min(MAX_TOOLS, len(ids) + 1)):
            row, col = divmod(i, 2); r = QRectF(x0+col*(bw+gap), y0+row*(bh+gap-2), bw, bh-2); hov = self._hover(r)
            if i >= len(ids):
                p.setPen(QPen(QColor(255,255,255, 90 if hov else 45), 1, Qt.PenStyle.DashLine)); p.setBrush(QColor(255,255,255, 14 if hov else 0)); p.drawRoundedRect(r, 18, 18)
                p.setFont(font(20)); p.setPen(QColor(255,255,255, 190 if hov else 110)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, "+")
                self._add_hit(r, self._open_tools_editor); continue
            ic, em, text = TOOL_CATALOG[ids[i]]
            self._glass(p, r, 18, hov)
            rec = ids[i] == "rec" and getattr(self, "_rec", None)
            accc = QColor(255, 90, 90) if rec else ACCENT
            plate = QRectF(r.x() + 12, r.center().y() - 15, 30, 30)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(accc, 62 if hov else 34)); p.drawRoundedRect(plate, 10, 10)
            col_ = QColor(255, 125, 125) if rec else (rgba(ACCENT.lighter(140), 255) if hov else QColor(255, 255, 255, 218)); ib = plate.adjusted(6, 6, -6, -6)
            if ic: draw_icon(p, ic, ib, col_)
            else: p.setFont(font(12, family="Segoe UI Emoji")); p.setPen(col_); p.drawText(plate, Qt.AlignmentFlag.AlignCenter, em)
            p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 250 if hov else 228))
            p.drawText(QRectF(r.x() + 52, r.y(), r.width() - 58, r.height()), fl, "Стоп" if rec else text)
            self._add_hit(r, self._tool_cb(ids[i]))

    def _record_screen(self):
        import shutil
        if getattr(self, "_rec", None):
            try: self._rec.stdin.write(b"q"); self._rec.stdin.flush()
            except Exception: pass
            self._rec = None; self._show_toast("Запись", "Сохранено в буфер", "🔴"); return
        ff = shutil.which("ffmpeg")
        if not ff: self._show_toast("", "Нужен ffmpeg в PATH", "🎥"); return
        out = os.path.join(os.path.expanduser("~"), "Videos", datetime.datetime.now().strftime("island_%Y%m%d_%H%M%S.mp4")); os.makedirs(os.path.dirname(out), exist_ok=True)
        try:
            self._rec = subprocess.Popen([ff, "-y", "-f", "gdigrab", "-framerate", "30", "-i", "desktop", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", out],
                                         stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            self._show_toast("Запись идёт", "Нажми ещё раз, чтобы остановить", "🔴")
        except Exception as ex: log_error(f"rec: {ex}")

    def _dock_launch(self, path):
        self._dock_bounce[path] = time.monotonic(); self._launch(path)

    def _draw_dock(self, p):
        y0 = 392; dock_w = 760; AL = Qt.AlignmentFlag; now_ = time.monotonic()
        bar = QRectF(20, y0, dock_w, 70); st = self._ui_style()
        if st == 0:
            g = QLinearGradient(0, y0, 0, y0 + 70); g.setColorAt(0, QColor(255, 255, 255, 40)); g.setColorAt(1, QColor(255, 255, 255, 16))
            p.setBrush(g); p.setPen(QPen(QColor(255, 255, 255, 46), 1)); p.drawRoundedRect(bar, 26, 26)
            p.setPen(QPen(QColor(255, 255, 255, 60), 1)); p.drawLine(QPointF(bar.x() + 26, y0 + 1.5), QPointF(bar.right() - 26, y0 + 1.5))
        else: self._glass(p, bar, 26)
        sr = QRectF(34, y0 + 17, 200, 36); act = self._ds_active; hv = self._hover(sr)
        p.setBrush(QColor(0, 0, 0, 70 if (act or hv) else 46)); p.setPen(QPen(rgba(ACCENT, 220) if act else QColor(255, 255, 255, 30), 1.3 if act else 1)); p.drawRoundedRect(sr, 18, 18)
        draw_icon(p, "search", QRectF(sr.x() + 12, sr.y() + 9, 18, 18), QColor(255, 255, 255, 235 if act else 160))
        tx = QRectF(sr.x() + 38, sr.y(), sr.width() - 48, sr.height()); p.setFont(font(12)); fm = QFontMetrics(p.font())
        if self._ds_text or act:
            shown = fm.elidedText(self._ds_text, Qt.TextElideMode.ElideLeft, int(tx.width() - 4)); p.setPen(QColor(255, 255, 255, 245)); p.drawText(tx, AL.AlignLeft | AL.AlignVCenter, shown)
            if act and int(now_ * 2) % 2 == 0:
                cx_ = tx.x() + fm.horizontalAdvance(shown) + 1; p.setPen(QPen(QColor(255, 255, 255, 230), 1.2)); p.drawLine(QPointF(cx_, sr.y() + 9), QPointF(cx_, sr.bottom() - 9))
        else:
            fm_, fu_, fok_ = self._ds_flash_msg
            if fm_ and now_ < fu_:
                p.setPen(QColor(120, 255, 170, 245) if fok_ else QColor(255, 190, 110, 245)); p.drawText(tx, AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(fm_, Qt.TextElideMode.ElideRight, int(tx.width() - 2)))
            else: p.setPen(QColor(255, 255, 255, 120)); p.drawText(tx, AL.AlignLeft | AL.AlignVCenter, "Что добавить в док…" if self._ds_add_mode else "Поиск приложений…")
        if act and not self._ds_text and self._ds_add_mode: p.setPen(QColor(255, 255, 255, 100)); p.drawText(tx.adjusted(6, 0, 0, 0), AL.AlignLeft | AL.AlignVCenter, "Что добавить в док…")
        self._add_hit(sr, self._ds_focus)
        mx = self._mouse.x() if (self._mouse is not None and bar.contains(self._mouse)) else None
        x = 252.0; bottom = y0 + 56.0; label = None
        for i, item in enumerate(self.dock):
            path = item.get("path", "")
            if not self._path_ok(path): continue
            if x + 40 > 20 + dock_w - 10: break
            cxi = x + 20; kt = 1.0 + 0.32 * math.exp(-(((mx - cxi) / 58.0) ** 2)) if mx is not None else 1.0
            key = "dk%d" % i; k = self._gv.get(key, 1.0); k += (kt - k) * 0.28; self._gv[key] = k
            bt = now_ - self._dock_bounce.get(path, -9.0); bnc = abs(math.sin(bt * 11.0)) * 15.0 * (1.0 - bt / 0.7) if 0 <= bt < 0.7 else 0.0
            size = 40.0 * k; ir = QRectF(cxi - size / 2, bottom - size - bnc, size, size)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, 60)); p.drawEllipse(QPointF(cxi, bottom + 5), 17 * k, 3.2)
            p.drawPixmap(ir.toRect(), self._ds_icon(path, 40, item.get("name")))
            hit = QRectF(x - 6, y0 + 4, 52, 62)
            if self._hover(hit): label = (cxi, item.get("name") or os.path.splitext(os.path.basename(path))[0])
            self._add_hit(hit, lambda pp=path: self._dock_launch(pp)); self._add_dock_right_click(hit, i); x += 52
        if len(self.dock) < DOCK_MAX and x + 40 <= 20 + dock_w - 10:
            rp = QRectF(x, y0 + 15, 40, 40); hov = self._hover(rp)
            p.setPen(QPen(QColor(255, 255, 255, 120 if hov else 70), 1.4, Qt.PenStyle.DashLine)); p.setBrush(QColor(255, 255, 255, 30 if hov else 12)); p.drawRoundedRect(rp, 12, 12)
            p.setFont(font(22, QFont.Weight.Light)); p.setPen(QColor(255, 255, 255, 230 if hov else 170)); p.drawText(rp, AL.AlignCenter, "+"); self._add_hit(rp, self._add_dock_item)
        if label is not None:       # подпись под доком, как при наведении в macOS/iPadOS
            lf = font(10, QFont.Weight.DemiBold); w_ = QFontMetrics(lf).horizontalAdvance(label[1]) + 22; lr = QRectF(max(24.0, min(776.0 - w_, label[0] - w_ / 2)), y0 + 76, w_, 24)
            p.setPen(QPen(QColor(255, 255, 255, 30), 1)); p.setBrush(QColor(34, 34, 38, 245)); p.drawRoundedRect(lr, 12, 12)
            p.setFont(lf); p.setPen(QColor(255, 255, 255, 245)); p.drawText(lr, AL.AlignCenter, label[1])

    # ── поиск приложений ──
    def _ds_panel_open(self): return self._ds_active and bool(self._ds_text.strip())
    def _ds_focus(self):
        self._ds_active = True; self.activateWindow(); self.setFocus()
        if self._app_index is not None and time.time() - self._app_index_ts > 600:
            self._app_index_ts = time.time(); threading.Thread(target=self._build_app_index, daemon=True).start()
        self.update()
    def _ds_reset(self): self._ds_active = False; self._ds_text = ""; self._ds_res = []; self._ds_sel = 0; self._ds_add_mode = False; self.update()
    def _ds_launch(self, path): self._launch(path); self._ds_reset(); (self.toggle_expand() if self.expanded else None)
    def _letter_tile(self, name, sz):
        pm = QPixmap(sz, sz); pm.fill(Qt.GlobalColor.transparent)
        pp = QPainter(pm); pp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        h = (sum(ord(c) for c in str(name)) * 47) % 360
        g = QLinearGradient(0, 0, sz, sz); g.setColorAt(0, QColor.fromHsv(h, 170, 235)); g.setColorAt(1, QColor.fromHsv((h + 40) % 360, 205, 150))
        pp.setPen(Qt.PenStyle.NoPen); pp.setBrush(g); pp.drawRoundedRect(QRectF(1, 1, sz - 2, sz - 2), sz * 0.26, sz * 0.26)
        pp.setPen(QColor(255, 255, 255)); pp.setFont(font(max(8, int(sz * 0.5)), QFont.Weight.Bold))
        pp.drawText(QRectF(0, 0, sz, sz), Qt.AlignmentFlag.AlignCenter, (str(name).strip()[:1] or "?").upper())
        pp.end(); return pm

    def _ds_icon(self, path, sz=28, name=None):
        key = (path, sz); pm = self._ds_icons.get(key)
        if pm is None:
            if str(path).lower().startswith(("shell:", "ms-settings:")): pm = self._letter_tile(name or path, sz)
            else:
                try: pm = QFileIconProvider().icon(QFileInfo(path)).pixmap(sz, sz)
                except Exception: pm = QPixmap(sz, sz)
                if pm.isNull(): pm = self._letter_tile(name or os.path.basename(path), sz)
            self._ds_icons[key] = pm
        return pm

    def _build_app_index(self):
        out = {}
        for root in (os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
                     os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
                     os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"), "Desktop"),
                     os.path.join(os.path.expanduser("~"), "Desktop")):
            for dp, _, fs in os.walk(root):
                for f in fs:
                    if f.lower().endswith((".lnk", ".exe", ".url")):
                        n = os.path.splitext(f)[0]
                        if any(w in n.lower() for w in ("uninstall", "удал", "readme", "help")): continue
                        out.setdefault(n.lower(), (n, os.path.join(dp, f)))
        for n, c in BUILTIN_APPS: out.setdefault(n.lower(), (n, c))
        try:    # приложения Microsoft Store (их нет в меню «Пуск» как ярлыков)
            raw = _ps("Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress", 25)
            data = json.loads(raw) if raw else []
            if isinstance(data, dict): data = [data]
            for a in data:
                n = str(a.get("Name") or "").strip(); aid = str(a.get("AppID") or "").strip()
                if not n or not aid or any(w in n.lower() for w in ("uninstall", "удал")): continue
                out.setdefault(n.lower(), (n, aid if os.path.isabs(aid) else "shell:AppsFolder\\" + aid))
        except Exception as ex: log_error(f"startapps: {ex}")
        for it in self.dock:
            pth = it.get("path", "")
            if pth: out.setdefault(os.path.splitext(os.path.basename(pth))[0].lower(), (it.get("name") or os.path.splitext(os.path.basename(pth))[0], pth))
        self._app_index = list(out.values()); self._app_index_ts = time.time()

    def _ds_match(self, q):
        sc = []
        for n, pth in self._app_index or []:
            l = n.lower()
            if l.startswith(q): s = 0
            elif any(w.startswith(q) for w in l.replace("-", " ").replace("_", " ").split()): s = 1
            elif q in l: s = 2
            else:
                it = iter(l)
                if all(c in it for c in q): s = 3
                else: continue
            sc.append((s, len(l), n, pth))
        sc.sort(); return [(n, pth) for _, _, n, pth in sc[:5]]

    def _ds_update(self):
        q = self._ds_text.strip().lower(); self._ds_sel = 0
        if not q: self._ds_res = []; return
        res = self._ds_match(q)
        if not res:
            tq = "".join(RU2EN.get(c, c) for c in q)
            if tq != q: res = self._ds_match(tq)
        self._ds_res = res

    def _ds_key(self, ev):
        K = Qt.Key; k = ev.key(); t = ev.text()
        if self._ds_active and k in (K.Key_Return, K.Key_Enter) and (ev.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
            self._ds_add_selected(); return True     # Ctrl/Shift+Enter — добавить в док, а не запускать
        if ev.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier): return False
        if self._ds_active:
            if k in (K.Key_Return, K.Key_Enter):
                if self._ds_add_mode: self._ds_add_selected()
                elif self._ds_res: self._ds_launch(self._ds_res[min(self._ds_sel, len(self._ds_res)-1)][1])
                return True
            if k == K.Key_Escape: self._ds_reset(); return True
            if k == K.Key_Backspace: self._ds_text = self._ds_text[:-1]; self._ds_update(); self.update(); return True
            if k in (K.Key_Down, K.Key_Up) and self._ds_res:
                self._ds_sel = (self._ds_sel + (1 if k == K.Key_Down else -1)) % len(self._ds_res); self.update(); return True
        if t and t.isprintable() and (not t.isspace() or self._ds_active):
            self._ds_active = True; self._ds_text += t; self._ds_update(); self.update(); return True
        return False

    def _draw_dsearch_results(self, p):
        if not self._ds_panel_open(): return
        res = self._ds_res; AL = Qt.AlignmentFlag; rh = 46; foot = 46 if res else 0
        h = max(1, len(res)) * rh + 16 + foot
        r = QRectF(32, 392 - h - 8, 420, h)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,90)); p.drawRoundedRect(r.adjusted(-2,3,2,5), 18, 18)
        p.setPen(QPen(QColor(255,255,255,34), 1)); p.setBrush(QColor(24,26,36,252)); p.drawRoundedRect(r, 16, 16)
        if not res:
            p.setFont(font(12)); p.setPen(QColor(255,255,255,120))
            p.drawText(r, AL.AlignCenter, "Индексирую приложения…" if self._app_index is None else "Ничего не найдено"); return
        in_dock = {self._dock_key(it.get("path", "")) for it in self.dock}
        for i, (n, path) in enumerate(res):
            rr = QRectF(r.x()+8, r.y()+8+i*rh, r.width()-16, rh-4); sel = i == self._ds_sel; hv = self._hover(rr)
            if sel or hv: p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 70 if sel else 30)); p.drawRoundedRect(rr, 10, 10)
            p.drawPixmap(QRectF(rr.x()+10, rr.y()+(rr.height()-28)/2, 28, 28).toRect(), self._ds_icon(path, 28, n))
            p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245))
            p.drawText(QRectF(rr.x()+50, rr.y(), rr.width()-130, rr.height()), AL.AlignLeft|AL.AlignVCenter, QFontMetrics(p.font()).elidedText(n, Qt.TextElideMode.ElideRight, int(rr.width()-130)))
            if sel and not self._ds_add_mode: p.setFont(font(13)); p.setPen(QColor(255,255,255,150)); p.drawText(QRectF(rr.right()-74, rr.y(), 26, rr.height()), AL.AlignCenter, "↵")
            self._add_hit(rr, (lambda nn=n, pp=path: self._ds_add(nn, pp)) if self._ds_add_mode else (lambda pp=path: self._ds_launch(pp)))
            ab = QRectF(rr.right()-38, rr.y()+(rr.height()-28)/2, 28, 28); added = self._dock_key(path) in in_dock; hb = self._hover(ab)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(120,255,170,60) if added else (rgba(ACCENT, 200 if hb else 110)))
            p.drawEllipse(ab)
            p.setFont(font(15, QFont.Weight.Bold)); p.setPen(QColor(120,255,170,240) if added else QColor(255,255,255,245)); p.drawText(ab, AL.AlignCenter, "✓" if added else "+")
            self._add_hit(ab, (lambda nn=n, pp=path: self._ds_add(nn, pp)))
        fr = QRectF(r.x()+8, r.bottom()-foot+2, r.width()-16, 38); hf = self._hover(fr)
        full = len(self.dock) >= DOCK_MAX
        fm_, fu_, fok_ = self._ds_flash_msg; flashing = bool(fm_) and time.monotonic() < fu_
        p.setPen(Qt.PenStyle.NoPen)
        if flashing: p.setBrush(QColor(60,200,120,70) if fok_ else QColor(230,150,60,70))
        else: p.setBrush(QColor(255,255,255,10) if full else rgba(ACCENT, 130 if hf else 90))
        p.drawRoundedRect(fr, 12, 12)
        sn = res[min(self._ds_sel, len(res)-1)][0]
        p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,235 if not full or flashing else 130))
        txt = fm_ if flashing else (f"Док заполнен ({len(self.dock)}/{DOCK_MAX})" if full else f"＋  Добавить «{sn}» в док   {len(self.dock)}/{DOCK_MAX}")
        p.drawText(fr.adjusted(10,0,-10,0), AL.AlignCenter, QFontMetrics(p.font()).elidedText(txt, Qt.TextElideMode.ElideRight, int(fr.width()-20)))
        self._add_hit(fr, self._ds_add_selected)
    _dock_right_regions = []
    def _add_dock_right_click(self, r, idx):
        self._dock_right_regions.append((r, idx))

    def _draw_timer(self, p):
        AL = Qt.AlignmentFlag; self._ios_title(p, "Таймер", "Выбери время или задай своё")
        card = QRectF(20, 104, 360, 414); self._ios_card(p, card, 28)
        cx, cy, R = 200.0, 250.0, 118.0; ring = QRectF(cx - R, cy - R, 2 * R, 2 * R)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if self.t_running:
            pulse = 0.5 + 0.5 * math.sin(self._glow * 6.28); p.setPen(QPen(rgba(ACCENT, int(26 + 26 * pulse)), 20)); p.drawEllipse(ring)
        p.setPen(QPen(QColor(255, 255, 255, 24), 9)); p.drawEllipse(ring)
        frac = (self.t_left / self.t_total) if self.t_total else 0
        if frac > 0.002:
            p.setPen(QPen(ACCENT, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(ring, 90 * 16, -int(360 * 16 * min(frac, 0.9999)))
        p.setFont(font(60, QFont.Weight.Light)); p.setPen(QColor(255, 255, 255, 252)); p.drawText(QRectF(cx - R, cy - 44, 2 * R, 84), AL.AlignCenter, fmt_mmss(self.t_left))
        if self.t_running: label = "Идёт отсчёт"
        elif self.t_left < self.t_total: label = "Пауза"
        else: label = f"Готов · {self.t_total // 60} мин" if self.t_total >= 60 else f"Готов · {self.t_total} сек"
        p.setFont(font(12)); p.setPen(IOS_GRAYT); p.drawText(QRectF(cx - R, cy + 42, 2 * R, 20), AL.AlignCenter, label)
        self._ios_round_btn(p, QPointF(cx - 92, 440), 74, "Сброс", QColor(150, 150, 160), self._timer_reset)
        self._ios_round_btn(p, QPointF(cx + 92, 440), 74, "Пауза" if self.t_running else "Старт", IOS_ORANGE if self.t_running else IOS_GREEN, self._timer_toggle)
        rc = QRectF(400, 104, 380, 414); self._ios_card(p, rc, 28)
        p.setFont(font(9, QFont.Weight.DemiBold, spacing=1.1)); p.setPen(IOS_GRAYT); p.drawText(QRectF(426, 124, 300, 14), AL.AlignLeft, "БЫСТРЫЙ ВЫБОР")
        x0, y0 = 426.0, 148.0
        for i, m in enumerate(self.TIMER_PRESETS):
            r2 = QRectF(x0 + (i % 4) * 86, y0 + (i // 4) * 52, 78, 42); act = (i == self.preset) and not self._timer_custom_mode
            self._ios_pill(p, r2, f"{m} мин", rgba(ACCENT, 255) if act else IOS_GRAY, QColor(8, 14, 20) if act else QColor(255, 255, 255, 240), lambda i=i: self._set_preset(i), 13)
        p.setFont(font(9, QFont.Weight.DemiBold, spacing=1.1)); p.setPen(IOS_GRAYT); p.drawText(QRectF(426, 270, 300, 14), AL.AlignLeft, "СВОЁ ВРЕМЯ")
        fx = 426.0
        for fid, val, unit in (("h", self._timer_h_input, "часы"), ("m", self._timer_m_input, "минуты"), ("s", self._timer_s_input, "секунды")):
            r_f = QRectF(fx, 294, 108, 80); act = self._timer_active_field == fid; hov = self._hover(r_f)
            p.setBrush(QColor(58, 58, 60, 255 if (act or hov) else 220)); p.setPen(QPen(ACCENT, 1.6) if act else Qt.PenStyle.NoPen); p.drawRoundedRect(r_f, 18, 18)
            disp = (val.zfill(2) if val else "00") + ("│" if act and int(time.monotonic() * 2) % 2 == 0 else "")
            p.setFont(font(32, QFont.Weight.Light)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(r_f.x(), r_f.y() + 6, r_f.width(), 46), AL.AlignCenter, disp)
            p.setFont(font(9)); p.setPen(IOS_GRAYT); p.drawText(QRectF(r_f.x(), r_f.y() + 54, r_f.width(), 16), AL.AlignCenter, unit)
            self._add_hit(r_f, lambda f=fid: self._activate_timer_field(f)); fx += 118
        self._ios_pill(p, QRectF(426, 396, 330, 48), "Задать время", IOS_BLUE, QColor(255, 255, 255), self._apply_custom_timer, 14)
        p.setFont(font(10)); p.setPen(IOS_GRAYT); p.drawText(QRectF(426, 456, 330, 40), int(AL.AlignLeft.value | AL.AlignTop.value | Qt.TextFlag.TextWordWrap.value), "Нажми на поле, введи цифры и подтверди. Когда время выйдет, остров будет сигналить, пока ты его не выключишь.")

    def _ws(self, k, d=0):
        try: return int(self.settings.value(k, d))
        except Exception: return d
    def _wb(self, k, d=True):
        try: return bool(self.settings.value(k, d, type=bool))
        except Exception: return d
    def _wtemp(self, v):
        if v is None: return "—"
        if self._ws("w_temp_unit") == 1: v = v * 9 / 5 + 32
        return f"{v:.0f}°"
    def _wwind(self, v):
        u = self._ws("w_wind_unit")
        return (f"{v:.0f}", "км/ч") if u == 0 else ((f"{v/3.6:.1f}", "м/с") if u == 1 else (f"{v*0.621371:.0f}", "миль/ч"))
    def _wpres(self, mm):
        u = self._ws("w_pres_unit")
        return (f"{mm:.0f}", "мм рт. ст.") if u == 0 else ((f"{mm/0.750062:.0f}", "гПа") if u == 1 else (f"{mm*0.0393701:.2f}", "inHg"))
    def _wcolors(self, code):
        t = self._ws("w_theme")
        if t == 1: return QColor(72,150,240), QColor(38,84,184)
        if t == 2: return QColor(255,140,90), QColor(190,70,120)
        if t == 3: return QColor(74,78,92), QColor(30,32,40)
        if t == 4: return QColor(130,100,240), QColor(60,40,150)
        if code in (95, 96, 99): return QColor(96,70,150), QColor(40,30,80)
        if code in (71, 73, 75, 77, 85, 86): return QColor(150,190,225), QColor(95,130,175)
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82): return QColor(70,110,160), QColor(36,54,100)
        if code in (2, 3, 45, 48): return QColor(120,134,156), QColor(70,80,100)
        if not (6 <= self.now.hour < 20): return QColor(40,48,110), QColor(18,22,56)
        return QColor(72,150,240), QColor(38,84,184)
    def _weather_refresh(self):
        try:
            self._weather_started = time.monotonic(); self._weather_loading = True
            self._weather_worker.refresh()
        except Exception as e: log_error(f"weather refresh: {e}")

    def _weather_fx(self, p, r, code, is_day):
        """Живой фон карточки: дождь, снег, лучи солнца, звёзды, плывущие облака."""
        t = time.monotonic(); p.save(); cp = QPainterPath(); cp.addRoundedRect(r, 20, 20); p.setClipPath(cp); p.setPen(Qt.PenStyle.NoPen)
        rain = code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99)
        snow = code in (71, 73, 75, 77, 85, 86)
        cloudy = code in (2, 3, 45, 48) or rain or snow
        if code in (0, 1) and is_day:
            gx, gy = r.right() - 44, r.y() + 62
            sg = QRadialGradient(QPointF(gx, gy), 130); sg.setColorAt(0, QColor(255, 236, 160, int(110 + 30 * math.sin(t * 1.4)))); sg.setColorAt(1, QColor(255, 220, 120, 0))
            p.setBrush(sg); p.drawEllipse(QPointF(gx, gy), 130, 130)
            p.setPen(QPen(QColor(255, 240, 190, 46), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for k in range(12):
                a = t * 0.18 + k * math.pi / 6
                p.drawLine(QPointF(gx + math.cos(a) * 34, gy + math.sin(a) * 34), QPointF(gx + math.cos(a) * (70 + 8 * math.sin(t * 2 + k)), gy + math.sin(a) * (70 + 8 * math.sin(t * 2 + k))))
            p.setPen(Qt.PenStyle.NoPen)
        if code in (0, 1) and not is_day:
            for i in range(26):
                sx = r.x() + (i * 53.7) % r.width(); sy = r.y() + (i * 31.3) % (r.height() * 0.6)
                p.setBrush(QColor(255, 255, 255, int(70 + 110 * (0.5 + 0.5 * math.sin(t * 1.6 + i * 1.9))))); p.drawEllipse(QPointF(sx, sy), 1.1 + (i % 3) * 0.4, 1.1 + (i % 3) * 0.4)
        if cloudy:
            for i in range(3):
                cx_ = r.x() - 90 + ((t * (7 + i * 3) + i * 120) % (r.width() + 180)); cy_ = r.y() + 40 + i * 46
                p.setBrush(QColor(255, 255, 255, 18 if i != 1 else 26))
                p.drawEllipse(QPointF(cx_, cy_), 56, 17); p.drawEllipse(QPointF(cx_ - 28, cy_ + 4), 34, 14); p.drawEllipse(QPointF(cx_ + 30, cy_ + 5), 38, 13)
        if rain:
            p.setPen(QPen(QColor(205, 228, 255, 120), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for i in range(30):
                sp_ = 240 + (i % 5) * 45; x = r.x() + (i * 37.3) % r.width(); y = r.y() + ((t * sp_ + i * 61.7) % (r.height() + 30)) - 15
                p.drawLine(QPointF(x, y), QPointF(x - 3, y + 11))
        elif snow:
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(34):
                x = r.x() + ((i * 43.7 + math.sin(t * 0.8 + i) * 12) % r.width()); y = r.y() + ((t * (24 + (i % 4) * 9) + i * 53.1) % (r.height() + 10))
                p.setBrush(QColor(255, 255, 255, 200)); p.drawEllipse(QPointF(x, y), 1.3 + (i % 3) * 0.6, 1.3 + (i % 3) * 0.6)
        p.restore()

    def _draw_weather(self, p):
        w = self.weather
        if not w.get("ok"):
            AL0 = Qt.AlignmentFlag; err = w.get("error") or ""
            if err and not self._weather_loading:
                p.setFont(font(15, QFont.Weight.DemiBold)); p.setPen(QColor(255, 170, 150))
                p.drawText(QRectF(60, 170, self.EW - 120, 28), AL0.AlignCenter, "Не удалось получить погоду")
                p.setFont(font(11)); p.setPen(QColor(255, 255, 255, 150))
                p.drawText(QRectF(100, 204, self.EW - 200, 60), int(AL0.AlignHCenter.value | AL0.AlignTop.value | Qt.TextFlag.TextWordWrap.value), err[:160])
                bt = QRectF(self.EW / 2 - 70, 276, 140, 38); hb = self._hover(bt)
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 200 if hb else 150)); p.drawRoundedRect(bt, 14, 14)
                p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255)); p.drawText(bt, AL0.AlignCenter, "↻ Повторить")
                self._add_hit(bt, self._weather_refresh)
                bt2 = QRectF(self.EW / 2 + 78, 276, 170, 38); hb2 = self._hover(bt2)
                p.setPen(QPen(QColor(255, 255, 255, 60 if hb2 else 34), 1)); p.setBrush(QColor(255, 255, 255, 26 if hb2 else 12)); p.drawRoundedRect(bt2, 14, 14)
                p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(bt2, AL0.AlignCenter, "Выбрать город")
                self._add_hit(bt2, self._open_settings)
            else:
                c_ = QPointF(self.EW / 2, 210); p.setPen(QPen(QColor(255, 255, 255, 40), 3)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(c_, 16, 16)
                p.setPen(QPen(rgba(ACCENT, 230), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(QRectF(c_.x() - 16, c_.y() - 16, 32, 32), int(-time.monotonic() * 300 % 360 * 16), 100 * 16)
                p.setFont(font(13)); p.setPen(QColor(255, 255, 255, 150)); p.drawText(QRectF(0, 240, self.EW, 30), AL0.AlignCenter, "Загрузка погоды…")
            return
        code = w.get("code", 0); desc, icon = WMO_CODES.get(code, ("—", "?")); city = w.get("city") or "—"
        AL = Qt.AlignmentFlag; is_day = bool(w.get("is_day", 1)); c1, c2 = self._wcolors(code)
        r = QRectF(20, 60, 288, 458); g = QLinearGradient(r.topLeft(), r.bottomRight()); g.setColorAt(0, c1); g.setColorAt(1, c2)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(g); p.drawRoundedRect(r, 30, 30); self._weather_fx(p, r, code, is_day)
        p.setFont(font(22, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(r.x() + 22, r.y() + 26, r.width() - 80, 30), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(city, Qt.TextElideMode.ElideRight, int(r.width() - 80)))
        p.setFont(font(13)); p.setPen(QColor(255, 255, 255, 205)); p.drawText(QRectF(r.x() + 22, r.y() + 58, r.width() - 44, 20), AL.AlignLeft | AL.AlignVCenter, desc)
        rfb = QRectF(r.right() - 46, r.y() + 22, 28, 28); hrf = self._hover(rfb)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 56 if hrf else 28)); p.drawEllipse(rfb)
        p.save(); p.translate(rfb.center()); p.rotate((time.monotonic() * 360) % 360 if self._weather_loading else 0)
        p.setFont(font(14, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, 240)); p.drawText(QRectF(-14, -14, 28, 28), AL.AlignCenter, "↻"); p.restore()
        self._add_hit(rfb, self._weather_refresh)
        p.setFont(font(92, QFont.Weight.Light)); p.setPen(QColor(255, 255, 255, 252)); p.drawText(QRectF(r.x(), r.y() + 90, r.width(), 112), AL.AlignCenter, self._wtemp(w.get("temp")))
        p.setFont(font(54, family="Segoe UI Emoji")); p.setPen(QColor(255, 255, 255, 245)); p.drawText(QRectF(r.x(), r.y() + 208, r.width(), 72), AL.AlignCenter, icon)
        p.setFont(font(14, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 235)); p.drawText(QRectF(r.x(), r.y() + 290, r.width(), 22), AL.AlignCenter, f"↑ {self._wtemp(w.get('tmax'))}    ↓ {self._wtemp(w.get('tmin'))}")
        chips = []
        if self._wb("w_show_feels", True): chips.append(f"Ощущается {self._wtemp(w.get('feels'))}")
        if self._wb("w_show_rain", True): chips.append(f"Осадки {(w.get('rain') or 0):.0f}%")
        cfm = QFontMetrics(font(11, QFont.Weight.DemiBold)); cy_ = r.y() + 330
        for ct in chips:
            cwid = cfm.horizontalAdvance(ct) + 24; rr_ = QRectF(r.center().x() - cwid / 2, cy_, cwid, 28)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 36)); p.drawRoundedRect(rr_, 14, 14)
            p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 240)); p.drawText(rr_, AL.AlignCenter, ct); cy_ += 36
        p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 170 if not w.get("stale") else 230))
        p.drawText(QRectF(r.x(), r.bottom() - 30, r.width(), 14), AL.AlignCenter, ((f"⚠ нет связи · данные на {w.get('updated', '—')}" if w.get("stale") else f"Обновлено в {w.get('updated', '—')}") if w.get("updated") else ""))
        rx, rw = 324.0, 456.0; top = 60.0
        if self._wb("w_show_hours", True) and w.get("hours"):
            hc = QRectF(rx, top, rw, 124); self._ios_card(p, hc, 24)
            p.setFont(font(9, QFont.Weight.DemiBold, spacing=1.1)); p.setPen(IOS_GRAYT); p.drawText(QRectF(rx + 20, top + 12, 300, 14), AL.AlignLeft, "ПОЧАСОВОЙ ПРОГНОЗ")
            hrs = w["hours"][:7]; cw_ = (rw - 24) / 7.0
            for k, (hh, ht, hc_) in enumerate(hrs):
                x = rx + 12 + k * cw_
                p.setFont(font(10)); p.setPen(IOS_GRAYT); p.drawText(QRectF(x, top + 34, cw_, 16), AL.AlignCenter, "Сейчас" if k == 0 else f"{hh:02d}")
                p.setFont(font(22, family="Segoe UI Emoji")); p.setPen(QColor(255, 255, 255, 245)); p.drawText(QRectF(x, top + 54, cw_, 32), AL.AlignCenter, WMO_CODES.get(hc_, ("", "?"))[1])
                p.setFont(font(14, QFont.Weight.DemiBold)); p.drawText(QRectF(x, top + 88, cw_, 22), AL.AlignCenter, self._wtemp(ht))
            top += 134.0
        days = (w.get("daily") or [])[:5]
        if days:
            dh = 40 + len(days) * 34; dc = QRectF(rx, top, rw, dh); self._ios_card(p, dc, 24)
            p.setFont(font(9, QFont.Weight.DemiBold, spacing=1.1)); p.setPen(IOS_GRAYT); p.drawText(QRectF(rx + 20, top + 12, 300, 14), AL.AlignLeft, "ПРОГНОЗ НА НЕСКОЛЬКО ДНЕЙ")
            vals = [(d[2], d[3]) for d in days if d[2] is not None and d[3] is not None]
            gmin = min([v[1] for v in vals] or [0]); gmax = max([v[0] for v in vals] or [1]); span = max(1.0, gmax - gmin)
            for k, (lab, dcode, tmx, tmn, rn) in enumerate(days):
                y = top + 34 + k * 34
                if k: p.setPen(QPen(QColor(255, 255, 255, 18), 1)); p.drawLine(QPointF(rx + 20, y), QPointF(rx + rw - 20, y))
                p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 240)); p.drawText(QRectF(rx + 20, y, 80, 34), AL.AlignLeft | AL.AlignVCenter, lab)
                p.setFont(font(15, family="Segoe UI Emoji")); p.drawText(QRectF(rx + 102, y, 30, 34), AL.AlignCenter, WMO_CODES.get(dcode, ("", "?"))[1])
                if rn is not None and rn >= 20: p.setFont(font(9, QFont.Weight.DemiBold)); p.setPen(rgba(IOS_BLUE, 255)); p.drawText(QRectF(rx + 130, y + 18, 36, 14), AL.AlignCenter, f"{rn:.0f}%")
                if tmx is None or tmn is None: continue
                p.setFont(font(13)); p.setPen(IOS_GRAYT); p.drawText(QRectF(rx + 172, y, 40, 34), AL.AlignRight | AL.AlignVCenter, self._wtemp(tmn))
                bx, bw = rx + 222, 150.0; p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 30)); p.drawRoundedRect(QRectF(bx, y + 14, bw, 6), 3, 3)
                f0 = (tmn - gmin) / span; f1 = (tmx - gmin) / span; bg = QLinearGradient(bx, 0, bx + bw, 0); bg.setColorAt(0, QColor(80, 190, 255)); bg.setColorAt(1, QColor(255, 190, 70))
                p.setBrush(bg); p.drawRoundedRect(QRectF(bx + bw * f0, y + 14, max(8.0, bw * (f1 - f0)), 6), 3, 3)
                p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 245)); p.drawText(QRectF(rx + 380, y, 56, 34), AL.AlignLeft | AL.AlignVCenter, self._wtemp(tmx))
            top += dh + 10.0
        tiles = []
        if self._wb("w_tile_hum", True): tiles.append(("ВЛАЖНОСТЬ", f"{w.get('hum', 0):.0f}", "%"))
        if self._wb("w_tile_wind", True): v_, u_ = self._wwind(w.get("wind", 0)); tiles.append(("ВЕТЕР", v_, u_))
        if self._wb("w_tile_pres", True): v_, u_ = self._wpres(w.get("pres", 0)); tiles.append(("ДАВЛЕНИЕ", v_, u_))
        if self._wb("w_tile_uv", True): tiles.append(("УФ-ИНДЕКС", f"{w.get('uv', 0):.0f}", ""))
        if self._wb("w_tile_rain", True): tiles.append(("ОСАДКИ", f"{(w.get('rain') or 0):.0f}", "%"))
        if self._wb("w_tile_sun", True): tiles.append(("ЗАКАТ", w.get("sunset") or "—", f"восход {w.get('sunrise') or '—'}"))
        tiles = tiles[:4]; th = max(80.0, 518.0 - top)
        if tiles:
            tw_ = (rw - 10 * (len(tiles) - 1)) / len(tiles)
            for k, (lb, val, unit) in enumerate(tiles):
                tr_ = QRectF(rx + k * (tw_ + 10), top, tw_, th); self._ios_card(p, tr_, 22)
                p.setFont(font(8, QFont.Weight.DemiBold, spacing=1.0)); p.setPen(IOS_GRAYT); p.drawText(QRectF(tr_.x() + 14, tr_.y() + 12, tr_.width() - 20, 12), AL.AlignLeft, lb)
                p.setFont(font(24, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(QRectF(tr_.x() + 14, tr_.y() + 28, tr_.width() - 20, 34), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(str(val), Qt.TextElideMode.ElideRight, int(tr_.width() - 24)))
                p.setFont(font(10)); p.setPen(IOS_GRAYT); p.drawText(QRectF(tr_.x() + 14, tr_.y() + 62, tr_.width() - 20, 14), AL.AlignLeft, QFontMetrics(p.font()).elidedText(unit, Qt.TextElideMode.ElideRight, int(tr_.width() - 24)))

    def _draw_calendar(self, p):
        AL = Qt.AlignmentFlag; y0 = self._cal_year; m0 = self._cal_month; today = datetime.date.today()
        f = font(28, QFont.Weight.Bold); p.setFont(f); p.setPen(QColor(255, 255, 255, 250)); mt = MONTH_NAMES[m0 - 1]
        p.drawText(QRectF(28, 48, 420, 40), AL.AlignLeft | AL.AlignVCenter, mt)
        p.setFont(font(28, QFont.Weight.Light)); p.setPen(rgba(ACCENT, 255)); p.drawText(QRectF(28 + QFontMetrics(f).horizontalAdvance(mt) + 12, 48, 120, 40), AL.AlignLeft | AL.AlignVCenter, str(y0))
        self._ios_pill(p, QRectF(self.EW - 232, 54, 92, 32), "Сегодня", IOS_GRAY, QColor(255, 255, 255, 240), lambda: self._cal_goto_today(), 12)
        for c, txt, d in ((QPointF(self.EW - 104, 70), "‹", -1), (QPointF(self.EW - 52, 70), "›", 1)):
            r = QRectF(c.x() - 17, c.y() - 17, 34, 34); self._ios_pill(p, r, txt, IOS_GRAY, QColor(255, 255, 255, 240), lambda d=d: self._cal_shift(d), 18)
        grid = QRectF(20, 100, self.EW - 40, 300); self._ios_card(p, grid, 24)
        cw = (self.EW - 56) / 7.0; gx = 28.0
        for i, dn in enumerate(WEEK_DAYS):
            p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(IOS_GRAYT if i < 5 else rgba(IOS_ORANGE, 230)); p.drawText(QRectF(gx + i * cw, 108, cw, 20), AL.AlignCenter, dn)
        try: weeks = _calendar.Calendar(firstweekday=0).monthdayscalendar(y0, m0)
        except Exception: weeks = []
        y = 132.0
        for week in weeks:
            for i, day in enumerate(week):
                if day == 0: continue
                date = datetime.date(y0, m0, day); r = QRectF(gx + i * cw, y, cw, 42); c = r.center(); dia = 36.0
                is_today = date == today; is_sel = date == self._cal_selected; rem = self._reminders.get(date.strftime("%Y-%m-%d")); hov = self._hover(r)
                p.setPen(Qt.PenStyle.NoPen)
                if is_today: p.setBrush(ACCENT); p.drawEllipse(c, dia / 2, dia / 2)
                elif is_sel: p.setBrush(QColor(255, 255, 255, 235)); p.drawEllipse(c, dia / 2, dia / 2)
                elif hov: p.setBrush(QColor(255, 255, 255, 28)); p.drawEllipse(c, dia / 2, dia / 2)
                if is_sel and is_today: p.setPen(QPen(QColor(255, 255, 255, 235), 2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(c, dia / 2 + 3, dia / 2 + 3)
                p.setFont(font(14, QFont.Weight.Bold if (is_today or is_sel) else QFont.Weight.Normal))
                p.setPen(QColor(8, 14, 20) if (is_today or is_sel) else (QColor(255, 255, 255, 240) if i < 5 else rgba(IOS_ORANGE, 220)))
                p.drawText(r.adjusted(0, -2, 0, -2), AL.AlignCenter, str(day))
                if rem: p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(8, 14, 20) if (is_today or is_sel) else IOS_ORANGE); p.drawEllipse(QPointF(c.x(), r.bottom() - 2.5), 2.2, 2.2)
                self._add_hit(r, lambda d=date: self._select_cal_day(d))
            y += 42.0
        panel = QRectF(20, 410, self.EW - 40, 110); self._ios_card(p, panel, 24)
        try: date_label = f"{self._cal_selected.day} {MONTH_NAMES[self._cal_selected.month - 1]} {self._cal_selected.year}"
        except Exception: date_label = self._cal_selected.strftime("%d.%m.%Y")
        p.setFont(font(9, QFont.Weight.DemiBold, spacing=1.0)); p.setPen(IOS_GRAYT); p.drawText(QRectF(panel.x() + 22, panel.y() + 12, 420, 14), AL.AlignLeft, f"НАПОМИНАНИЯ · {date_label.upper()}")
        items = self._reminders.for_date(self._cal_selected.strftime("%Y-%m-%d")); lx = panel.x() + 22; ly = panel.y() + 32
        if not items: p.setFont(font(12)); p.setPen(IOS_GRAYT); p.drawText(QRectF(lx, ly + 8, 380, 24), AL.AlignLeft | AL.AlignVCenter, "Нет напоминаний — добавь справа")
        for k, it in enumerate(items[:3]):
            ry = ly + k * 25; rr_ = QRectF(lx - 6, ry, 392, 24); hov = self._hover(rr_); dim = 110 if it.get("fired") else 245
            if hov: p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 14)); p.drawRoundedRect(rr_, 9, 9)
            pill = QRectF(lx, ry + 3, 62, 18); p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 70 if not it.get("fired") else 28)); p.drawRoundedRect(pill, 9, 9)
            p.setFont(font(9, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255, dim)); p.drawText(pill, AL.AlignCenter, it.get("time") or "весь день")
            p.setFont(font(12)); p.setPen(QColor(255, 255, 255, dim)); p.drawText(QRectF(lx + 72, ry, 270, 24), AL.AlignLeft | AL.AlignVCenter, QFontMetrics(p.font()).elidedText(it.get("text", ""), Qt.TextElideMode.ElideRight, 266))
            if hov:
                xb = QRectF(lx + 350, ry + 3, 18, 18); hx = self._hover(xb); p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(IOS_RED, 235 if hx else 160)); p.drawEllipse(xb)
                p.setFont(font(11, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255)); p.drawText(xb, AL.AlignCenter, "×"); self._add_hit(xb, lambda rid=it["id"]: self._remove_reminder_id(rid))
        if len(items) > 3: p.setFont(font(9)); p.setPen(IOS_GRAYT); p.drawText(QRectF(lx + 250, panel.y() + 10, 130, 16), AL.AlignRight, f"и ещё {len(items) - 3}")
        ix = panel.x() + 422; iy = panel.y() + 28; act = self._reminder_active
        tr = QRectF(ix, iy, 180, 36); tm = QRectF(ix + 188, iy, 66, 36); ad = QRectF(ix + 262, iy, 56, 36)
        for r_, field in ((tr, "text"), (tm, "time")):
            on = act and self._reminder_field == field
            p.setBrush(QColor(58, 58, 60, 255 if (on or self._hover(r_)) else 225)); p.setPen(QPen(ACCENT, 1.6) if on else Qt.PenStyle.NoPen); p.drawRoundedRect(r_, 18, 18)
            cur = "▏" if on and int(time.monotonic() * 2) % 2 == 0 else ""
            val = (self._reminder_text if field == "text" else self._reminder_time) if act else ""
            if val or on: p.setFont(font(13)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(r_.adjusted(14, 0, -10, 0), AL.AlignVCenter | (AL.AlignLeft if field == "text" else AL.AlignHCenter), QFontMetrics(p.font()).elidedText(val + cur, Qt.TextElideMode.ElideLeft, int(r_.width() - 26)))
            else: p.setFont(font(12)); p.setPen(IOS_GRAYT); p.drawText(r_.adjusted(14, 0, -10, 0), AL.AlignVCenter | (AL.AlignLeft if field == "text" else AL.AlignHCenter), "Что напомнить" if field == "text" else "ЧЧ:ММ")
            self._add_hit(r_, lambda f=field: self._reminder_focus(f))
        self._ios_pill(p, ad, "＋", IOS_BLUE, QColor(255, 255, 255), self._save_reminder if (act and self._reminder_text.strip()) else (lambda: self._reminder_focus("text")), 18)
        p.setFont(font(9)); p.setPen(IOS_GRAYT); p.drawText(QRectF(ix, iy + 42, 330, 28), int(AL.AlignLeft.value | AL.AlignTop.value | Qt.TextFlag.TextWordWrap.value), "Время не нужно — тогда напомню в 09:00. Tab — переключить поле, Enter — добавить.")

    def _cal_goto_today(self):
        t = datetime.date.today(); self._cal_year = t.year; self._cal_month = t.month; self._cal_selected = t; self.update()

    def _cal_shift(self, delta):
        m = self._cal_month + delta; y = self._cal_year
        if m < 1: m = 12; y -= 1
        elif m > 12: m = 1; y += 1
        self._cal_month = m; self._cal_year = y
        self._reminder_active = False; self.update()

    def _select_cal_day(self, date):
        self._cal_selected = date
        self._reminder_active = False; self._reminder_text = ""
        self.update()

    def _remove_reminder(self):
        date_key = self._cal_selected.strftime("%Y-%m-%d")
        self._reminders.remove(date_key)
        self._reminder_active = False; self._reminder_text = ""
        self.update()

    def _clip_copy_flash(self, item, i):
        self._clipboard_copy(item); self._clip_flash = (i, time.monotonic() + 1.3)

    def _draw_clipboard(self, p):
        AL = Qt.AlignmentFlag; cl = self._clipboard; count = len(cl.items); items = cl.items[:6]; now_ = time.monotonic()
        p.setFont(font(16, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 240)); p.drawText(QRectF(24, 56, 300, 28), AL.AlignLeft | AL.AlignVCenter, "Буфер обмена")
        p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 120))
        p.drawText(QRectF(24, 84, 460, 16), AL.AlignLeft | AL.AlignVCenter, f"{count} в истории · клик по карточке копирует" if count else "История пока пуста")
        if count:
            rc = QRectF(self.EW - 124, 62, 104, 28); hv = self._hover(rc)
            p.setPen(QPen(QColor(255, 255, 255, 46 if hv else 24), 1)); p.setBrush(QColor(255, 90, 100, 60 if hv else 0)); p.drawRoundedRect(rc, 14, 14)
            p.setFont(font(10, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 215 if hv else 150)); p.drawText(rc, AL.AlignCenter, "Очистить")
            self._add_hit(rc, cl.clear)
        if not items:
            draw_icon(p, "clip", QRectF(self.EW / 2 - 28, 190, 56, 56), QColor(255, 255, 255, 90), w=1.6)
            p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 190)); p.drawText(QRectF(0, 262, self.EW, 22), AL.AlignCenter, "Скопируйте что-нибудь")
            p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 110)); p.drawText(QRectF(0, 286, self.EW, 18), AL.AlignCenter, "Текст и картинки появятся здесь")
            return
        cw = (self.EW - 40 - 12) / 2; ch = 104
        for i, item in enumerate(items):
            card = QRectF(20 + (i % 2) * (cw + 12), 112 + (i // 2) * (ch + 10), cw, ch); hov = self._hover(card)
            fl = self._clip_flash; flashing = bool(fl) and fl[0] == i and now_ < fl[1]
            self._glass(p, card, 16, hov)
            is_img = item.get("type") == "image"; tx = card.x() + 16
            if is_img and item.get("image") is not None:
                pm = self._clip_thumbs.get(id(item))
                if pm is None:
                    if len(self._clip_thumbs) > 40: self._clip_thumbs.clear()
                    pm = QPixmap.fromImage(item["image"].scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)); self._clip_thumbs[id(item)] = pm
                th = QRectF(card.x() + 12, card.y() + 12, 80, ch - 24); tp = QPainterPath(); tp.addRoundedRect(th, 10, 10)
                p.save(); p.setClipPath(tp); p.drawPixmap(th.toRect(), pm); p.restore(); tx = card.x() + 104
            p.setFont(font(8, QFont.Weight.DemiBold, spacing=0.9)); p.setPen(rgba(ACCENT, 210))
            p.drawText(QRectF(tx, card.y() + 11, 120, 12), AL.AlignLeft | AL.AlignVCenter, "ИЗОБРАЖЕНИЕ" if is_img else "ТЕКСТ")
            p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 105))
            p.drawText(QRectF(card.right() - 100, card.y() + 10, 66 if hov else 84, 14), AL.AlignRight | AL.AlignVCenter, item.get("time", ""))
            body = QRectF(tx, card.y() + 30, card.right() - tx - 16, ch - 40)
            p.save(); p.setClipRect(body); p.setFont(font(11)); p.setPen(QColor(255, 255, 255, 232))
            p.drawText(body, int(AL.AlignTop.value | AL.AlignLeft.value | Qt.TextFlag.TextWordWrap.value), (item.get("preview", "") or "")[:140]); p.restore()
            if flashing:
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 60)); p.drawRoundedRect(card, 16, 16)
                p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 250)); p.drawText(card, AL.AlignCenter, "✓ Скопировано")
            self._add_hit(card, lambda it=item, idx=i: self._clip_copy_flash(it, idx))
            if hov:
                xb = QRectF(card.right() - 30, card.y() + 8, 22, 22); hx = self._hover(xb)
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 90, 100, 200 if hx else 90)); p.drawEllipse(xb)
                p.setFont(font(13, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255)); p.drawText(xb, AL.AlignCenter, "×")
                self._add_hit(xb, lambda idx=i: cl.remove(idx))

    NOTE_PALETTE = [
        ("Без цвета", None),
        ("Лаванда", "#9B8CFF"),
        ("Голубой", "#55B9F5"),
        ("Мятный", "#55D6A3"),
        ("Зелёный", "#83C96B"),
        ("Жёлтый", "#F2C75C"),
        ("Оранжевый", "#F39A55"),
        ("Розовый", "#F17FA8"),
        ("Красный", "#EF6B73"),
        ("Бирюзовый", "#4CCBC5"),
    ]

    def _note_choose_color(self, index):
        if not (0 <= index < len(self._notes.items)):
            return
        menu = QMenu(self)
        for label, value in self.NOTE_PALETTE:
            swatch = QColor(value or "#8C95A4")
            pm = QPixmap(16, 16); pm.fill(Qt.GlobalColor.transparent)
            pp = QPainter(pm); pp.setRenderHint(QPainter.RenderHint.Antialiasing)
            pp.setPen(QPen(QColor(255, 255, 255, 90), 1)); pp.setBrush(swatch)
            pp.drawEllipse(QRectF(2, 2, 12, 12)); pp.end()
            action = menu.addAction(QIcon(pm), label)
            action.triggered.connect(lambda checked=False, idx=index, color=value: self._notes.set_color(idx, color))
        menu.exec(QCursor.pos())
        self.update()

    def _note_toggle_pin(self, index):
        self._notes.toggle_pin(index)
        self.update()

    def _save_note_dialog(self, title, body, index):
        if index >= 0:
            self._notes.update(index, body, title)
            return index
        if title.strip() or body.strip():
            self._notes.add(body, title)
            return 0
        return -1

    def _delete_note_dialog(self, index):
        self._notes.remove(index); self.update()

    def _open_note_editor(self, index=-1):
        if not hasattr(self, "_note_editor") or self._note_editor is None:
            self._note_editor = InlineNoteEditor(self)
        self.current_page = "notes"
        self._note_editor.open_note(index)


    def _start_edit_note(self, i):
        if 0 <= i < len(self._notes.items): self._open_note_editor(i)

    def _cancel_note(self):
        self._new_note_active = False; self._new_note_text = ""; self._edit_note_idx = -1; self.update()

    def _draw_notes(self, p):
        AL = Qt.AlignmentFlag
        notes = self._notes.items
        if getattr(self, "_note_editor", None) and self._note_editor.isVisible():
            return
        pinned_count = sum(1 for n in notes if n.get("pin", False))
        subtitle = f"{len(notes)} заметок · {pinned_count} закреплено" if pinned_count else f"{len(notes)} заметок · всё сохраняется автоматически"
        self._ios_title(p, "Заметки", subtitle)

        r_new = QRectF(20, 108, self.EW - 40, 54)
        self._ios_card(p, r_new, 25, self._hover(r_new))
        draw_icon(p, "note", QRectF(r_new.x() + 18, r_new.y() + 17, 20, 20), rgba(ACCENT, 245))
        p.setFont(font(14, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,235))
        p.drawText(QRectF(r_new.x()+54, r_new.y()+7, r_new.width()-190, 20), AL.AlignVCenter|AL.AlignLeft, "Создать новую заметку")
        p.setFont(font(10)); p.setPen(QColor(160,168,182))
        p.drawText(QRectF(r_new.x()+54, r_new.y()+29, r_new.width()-190, 16), AL.AlignVCenter|AL.AlignLeft, "Идеи · планы · списки дел")
        self._ios_pill(p, QRectF(r_new.right()-118, r_new.y()+10, 102, 34), "＋  Новая", IOS_BLUE, QColor(255,255,255), self._activate_note_input, 12)
        self._add_hit(r_new, self._activate_note_input)

        # Закреплённые заметки идут первыми, остальные сохраняют исходный порядок.
        rows = sorted(enumerate(notes), key=lambda pair: (not bool(pair[1].get("pin", False)), pair[0]))[:6]
        if not rows:
            empty = QRectF(24, 190, self.EW-48, 178)
            p.setPen(QPen(QColor(255,255,255,18), 1)); p.setBrush(QColor(255,255,255,7)); p.drawRoundedRect(empty, 24, 24)
            cx, cy = self.EW/2, 239
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 24)); p.drawEllipse(QPointF(cx,cy),25,25)
            draw_icon(p, "note", QRectF(cx-12,cy-12,24,24), ACCENT, 1.8)
            p.setFont(font(15, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,225))
            p.drawText(QRectF(0, 278, self.EW, 24), AL.AlignCenter, "Здесь появятся ваши заметки")
            p.setFont(font(11)); p.setPen(QColor(160,168,182))
            p.drawText(QRectF(30, 306, self.EW-60, 22), AL.AlignCenter, "Сохраняйте идеи, планы и важные мысли")
            return

        rh = 66.0
        lst = QRectF(20, 174, self.EW-40, rh*len(rows))
        self._ios_card(p, lst, 22)
        palette = [QColor(c) for _n, c in self.NOTE_PALETTE[1:]]
        for visual_i, (note_idx, note) in enumerate(rows):
            r = QRectF(lst.x(), lst.y()+visual_i*rh, lst.width(), rh)
            hov = self._hover(r)
            if hov:
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,12))
                p.drawRoundedRect(r.adjusted(5,3,-5,-3),16,16)

            color_idx = note.get("color")
            marker_col = QColor("#8C95A4")
            if isinstance(color_idx, int) and 0 <= color_idx < len(palette):
                marker_col = palette[color_idx]
            elif isinstance(color_idx, str):
                try: marker_col = QColor(color_idx)
                except Exception: pass

            raw = str(note.get("text", ""))
            title = note.get("title", "") or (raw.splitlines() or ["Без названия"])[0][:70]
            rest = raw if note.get("title") else " ".join(raw.splitlines()[1:]).strip()
            if not rest: rest = raw if note.get("title") else "Откройте, чтобы продолжить редактирование"

            p.setPen(Qt.PenStyle.NoPen); p.setBrush(marker_col)
            p.drawRoundedRect(QRectF(r.x()+12,r.y()+18,4,32), 2, 2)
            text_w = r.width()-180
            p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,248))
            p.drawText(QRectF(r.x()+27,r.y()+10,text_w,22), AL.AlignLeft|AL.AlignVCenter,
                       QFontMetrics(p.font()).elidedText(title,Qt.TextElideMode.ElideRight,int(text_w)))
            p.setFont(font(10)); p.setPen(QColor(158,166,180))
            p.drawText(QRectF(r.x()+27,r.y()+37,text_w,18), AL.AlignLeft|AL.AlignVCenter,
                       QFontMetrics(p.font()).elidedText(rest.replace("\\n","  ·  "),Qt.TextElideMode.ElideRight,int(text_w)))

            self._add_hit(r, lambda idx=note_idx: self._start_edit_note(idx))

            if note.get("pin", False):
                p.setFont(font(11, QFont.Weight.Bold)); p.setPen(QColor(255,205,95,235))
                p.drawText(QRectF(r.right()-69,r.y()+9,18,18), AL.AlignCenter, "★")

            if hov:
                # Компактные действия появляются только при наведении и не мешают чтению.
                pin_r = QRectF(r.right()-68, r.y()+22, 22, 22)
                color_r = QRectF(r.right()-42, r.y()+22, 22, 22)
                for action_r in (pin_r, color_r):
                    p.setPen(QPen(QColor(255,255,255,32), 1)); p.setBrush(QColor(255,255,255,13))
                    p.drawRoundedRect(action_r, 7, 7)
                p.setFont(font(12, QFont.Weight.Bold)); p.setPen(QColor(255,215,120,245))
                p.drawText(pin_r, AL.AlignCenter, "★" if note.get("pin", False) else "☆")
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(marker_col)
                p.drawEllipse(QRectF(color_r.x()+6, color_r.y()+6, 10, 10))
                self._add_hit(pin_r, lambda idx=note_idx: self._note_toggle_pin(idx))
                self._add_hit(color_r, lambda idx=note_idx: self._note_choose_color(idx))
                p.setFont(font(9)); p.setPen(QColor(135,144,160))
                p.drawText(QRectF(r.right()-150,r.y()+5,76,13), AL.AlignRight|AL.AlignVCenter, note.get("time",""))
            else:
                p.setFont(font(9)); p.setPen(QColor(135,144,160))
                p.drawText(QRectF(r.right()-150,r.y()+12,118,16), AL.AlignRight|AL.AlignVCenter, note.get("time",""))

            draw_icon(p,"chevron-right",QRectF(r.right()-19,r.center().y()-7,12,14),QColor(150,155,165))
            if visual_i < len(rows)-1:
                p.setPen(QPen(QColor(255,255,255,18),1))
                p.drawLine(QPointF(r.x()+20,r.bottom()),QPointF(r.right()-14,r.bottom()))
        if len(notes)>6:
            p.setFont(font(10)); p.setPen(IOS_GRAYT)
            p.drawText(QRectF(20,lst.bottom()+5,self.EW-40,18),AL.AlignCenter,f"Показаны последние 6 · ещё {len(notes)-6}")

    # ═══════════════════ AI ═══════════════════
    def _ensure_ai_view(self):
        if not self._ai_webengine_ok: return None
        if self._ai_view is None:
            try:
                from PyQt6.QtWebEngineWidgets import QWebEngineView
                from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
                self._ai_profile = QWebEngineProfile("island_ai", self)
                self._ai_profile.setPersistentStoragePath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_profile"))
                self._ai_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
                self._ai_profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
                self._ai_view = QWebEngineView(self)
                self._ai_view.setPage(QWebEnginePage(self._ai_profile, self._ai_view))
                self._ai_view.setStyleSheet("background: #0a0c14;")
                self._ai_view.hide()
            except Exception as e:
                log_error(f"ai view: {e}"); self._ai_webengine_ok = False; return None
        return self._ai_view

    def _update_ai_visibility(self):
        if self._ai_view is None: return
        show = self.expanded and not self._animating and self.current_page == "ai" and bool(self._ai_url)
        if show:
            self._position_ai_view()
            self._ai_view.show(); self._ai_view.raise_()
        else:
            self._ai_view.hide()

    def _position_ai_view(self):
        if self._ai_view is None or not self.expanded: return
        self._ai_view.setGeometry(int(round(self._org_x() + 20)), int(round(self._org_y() + 56)), max(1, self.EW - 40), max(1, self.EH - 76))

    def _ai_open_inline(self, url):
        view = self._ensure_ai_view()
        if view is None:
            self._ai_open_window(url, "ИИ"); return
        try:
            from PyQt6.QtCore import QUrl
            self._ai_url = url; self._ai_service = "gemini" if "gemini" in url else "deepseek"
            view.setUrl(QUrl(url))
            self._update_ai_visibility()
        except Exception as e: log_error(f"ai open inline: {e}")

    def _ai_close_inline(self):
        self._ai_url = ""; self._update_ai_visibility(); self.update()
    def _ai_pop_out(self):
        """Перенести текущий открытый ИИ из островка в отдельное окно."""
        if self._ai_url:
            self._ai_open_window(self._ai_url, "AI Чат")
            self._ai_close_inline()

    def _ai_open_window(self, url, name="ИИ"):
        try:
            w = AIWindow(url, name)
            self._ai_windows.append(w)
            w.show(); w.raise_()
        except Exception as e: log_error(f"ai window: {e}")

    def _open_ai_window_quick(self):
        self._ai_open_window("https://chat.deepseek.com", "DeepSeek")

    @staticmethod
    def _sparkle(cx, cy, r, k=0.16):
        pp = QPainterPath(); pp.moveTo(cx, cy - r)
        pp.quadTo(cx + r * k, cy - r * k, cx + r, cy); pp.quadTo(cx + r * k, cy + r * k, cx, cy + r)
        pp.quadTo(cx - r * k, cy + r * k, cx - r, cy); pp.quadTo(cx - r * k, cy - r * k, cx, cy - r)
        pp.closeSubpath(); return pp

    def _draw_ai(self, p):
        if self._ai_view is not None and self._ai_view.isVisible(): return
        AL = Qt.AlignmentFlag; t = time.monotonic(); NP = Qt.PenStyle.NoPen
        g = QLinearGradient(26, 62, 50, 86); g.setColorAt(0, ACCENT); g.setColorAt(1, VIOLET)
        p.setPen(NP); p.setBrush(g); p.drawPath(self._sparkle(38, 74, 11 + math.sin(t * 2) * 0.8))
        p.setFont(font(17, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 245))
        p.drawText(QRectF(60, 58, 400, 32), AL.AlignLeft | AL.AlignVCenter, "Искусственный интеллект")
        p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 130))
        p.drawText(QRectF(60, 88, self.EW - 80, 18), AL.AlignLeft | AL.AlignVCenter,
                   "Открывается прямо в островке · вход в аккаунт сохраняется" if self._ai_webengine_ok else "Откроется в отдельном окне (для встроенного режима нужен PyQt6-WebEngine)")
        services = [("DeepSeek", "https://chat.deepseek.com", QColor(77, 107, 254), "Умный чат, рассуждения и код", ("Рассуждения", "Код", "Длинные тексты")),
                    ("Gemini", "https://gemini.google.com/app", QColor(66, 133, 244), "Ассистент от Google", ("Поиск", "Изображения", "Google"))]
        gap = 16; cw = (self.EW - 40 - gap) / 2; ch = self.EH - 156; y = 118
        for i, (name, url, accent, desc, chips) in enumerate(services):
            r0 = QRectF(20 + i * (cw + gap), y, cw, ch); hov = self._hover(r0)
            r = r0.translated(0, -3.0 if hov else 0.0)
            cp = QPainterPath(); cp.addRoundedRect(r, 24, 24)
            p.save(); p.setClipPath(cp)
            cg = QLinearGradient(r.topLeft(), r.bottomRight()); cg.setColorAt(0, rgba(accent, 120 if hov else 74)); cg.setColorAt(0.6, QColor(16, 18, 26, 250)); cg.setColorAt(1, QColor(10, 12, 18, 252))
            p.fillPath(cp, cg)
            for k in range(3):     # плавающие световые пятна
                ox_ = r.x() + r.width() * (0.2 + 0.3 * k) + math.sin(t * 0.7 + k * 2.1 + i) * 26
                oy_ = r.y() + r.height() * (0.25 + 0.18 * k) + math.cos(t * 0.55 + k * 1.7) * 20
                og = QRadialGradient(QPointF(ox_, oy_), 80); og.setColorAt(0, rgba(accent, 64 if k == 0 else 44)); og.setColorAt(1, rgba(accent, 0))
                p.setPen(NP); p.setBrush(og); p.drawEllipse(QPointF(ox_, oy_), 80, 80)
            p.restore()
            p.setPen(QPen(rgba(accent, 210) if hov else QColor(255, 255, 255, 32), 1.2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRoundedRect(r, 24, 24)
            ic = QRectF(r.center().x() - 38, r.y() + 30, 76, 76)
            ig = QLinearGradient(ic.topLeft(), ic.bottomRight()); ig.setColorAt(0, rgba(accent, 255)); ig.setColorAt(1, rgba(VIOLET, 230))
            hg = QRadialGradient(ic.center(), 66); hg.setColorAt(0, rgba(accent, 120 if hov else 80)); hg.setColorAt(1, rgba(accent, 0))
            p.setPen(NP); p.setBrush(hg); p.drawEllipse(ic.center(), 66, 66)
            p.setBrush(ig); p.drawRoundedRect(ic, 24, 24)
            if name == "Gemini":
                p.setBrush(QColor(255, 255, 255, 250)); p.drawPath(self._sparkle(ic.center().x(), ic.center().y(), 24 + math.sin(t * 2.2) * 1.5, 0.14))
            else:
                p.setPen(QPen(QColor(255, 255, 255, 245), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(ic.center(), 16, 16); p.setPen(NP); p.setBrush(QColor(255, 255, 255, 250)); p.drawEllipse(QPointF(ic.center().x() + 4, ic.center().y() - 1), 5.5, 5.5)
            p.setFont(font(20, QFont.Weight.Bold)); p.setPen(QColor(255, 255, 255))
            p.drawText(QRectF(r.x(), ic.bottom() + 16, r.width(), 30), AL.AlignCenter, name)
            p.setFont(font(11)); p.setPen(QColor(255, 255, 255, 160))
            p.drawText(QRectF(r.x(), ic.bottom() + 48, r.width(), 20), AL.AlignCenter, desc)
            cfont = font(9, QFont.Weight.DemiBold); fm = QFontMetrics(cfont); cwid = [fm.horizontalAdvance(c_) + 18 for c_ in chips]
            cx_ = r.center().x() - (sum(cwid) + 8 * (len(chips) - 1)) / 2; cy_ = ic.bottom() + 82
            for c_, w_ in zip(chips, cwid):
                p.setPen(QPen(QColor(255, 255, 255, 26), 1)); p.setBrush(QColor(255, 255, 255, 14)); p.drawRoundedRect(QRectF(cx_, cy_, w_, 22), 11, 11)
                p.setFont(cfont); p.setPen(QColor(255, 255, 255, 190)); p.drawText(QRectF(cx_, cy_, w_, 22), AL.AlignCenter, c_); cx_ += w_ + 8
            rb = QRectF(r.x() + 24, r.bottom() - 66, r.width() - 48 - 96, 44); hb = self._hover(rb)
            gb = QLinearGradient(rb.topLeft(), rb.bottomRight()); gb.setColorAt(0, rgba(accent, 255 if hb else 215)); gb.setColorAt(1, rgba(VIOLET, 255 if hb else 215))
            p.setPen(NP); p.setBrush(gb); p.drawRoundedRect(rb, 14, 14)
            p.setFont(font(12, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255)); p.drawText(rb, AL.AlignCenter, "Открыть здесь")
            rw = QRectF(rb.right() + 10, rb.y(), 86, 44); hw = self._hover(rw)
            p.setPen(QPen(QColor(255, 255, 255, 60 if hw else 34), 1)); p.setBrush(QColor(255, 255, 255, 30 if hw else 14)); p.drawRoundedRect(rw, 14, 14)
            p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 230)); p.drawText(rw, AL.AlignCenter, "↗ Окно")
            self._add_hit(r, lambda u=url: self._ai_open_inline(u))
            self._add_hit(rw, lambda u=url, n=name: self._ai_open_window(u, n))
            self._add_hit(rb, lambda u=url: self._ai_open_inline(u))

    def _draw_system(self, p):
        if self.system_view == "menu":
            if not hasattr(self, "_dark"): self._dark = self._theme_dark()
            X = [20 + i*193 for i in range(4)]
            wst = self._wifi_cur or ("Выключен" if self._wifi_on == "off" else "Сети")
            bst = {"on": "Включён", "off": "Выключен"}.get(self.bt_state, "Устройства")
            self._tile(p, QRectF(X[0],60,181,150), "wifi", "Wi-Fi", wst[:20], lambda: self._open_system_sub("wifi"), self._wifi_on == "on")
            self._tile(p, QRectF(X[1],60,181,150), "bt", "Bluetooth", bst, lambda: self._open_system_sub("bt"), self.bt_state == "on")
            self._tile(p, QRectF(X[2],60,181,150), "theme", "Тёмная тема", "Включена" if self._dark else "Выключена", self._toggle_theme, self._dark)
            self._tile(p, QRectF(X[3],60,181,150), "vol", "Звук", "Вкл / выкл", self._mute_toggle)
            self._small(p, QRectF(X[0],224,181,84), "lock", "Блокировка", lambda: user32.LockWorkStation())
            self._small(p, QRectF(X[1],224,181,84), "moon", "Сон", lambda: self._confirm("Сон", "В спящий режим?", self._sleep_pc))
            self._small(p, QRectF(X[2],224,181,84), "restart", "Перезагрузка", lambda: self._confirm("Перезагрузка", "Перезагрузить?", self._restart_pc))
            self._small(p, QRectF(X[3],224,181,84), "power", "Выключение", lambda: self._confirm("Выключение", "Выключить?", self._shutdown_pc))
            self._draw_system_stats(p)
        elif self.system_view == "wifi": self._draw_wifi_panel(p)
        elif self.system_view == "bt": self._draw_bt_panel(p)

    @staticmethod
    def _fmt_speed(b):
        if b < 1024: return f"{b:.0f} Б/с"
        if b < 1048576: return f"{b / 1024:.0f} КБ/с"
        return f"{b / 1048576:.1f} МБ/с"

    def _gauge(self, p, r, key, label, frac, big, sub, c1, low_bad=False):
        AL = Qt.AlignmentFlag
        cur = self._gv.get(key, 0.0); cur += (frac - cur) * 0.16; self._gv[key] = cur
        f = max(0.0, min(1.0, cur)); load = (1.0 - f) if low_bad else f
        col = QColor(255, 90, 90) if load > 0.85 else (QColor(255, 170, 70) if load > 0.65 else c1)
        self._glass(p, r, 18, self._hover(r))
        cx = r.center().x(); cy = r.y() + 64; R = 38.0; arc = QRectF(cx - R, cy - R, 2 * R, 2 * R)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 26), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 225 * 16, -270 * 16)
        if f > 0.004:
            for w_, a_ in ((18, 22), (12, 46)):
                p.setPen(QPen(rgba(col, a_), w_, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 225 * 16, int(-270 * 16 * f))
            p.setPen(QPen(col, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(arc, 225 * 16, int(-270 * 16 * f))
        p.setFont(font(19, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 245)); p.drawText(QRectF(cx - 42, cy - 16, 84, 32), AL.AlignCenter, big)
        p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255, 255, 255, 215)); p.drawText(QRectF(r.x(), r.y() + 108, r.width(), 18), AL.AlignCenter, label)
        p.setFont(font(9)); p.setPen(QColor(255, 255, 255, 120)); p.drawText(QRectF(r.x(), r.y() + 126, r.width(), 16), AL.AlignCenter, sub)

    def _draw_system_stats(self, p):
        if not self._wb("sys_stats", True): return
        AL = Qt.AlignmentFlag; items = []
        if self._wb("sys_cpu", True): items.append(("cpu", "Процессор", self.d["cpu"] / 100.0, f"{self.d['cpu']:.0f}%", f"{psutil.cpu_count()} потоков", ACCENT, False))
        if self._wb("sys_ram", True): items.append(("ram", "Память", self.d["mem"] / 100.0, f"{self.d['mem']:.0f}%", f"{self.mem_used:.1f} / {self.mem_total:.0f} ГБ", VIOLET, False))
        if self._wb("sys_disk", True): items.append(("disk", "Диск C:", self.d["disk"] / 100.0, f"{self.d['disk']:.0f}%", "занято", QColor(90, 220, 170), False))
        if self._wb("sys_gpu", True):
            g = self._gpu; sub = (f"{g.temp:.0f}°C" + (f" · {g.vram[0]:.1f}/{g.vram[1]:.0f} ГБ" if g.vram else "")) if (g.ok and g.temp is not None) else (g.name[:18] if g.name else "загрузка")
            items.append(("gpu", "Видеокарта", g.load / 100.0 if g.ok else 0.0, f"{g.load:.0f}%" if g.ok else "…", sub, QColor(255, 150, 100), False))
        if self._wb("sys_batt", True) and self.battery:
            pct, plug = self.battery; items.append(("batt", "Батарея", pct / 100.0, f"{pct:.0f}%", "заряжается" if plug else "от батареи", QColor(120, 230, 120), True))
        gap = 12; n = len(items)
        for i, (k, lb, fr, big, sub, c1, lowbad) in enumerate(items):
            w = (760 - gap * (n - 1)) / n
            self._gauge(p, QRectF(20 + i * (w + gap), 322, w, 150), k, lb, fr, big, sub, c1, lowbad)
        if self._wb("sys_net", True):
            r = QRectF(20, 484, 760, 40); self._glass(p, r, 16)
            p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(110, 230, 255, 235))
            p.drawText(QRectF(r.x() + 18, r.y(), 170, r.height()), AL.AlignLeft | AL.AlignVCenter, "↓ " + self._fmt_speed(self.net_down))
            p.setPen(QColor(255, 170, 200, 235)); p.drawText(QRectF(r.x() + 178, r.y(), 170, r.height()), AL.AlignLeft | AL.AlignVCenter, "↑ " + self._fmt_speed(self.net_up))
            try:
                up = time.time() - psutil.boot_time(); h_, m_ = int(up // 3600), int(up % 3600 // 60)
                p.setFont(font(10)); p.setPen(QColor(255, 255, 255, 130)); p.drawText(QRectF(r.x() + 330, r.y(), 170, r.height()), AL.AlignLeft | AL.AlignVCenter, f"Работает {h_} ч {m_} м")
            except Exception: pass
            hist = self._cpu_hist
            if len(hist) > 2:
                sx, sw, sy, sh = r.right() - 232, 214, r.y() + 8, r.height() - 16
                pts = [QPointF(sx + sw * i / (len(hist) - 1), sy + sh * (1 - min(100.0, hist[i]) / 100.0)) for i in range(len(hist))]
                ar = QPainterPath(); ar.moveTo(sx, sy + sh)
                for pt in pts: ar.lineTo(pt)
                ar.lineTo(sx + sw, sy + sh); ar.closeSubpath()
                g = QLinearGradient(0, sy, 0, sy + sh); g.setColorAt(0, rgba(ACCENT, 90)); g.setColorAt(1, rgba(ACCENT, 0)); p.fillPath(ar, g)
                ln = QPainterPath(); ln.moveTo(pts[0])
                for pt in pts[1:]: ln.lineTo(pt)
                p.setPen(QPen(rgba(ACCENT, 230), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(ln)

    def _sys_stats_menu(self, gpos):
        m = QMenu(self)
        m.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(0,205,255,80)}QMenu::separator{height:1px;background:rgba(255,255,255,25);margin:4px 8px}")
        def add(label, key):
            a = m.addAction(label); a.setCheckable(True); a.setChecked(self._wb(key, True))
            a.toggled.connect(lambda v, k=key: (self.settings.setValue(k, bool(v)), self.update()))
        add("Показывать системный монитор", "sys_stats"); m.addSeparator()
        add("Процессор", "sys_cpu"); add("Память", "sys_ram"); add("Диск", "sys_disk"); add("Видеокарта", "sys_gpu"); add("Батарея", "sys_batt"); add("Сеть, время работы и график", "sys_net")
        m.addSeparator(); m.addAction("⚙ Настройки…", self._open_settings); m.exec(gpos)

    def _open_system_sub(self, sub):
        self.system_view = sub
        if sub == "wifi": self._load_wifi_networks()
        elif sub == "bt": self._bt_toggle()
        self.update()

    def _btn(self, p, r, text, cb, primary=False, size=11):
        hov = self._hover(r); p.setPen(Qt.PenStyle.NoPen)
        if primary:
            g = QLinearGradient(r.topLeft(), r.bottomRight()); g.setColorAt(0, rgba(ACCENT, 255 if hov else 210)); g.setColorAt(1, rgba(VIOLET, 255 if hov else 210)); p.setBrush(g)
        else: p.setBrush(QColor(255,255,255, 40 if hov else 20))
        p.drawRoundedRect(r, 10, 10); p.setFont(font(size, QFont.Weight.DemiBold))
        p.setPen(QColor(10,12,20) if primary else QColor(255,255,255,235)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, text); self._add_hit(r, cb)

    def _panel_head(self, p, title):
        self._btn(p, QRectF(20, 60, 100, 36), "← Назад", lambda: setattr(self, "system_view", "menu"), size=12)
        p.setFont(font(16, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245))
        p.drawText(QRectF(136, 60, 260, 36), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, title)

    def _draw_wifi_panel(self, p):
        AL = Qt.AlignmentFlag; self._panel_head(p, "Wi-Fi")
        on = self._wifi_on == "on"
        self._btn(p, QRectF(self.EW-300, 60, 140, 36), "Выключить" if on else "Включить", self._wifi_toggle, True)
        self._btn(p, QRectF(self.EW-150, 60, 130, 36), "Обновить", self._load_wifi_networks)
        sub = f"Подключено: {self._wifi_cur}" if self._wifi_cur else ("Wi-Fi выключен" if self._wifi_on == "off" else "Не подключено")
        p.setFont(font(11)); p.setPen(QColor(255,255,255,150)); p.drawText(QRectF(20, 100, self.EW-40, 20), AL.AlignLeft|AL.AlignVCenter, sub)
        if not self.wifi_networks:
            p.setFont(font(12)); p.setPen(QColor(255,255,255,120)); p.drawText(QRectF(20, 200, self.EW-40, 40), AL.AlignCenter, "Сети не найдены")
        y = 128
        for net in self.wifi_networks[:6]:
            r = QRectF(20, y, self.EW-40, 52); hov = self._hover(r); cur = net["ssid"] == self._wifi_cur
            p.setPen(QPen(rgba(ACCENT, 160) if cur else QColor(255,255,255, 50 if hov else 20), 1))
            p.setBrush(QColor(38,40,52, 240 if hov else 210)); p.drawRoundedRect(r, 12, 12)
            p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245))
            p.drawText(QRectF(r.x()+18, r.y()+6, r.width()-300, 22), AL.AlignLeft|AL.AlignVCenter, net["ssid"][:40])
            saved = net["ssid"] in self._wifi_profiles
            p.setFont(font(9)); p.setPen(QColor(255,255,255,140))
            p.drawText(QRectF(r.x()+18, r.y()+29, r.width()-300, 16), AL.AlignLeft|AL.AlignVCenter, f"{net['auth']}{' · сохранена' if saved else ''}")
            try: lvl = int(net["signal"].rstrip("%")) // 25 + 1
            except Exception: lvl = 1
            for b in range(4):
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 230) if b < lvl else QColor(255,255,255,40))
                p.drawRoundedRect(QRectF(r.right()-190+b*7, r.y()+30-b*5, 4, 6+b*5), 1.5, 1.5)
            p.setFont(font(10)); p.setPen(QColor(255,255,255,150)); p.drawText(QRectF(r.right()-155, r.y(), 50, r.height()), AL.AlignLeft|AL.AlignVCenter, net["signal"])
            rb = QRectF(r.right()-100, r.y()+10, 88, r.height()-20)
            if cur: p.setPen(rgba(ACCENT, 255)); p.setFont(font(11, QFont.Weight.DemiBold)); p.drawText(rb, AL.AlignCenter, "✓ Активна")
            else: self._btn(p, rb, "Подключить", lambda n=net: self._wifi_click(n), True, 10)
            y += 58
        if self._wifi_msg:
            p.setFont(font(11)); p.setPen(rgba(ACCENT, 240)); p.drawText(QRectF(20, self.EH-60, self.EW-40, 22), AL.AlignLeft|AL.AlignVCenter, self._wifi_msg)
        if self._wifi_pw_for is not None:
            self._add_hit(QRectF(0, 100, self.EW, self.EH-100), lambda: None)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,170)); p.drawRect(QRectF(0, 100, self.EW, self.EH-100))
            c = QRectF(self.EW/2-250, 170, 500, 190); p.setPen(QPen(QColor(255,255,255,40), 1)); p.setBrush(QColor(28,30,42,252)); p.drawRoundedRect(c, 18, 18)
            p.setFont(font(14, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245)); p.drawText(QRectF(c.x()+24, c.y()+16, c.width()-48, 26), AL.AlignLeft|AL.AlignVCenter, f"Пароль для «{self._wifi_pw_for['ssid'][:28]}»")
            fr = QRectF(c.x()+24, c.y()+58, c.width()-48, 44); p.setPen(QPen(rgba(ACCENT, 200), 1.2)); p.setBrush(QColor(255,255,255,18)); p.drawRoundedRect(fr, 10, 10)
            p.setFont(font(16)); p.setPen(QColor(255,255,255,245)); dots = "•" * len(self._wifi_pw) + ("|" if int(time.monotonic()*2) % 2 == 0 else "")
            p.drawText(fr.adjusted(14, 0, -14, 0), AL.AlignLeft|AL.AlignVCenter, dots)
            p.setFont(font(10)); p.setPen(QColor(255,255,255,120)); p.drawText(QRectF(c.x()+24, c.y()+108, c.width()-48, 18), AL.AlignLeft|AL.AlignVCenter, "Введите пароль и нажмите Enter")
            def _ok():
                net = self._wifi_pw_for; pw = self._wifi_pw; self._wifi_pw_for = None; self._wifi_pw = ""
                if net and pw: self._wifi_connect(net, pw)
                self.update()
            self._btn(p, QRectF(c.x()+24, c.bottom()-52, 150, 38), "Подключить", _ok, True, 12)
            self._btn(p, QRectF(c.x()+186, c.bottom()-52, 110, 38), "Отмена", lambda: (setattr(self, "_wifi_pw_for", None), self.update()), size=12)

    def _draw_bt_panel(self, p):
        AL = Qt.AlignmentFlag; self._panel_head(p, "Bluetooth")
        on = self.bt_state == "on"
        self._btn(p, QRectF(self.EW-300, 60, 140, 36), "Выключить" if on else "Включить", self._bt_actual_toggle, True)
        self._btn(p, QRectF(self.EW-150, 60, 130, 36), "Обновить", self._bt_toggle)
        r = QRectF(20, 110, self.EW-40, 70); p.setPen(QPen(QColor(255,255,255,30), 1)); p.setBrush(QColor(38,40,52,240)); p.drawRoundedRect(r, 14, 14)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(rgba(ACCENT, 230) if on else QColor(255,255,255,50)); p.drawEllipse(QPointF(r.x()+36, r.center().y()), 12, 12)
        draw_icon(p, "bt", QRectF(r.x()+28, r.center().y()-8, 16, 16), QColor(10,12,20) if on else QColor(255,255,255,200))
        st = {"on": "Включён", "off": "Выключен"}.get(self.bt_state, "Недоступен")
        p.setFont(font(15, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245)); p.drawText(QRectF(r.x()+64, r.y(), 300, r.height()), AL.AlignLeft|AL.AlignVCenter, f"Bluetooth: {st}")
        p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,150)); p.drawText(QRectF(20, 196, 400, 20), AL.AlignLeft|AL.AlignVCenter, "СОПРЯЖЁННЫЕ УСТРОЙСТВА")
        if not self._bt_devs:
            p.setFont(font(12)); p.setPen(QColor(255,255,255,110)); p.drawText(QRectF(20, 230, self.EW-40, 40), AL.AlignCenter, "Устройства не найдены")
        for i, d in enumerate(self._bt_devs):
            rr = QRectF(20, 222+i*46, self.EW-40, 40); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,14)); p.drawRoundedRect(rr, 10, 10)
            p.setFont(font(12)); p.setPen(QColor(255,255,255,235)); p.drawText(QRectF(rr.x()+16, rr.y(), rr.width()-32, rr.height()), AL.AlignLeft|AL.AlignVCenter, d[:60])

    def _theme_dark(self):
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
        except: return True

    def _toggle_theme(self):
        try:
            import winreg
            self._dark = not getattr(self, "_dark", True); v = 0 if self._dark else 1
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
            for n in ("AppsUseLightTheme", "SystemUsesLightTheme"): winreg.SetValueEx(k, n, 0, winreg.REG_DWORD, v)
        except Exception as ex: log_error(f"theme: {ex}")
        self.update()

    def _tile(self, p, r, icon, title, status, cb, active=False):
        hov = self._hover(r); AL = Qt.AlignmentFlag
        p.setBrush(QColor(255,255,255, 30 if active else (20 if hov else 11))); p.setPen(QPen(QColor(255,255,255, 40 if active else 14), 1)); p.drawRoundedRect(r, 20, 20)
        c = QRectF(r.x()+16, r.y()+16, 46, 46); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255,255,255,235) if active else QColor(255,255,255,22)); p.drawEllipse(c)
        draw_icon(p, icon, c.adjusted(12,12,-12,-12), QColor(10,10,12) if active else QColor(255,255,255,235))
        p.setFont(font(13, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,245)); p.drawText(QRectF(r.x()+16, r.bottom()-52, r.width()-24, 22), AL.AlignLeft|AL.AlignVCenter, title)
        p.setFont(font(10)); p.setPen(QColor(255,255,255,140)); p.drawText(QRectF(r.x()+16, r.bottom()-30, r.width()-24, 18), AL.AlignLeft|AL.AlignVCenter, status)
        self._add_hit(r, cb)

    def _small(self, p, r, icon, title, cb):
        hov = self._hover(r); AL = Qt.AlignmentFlag
        p.setBrush(QColor(255,255,255, 20 if hov else 11)); p.setPen(QPen(QColor(255,255,255,14), 1)); p.drawRoundedRect(r, 18, 18)
        draw_icon(p, icon, QRectF(r.center().x()-10, r.y()+14, 20, 20))
        p.setFont(font(11, QFont.Weight.DemiBold)); p.setPen(QColor(255,255,255,220)); p.drawText(QRectF(r.x(), r.y()+46, r.width(), 22), AL.AlignCenter, title)
        self._add_hit(r, cb)

    def _icon_btn(self, p, r, text, cb, big=False):
        hov = self._hover(r); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255,255,255, 255 if big else (40 if hov else 0))); p.drawEllipse(r)
        nm = {"⏮": "prev", "⏭": "next", "⏸": "pause", "▶": "play"}.get(text)
        if nm: draw_icon(p, nm, r.adjusted(r.width()*0.3, r.height()*0.3, -r.width()*0.3, -r.height()*0.3), QColor(8,8,10) if big else QColor(255,255,255,235))
        else:
            p.setFont(font(22 if big else 16)); p.setPen(QColor(8,8,10) if big else QColor(255,255,255,235)); p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        self._add_hit(r, cb)

    def _hover(self, r): return self._mouse is not None and r.contains(self._mouse)
    def _add_hit(self, r, cb): self._hits.append((r, cb))
    def _pos(self, ev): return ev.position() - QPointF(self._org_x() + self._ox, self._org_y())
    def _in_island(self, pos): return QRectF(-self._ox, 0, self._iw, self._ih).contains(pos)

    def _on_single_click(self):
        if self._moving: return
        if not self.expanded: self.toggle_expand()

    def _shelf_start_drag(self, i):
        try:
            path = self._shelf.items[i]["path"]
            if not os.path.exists(path): return
            md = QMimeData(); md.setUrls([QUrl.fromLocalFile(path)])
            dr = QDrag(self); dr.setMimeData(md); dr.setPixmap(self._ds_icon(path, 48, os.path.basename(path)))
            self._dragging_out = True
            try: dr.exec(Qt.DropAction.CopyAction | Qt.DropAction.LinkAction)
            finally: self._dragging_out = False
        except Exception as e: log_error(f"shelf drag: {e}")

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls() and not self._dragging_out:
            ev.acceptProposedAction(); self._drag_over = True; self._set_show_target(1.0)
            if self._wb("shelf_auto", True):
                if not self.expanded: self._switch_page("shelf"); self.toggle_expand()
                elif self.current_page != "shelf": self._switch_page("shelf")
            self._wake(); self.update()
        else: ev.ignore()

    def dragMoveEvent(self, ev):
        if ev.mimeData().hasUrls() and not self._dragging_out: ev.acceptProposedAction()
        else: ev.ignore()

    def dragLeaveEvent(self, ev): self._drag_over = False; self.update()

    def dropEvent(self, ev):
        self._drag_over = False
        try:
            if self._dragging_out or not ev.mimeData().hasUrls(): ev.ignore(); return
            paths = [u.toLocalFile() for u in ev.mimeData().urls() if u.isLocalFile()]
            added, dup, full = self._shelf.add(paths)
            if added: msg, ok = (f"✓ Положено на полку: {added}", True)
            elif full: msg, ok = (f"⚠ Полка заполнена ({SHELF_MAX})", False)
            elif dup: msg, ok = ("Уже лежит на полке", False)
            else: msg, ok = ("⚠ Не удалось добавить", False)
            if added and full: msg += f" · полка заполнена ({SHELF_MAX})"
            self._shelf_flash = (msg, time.monotonic() + 2.6, ok); ev.acceptProposedAction()
            if self.expanded and self.current_page != "shelf": self._switch_page("shelf")
        except Exception as e: log_error(f"drop: {e}")
        self.update()

    def _shelf_menu(self, i, gpos):
        if not (0 <= i < len(self._shelf.items)): return
        path = self._shelf.items[i]["path"]
        m = QMenu(self)
        m.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(0,205,255,80)}")
        m.addAction("📂 Открыть", lambda: self._launch(path))
        m.addAction("🔎 Показать в папке", lambda: subprocess.Popen(["explorer", "/select,", os.path.normpath(path)]))
        m.addAction("📋 Копировать путь", lambda: QApplication.clipboard().setText(path))
        m.addSeparator(); m.addAction("✖ Убрать с полки", lambda: (self._shelf.remove(i), self.update())); m.exec(gpos)

    def mouseMoveEvent(self, ev):
        self._mouse = self._pos(ev)
        if self.expanded: self.update()
        if self._mx_drag is not None and (ev.buttons() & Qt.MouseButton.LeftButton): self._mx_apply(); return
        if self._move_press is not None and (ev.buttons() & Qt.MouseButton.LeftButton) and not self.expanded:
            p0, c0 = self._move_press; d = ev.globalPosition() - p0
            if not self._moving and d.manhattanLength() > 8:
                self._moving = True; self._gliding = False
                if self._click_timer is not None: self._click_timer.stop()
            if self._moving:
                s = self._virt_geom(); hw, hh = self._iw / 2.0, self._ih / 2.0
                fx = max(s.x() + hw, min(s.x() + s.width() - hw, c0.x() + d.x())); fy = max(s.y() + hh, min(s.y() + s.height() - hh, c0.y() + d.y()))
                self._free = (fx, fy); self._place_window(); self.update(); return
        if self._shelf_press is not None and (ev.buttons() & Qt.MouseButton.LeftButton):
            si, p0 = self._shelf_press
            if (ev.position() - p0).manhattanLength() > 10: self._shelf_press = None; self._shelf_start_drag(si); return
        if self._vol_drag:
            vsx = 66; vsw = 300
            v = (self._mouse.x() - vsx) / vsw
            self._volume = max(0.0, min(1.0, v)); set_volume(self._volume)
        if self._seek_drag:
            rel = (self._mouse.x()-44)/282; rel = max(0.0, min(1.0, rel))
            self.media["position"] = rel * self.media["duration"]
        self.update()

    def leaveEvent(self, _): self._mouse = None; self.update()

    def wheelEvent(self, ev):
        if not (self.expanded and self.current_page == "home"): return
        try:
            steps = ev.angleDelta().y() / 120.0
            if steps == 0: return
            v = max(0.0, min(1.0, self._volume + steps * 0.04))
            self._volume = v; set_volume(v); self.update()
        except Exception as ex: log_error(f"wheel: {ex}")

    def mouseDoubleClickEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(ev); return
        if self._click_timer is not None and self._click_timer.isActive():
            self._click_timer.stop()
            if not self.expanded and self.media.get("active") and self.mod_music:
                self._media_control("toggle"); return
        super().mouseDoubleClickEvent(ev)

    def mousePressEvent(self, ev):
        pos = self._pos(ev); self._move_press = None
        if not self._in_island(pos): ev.ignore(); return
        if self._alarm and not self.expanded and ev.button() == Qt.MouseButton.LeftButton:
            ip = QPointF(pos.x() + self._ox, pos.y()); sn = self._alarm_rects.get("snooze")
            if sn is not None and sn.contains(ip): self._alarm_snooze()
            else: self._alarm_stop()
            return
        self.activateWindow(); self.setFocus()
        self._happy_until = time.monotonic() + 1.4
        self._bounce_start = time.monotonic()
        self._last_move = time.monotonic()
        self._grace_until = time.monotonic() + 0.4
        if ev.button() == Qt.MouseButton.RightButton:
            if self.current_page == "home":
                for r, idx in self._dock_right_regions:
                    if r.contains(pos):
                        menu = QMenu(self)
                        menu.setStyleSheet("QMenu{background:#1e2030;color:white;border:1px solid rgba(255,255,255,30);border-radius:8px;padding:6px}QMenu::item{padding:8px 24px;border-radius:6px}QMenu::item:selected{background:rgba(255,80,80,120)}")
                        menu.addAction(f"🗑 Удалить: {os.path.basename(self.dock[idx].get('path',''))[:30]}", lambda i=idx: self._remove_dock_item(i))
                        menu.addAction("🚀 Открыть", lambda pp=self.dock[idx].get('path',''): self._launch(pp))
                        menu.exec(ev.globalPosition().toPoint())
                        return
            if self.current_page == "shelf" and self.expanded:
                for r, si in self._shelf_rects:
                    if r.contains(pos): self._shelf_menu(si, ev.globalPosition().toPoint()); return
            if self.current_page == "system" and self.system_view == "menu" and self._sys_stats_rect.contains(pos):
                self._sys_stats_menu(ev.globalPosition().toPoint()); return
            if not self.expanded:
                self._compact_menu(ev.globalPosition().toPoint()); return
            self.menu.exec(ev.globalPosition().toPoint()); return
        if ev.button() != Qt.MouseButton.LeftButton: return
        if not self.expanded:
            if self._notify: self._clear_notification(); return
            if self._show < 0.85 or self._show_target < 1.0:      # клик по миниатюре — капля вырастает в остров
                self._reveal_started = 0.0; self._set_show_target(1.0); return
            if self._click_timer is None:
                self._click_timer = QTimer(self)
                self._click_timer.setSingleShot(True)
                self._click_timer.timeout.connect(self._on_single_click)
            self._move_press = (ev.globalPosition(), self._island_screen_rect().center())
            self._click_timer.start(250)
            return
        if self.current_page == "home" and not self._ds_panel_open():
            if QRectF(44,248,282,18).contains(pos):
                self._seek_drag = True; rel = (pos.x()-44)/282
                self.media["position"] = rel * self.media["duration"]; return
            vsx = 66; vsy = 364; vsw = 300
            if QRectF(vsx, vsy - 8, vsw, 20).contains(pos):
                self._vol_drag = True
                v = (pos.x() - vsx) / vsw
                self._volume = max(0.0, min(1.0, v)); set_volume(self._volume); return
        if self.current_page == "shelf":
            for r, si in self._shelf_x:
                if r.contains(pos): self._shelf.remove(si); self.update(); return
            for r, si in self._shelf_rects:
                if r.contains(pos) and not any(hr.contains(pos) and hr.width() < 150 for hr, _cb in self._hits[-2:]): self._shelf_press = (si, ev.position()); return
        if self.current_page == "notes":
            if QRectF(20, 90, self.EW-40, 52).contains(pos) and not self._new_note_active:
                self._activate_note_input(); return
        for r, cb in reversed(self._hits):
            if r.contains(pos): cb(); return

    def mouseReleaseEvent(self, ev):
        self._mx_drag = None
        if self._moving: self._finish_move(); self._move_press = None; return
        self._move_press = None
        if self._shelf_press is not None:
            si, _p0 = self._shelf_press; self._shelf_press = None
            try: self._launch(self._shelf.items[si]["path"])
            except Exception as e: log_error(f"shelf open: {e}")
        if self._seek_drag:
            self._seek_drag = False
            sec = float(self.media["position"]); self._seek_lock_until = time.monotonic()+1.5
            self._media_bridge.control("seek", sec)
        if self._vol_drag: self._vol_drag = False
        super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape and getattr(self, "_note_editor", None) and self._note_editor.isVisible():
            self._note_editor.close_editor(); return
        if self._timer_active_field:
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._apply_custom_timer(); return
            elif ev.key() == Qt.Key.Key_Escape:
                self._timer_active_field = None
                self._timer_h_input = ""; self._timer_m_input = ""; self._timer_s_input = ""
                self.update(); return
            elif ev.key() == Qt.Key.Key_Tab:
                order = ['h', 'm', 's']
                try:
                    idx = order.index(self._timer_active_field)
                    self._timer_active_field = order[(idx + 1) % 3]
                    self._timer_field_fresh = True
                except: pass
                self.update(); return
            elif ev.key() == Qt.Key.Key_Backspace:
                f = self._timer_active_field
                cur = getattr(self, f"_timer_{f}_input", "")
                setattr(self, f"_timer_{f}_input", cur[:-1])
                self._timer_field_fresh = False
                self.update(); return
            else:
                t = ev.text()
                if t.isdigit():
                    f = self._timer_active_field
                    if getattr(self, '_timer_field_fresh', True):
                        setattr(self, f"_timer_{f}_input", t)
                        self._timer_field_fresh = False
                    else:
                        cur = getattr(self, f"_timer_{f}_input", "")
                        setattr(self, f"_timer_{f}_input", (cur + t)[-2:])
                    self.update(); return
        if self._new_note_active:
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._add_note(self._new_note_text); return
            elif ev.key() == Qt.Key.Key_Escape:
                self._cancel_note(); return
            elif ev.key() == Qt.Key.Key_Backspace:
                self._new_note_text = self._new_note_text[:-1]; self.update(); return
            else:
                t = ev.text()
                if t and t.isprintable():
                    self._new_note_text = (self._new_note_text + t)[:240]; self.update(); return
        if self._reminder_active:
            k = ev.key()
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self._save_reminder(); return
            elif k == Qt.Key.Key_Escape: self._reminder_active = False; self._reminder_text = ""; self._reminder_time = ""; self.update(); return
            elif k == Qt.Key.Key_Tab: self._reminder_field = "time" if self._reminder_field == "text" else "text"; self.update(); return
            elif k == Qt.Key.Key_Backspace:
                if self._reminder_field == "time": self._reminder_time = self._reminder_time[:-1]
                else: self._reminder_text = self._reminder_text[:-1]
                self.update(); return
            else:
                t = ev.text()
                if t and t.isprintable():
                    if self._reminder_field == "time":
                        if t.isdigit() or t == ":":
                            v = self._reminder_time + t
                            if t != ":" and len(v) == 2 and ":" not in v: v += ":"
                            self._reminder_time = v[:5]
                    else: self._reminder_text = (self._reminder_text + t)[:100]
                    self.update(); return
        if self.expanded and self.current_page == "home" and self._ds_key(ev): return
        if self.current_page == "system" and self.system_view == "wifi" and self._wifi_pw_for is not None and self._wifi_key(ev): return
        if self.expanded and ev.key() == Qt.Key.Key_Escape:
            self.toggle_expand(); return
        super().keyPressEvent(ev)

    def closeEvent(self, ev):
        if getattr(self, "_note_editor", None): self._note_editor.close_editor()
        if self._log_window: self._log_window.close()
        if self._settings_window: self._settings_window.close()
        for w in list(self._ai_windows):
            try: w.close()
            except Exception: pass
        self._ai_windows.clear()
        super().closeEvent(ev)


if __name__ == "__main__":
    try:
        k = ctypes.windll.kernel32
        _m = k.CreateMutexW(None, False, "DynamicIslandSingleton")
        if k.GetLastError() == 183: sys.exit(0)
        from PyQt6.QtCore import QCoreApplication, Qt
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        app = QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
        island = DynamicIsland()
        sys.exit(app.exec())
    except Exception:
        log_error("CRASH:\n" + traceback.format_exc()); raise
