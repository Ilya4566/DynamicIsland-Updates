# -*- coding: utf-8 -*-
"""Логика, зависимости, фоновые потоки, утилиты."""
import os, sys, math, time, json, asyncio, threading, ctypes, ctypes.wintypes as wt
import datetime, subprocess, winreg, traceback, sqlite3, shutil, tempfile, re
import xml.etree.ElementTree as ET
import queue, ssl
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QColor, QFont, QFontMetrics, QGuiApplication

# ═══════════════════════════════════════════════════════════════════
# ФИКС ДЛЯ PYTHON 3.15: Добавляем пути к DLL Qt для WebEngine
# ═══════════════════════════════════════════════════════════════════
try:
    import PyQt6
    _qt_bin = Path(PyQt6.__file__).parent / "Qt6" / "bin"
    if _qt_bin.exists():
        os.add_dll_directory(str(_qt_bin))
except Exception:
    pass
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "island_error.log")

def log_error(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%H:%M:%S}] {msg}\n")
    except: pass

log_error("===== START v43 (Core) =====")

HAS_PYCAW = False
AudioUtilities = None
try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception as _e: log_error(f"pycaw: {_e}")

HAS_WINRT = False
winrt_media_control = None
DataReader = None
InputStreamOptions = None
try:
    from winrt.windows.media import control as winrt_media_control
    from winrt.windows.storage.streams import DataReader, InputStreamOptions
    HAS_WINRT = True
except Exception as _e: log_error(f"winrt: {_e}")

user32 = ctypes.windll.user32
try: ctypes.windll.winmm.timeBeginPeriod(1)
except Exception: pass
try: dwmapi = ctypes.windll.dwmapi
except: dwmapi = None
HWND_TOPMOST, SWP_FLAGS = -1, 0x0001 | 0x0002 | 0x0010
GW_EXSTYLE, WS_EX_TOOLWINDOW, DWMWA_CLOAKED = -20, 0x80, 14
SHELL_CLASSES = {"Progman","WorkerW","Shell_TrayWnd","Shell_SecondaryTrayWnd",
    "Windows.UI.Core.CoreWindow","XamlExplorerHostIslandWindow",
    "Windows.Internal.Shell.TabProxyWindow","MultitaskingViewFrame",
    "ForegroundStaging","TaskListThumbnailWnd"}
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DynamicIsland"

M = 22
CW, CH = 260, 40
EW, EH = 800, 540
TOP = 0
ACCENT = QColor(0, 205, 255)
VIOLET = QColor(150, 110, 255)
MUSIC_COLOR = QColor(255, 100, 150)
TOOL_BG = QColor(38, 40, 50)
WEATHER_COLOR = QColor(255, 200, 80)

_FONT_CACHE = {}
def font(px, weight=QFont.Weight.Normal, family="Segoe UI", spacing=0.0):
    """Шрифты кэшируются (быстрее отрисовка). Размер приводится к int: PyQt6 не принимает float в setPixelSize —
    из-за этого на главной «пропадало» всё, кроме плеера (ошибка в блоке текста песни обрывала остальную отрисовку)."""
    key = (max(1, int(round(px))), weight, family, spacing); f = _FONT_CACHE.get(key)
    if f is None:
        f = QFont(family); f.setPixelSize(key[0]); f.setWeight(weight)
        if spacing: f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        _FONT_CACHE[key] = f
    return f

def rgba(c, a): return QColor(c.red(), c.green(), c.blue(), max(0, min(255, int(a))))

def fmt_mmss(sec):
    sec = max(0, int(math.ceil(sec))); return f"{sec//60:02d}:{sec%60:02d}"

_app_session = None
def find_active_app_session():
    global _app_session
    if not HAS_PYCAW: return None
    try:
        sessions = AudioUtilities.GetAllSessions()
        best, best_peak = None, 0.01
        for s in sessions:
            try:
                peak = s.AudioMeterInformation.GetPeakValue()
                if peak > best_peak: best_peak = peak; best = s
            except: pass
        if best: _app_session = best
        return _app_session
    except: return None

def get_volume():
    if not HAS_PYCAW: return None
    sess = find_active_app_session()
    if sess:
        try: return float(sess.SimpleAudioVolume.GetMasterVolume())
        except: pass
    try: return float(AudioUtilities.GetSpeakers().EndpointVolume.GetMasterVolumeLevelScalar())
    except: return None

def set_volume(val):
    if not HAS_PYCAW: return
    v = max(0.0, min(1.0, float(val)))
    sess = find_active_app_session()
    if sess:
        try: sess.SimpleAudioVolume.SetMasterVolume(v, None); return
        except: pass
    try: AudioUtilities.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(v, None)
    except: pass

def get_app_name():
    if _app_session:
        try:
            if _app_session.Process: return _app_session.Process.name()
        except: pass
    return "Система"

def no_app_window_open(hwnd_self):
    found = [False]
    def cb(hwnd, _):
        if found[0] or hwnd == hwnd_self: return True
        try:
            if not user32.IsWindowVisible(hwnd): return True
            if user32.IsIconic(hwnd): return True
            buf = ctypes.create_unicode_buffer(256); user32.GetClassNameW(hwnd, buf, 256)
            if buf.value in SHELL_CLASSES: return True
            try:
                if user32.GetWindowLongW(hwnd, GW_EXSTYLE) & WS_EX_TOOLWINDOW: return True
            except: pass
            if dwmapi:
                try:
                    c = ctypes.c_int(0)
                    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(c), 4)
                    if c.value: return True
                except: pass
            r = wt.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
            if r.right-r.left < 40 or r.bottom-r.top < 40: return True
        except: return True
        found[0] = True; return False
    user32.EnumWindows(ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(cb), 0)
    return not found[0]

def is_window_overlapping(hwnd_self, rect=None):
    """Проверяет, перекрывает ли какое-либо окно наш островок.
    rect = (left, top, right, bottom) в координатах экрана; без него берётся рамка самого окна."""
    if rect:
        left, top, right, bottom = rect
    else:
        own_rect = wt.RECT()
        user32.GetWindowRect(hwnd_self, ctypes.byref(own_rect))
        margin = 25
        left = own_rect.left + margin
        top = own_rect.top + margin
        right = own_rect.right - margin
        bottom = own_rect.bottom - margin

    overlapped = [False]
    def cb(hwnd, _):
        if overlapped[0] or hwnd == hwnd_self: return True
        try:
            if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd): return True
            
            buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buf, 256)
            if buf.value in SHELL_CLASSES: return True
            
            if user32.GetWindowLongW(hwnd, GW_EXSTYLE) & WS_EX_TOOLWINDOW: return True
            
            if dwmapi:
                c = ctypes.c_int(0)
                dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(c), 4)
                if c.value: return True
            
            r = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            
            if (r.left < right and r.right > left and r.top < bottom and r.bottom > top):
                overlapped[0] = True
                return False
        except: return True
        return True

    user32.EnumWindows(ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(cb), 0)
    return overlapped[0]

def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME); return True
    except: return False

def set_autostart(on):
    cmd = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if on: winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try: winreg.DeleteValue(k, APP_NAME)
                except: pass
    except: pass

