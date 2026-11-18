# -*- coding: utf-8 -*-
"""GitHub Releases updater for DynamicIsland."""
import os, sys, json, tempfile, zipfile, subprocess, urllib.request
from PyQt6.QtCore import QObject, QThread, pyqtSignal

UPDATE_REPO = "Ilya4566/DynamicIsland-Updates"
CURRENT_VERSION = "0.2.6"
API_URL = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"


def _version_tuple(value):
    parts = []
    for part in str(value).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple((parts + [0, 0, 0, 0])[:4])


class _Worker(QThread):
    checked = pyqtSignal(dict)
    progress = pyqtSignal(int, int, int, str)
    installed = pyqtSignal(str)

    def __init__(self, mode, parent=None, url=None, app_path=None, manual=False):
        super().__init__(parent)
        self.mode, self.url, self.app_path, self.manual = mode, url, app_path, manual

    def _request(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "DynamicIsland-Updater/0.2.6", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()

    def run(self):
        if self.mode == "check":
            try:
                data = json.loads(self._request(API_URL).decode("utf-8"))
                tag = data.get("tag_name", "")
                version = tag.lstrip("vV")
                asset = next((a for a in data.get("assets", []) if a.get("name", "").lower().endswith(".zip")), None)
                if not asset or not asset.get("browser_download_url"):
                    raise RuntimeError("В последнем GitHub-релизе не найден ZIP-файл обновления")
                available = _version_tuple(version) > _version_tuple(CURRENT_VERSION)
                self.checked.emit({"ok": True, "manual": self.manual, "available": available,
                                   "version": version, "url": asset["browser_download_url"],
                                   "notes": data.get("body", "")})
            except Exception as exc:
                self.checked.emit({"ok": False, "manual": self.manual, "error": f"{type(exc).__name__}: {exc}"})
            return
        archive_path = None
        try:
            if not self.url or not self.app_path:
                raise RuntimeError("Не задан адрес архива или путь приложения")
            folder = os.path.dirname(os.path.abspath(self.app_path))
            self.progress.emit(0, 0, 0, "Подключаюсь к серверу обновлений")
            req = urllib.request.Request(self.url, headers={"User-Agent": "DynamicIsland-Updater/0.2.6"})
            with urllib.request.urlopen(req, timeout=60) as response:
                total = int(response.headers.get("Content-Length", "0") or 0)
                fd, archive_path = tempfile.mkstemp(prefix="dynamicisland_update_", suffix=".zip", dir=folder)
                received = 0
                with os.fdopen(fd, "wb") as out:
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk: break
                        out.write(chunk); received += len(chunk)
                        pct = int(received * 100 / total) if total else 0
                        self.progress.emit(min(99, pct), received, total, "Скачиваю обновление")
            self.progress.emit(100, received, total, "Проверяю архив обновления")
            with zipfile.ZipFile(archive_path, "r") as zf:
                bad = zf.testzip()
                names = {os.path.basename(n).lower() for n in zf.namelist() if not n.endswith("/")}
                if bad: raise RuntimeError(f"Архив повреждён: {bad}")
                required = {"island.pyw", "core.py", "update_client.py", "update_apply.py"}
                if not required.issubset(names):
                    raise RuntimeError("В архиве отсутствуют обязательные файлы приложения")
            apply_path = os.path.join(folder, "update_apply.py")
            if not os.path.isfile(apply_path):
                raise RuntimeError("Не найден update_apply.py рядом с приложением")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
            subprocess.Popen([sys.executable, apply_path, str(os.getpid()), archive_path, os.path.abspath(self.app_path)],
                             cwd=folder, creationflags=flags, close_fds=True)
            self.installed.emit("Загрузка завершена. Закрываю приложение и запускаю установщик…")
        except Exception as exc:
            self.installed.emit(f"Ошибка обновления: {type(exc).__name__}: {exc}")
            if archive_path:
                try: os.remove(archive_path)
                except OSError: pass


class UpdateManager(QObject):
    checked = pyqtSignal(dict)
    progress = pyqtSignal(int, int, int, str)
    installed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers = []

    def _start(self, worker):
        self._workers.append(worker)
        worker.checked.connect(self.checked.emit)
        worker.progress.connect(self.progress.emit)
        worker.installed.connect(self.installed.emit)
        worker.finished.connect(lambda w=worker: self._cleanup(w))
        worker.start()

    def _cleanup(self, worker):
        try: self._workers.remove(worker)
        except ValueError: pass
        worker.deleteLater()

    def check(self, manual=False):
        self._start(_Worker("check", self, manual=manual))

    def install(self, url, app_path):
        self._start(_Worker("install", self, url=url, app_path=app_path))