class MediaBridge(QObject):
    changed = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self._loop = None; self._manager = None; self._img_cache = {}
        if HAS_WINRT: threading.Thread(target=self._run, daemon=True).start()
    def _run(self):
        try:
            self._loop = asyncio.new_event_loop(); asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._listen())
        except Exception as e: log_error(f"MediaBridge: {e}")
    async def _listen(self):
        try: self._manager = await winrt_media_control.GlobalSystemMediaTransportControlsSessionManager.request_async()
        except Exception as e: log_error(f"SMTC: {e}"); return
        while True:
            try:
                s = self._manager.get_current_session()
                if s is None: self.changed.emit({"active": False})
                else: self.changed.emit(await self._read(s))
            except Exception as e: log_error(f"SMTC: {e}"); self.changed.emit({"active": False})
            await asyncio.sleep(0.8)
    async def _load_thumb(self, ref):
        try:
            stream = await ref.open_read_async()
            if not stream: return None
            size = int(stream.size) if int(stream.size) > 0 else 1024*1024
            data = b""
            try:
                reader = DataReader(stream); await reader.load_async(size)
                n = int(reader.unconsumed_buffer_length)
                if n > 0: ba = bytearray(n); reader.read_bytes(ba); data = bytes(ba)
            except: pass
            if not data:
                try:
                    buf = await stream.read_async(size, InputStreamOptions.NONE)
                    n = int(buf.length) if int(buf.length) > 0 else 0
                    if n > 0: reader = DataReader.from_buffer(buf); ba = bytearray(n); reader.read_bytes(ba); data = bytes(ba)
                except: pass
            if not data: return None
            img = QImage.fromData(data)
            return img if not img.isNull() else None
        except: return None
    async def _read(self, session):
        info = await session.try_get_media_properties_async()
        tl = session.get_timeline_properties(); pb = session.get_playback_info()
        def sec(td):
            try: return td.total_seconds()
            except: return 0.0
        duration = sec(tl.end_time) or 1.0; position = sec(tl.position)
        playing = int(pb.playback_status) == 4
        if playing:     # position — это позиция на момент last_updated_time; добавляем прошедшее с тех пор время
            try:
                lu = tl.last_updated_time
                now_ = datetime.datetime.now(lu.tzinfo) if getattr(lu, "tzinfo", None) else datetime.datetime.utcnow()
                lag = (now_ - lu).total_seconds()
                if 0.0 <= lag <= 4.0: position += lag
            except Exception: pass
        title = info.title or ""; artist = info.artist or ""
        img = None
        try:
            if info.thumbnail:
                key = f"{title}|{artist}"
                if key in self._img_cache: img = self._img_cache[key]
                else:
                    img = await self._load_thumb(info.thumbnail)
                    if img is not None:
                        self._img_cache[key] = img
                        if len(self._img_cache) > 20: self._img_cache.pop(next(iter(self._img_cache)))
        except: pass
        return {"active": True, "title": title, "artist": artist,
                "duration": max(duration, 1.0), "position": max(0.0, position),
                "playing": playing, "thumb_image": img}
    def control(self, action, value=None):
        if not HAS_WINRT or not self._loop: return
        asyncio.run_coroutine_threadsafe(self._do(action, value), self._loop)
    async def _do(self, action, value):
        try:
            mgr = await winrt_media_control.GlobalSystemMediaTransportControlsSessionManager.request_async()
            s = mgr.get_current_session()
            if not s: return
            if action == "toggle": await s.try_toggle_play_pause_async()
            elif action == "next": await s.try_skip_next_async()
            elif action == "prev": await s.try_skip_previous_async()
            elif action == "seek" and value is not None:
                await s.try_change_playback_position_async(int(float(value) * 10_000_000))
        except Exception as e: log_error(f"do_control: {e}")

def _http_json(url, timeout=8.0, tries=2):
    """JSON по HTTP: нормальный User-Agent, повторы; при ошибке сертификата (бывает на чужих ПК и в корпоративных сетях)
    повторяем без проверки — данные публичные (погода, геокодер)."""
    last = None
    for i in range(max(1, tries)):
        for mode in (0, 1):
            try:
                req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DynamicIsland/39", "Accept": "application/json"})
                kw = {"timeout": timeout}
                if mode == 1: kw["context"] = ssl._create_unverified_context()
                with urlopen(req, **kw) as r: return json.loads(r.read().decode("utf-8", "replace"))
            except Exception as e:
                last = e
                if mode == 0 and ("CERTIFICATE" in str(e).upper() or isinstance(e, ssl.SSLError) or "SSL" in str(e).upper()): continue
                break
        if i + 1 < tries: time.sleep(0.6 + i * 0.8)
    raise last if last else RuntimeError("http")

def search_places(query, count=6):
    """Поиск города: (название, страна, регион, широта, долгота). Сначала geocoding-api.open-meteo, запасной — OpenStreetMap."""
    q = quote(query.strip()); out = []
    try:
        d = _http_json(f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count={count}&language=ru", timeout=8, tries=2)
        for r in d.get("results") or []: out.append((r.get("name", ""), r.get("country", ""), r.get("admin1", ""), float(r["latitude"]), float(r["longitude"])))
    except Exception as e: log_error(f"geocode open-meteo: {e}")
    if not out:
        try:
            d = _http_json(f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit={count}&accept-language=ru", timeout=9, tries=2)
            for r in d:
                parts = [x.strip() for x in str(r.get("display_name", "")).split(",")]
                out.append((parts[0], parts[-1] if len(parts) > 1 else "", ", ".join(parts[1:-1][:2]) if len(parts) > 2 else "", float(r["lat"]), float(r["lon"])))
        except Exception as e: log_error(f"geocode nominatim: {e}")
    return out

WTTR_MAP = {113: 0, 116: 2, 119: 3, 122: 3, 143: 45, 248: 45, 260: 48, 176: 80, 179: 71, 182: 61, 185: 56, 200: 95, 227: 71, 230: 75, 263: 51, 266: 53,
            281: 56, 284: 57, 293: 61, 296: 61, 299: 63, 302: 63, 305: 65, 308: 65, 311: 66, 314: 67, 317: 67, 320: 71, 323: 71, 326: 71, 329: 73,
            332: 73, 335: 75, 338: 75, 350: 77, 353: 80, 356: 81, 359: 82, 362: 85, 365: 85, 368: 85, 371: 86, 374: 77, 377: 77, 386: 95, 389: 99, 392: 95, 395: 86}

def _hhmm(s):
    try:
        t = datetime.datetime.strptime(s.strip(), "%I:%M %p"); return t.strftime("%H:%M")
    except Exception: return ""

def _fetch_wttr(lat, lon, city):
    """Резервный источник погоды (wttr.in) — если основной недоступен."""
    d = _http_json(f"https://wttr.in/{lat:.3f},{lon:.3f}?format=j1&lang=ru", timeout=10, tries=2)
    cur = d["current_condition"][0]; days = d.get("weather") or []
    code = lambda x: WTTR_MAP.get(int(x), 3)
    d0 = days[0] if days else {}; astro = (d0.get("astronomy") or [{}])[0]
    sr, ss = _hhmm(astro.get("sunrise", "")), _hhmm(astro.get("sunset", "")); nowh = datetime.datetime.now().strftime("%H:%M")
    rains = [int(h.get("chanceofrain", 0)) for h in d0.get("hourly", [])] or [0]
    out = {"ok": True, "temp": float(cur["temp_C"]), "code": code(cur.get("weatherCode", 119)), "wind": float(cur.get("windspeedKmph", 0)), "hum": float(cur.get("humidity", 0)),
           "city": city, "feels": float(cur.get("FeelsLikeC", cur["temp_C"])), "is_day": 1 if (sr and ss and sr <= nowh < ss) else (0 if sr and ss else 1),
           "tmax": float(d0.get("maxtempC", cur["temp_C"])), "tmin": float(d0.get("mintempC", cur["temp_C"])), "rain": max(rains),
           "pres": float(cur.get("pressure", 0)) * 0.750062, "sunrise": sr, "sunset": ss, "uv": float(d0.get("uvIndex", 0) or 0), "psum": float(d0.get("totalSnow_cm", 0) or 0),
           "ts": time.time(), "updated": datetime.datetime.now().strftime("%H:%M"), "hours": [], "daily": [], "src": "wttr.in"}
    now = datetime.datetime.now(); hrs = []
    for day in days[:2]:
        for h in day.get("hourly", []):
            hh = int(h.get("time", 0)) // 100; dt = datetime.datetime.strptime(day["date"], "%Y-%m-%d").replace(hour=hh)
            if dt >= now.replace(minute=0, second=0, microsecond=0): hrs.append((hh, float(h["tempC"]), code(h.get("weatherCode", 119))))
    out["hours"] = hrs[:8]
    for i, day in enumerate(days[:3]):
        wd = datetime.date.fromisoformat(day["date"]).weekday(); hl = day.get("hourly", [])
        out["daily"].append(("Сегодня" if i == 0 else _WD[wd], code(hl[4].get("weatherCode", 119)) if len(hl) > 4 else 3, float(day.get("maxtempC", 0)), float(day.get("mintempC", 0)), max([int(h.get("chanceofrain", 0)) for h in hl] or [0])))
    return out

def _ip_locate():
    """Определение места по IP: несколько сервисов по очереди (раньше при отказе тихо подставлялась Москва)."""
    def a(d): return (d["latitude"], d["longitude"], d.get("city")) if d.get("success", True) and d.get("latitude") is not None else None
    def b(d): return (float(d["latitude"]), float(d["longitude"]), d.get("city")) if d.get("latitude") else None
    def c(d):
        la, lo = str(d.get("loc", "")).split(",")[:2]; return (float(la), float(lo), d.get("city"))
    def e(d): return (d["lat"], d["lon"], d.get("city")) if d.get("status", "success") == "success" and d.get("lat") is not None else None
    for url, fn in (("https://ipwho.is/", a), ("https://get.geojs.io/v1/ip/geo.json", b),
                    ("https://ipinfo.io/json", c), ("https://ipapi.co/json/", b), ("http://ip-api.com/json/?lang=ru", e)):
        try:
            r = fn(_http_json(url, timeout=6, tries=1))
            if r and r[0] is not None: return float(r[0]), float(r[1]), (r[2] or "")
        except Exception as ex: log_error(f"ip locate {url}: {ex}")
    return None

_WD = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

class WeatherWorker(QObject):
    changed = pyqtSignal(dict)
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.last_error = ""; self.diag = ""; self.diag_busy = False
        self._wake = threading.Event()
        try:
            cache = self.settings.value("weather_cache", "")
            self.data = json.loads(cache) if cache else {"ok": False}
            if not isinstance(self.data, dict): self.data = {"ok": False}
        except Exception: self.data = {"ok": False}
        threading.Thread(target=self._run, daemon=True).start()

    def refresh(self):
        """Обновить сейчас (вызывается из GUI, поток не плодится)."""
        self._wake.set()

    def _emit_fail(self, msg):
        self.last_error = msg
        if self.data.get("ok"):
            d = dict(self.data); d["stale"] = True; d["error"] = msg; self.changed.emit(d)
        else:
            self.changed.emit({"ok": False, "error": msg})

    def _run(self):
        if self.data.get("ok"):
            d = dict(self.data); d["stale"] = True; self.changed.emit(d)   # сразу показываем кэш
        fails = 0
        while True:
            try:
                self._fetch(); ok = True; self.last_error = ""
            except Exception as e:
                ok = False; msg = str(e) or e.__class__.__name__
                log_error(f"weather: {msg}"); self._emit_fail(msg)
            fails = 0 if ok else fails + 1
            try: interval = int(self.settings.value("weather_interval", 1))
            except Exception: interval = 1
            secs = [300, 600, 1800, 3600][max(0, min(3, interval))]
            if not ok: secs = min(60, 8 * (2 ** min(fails - 1, 3)))
            self._wake.wait(secs); self._wake.clear()

    def _place(self):
        S = self.settings
        custom = str(S.value("weather_city", "") or "").strip()
        src = str(S.value("weather_src", "") or "")
        try: lat = float(S.value("weather_lat", 0) or 0); lon = float(S.value("weather_lon", 0) or 0)
        except Exception: lat = lon = 0.0
        city = str(S.value("weather_city_res", "") or "")
        if custom:
            if custom != src or not (lat or lon):
                res = search_places(custom, 1)
                if not res: raise RuntimeError(f"Город «{custom}» не найден (или нет доступа к поиску городов)")
                lat, lon, city = res[0][3], res[0][4], (res[0][0] or custom)
                S.setValue("weather_src", custom)
        else:
            ts = 0.0
            try: ts = float(S.value("weather_ip_ts", 0) or 0)
            except Exception: pass
            if src != "" or not (lat or lon) or time.time() - ts > 6 * 3600:
                loc = _ip_locate()
                if loc:
                    lat, lon, city = loc[0], loc[1], (loc[2] or "Моё место")
                    S.setValue("weather_ip_ts", time.time()); S.setValue("weather_src", "")
                elif src != "" or not (lat or lon):
                    raise RuntimeError("Не удалось определить местоположение — впиши город в настройках погоды")
        S.setValue("weather_lat", lat); S.setValue("weather_lon", lon); S.setValue("weather_city_res", city)
        return lat, lon, city

    def _fetch_om(self, lat, lon, city):
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,surface_pressure,is_day"
               "&hourly=temperature_2m,weather_code"
               "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max,precipitation_sum"
               "&forecast_days=6&timezone=auto")
        data = _http_json(url, timeout=10, tries=3)
        cur = data.get("current") or {}
        if cur.get("temperature_2m") is None: raise RuntimeError("Сервис погоды не вернул температуру")
        d = data.get("daily") or {}
        def d0(k, default=None):
            try: return (d.get(k) or [default])[0]
            except Exception: return default
        out = {"ok": True, "temp": cur.get("temperature_2m"), "code": cur.get("weather_code", 0) or 0,
               "wind": cur.get("wind_speed_10m", 0) or 0, "hum": cur.get("relative_humidity_2m", 0) or 0, "city": city,
               "feels": cur.get("apparent_temperature"), "is_day": cur.get("is_day", 1),
               "tmax": d0("temperature_2m_max"), "tmin": d0("temperature_2m_min"), "rain": d0("precipitation_probability_max"),
               "pres": (cur.get("surface_pressure") or 0) * 0.750062,
               "sunrise": str(d0("sunrise", "") or "")[11:16], "sunset": str(d0("sunset", "") or "")[11:16],
               "uv": d0("uv_index_max", 0) or 0, "psum": d0("precipitation_sum", 0) or 0,
               "ts": time.time(), "updated": datetime.datetime.now().strftime("%H:%M"), "hours": [], "daily": []}
        try:
            hr = data.get("hourly") or {}; ts = hr.get("time", []); tt = hr.get("temperature_2m", []); cc = hr.get("weather_code", [])
            now_h = (cur.get("time") or "")[:13] + ":00"
            st = next((i for i, x in enumerate(ts) if x >= now_h), 0)
            out["hours"] = [(int(ts[k][11:13]), tt[k], cc[k] or 0) for k in range(st, min(st + 12, len(ts), len(tt), len(cc)))]
        except Exception as ex: log_error(f"weather hours: {ex}")
        try:
            days = d.get("time") or []
            for i, ds in enumerate(days[:6]):
                wd = datetime.date.fromisoformat(ds).weekday()
                out["daily"].append(("Сегодня" if i == 0 else _WD[wd], (d.get("weather_code") or [0] * 6)[i] or 0,
                                     (d.get("temperature_2m_max") or [None] * 6)[i], (d.get("temperature_2m_min") or [None] * 6)[i],
                                     (d.get("precipitation_probability_max") or [None] * 6)[i]))
        except Exception as ex: log_error(f"weather daily: {ex}")
        return out

    def _fetch(self):
        lat, lon, city = self._place()
        try: out = self._fetch_om(lat, lon, city)
        except Exception as e1:
            log_error(f"open-meteo: {e1} — пробую wttr.in")
            try: out = _fetch_wttr(lat, lon, city)
            except Exception as e2: raise RuntimeError(f"нет связи с сервисами погоды ({str(e1)[:70]}); резерв: {str(e2)[:70]}")
        self.data = out
        try: self.settings.setValue("weather_cache", json.dumps(out, ensure_ascii=False))
        except Exception: pass
        log_error(f"weather OK: {city} {out['temp']}° ({out.get('src', 'open-meteo')})")
        self.changed.emit(out)

    def use_place(self, name, lat, lon):
        S = self.settings; S.setValue("weather_city", name); S.setValue("weather_src", name)
        S.setValue("weather_lat", float(lat)); S.setValue("weather_lon", float(lon)); S.setValue("weather_city_res", name); self.refresh()

    def diagnose(self):
        def run():
            lines = []
            def t(label, fn):
                t0 = time.time()
                try: r = fn(); lines.append(f"✓ {label}: {r}  ({time.time() - t0:.1f} с)")
                except Exception as e: lines.append(f"✗ {label}: {str(e)[:100]}")
            t("Погода (open-meteo)", lambda: _http_json("https://api.open-meteo.com/v1/forecast?latitude=52.5&longitude=13.4&current=temperature_2m", 8, 1)["current"]["temperature_2m"])
            t("Резерв (wttr.in)", lambda: _http_json("https://wttr.in/Berlin?format=j1", 9, 1)["current_condition"][0]["temp_C"])
            t("Поиск городов", lambda: f"найдено {len(search_places('Berlin', 1))}")
            t("Место по IP", lambda: (lambda r: f"{r[2] or '?'} ({r[0]:.2f}, {r[1]:.2f})" if r else (_ for _ in ()).throw(RuntimeError("ни один сервис не ответил")))(_ip_locate()))
            self.diag = "\n".join(lines); self.diag_busy = False
        self.diag_busy = True; self.diag = "Проверяю…"; threading.Thread(target=run, daemon=True).start()


class AudioLevels:
    """Уровень и спектр звука. Уровень — peak-метр pycaw (реальный). Спектр — настоящий FFT через WASAPI loopback,
    если установлены numpy и soundcard; иначе остаётся peak-уровень, а форму спектра рисует остров."""
    NB = 32
    def __init__(self, use_loopback=True):
        self.level = 0.0
        self.bands = [0.0] * self.NB
        self.real = False
        self.audible_ts = 0.0
        self._real_ts = 0.0
        self._stop = False
        threading.Thread(target=self._peak_loop, daemon=True).start()
        if use_loopback: threading.Thread(target=self._fft_loop, daemon=True).start()

    def stop(self): self._stop = True
    def is_real(self): return self.real and (time.monotonic() - self._real_ts) < 0.4

    def _peak_loop(self):
        if not HAS_PYCAW: return
        try:
            import comtypes; comtypes.CoInitialize()
        except Exception: pass
        sessions = []; last = 0.0; lvl = 0.0; errs = 0
        while not self._stop:
            try:
                now = time.monotonic()
                if now - last > 1.5:
                    sessions = list(AudioUtilities.GetAllSessions()); last = now
                pk = 0.0
                for s in sessions:
                    try: pk = max(pk, float(s.AudioMeterInformation.GetPeakValue()))
                    except Exception: pass
                lvl = max(pk, lvl * 0.88)
                self.level = lvl
                if pk > 0.003: self.audible_ts = now
                errs = 0
            except Exception as e:
                errs += 1
                if errs < 3: log_error(f"audio peak: {e}")
                time.sleep(1.0)
            time.sleep(0.02)

    @staticmethod
    def band_indices(freqs, nb, lo=45.0, hi=16000.0):
        import numpy as np
        edges = np.geomspace(lo, hi, nb + 1); out = []
        for i in range(nb):
            sel = np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0]
            if len(sel) == 0:
                c = (edges[i] * edges[i + 1]) ** 0.5; sel = np.array([int(np.argmin(np.abs(freqs - c)))])
            out.append(sel)
        return out

    @staticmethod
    def spectrum(mono, win, idx, n):
        import numpy as np
        mag = np.abs(np.fft.rfft(mono * win)) / (n / 4.0)
        res = []; nb = len(idx)
        for i, sel in enumerate(idx):
            v = float(mag[sel].max())
            db = 20.0 * math.log10(v + 1e-6)
            x = (db + 64.0) / 50.0 * (0.88 + 0.30 * i / max(1, nb - 1))   # лёгкий наклон: верха обычно тише
            res.append(max(0.0, min(1.0, x)))
        return res

    def _fft_loop(self):
        try:
            import numpy as np
            import soundcard as sc
        except Exception as e:
            log_error(f"audio fft недоступен ({e}) — спектр строится по уровню"); return
        try:
            try:
                import comtypes; comtypes.CoInitialize()
            except Exception: pass
            sr, n = 44100, 1024
            spk = sc.default_speaker()
            mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
            win = np.hanning(n).astype(np.float32)
            idx = self.band_indices(np.fft.rfftfreq(n, 1.0 / sr), self.NB)
            with mic.recorder(samplerate=sr, channels=2, blocksize=n) as rec:
                while not self._stop:
                    data = rec.record(numframes=n)
                    mono = np.asarray(data, dtype=np.float32).mean(axis=1)
                    if len(mono) < n: continue
                    self.bands = self.spectrum(mono[:n], win, idx, n)
                    self.real = True; self._real_ts = time.monotonic()
        except Exception as e:
            self.real = False
            log_error(f"audio fft: {e}")


# ═══════════ Уведомления Windows → остров ═══════════
# (подстрока идентификатора приложения, имя, значок, цвет)
MESSENGERS = [
    ("telegram", "Telegram", "✈", (42, 171, 238)), ("whatsapp", "WhatsApp", "💬", (37, 211, 102)),
    ("discord", "Discord", "🎮", (88, 101, 242)), ("viber", "Viber", "📞", (115, 96, 242)),
    ("slack", "Slack", "#", (224, 30, 90)), ("teams", "Teams", "👥", (98, 100, 167)),
    ("skype", "Skype", "S", (0, 175, 240)), ("outlook", "Outlook", "✉", (0, 120, 212)),
    ("gmail", "Gmail", "✉", (234, 67, 53)), ("microsoft.windowscommunicationsapps", "Почта", "✉", (0, 120, 212)),
    ("vk", "VK", "В", (0, 119, 255)), ("max", "MAX", "M", (120, 80, 255)), ("signal", "Signal", "🔒", (58, 118, 240)),
    ("zoom", "Zoom", "📹", (45, 140, 255)), ("element", "Element", "🔷", (13, 189, 139)),
]

WEB_SITES = [("web.telegram.org", "Telegram"), ("telegram.org", "Telegram"), ("web.whatsapp.com", "WhatsApp"), ("whatsapp.com", "WhatsApp"),
             ("vk.com", "VK"), ("vk.ru", "VK"), ("discord.com", "Discord"), ("slack.com", "Slack"), ("teams.microsoft.com", "Teams"),
             ("teams.live.com", "Teams"), ("mail.google.com", "Gmail"), ("outlook.live.com", "Outlook"), ("outlook.office.com", "Outlook"),
             ("outlook.office365.com", "Outlook"), ("messenger.com", "Messenger"), ("facebook.com", "Facebook"), ("instagram.com", "Instagram"),
             ("web.max.ru", "MAX"), ("max.ru", "MAX"), ("signal.org", "Signal"), ("zoom.us", "Zoom"), ("ok.ru", "OK"), ("viber.com", "Viber")]
WEB_EXTRA = {"Messenger": ("💬", (0, 132, 255)), "Facebook": ("f", (24, 119, 242)), "Instagram": ("📷", (225, 48, 108)), "OK": ("О", (238, 130, 8))}

class SysNotifyListener(QObject):
    """Читает базу уведомлений Windows (wpndatabase.db) и сообщает островку о новых тостах.
    Работает без разрешений и без пакетной идентичности — в отличие от UserNotificationListener."""
    got = pyqtSignal(str, str, str, str, object)   # приложение, заголовок, текст, значок, (r,g,b)
    SQL = ("SELECT n.Id, n.Payload, h.PrimaryId FROM Notification n LEFT JOIN NotificationHandler h "
           "ON n.HandlerId = h.RecordId WHERE n.Type = 'toast' AND n.Id > ? ORDER BY n.Id")
    def __init__(self, settings):
        super().__init__()
        self.settings = settings; self._stop = False; self._errs = 0
        self.db = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Notifications", "wpndatabase.db")
        if os.path.exists(self.db): threading.Thread(target=self._run, daemon=True).start()
        else: log_error("notify: wpndatabase.db не найден")

    def _query(self, last):
        def q(target, uri):
            con = sqlite3.connect(target, uri=uri, timeout=1.0)
            try: return con.execute(self.SQL, (last,)).fetchall()
            finally: con.close()
        try: return q(Path(self.db).as_uri() + "?mode=ro", True)
        except Exception:
            tmp = tempfile.mkdtemp()
            try:
                for suf in ("", "-wal", "-shm"):
                    if os.path.exists(self.db + suf): shutil.copy2(self.db + suf, os.path.join(tmp, "w.db" + suf))
                return q(os.path.join(tmp, "w.db"), False)
            finally: shutil.rmtree(tmp, ignore_errors=True)

    def _run(self):
        last = None
        while not self._stop:
            try:
                if not self.settings.value("notif_msgr", True, type=bool):
                    last = None; time.sleep(2.0); continue
                rows = self._query(last if last is not None else 0)
                if last is None: last = rows[-1][0] if rows else 0     # старые уведомления не показываем
                else:
                    for rid, payload, pid in rows:
                        last = max(last, rid)
                        try: self._handle(payload, pid)
                        except Exception as e: log_error(f"notify parse: {e}")
                self._errs = 0
            except Exception as e:
                self._errs += 1
                if self._errs in (1, 20): log_error(f"notify db: {e}")
            time.sleep(1.2)

    def _handle(self, payload, pid):
        if isinstance(payload, (bytes, bytearray)):
            s = bytes(payload).decode("utf-8", "ignore")
            if "\x00" in s: s = bytes(payload).decode("utf-16", "ignore")
        else: s = str(payload or "")
        s = s.strip().lstrip("\ufeff")
        if not s: return
        root = ET.fromstring(s)
        texts = [t.text.strip() for t in root.iter("text") if t.text and t.text.strip() and t.get("placement") != "attribution"]
        if not texts: return
        pid = str(pid or ""); low = pid.lower(); app = icon = None; col = None
        for key, name, ic, c in MESSENGERS:
            if key in low: app, icon, col = name, ic, c; break
        if app is None:      # уведомление из браузера: сайт указан в тексте/атрибуции/ссылке запуска
            sl = s.lower()
            for dom, name in WEB_SITES:
                if dom in sl:
                    ex = WEB_EXTRA.get(name) or next(((ic, c) for k, n, ic, c in MESSENGERS if n == name), ("🌐", (120, 140, 255)))
                    app, icon, col = name + " Web", ex[0], ex[1]; break
        if app is None:
            if not self.settings.value("notif_msgr_all", False, type=bool): return
            app = pid.split("!")[0].split("_")[0].split(".")[-1] or "Windows"; icon = "🔔"
        title = texts[0]; body = " ".join(texts[1:])
        self.got.emit(app, title, body, icon, col)


class InputStateWatcher(QObject):
    """Отслеживает Caps Lock и язык активной раскладки Windows без перехвата клавиш."""
    changed = pyqtSignal(str, str)  # kind, label
    LANGS = {
        0x0409: "ENG · США", 0x0809: "ENG · UK", 0x0419: "РУС",
        0x0407: "DEU", 0x040C: "FRA", 0x0410: "ITA",
        0x0C0A: "ESP", 0x0416: "PT-BR", 0x0411: "日本語",
        0x0804: "中文", 0x0412: "한국어", 0x040A: "ESP",
    }
    def __init__(self):
        super().__init__()
        self._stop = threading.Event()
        threading.Thread(target=self._run, name="InputStateWatcher", daemon=True).start()
    @classmethod
    def _snapshot(cls):
        try:
            u = ctypes.windll.user32
            caps = bool(u.GetKeyState(0x14) & 1)
            hwnd = u.GetForegroundWindow()
            tid = u.GetWindowThreadProcessId(hwnd, None) if hwnd else 0
            hkl = u.GetKeyboardLayout(tid) if tid else u.GetKeyboardLayout(0)
            lang_id = int(hkl) & 0xFFFF
            return caps, cls.LANGS.get(lang_id, f"ЯЗЫК · {lang_id:04X}")
        except Exception:
            return None, None
    def _run(self):
        previous = self._snapshot()
        while not self._stop.wait(0.16):
            current = self._snapshot()
            if current[0] is not None and previous[0] is not None and current[0] != previous[0]:
                self.changed.emit("caps", "ВКЛ" if current[0] else "ВЫКЛ")
            if current[1] and previous[1] and current[1] != previous[1]:
                self.changed.emit("language", current[1])
            previous = current
    def stop(self):
        self._stop.set()


class GpuMonitor:
    """Загрузка видеокарты. NVIDIA — через nvidia-smi (ещё температура и память); остальные — счётчики Windows (GPUEngine)."""
    def __init__(self):
        self.load = 0.0; self.temp = None; self.vram = None; self.name = ""; self.ok = False; self.want = False
        self._smi = shutil.which("nvidia-smi")
        if not self._smi:
            for pth in (r"C:\Windows\System32\nvidia-smi.exe", r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"):
                if os.path.exists(pth): self._smi = pth; break
        self._err = 0
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while True:
            if not self.want: time.sleep(0.5); continue
            try:
                if not (self._smi and self._nv()): self._wmi()
                self._err = 0
            except Exception as e:
                self._err += 1
                if self._err in (1, 30): log_error(f"gpu: {e}")
                self.ok = False; time.sleep(2.0)
            time.sleep(1.2)

    def _nv(self):
        try:
            out = subprocess.check_output([self._smi, "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,name", "--format=csv,noheader,nounits"],
                                          creationflags=0x08000000, timeout=4).decode("utf-8", "ignore")
            parts = [x.strip() for x in out.strip().splitlines()[0].split(",")]
            self.load = float(parts[0]); self.temp = float(parts[1]); self.vram = (float(parts[2]) / 1024.0, float(parts[3]) / 1024.0)
            self.name = parts[4]; self.ok = True; return True
        except Exception as e:
            log_error(f"nvidia-smi: {e}"); self._smi = None; return False

    def _wmi(self):
        cmd = "Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine | Select-Object Name,UtilizationPercentage | ConvertTo-Json -Compress"
        out = subprocess.check_output(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], creationflags=0x08000000, timeout=10).decode("utf-8", "ignore")
        data = json.loads(out) if out.strip() else []
        if isinstance(data, dict): data = [data]
        groups = {}
        for r in data:
            m = re.search(r"engtype_(\w+)", str(r.get("Name", ""))); k = m.group(1) if m else "x"
            groups[k] = groups.get(k, 0.0) + float(r.get("UtilizationPercentage") or 0)
        self.load = min(100.0, max(groups.values())) if groups else 0.0
        self.temp = None; self.vram = None; self.ok = True


# ═══════════ Загрузки из браузеров ═══════════
PARTIAL_EXT = (".crdownload", ".part", ".opdownload", ".download", ".partial")
SHELF_MAX = 12

def _downloads_dir(settings):
    try:
        c = str(settings.value("dl_folder", "") or "").strip()
        if c and os.path.isdir(c): return c
    except Exception: pass
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        v, _ = winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}"); v = os.path.expandvars(v)
        if os.path.isdir(v): return v
    except Exception: pass
    return os.path.join(os.path.expanduser("~"), "Downloads")

def _history_files():
    la = os.environ.get("LOCALAPPDATA", ""); ap = os.environ.get("APPDATA", ""); out = []
    for r in (os.path.join(la, "Google", "Chrome", "User Data"), os.path.join(la, "Microsoft", "Edge", "User Data"),
              os.path.join(la, "BraveSoftware", "Brave-Browser", "User Data"), os.path.join(la, "Yandex", "YandexBrowser", "User Data"),
              os.path.join(la, "Vivaldi", "User Data"), os.path.join(la, "Chromium", "User Data")):
        if not os.path.isdir(r): continue
        try: profs = ["Default"] + [d for d in os.listdir(r) if d.startswith("Profile ")]
        except Exception: profs = ["Default"]
        for pr in profs:
            f = os.path.join(r, pr, "History")
            if os.path.exists(f): out.append(f)
    for r in (os.path.join(ap, "Opera Software", "Opera Stable"), os.path.join(ap, "Opera Software", "Opera GX Stable")):
        f = os.path.join(r, "History")
        if os.path.exists(f): out.append(f)
    return out

class DownloadWatcher(QObject):
    """Следит за папкой загрузок: любой браузер пишет файл во временный .crdownload/.part — по нему видно размер и скорость.
    Настоящее имя и полный размер Chromium-браузеров берутся из их базы истории (копия файла History)."""
    finished = pyqtSignal(str, int, str)    # имя, размер, путь
    RETRY = (0.4, 1.5, 4.0, 8.0, 15.0, 30.0)
    def __init__(self, settings):
        super().__init__()
        self.settings = settings; self.active = {}; self._lock = threading.Lock(); self._ignored = {}; self._final = []
        self._hist = []; self._hist_ts = 0.0; self._errs = 0
        threading.Thread(target=self._run, daemon=True).start()

    def snapshot(self):
        with self._lock: return sorted((dict(v) for v in self.active.values()), key=lambda d: d["start"])

    def _lookup(self, d):
        full = d["path"].lower()
        if time.time() - self._hist_ts > 60: self._hist = _history_files(); self._hist_ts = time.time()
        for hf in self._hist:
            tmp = os.path.join(tempfile.gettempdir(), "di_hist_%d.db" % (abs(hash(hf)) % 100000))
            try:
                shutil.copy2(hf, tmp)
                con = sqlite3.connect(tmp, timeout=1.0)
                try: row = con.execute("SELECT target_path,total_bytes FROM downloads WHERE lower(current_path)=? ORDER BY id DESC LIMIT 1", (full,)).fetchone()
                finally: con.close()
                if row:
                    tp, tot = row
                    with self._lock:
                        if tp: d["final"] = tp; d["name"] = os.path.basename(tp)
                        if tot and tot > 0: d["total"] = int(tot)
                    return True
            except Exception as e:
                self._errs += 1
                if self._errs in (1, 25): log_error(f"download history: {e}")
        return False

    def _find_final(self, d):
        fin = d.get("final")
        try:
            if fin and os.path.exists(fin) and os.path.getmtime(fin) >= d["start"] - 3: return fin
            folder = os.path.dirname(d["path"]); best = None; last = d["last_size"]
            for e in os.scandir(folder):
                if not e.is_file() or e.name.lower().endswith(PARTIAL_EXT): continue
                st = e.stat()
                if st.st_mtime >= d["start"] - 3 and st.st_size >= max(1, last * 0.9):
                    if best is None or st.st_mtime > best[0]: best = (st.st_mtime, e.path)
            return best[1] if best else None
        except Exception: return None

    def _run(self):
        folder = ""; folder_ts = 0.0
        while True:
            try:
                if not self.settings.value("dl_track", True, type=bool):
                    with self._lock: self.active.clear()
                    time.sleep(1.0); continue
                now = time.time()
                if now - folder_ts > 20: folder = _downloads_dir(self.settings); folder_ts = now
                seen = set()
                if os.path.isdir(folder):
                    for e in os.scandir(folder):
                        if not e.is_file() or not e.name.lower().endswith(PARTIAL_EXT): continue
                        try: st = e.stat()
                        except Exception: continue
                        path = e.path; seen.add(path)
                        with self._lock: d = self.active.get(path)
                        if d is None:
                            if now - st.st_mtime > 15 or self._ignored.get(path) == st.st_mtime: continue     # старые «хвосты» не показываем
                            low = e.name
                            for sx in PARTIAL_EXT:
                                if low.lower().endswith(sx): low = low[:-len(sx)]; break
                            d = {"path": path, "start": now, "size": st.st_size, "last_size": st.st_size, "last_t": now, "speed": 0.0, "total": 0,
                                 "name": low, "final": os.path.join(folder, low), "lookups": 0, "next": now + self.RETRY[0], "mtime": st.st_mtime}
                            with self._lock: self.active[path] = d
                        else:
                            dt = now - d["last_t"]
                            if dt >= 0.4:
                                inst = max(0.0, (st.st_size - d["last_size"]) / dt)
                                d["speed"] = d["speed"] * 0.6 + inst * 0.4 if d["speed"] else inst
                                d["last_size"] = st.st_size; d["last_t"] = now
                            d["size"] = st.st_size
                            if st.st_mtime != d["mtime"]: d["mtime"] = st.st_mtime
                        if d["lookups"] < len(self.RETRY) and now >= d["next"] and (d["name"].lower().startswith("unconfirmed") or not d["total"]):
                            self._lookup(d); d["lookups"] += 1
                            d["next"] = now + (self.RETRY[d["lookups"]] if d["lookups"] < len(self.RETRY) else 1e9)
                        if now - d["mtime"] > 90 and d["speed"] < 1:       # давно не растёт — считаем зависшей
                            with self._lock: self.active.pop(path, None)
                            self._ignored[path] = d["mtime"]
                with self._lock: gone = [p for p in self.active if p not in seen]
                for p in gone:
                    with self._lock: d = self.active.pop(p, None)
                    if d: self._final.append((d, now + 4.0))
                keep = []
                for d, deadline in self._final:
                    fp = self._find_final(d)
                    if fp:
                        try: sz = os.path.getsize(fp)
                        except Exception: sz = d["last_size"]
                        self.finished.emit(os.path.basename(fp), int(sz), fp)
                    elif time.time() < deadline: keep.append((d, deadline))
                self._final = keep
            except Exception as e:
                self._errs += 1
                if self._errs in (1, 25): log_error(f"download watcher: {e}")
            time.sleep(0.45)


class ShelfStore:
    """Полка для файлов: хранит ссылки на файлы, лимит SHELF_MAX."""
    def __init__(self, settings):
        self.settings = settings
        try: self.items = json.loads(settings.value("shelf_data", "[]") or "[]")
        except Exception: self.items = []
    def save(self):
        try: self.settings.setValue("shelf_data", json.dumps(self.items, ensure_ascii=False))
        except Exception: pass
    def add(self, paths):
        added = dup = 0; full = False
        have = {os.path.normcase(os.path.normpath(i["path"])) for i in self.items}
        for p in paths:
            if not p or not os.path.exists(p): continue
            k = os.path.normcase(os.path.normpath(p))
            if k in have: dup += 1; continue
            if len(self.items) >= SHELF_MAX: full = True; break
            self.items.append({"path": os.path.normpath(p), "name": os.path.basename(p.rstrip("\\/")) or p, "added": time.strftime("%d.%m %H:%M")})
            have.add(k); added += 1
        if added: self.save()
        return added, dup, full
    def remove(self, idx):
        if 0 <= idx < len(self.items): self.items.pop(idx); self.save()
    def clear(self): self.items = []; self.save()


# ═══════════ Живые активности: микрофон / камера / запись экрана, устройства, Wi-Fi ═══════════
CAP_ROOT = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore"

class PrivacyWatcher:
    """Кто сейчас использует микрофон, камеру или захват экрана — Windows отмечает это в реестре (LastUsedTimeStop == 0)."""
    CAPS = (("mic", "microphone"), ("cam", "webcam"), ("rec", "graphicsCaptureProgrammatic"), ("rec", "graphicsCaptureWithoutBorder"))
    def __init__(self):
        self.active = {}      # вид -> (приложение, время начала, epoch)
        threading.Thread(target=self._run, daemon=True).start()

    @staticmethod
    def _app_name(name):
        n = name.replace("#", "\\").split("\\")[-1]
        return n[:-4] if n.lower().endswith(".exe") else n

    def _scan(self, cap):
        out = []; base = CAP_ROOT + "\\" + cap
        for sub in (base, base + r"\NonPackaged"):
            try: key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub)
            except OSError: continue
            try:
                i = 0
                while True:
                    try: nm = winreg.EnumKey(key, i)
                    except OSError: break
                    i += 1
                    if nm == "NonPackaged" or "python" in nm.lower(): continue
                    try:
                        with winreg.OpenKey(key, nm) as k2:
                            st = winreg.QueryValueEx(k2, "LastUsedTimeStart")[0]; sp = winreg.QueryValueEx(k2, "LastUsedTimeStop")[0]
                    except OSError: continue
                    if st and not sp: out.append((self._app_name(nm), (st - 116444736000000000) / 1e7))
            finally:
                try: winreg.CloseKey(key)
                except Exception: pass
        return out

    def _run(self):
        errs = 0
        while True:
            try:
                act = {}
                for kind, cap in self.CAPS:
                    for app, st in self._scan(cap):
                        if kind not in act or st < act[kind][1]: act[kind] = (app, st)
                self.active = act; errs = 0
            except Exception as e:
                errs += 1
                if errs in (1, 20): log_error(f"privacy: {e}")
            time.sleep(1.5)


class DeviceWatcher(QObject):
    """Смена устройства вывода звука (наушники) и подключение/отключение Wi-Fi."""
    audio = pyqtSignal(str)
    wifi = pyqtSignal(str, bool)
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        threading.Thread(target=self._run, daemon=True).start()

    def _audio_id(self):
        if not HAS_PYCAW: return None
        dev = AudioUtilities.GetSpeakers()
        name = getattr(dev, "FriendlyName", None); did = getattr(dev, "id", None)
        if did is None:
            try: did = str(dev.GetId())
            except Exception: did = None
        return (str(did) if did else None, str(name) if name else "")

    def _ssid(self):
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], creationflags=0x08000000, timeout=5)
        try: txt = out.decode("oem", "ignore")
        except Exception: txt = out.decode("cp866", "ignore")
        m = re.search(r"^\s*SSID\s*:\s*(.+?)\s*$", txt, re.M)
        return m.group(1) if m else ""

    def _run(self):
        try:
            import comtypes; comtypes.CoInitialize()
        except Exception: pass
        last_a = "?"; last_w = None; tick = 0; errs = 0
        while True:
            try:
                if self.settings.value("la_audio", True, type=bool):
                    a = self._audio_id()
                    if a is not None:
                        if last_a != "?" and a[0] != last_a: self.audio.emit(a[1] or "")
                        last_a = a[0]
                if tick % 3 == 0 and self.settings.value("la_wifi", True, type=bool):
                    s = self._ssid()
                    if last_w is not None and s != last_w: self.wifi.emit(s, bool(s))
                    last_w = s
                errs = 0
            except Exception as e:
                errs += 1
                if errs in (1, 30): log_error(f"devices: {e}")
            tick += 1; time.sleep(2.0)


class MixerWatcher:
    """Громкость по приложениям (микшер Windows): список сессий и команды изменения — всё в отдельном потоке с COM."""
    def __init__(self):
        self.apps = []; self.want = False; self._q = queue.Queue()
        threading.Thread(target=self._run, daemon=True).start()

    def set_volume(self, pid, v): self._q.put(("vol", int(pid), max(0.0, min(1.0, float(v)))))
    def set_mute(self, pid, m): self._q.put(("mute", int(pid), bool(m)))

    def _run(self):
        if not HAS_PYCAW: return
        try:
            import comtypes; comtypes.CoInitialize()
        except Exception: pass
        errs = 0
        while True:
            try:
                cmd = None
                try: cmd = self._q.get(timeout=0.25 if self.want else 1.0)
                except queue.Empty: pass
                if not self.want and cmd is None: continue
                sessions = list(AudioUtilities.GetAllSessions())
                while cmd is not None:
                    kind, pid, val = cmd
                    for s in sessions:
                        if (getattr(s, "ProcessId", 0) or 0) != pid: continue
                        try:
                            if kind == "vol": s.SimpleAudioVolume.SetMasterVolume(val, None)
                            else: s.SimpleAudioVolume.SetMute(1 if val else 0, None)
                        except Exception: pass
                    try: cmd = self._q.get_nowait()
                    except queue.Empty: cmd = None
                if not self.want: continue
                apps = {}
                for s in sessions:
                    pid = getattr(s, "ProcessId", 0) or 0
                    try:
                        if getattr(s, "State", 1) == 2: continue
                        sv = s.SimpleAudioVolume; vol = float(sv.GetMasterVolume()); mute = bool(sv.GetMute())
                    except Exception: continue
                    try: peak = float(s.AudioMeterInformation.GetPeakValue())
                    except Exception: peak = 0.0
                    name = exe = ""
                    try:
                        pr = s.Process
                        if pr is not None: name = pr.name(); exe = pr.exe()
                    except Exception: pass
                    if pid == 0: name = "Системные звуки"
                    a = apps.get(pid)
                    if a is None: apps[pid] = {"pid": pid, "name": name, "exe": exe, "vol": vol, "mute": mute, "peak": peak}
                    else: a["peak"] = max(a["peak"], peak)
                self.apps = sorted(apps.values(), key=lambda a: (0 if a["peak"] > 0.002 else 1, a["name"].lower()))
                errs = 0
            except Exception as e:
                errs += 1
                if errs in (1, 30): log_error(f"mixer: {e}")
                time.sleep(1.0)


class ClipboardMonitor(QObject):
    changed = pyqtSignal()
    def __init__(self, max_items=20):
        super().__init__()
        self.items = []; self.max_items = max_items
        try:
            QGuiApplication.clipboard().dataChanged.connect(self._on_change)
            QTimer.singleShot(300, self._on_change)
        except Exception as e: log_error(f"clipboard init: {e}")
    def _on_change(self):
        try:
            cb = QGuiApplication.clipboard()
            mime = cb.mimeData()
            if mime.hasImage():
                img = cb.image()
                if not img.isNull():
                    for it in self.items[:3]:
                        if it.get("type") == "image" and it.get("size") == (img.width(), img.height()): return
                    self.items.insert(0, {"type": "image", "image": img.copy(),
                                          "size": (img.width(), img.height()),
                                          "preview": f"Изображение {img.width()}×{img.height()}",
                                          "time": datetime.datetime.now().strftime("%H:%M")})
                    if len(self.items) > self.max_items: self.items = self.items[:self.max_items]
                    self.changed.emit(); return
            text = cb.text()
            if text:
                for it in self.items[:3]:
                    if it.get("type") == "text" and it.get("data") == text: return
                self.items.insert(0, {"type": "text", "data": text,
                                      "preview": text.replace('\n',' ').strip()[:160],
                                      "time": datetime.datetime.now().strftime("%H:%M")})
                if len(self.items) > self.max_items: self.items = self.items[:self.max_items]
                self.changed.emit()
        except Exception as e: log_error(f"clipboard: {e}")
    def to_clipboard(self, item):
        try:
            cb = QGuiApplication.clipboard()
            if item.get("type") == "image": cb.setImage(item["image"])
            else: cb.setText(item["data"])
        except: pass
    def remove(self, idx):
        try:
            if 0 <= idx < len(self.items): self.items.pop(idx); self.changed.emit()
        except: pass
    def clear(self):
        self.items = []; self.changed.emit()

class NotesStore(QObject):
    changed = pyqtSignal()
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        try:
            raw = settings.value("notes_data", "[]")
            if isinstance(raw, str): self.items = json.loads(raw) if raw else []
            else: self.items = raw if isinstance(raw, list) else []
            if not isinstance(self.items, list): self.items = []
            # Сохраняем старые заметки с полями title/text и отбрасываем только повреждённые записи.
            self.items = [n for n in self.items if isinstance(n, dict) and
                          isinstance(n.get("text", ""), str) and isinstance(n.get("title", ""), str)]
        except Exception as e:
            log_error(f"notes load: {e}"); self.items = []
    def save(self):
        try: self.settings.setValue("notes_data", json.dumps(self.items, ensure_ascii=False))
        except: pass
        self.changed.emit()
    def add(self, text, title=""):
        text = str(text or "").strip(); title = str(title or "").strip()
        if not text and not title: return
        self.items.insert(0, {"title": title, "text": text, "time": datetime.datetime.now().strftime("%d.%m %H:%M")})
        log_error(f"note added total={len(self.items)}")
        self.save()
    def remove(self, idx):
        if 0 <= idx < len(self.items): self.items.pop(idx); self.save()
    def update(self, idx, text, title=None):
        if 0 <= idx < len(self.items):
            text = str(text or "").strip(); title = self.items[idx].get("title", "") if title is None else str(title or "").strip()
            if not text and not title: return
            self.items[idx]["text"] = text; self.items[idx]["title"] = title
            self.items[idx]["time"] = datetime.datetime.now().strftime("%d.%m %H:%M")
            self.save()
    def set_color(self, idx, color):
        """Цвет заметки; None означает нейтральный цвет без метки."""
        if 0 <= idx < len(self.items):
            if color is None:
                self.items[idx].pop("color", None)
            elif isinstance(color, str):
                self.items[idx]["color"] = color
            else:
                self.items[idx]["color"] = max(0, min(8, int(color)))
            self.save()
    def toggle_pin(self, idx):
        if 0 <= idx < len(self.items):
            self.items[idx]["pin"] = not bool(self.items[idx].get("pin", False))
            self.save()

class RemindersStore(QObject):
    """Напоминания по дате и времени. Элемент: {id, date 'YYYY-MM-DD', time 'HH:MM' или '' (весь день → 09:00), text, fired}."""
    changed = pyqtSignal()
    DEFAULT_TIME = "09:00"
    def __init__(self, settings):
        super().__init__()
        self.settings = settings; self.items = []
        try:
            raw = settings.value("reminders_v2", "")
            if raw:
                self.items = json.loads(raw) if isinstance(raw, str) else []
            else:        # перенос старых напоминаний «одно на день»
                old = settings.value("reminders_data", "{}"); od = json.loads(old) if isinstance(old, str) and old else {}
                if isinstance(od, dict):
                    for i, (dk, tx) in enumerate(od.items()):
                        if tx: self.items.append({"id": f"old{i}", "date": dk, "time": "", "text": str(tx), "fired": dk < datetime.date.today().strftime("%Y-%m-%d")})
                    if self.items: self.save()
        except Exception as e:
            log_error(f"reminders load: {e}"); self.items = []
        if not isinstance(self.items, list): self.items = []

    def save(self):
        try: self.settings.setValue("reminders_v2", json.dumps(self.items, ensure_ascii=False))
        except Exception: pass
        self.changed.emit()

    @staticmethod
    def _norm_time(tm):
        tm = (tm or "").strip().replace(".", ":")
        if not tm: return ""
        m = re.fullmatch(r"(\d{1,2}):?(\d{2})?", tm)
        if not m: return None
        h = int(m.group(1)); mi = int(m.group(2) or 0)
        return f"{h:02d}:{mi:02d}" if 0 <= h < 24 and 0 <= mi < 60 else None

    def add(self, date_key, tm, text):
        text = (text or "").strip(); t = self._norm_time(tm)
        if not text or t is None: return None
        it = {"id": f"{int(time.time() * 1000)}{len(self.items)}", "date": date_key, "time": t, "text": text[:100], "fired": False}
        self.items.append(it); self.save(); return it

    def remove_id(self, rid):
        n = len(self.items); self.items = [i for i in self.items if i.get("id") != rid]
        if len(self.items) != n: self.save()

    def remove(self, date_key):
        n = len(self.items); self.items = [i for i in self.items if i.get("date") != date_key]
        if len(self.items) != n: self.save()

    def for_date(self, date_key):
        return sorted((i for i in self.items if i.get("date") == date_key), key=lambda i: (i.get("time") or self.DEFAULT_TIME, i.get("id", "")))

    def has(self, date_key): return any(i.get("date") == date_key for i in self.items)
    def get(self, date_key): return "; ".join(i["text"] for i in self.for_date(date_key))

    def _when(self, it):
        try: return datetime.datetime.strptime(it["date"] + " " + (it.get("time") or self.DEFAULT_TIME), "%Y-%m-%d %H:%M")
        except Exception: return None

    def due(self, now):
        out = []; changed = False
        for it in self.items:
            if it.get("fired"): continue
            w = self._when(it)
            if w is None: it["fired"] = True; changed = True; continue
            if w <= now:
                if (now - w).total_seconds() > 36 * 3600: it["fired"] = True; changed = True      # слишком старое — молча закрываем
                else: out.append(it)
        if changed: self.save()
        return out

    def mark_fired(self, rid):
        for it in self.items:
            if it.get("id") == rid: it["fired"] = True
        self.save()

    def snooze(self, rid, minutes):
        for it in self.items:
            if it.get("id") == rid:
                w = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
                self.add(w.strftime("%Y-%m-%d"), w.strftime("%H:%M"), it.get("text", "")); return

    def next_today(self, now):
        best = None; today = now.strftime("%Y-%m-%d")
        for it in self.items:
            if it.get("fired") or it.get("date") != today: continue
            w = self._when(it)
            if w is not None and (best is None or w < best[0]): best = (w, it)
        return best[1] if best else None